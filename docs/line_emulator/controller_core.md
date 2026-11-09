# Ядро Modbus/Doypack (`core/controller/`)

| Параметр | Значение |
|----------|----------|
| Версия проекта | `client_info.VERSION` (актуально `1.0.0.1.b0013`) |
| Контекст приложения | эмулятор линии — см. [line_emulator.md](line_emulator.md) |
| Зависимость Modbus | `pymodbus==3.12.1` (`requirements.txt`) |

Назначение: асинхронный TCP-сервер Modbus (карточка контроллера) и клиентская эмуляция очереди Doypack поверх регистров. Документ описывает **устройство модулей и контракты**, без пользовательских инструкций.

## Расположение пакета

| Путь | Содержание |
|------|------------|
| `core/controller/__init__.py` | Пакет без re-export; подмодули импортируются явно (`modbus_server`, `doypack`, `data`, `dmc_modbus`, …). |
| `core/controller/modbus_server.py` | `ModbusEmulator` — `ModbusTcpServer`, datastore, жизненный цикл `start` / `stop`. |
| `core/controller/doypack.py` | `DoypackEmulation` — фоновый цикл опроса/записи регистров через `DmcModbusBase`. |
| `core/controller/dmc_modbus/base.py` | `DmcModbusBase` — тонкий async-прокси к `AsyncModbusTcpClient`. |
| `core/controller/dmc_modbus/helpers.py` | `get_modbus(addr)` — разбор строки `host:port` / `[IPv6]:port` и фабрика клиента. |
| `core/controller/dmc_modbus/exceptions.py` | `LineControllerException` — ошибки разбора адреса и сценариев контроллера. |
| `core/controller/data.py` | Конфигурация контроллера (`ControllerConfig` и связанные модели), в т.ч. домен `queue_size`. |
| `core/controller/runtime.py` | `ControllerRuntime` — отдельный поток, свой asyncio-цикл, оркестрация `ModbusEmulator` + `DoypackEmulation` (синхронный API для UI). |
| `core/controller/controller_widget.py` | `ControllerWidget` — Qt-карточка контроллера (поля, R/S, удаление); подробнее — [controller_widget.md](controller_widget.md). |

Реэкспорт удобных имён: `core/controller/dmc_modbus/__init__.py` (`DmcModbusBase`, `get_modbus`, `LineControllerException`).

## `ControllerRuntime` (`runtime.py`)

Класс **`ControllerRuntime`** поднимает **`ModbusEmulator`** и **`DoypackEmulation`** на **выделенном потоке** с **отдельным** `asyncio` event loop. Публичные **`start()`** / **`stop()`** — **синхронные**, их можно вызывать из потока UI (например Qt); внутри модуля Qt не используется (регрессия: в `runtime.py` нет импорта `qasync` — см. тесты).

### Поток и синхронизация

- Воркер — **`threading.Thread(..., name=f"controller-{port}", daemon=False)`** (не демон).
- **`_start_lock`** сериализует только **`start()`** в паре с **`_state_lock`**, чтобы два параллельных вызова не проходили проверку «уже запущено» до назначения `_thread`.
- **`_state_lock`** защищает ссылки на поток, цикл, экземпляры Modbus/Doypack и порт.

### Старт: проверка порта, бюджет 5 с, порядок Modbus → Doypack, откат

- Перед созданием потока вызывается **`_assert_listen_port_available(port)`**: убедиться, что на loopback порт ещё не принимает соединения «чужим» слушателем, и что привязка к **`0.0.0.0:{port}`** возможна (на Windows дополнительно пробуется **`SO_EXCLUSIVEADDRUSE`** для типичного случая «порт занят»).
- Внутри воркера **`ModbusEmulator(host="0.0.0.0", port=port)`** и **`DoypackEmulation(f"127.0.0.1:{port}", …)`**; подъём — **`await modbus.start()`**, затем **`await doypack.start()`**. Весь блок обёрнут в **`asyncio.wait_for(..., timeout=5.0)`** — при превышении бюджета или исключении выполняется **откат**: **`await doypack.stop()`** (если объект создан), затем **`await modbus.stop()`** (если создан), затем слив задач и закрытие цикла.
- Готовность наружу передаётся через **`concurrent.futures.Future`**; вызывающий поток ждёт **`ready.result(timeout=5.0)`**. При таймауте готовности или ошибке старта воркер дополнительно **дожимается** `join` (до ~65 с); ссылки очищаются, если поток завершился.
- **`queue_size`** — только **`int`** в диапазоне **1..1000** (как у `DoypackEmulation` / `ControllerConfig`); иначе **`ValueError`** до запуска потока.

### Остановка: порядок Doypack → Modbus, планирование в цикле воркера, join, проверка порта

- **`stop()`** идемпотентен: нет потока — выход; поток уже мёртв — очистка ссылок.
- Остановка на цикле воркера: корутина планируется через **`asyncio.run_coroutine_threadsafe`**; внутри последовательно **`await doypack.stop()`**, **`await modbus.stop()`**, затем **`loop.call_soon_threadsafe(loop.stop)`** для выхода из **`run_forever`**. Ожидание завершения корутины — **`fut.result(timeout=60.0)`**; при сбое — попытка остановить цикл извне и запись ERROR в лог.
- После этого **`thread.join(timeout=5.0)`**. Если join успешен, вызывается **`_wait_bind_free`** (до ~2 с) и проверка **`_can_bind_port`**; если порт всё ещё занят — ERROR в лог (ссылки при неуспешном join могут сохраняться — см. код).
- Если цикл недоступен/закрыт, но поток ещё жив — ограниченный **`join`** без `run_coroutine_threadsafe`.

### Чтение holding: `read_holding_registers`

Синхронный метод **`read_holding_registers(addresses)`** предназначен для потока UI (например Qt): значения читаются **на цикле воркера** через **`asyncio.run_coroutine_threadsafe`**, результат возвращается вызывающему потоку через **`concurrent.futures.Future.result(timeout=0.25)`**.

- **Источник данных:** для каждого валидного адреса вызывается **`ModbusEmulator.get_holding_register`** — прямое чтение **локального datastore** TCP-сервера (`context[0].getValues(3, …)` в `modbus_server.py`). Отдельный Modbus-клиент в **`runtime.py`** не создаётся (в т.ч. нет импорта **`AsyncModbusTcpClient`**).
- **Почему не через Doypack-клиент:** эмуляция Doypack (`DoypackEmulation` / `DmcModbusBase`) — это **тот же** сервер по loopback, но отдельный асинхронный путь опроса/записи очереди. Для «снимка» регистров UI достаточно **одного** обращения к datastore сервера; это не дублирует TCP-трафик внешнего клиента и не завязано на цикл Doypack / `get_status`.
- **Валидация адресов:** только целые **`int`**, **`bool` отклоняется**; диапазон **0…10000 включительно** (согласован с допустимой верхней границей holding в datastore, см. `ModbusEmulator`). Вне домена — **`None`** для соответствующего элемента, без записи в память.
- **Таймаут и ошибки:** на **весь** запрос отведено **0.25 с**; при **`concurrent.futures.TimeoutError`**, сбое планирования корутины, исключении внутри `get_holding_register` или если рантайм **не запущен** / **остановлен** / цикл **недоступен** — для затронутых позиций или всего списка возвращаются **`None`** (пустой входной список → **`[]`**). Диагностика — **DEBUG** в лог **`CTL`**.
- **Тесты:** `tests/test_core/test_controller_runtime.py` — класс **`TestControllerRuntimeReadHoldingRegisters`** (внешний клиент пишет регистры, чтение через рантайм; пустой список; до `start` и после `stop`).

### Чтение holding и coil: `read_points`

Синхронный метод **`read_points(points)`** предназначен для потока UI: за **один** вызов читается упорядоченный список точек **`Sequence[tuple[str, int]]`** — каждый элемент **`("holding", address)`** или **`("coil", address)`**. Работа планируется **на цикле воркера** через **`asyncio.run_coroutine_threadsafe`**, итог возвращается вызывающему потоку через **`concurrent.futures.Future.result(timeout=0.25)`** (тот же бюджет, что у **`read_holding_registers`**).

- **Источник данных:** для валидных holding — **`ModbusEmulator.get_holding_register`** (локальный datastore TCP-сервера); для валидных coil — **`ModbusEmulator.get_coil`** (`context[0].getValues(1, …)` в `modbus_server.py`). Отдельный Modbus-клиент в **`runtime.py`** по-прежнему **не** создаётся; **`DoypackEmulation.get_status`** и второй TCP-путь не используются — снимок идёт напрямую в datastore сервера на том же цикле, что Modbus/Doypack.
- **Валидация по слоту:** первый элемент кортежа должен быть строкой **`"holding"`** или **`"coil"`** (иные теги, например `"discrete"`, дают **`None`** без обращения к datastore). Адрес — только целый **`int`**, **`bool` отклоняется**. Holding: **0…10000** включительно (верхняя граница datastore, см. комментарий в `runtime.py`: `holding_registers_size - 2`). Coil: **0…5000** включительно (`coils_size - 2`). Вне домена — **`None`** для этого слота.
- **Типы в ответе:** успешное holding — **`int`** (через `int(...)`, не **`bool`**); успешное coil — **`bool`**. Порядок результатов совпадает с порядком **`points`**; пустой вход → **`[]`**.
- **Ошибки одной точки:** исключение внутри `get_holding_register` / `get_coil` для одной точки — **DEBUG** в лог **`CTL`**, слот **`None`**, остальные точки в том же вызове читаются дальше.
- **Таймаут и сбой всего запроса:** на **весь** вызов отведено **0.25 с**; при **`concurrent.futures.TimeoutError`**, сбое планирования корутины, прочем исключении **`fut.result`** или если рантайм **не запущен** / поток мёртв / цикл **недоступен** — **`[None] * n`** для непустого списка (как у остановленного **`read_holding_registers`**).
- **Связь с `read_holding_registers`:** сигнатура и поведение **`read_holding_registers(addresses)`** **не менялись** (только holding, тот же каркас threadsafe и таймаут). Для смешанных holding/coil и одного round-trip UI предназначен **`read_points`**; legacy-вызовы только по списку адресов holding по-прежнему используют **`read_holding_registers`**.
- **Тесты:** `tests/test_core/test_controller_runtime.py` — класс **`TestControllerRuntimeReadPoints`** (внешний клиент задаёт holding/coil; границы 5000/10000 и 5001/10001; пустой список; до `start` и после `stop`; невалидный kind; наблюдение за циклом Doypack: запись **1** в holding **4146** снаружи, в течение **3 с** чтение **`[3]`**).

### Запись holding и coil: `write_point`

Синхронный метод **`write_point(kind, address, value)`** предназначен для потока UI: за **один** вызов в **локальный datastore** TCP-сервера записывается одна точка — holding или coil. Работа планируется **на цикле воркера** одной корутиной через **`asyncio.run_coroutine_threadsafe`**, итог возвращается вызывающему потоку как **`bool`** через **`concurrent.futures.Future.result(timeout=0.25)`** (тот же бюджет **0.25 с**, что у чтения).

- **Источник записи:** на цикле вызываются **`ModbusEmulator.update_holding_register(address, int)`** и **`ModbusEmulator.update_coil(address, bool)`** (`modbus_server.py`) — прямая запись в datastore сервера, без второго Modbus-клиента и без TCP loopback. Импорт **`AsyncModbusTcpClient`** в **`runtime.py`** по-прежнему отсутствует.
- **Сигнатура:** `write_point(self, kind: str, address: int, value: int | bool) -> bool`. Один вызов = одна корутина; пакетов точек и слияния с тиком **`read_points`** нет.
- **Валидация holding:** `kind == "holding"` — адрес только целый **`int`**, **`bool` отклоняется**, диапазон **0…10000** включительно (как у **`read_points`**). Значение — только целый **`int`**, **не `bool`**, диапазон **0…65535** (16-битный регистр Modbus; верхняя граница **значения** не совпадает с верхней границей **адреса** holding). При невалидных аргументах — **`False`**, **`update_holding_register`** не вызывается, исключение наружу **не** бросается.
- **Валидация coil:** `kind == "coil"` — адрес **`int`**, не **`bool`**, **0…5000** включительно. Значение — **только `bool`** (`type(value) is bool`); целые **`0`** / **`1`** отклоняются (виджет преобразует числовой ввод в `bool` до вызова). Иначе **`False`**, **`update_coil`** не вызывается.
- **Иной `kind`** (например `"discrete"`) или невалидный адрес/`value` — **`False`**, datastore не меняется; без DEBUG-лога (как для невалидного адреса в **`read_points`**).
- **Успех и ошибки на цикле:** **`True`** только если запись на воркере завершилась. Исключение внутри **`update_*`** — **DEBUG** в лог **`CTL`** (без traceback), **`False`**. Рантайм **не запущен**, поток мёртв, цикл **закрыт**, **`modbus is None`**, сбой планирования корутины, **`concurrent.futures.TimeoutError`**, прочее исключение **`fut.result`** — **DEBUG** (`schedule failed` / `timed out after 0.25s` / `result failed`), **`False`**.
- **Связь с `read_points` / `read_holding_registers`:** сигнатуры и поведение методов чтения **не менялись**. Запись в holding очереди Doypack (например **4146** при Delta) **разрешена**; следующий шаг цикла **`DoypackEmulation`** может перезаписать регистр — это ожидаемо, критерий успеха — возврат **`True`**, а не удержание значения.
- **Тесты:** `tests/test_core/test_controller_runtime.py` — класс **`TestControllerRuntimeWritePoint`** (запись holding/coil, границы значения и адреса, отклонение `bool` как holding-значения и `0`/`1` как coil-значения, невалидный `kind`, до `start` и после `stop`; внешний клиент читает тот же datastore после записи holding).

## `ModbusEmulator` (`modbus_server.py`)

- **Привязка:** по умолчанию `host="0.0.0.0"` (слушать на всех IPv4-интерфейсах), `port=5020`, `slave_id=1` (идентификатор устройства для логов и возможной маршрутизации; контекст сервера собирается в режиме single-device, в тестах клиент часто использует `device_id=0`).
- **Версия стека:** цикл жизни рассчитан на **pymodbus 3.12** (`ModbusTcpServer`, `serve_forever`, `shutdown`, `is_active`).
- **Datastore:** размеры блоков задаются так, чтобы при нумерации pymodbus 3.x (смещение `address + 1` внутри `ModbusDeviceContext`) были допустимы обращения к coil `5000` и holding `10000` (см. комментарии и приёмочные тесты в `tests/test_core/test_controller_modbus.py`). Начальные значения в `setup_datastore` задаются картами Modbus-адресов `coils` / `holding_registers`; вне диапазона — предупреждение в лог, значение пропускается.

### Жизненный цикл

1. **`start(initial_values=None)`** — строит datastore, создаёт `ModbusTcpServer(..., address=(host, port))`, поднимает `asyncio`-задачу с `serve_forever()`. До **5 с** опрашивает `is_active()`; при раннем падении задачи или таймауте — откат через `stop()` (где применимо), `RuntimeError` наружу.
2. **`stop()`** — вызывает **`await server.shutdown()`** на экземпляре сервера, затем ожидает завершения задачи `serve_forever` (с таймаутом и отменой при необходимости). Состояние `_server`, `_serve_task`, `context` сбрасывается.

### Почему не «глобальная» остановка pymodbus (`ServerStop`)

Для корректной работы **нескольких** эмуляторов на разных портах остановка должна идти через **`shutdown()` конкретного `ModbusTcpServer`**. Глобальные остановщики уровня процесса (в терминологии pymodbus — условный `ServerStop`, останавливающий «последний» активный сервер) не используются: они привязаны к одному глобальному состоянию и могут мешать соседним экземплярам. Эмулятор линии опирается на **пер-экземплярный** `shutdown` + ожидание задачи.

Синхронные методы чтения/записи datastore (`update_coil`, `get_holding_register`, …) требуют предварительного `start()` или `setup_datastore()`; иначе `RuntimeError`.

## `DoypackEmulation` (`doypack.py`)

Подключение к уже поднятому Modbus TCP (например к `ModbusEmulator` на loopback) через строку `ip` в формате `host:port` (разбор — `get_modbus`).

### Очередь: формула и границы регистров

- **`queue_size`:** только целое `int` в диапазоне **1..1000** (тот же домен, что у `ControllerConfig.queue_size` в `core/controller/data.py`). Иначе `ValueError`.
- **Шаг слота:** `step = 2` при `duplex=True`, иначе `step = 1`.
- **Граница очереди:** `q_end = q_start + (queue_size + 1) * step`.

Базовые адреса (holding), в зависимости от режима ПЛК:

| Режим | `q_start` | `can_start_work` (coil) |
|-------|-----------|-------------------------|
| Xinje (`xinje=True`) | `20` | `11` |
| Delta (`xinje=False`) | `4146` | `2567` |

Фоновый цикл `_run` перебирает адреса от `q_start` до `q_end` с шагом `step`; на каждом шаге `_step_queue_iteration`: сброс coil «можно начинать работу», чтение holding, запись кода статуса (3 или 4), пауза 0.1 с. Запуск/остановка: `start()` / `stop()`; контекстный менеджер вызывает их в `__aenter__` / `__aexit__`.

## `get_modbus` (`dmc_modbus/helpers.py`)

Строка `addr` после `strip()`:

- Обязательно наличие **`:`** (разделитель хоста и порта). Без двоеточия — `LineControllerException`.
- **IPv6:** только вид **`[IPv6]:port`** (например `[::1]:5020`). Сырой IPv6 с несколькими `:` без скобок отклоняется как неоднозначный.
- **IPv4 / имя хоста:** `host:port`, разбор через последний `:` (`rsplit`); хост не может быть **пустым** после trim — иначе `LineControllerException`.
- **Порт:** целое число, диапазон **1..65535**; иначе `LineControllerException`.
- Литеральный IP проверяется через `ipaddress.ip_address`; для имён хостов ошибка разбора IP игнорируется — разрешение выполнит клиент при `connect`.

Возвращается `AsyncModbusTcpClient` с `timeout=0.3`, `retries=1`, `name=addr`.

## Логирование (`CTL`)

В `libs/loggers.py` задано **`CONTROLLER_LOGGER = 'CTL'`**.

В модулях ядра контроллера (`modbus_server.py`, `doypack.py`, `dmc_modbus/base.py`) используется **стандартный** `logging.getLogger(CONTROLLER_LOGGER)`, **не** `get_dmc_logger` из `libs/log_data.py`. Это согласованное исключение **плана #1** по линии: единое имя логгера `CTL` для подсистемы контроллера без DMC-обёрток.

## Связанные тесты

- `tests/test_core/test_controller_modbus.py` — сервер, адреса, повторный `start`, `get_modbus`,Datastore.
- `tests/test_core/test_controller_doypack.py` — эмуляция Doypack, валидация очереди.
- `tests/test_core/test_controller_config.py` — модели конфигурации контроллера.
- `tests/test_core/test_controller_runtime.py` — `ControllerRuntime`: жизненный цикл, порты, двойной `start`, порядок остановки Doypack затем Modbus, откат при сбое старта, отсутствие `qasync` в `runtime.py`; **`read_holding_registers`**, **`read_points`** и **`write_point`** (см. разделы выше).

## См. также

- [controller_widget.md](controller_widget.md) — UI-карточка `ControllerWidget` и `forms/ui/Controller.ui`.
- [line_emulator.md](line_emulator.md) — общая карта эмулятора линии.
