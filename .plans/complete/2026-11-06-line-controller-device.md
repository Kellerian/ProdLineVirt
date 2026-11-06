---
title: Карточка «Контроллер» на холсте линии
created: 2026-11-06
updated: 2026-11-06
status: completed
priority: high
estimated_subtasks: 7
---

# Карточка «Контроллер» на холсте линии

## Контекст и цель

В эмулятор производственной линии (`main.py` → `MainLineField`) нужно добавить тип устройства «Контроллер». Он повторяет функциональность отдельного приложения `C:\DmcLineEmulator\ProdLineVirt\ControllerServerEmulator` (Modbus TCP-сервер + цикл Doypack), но живёт как карточка на холсте устройств рядом с принтером, камерой и сканером.

Успех: несколько карточек, у каждой свой порт (по умолчанию с 5020); одна кнопка `tbRun` поднимает сервер на всех интерфейсах и клиент Doypack на `127.0.0.1` этого порта, стоп снимает их в обратном порядке и освобождает порт; настройки пишутся в секцию `controllers` того же JSON, старые файлы без секции открываются; меню «Добавить» и «Управление» (Запустить/Остановить, включая «Всё») знают о контроллерах; в «Очистить данные», перевозчиках и генераторах контроллера нет. Отдельное приложение ControllerServerEmulator не изменяется и не импортируется в runtime. Главный цикл Qt остаётся `QApplication.exec()` — без `qasync`. БД и Alembic не участвуют. `client_info.DB_VERSION` не менять.

Оценка: 2–3 рабочих дня. Стек всех подзадач — **backend** (PySide desktop): `developer` → `code-review` → `tech-writer`.

## Обзор подхода

Код эмулятора копируется в `core/controller/` и адаптируется под логгер линии и отдельный поток `asyncio` на карточку. GUI исходного приложения (две кнопки, журнал, поле IP, `qasync`) не переносится.

Поведение, которое сохраняется дословно:

- Сервер: `ModbusTcpServer` / datastore как в `modbus_server.py` — coils 5001, discrete inputs 101, holding 10001, input registers 101; `ModbusDeviceContext` (`di`/`co`/`hr`/`ir`); `ModbusServerContext(..., single=True)`; identity VendorName `PyModbus`, ProductCode `EMU`. Слушает `0.0.0.0` (все IPv4-интерфейсы), чтобы DataManager с другой машины подключался так же, как к принтеру и камере (`libs/sockets.py`: `bind(("", port))`).
- Клиент Doypack всегда `127.0.0.1:<порт карточки>`. `DmcModbusBase(..., slave_id=0)` по умолчанию не менять: в `BaseModbusProxy.py` аргумент `slave_id: int = 0`, в запросы уходит `device_id=self.id`. Серверный `slave_id=1` при `single=True` остаётся как в исходнике.
- Адреса Doypack (`doypack_emulation.py`): Xinje `q_start=20`, `can_start_work=11`; Delta `q_start=4146`, `can_start_work=2567`; `step=2` если Duplex, иначе `1`; `q_end = q_start + (queue_size + 1) * step`. Цикл: запись coil `can_start_work=False`, чтение holding, `1→3`, `0→4`, `sleep(0.1)`; при ошибке итерации пауза `0.5` с и продолжение, пока карточка запущена.
- Клиент TCP: `AsyncModbusTcpClient`, адрес только формата `IP:PORT` (`helpers.get_modbus`: в строке есть `:` и `.`), `timeout=0.3`, `retries=1`, на сокете `TCP_NODELAY` и `SO_KEEPALIVE`.

Надёжный stop (pymodbus **3.12.1**, пакет уже стоит в venv ControllerServerEmulator; сверяться с ним, не с `task.cancel()`):

- `StartAsyncTcpServer` (`pymodbus/server/startstop.py`) создаёт `ModbusTcpServer` и сразу `await serve_forever()`. В `ModbusBaseServer.serve_forever` (`pymodbus/server/base.py`) `CancelledError` подавляется, `close()` не вызывается. Поэтому отмена задачи, как в `ModbusEmulator.stop_server` исходника, оставляет порт в LISTEN.
- `ServerAsyncStop` / `ServerStop` останавливают только классовое поле `ModbusBaseServer.active_server` (последний созданный сервер). Для нескольких карточек их вызывать нельзя.
- На карточку: свой экземпляр `ModbusTcpServer`, созданный **внутри** event loop потока (в `__init__` сервер берёт `asyncio.get_running_loop()`). Старт: `await server.listen()` через `serve_forever()` в задаче. Стоп: `await server.shutdown()` (`serving.set_result` + `close()` → `transport.close()` слушающего сокета и активных соединений), затем дождаться завершения задачи `serve_forever` без предварительного `cancel`. `cancel` допустим только как запасной путь, если после `shutdown()` задача не завершилась за таймаут, и только после `shutdown()`.
- После join потока проверка: новый `socket.socket(AF_INET, SOCK_STREAM)` без `SO_REUSEADDR` успешно делает `bind(("", port))` и закрывается. Иначе ERROR в лог. Клиент Doypack отключается **до** `shutdown()`, чтобы не держать соединение.

Поток карточки: не daemon, свой `asyncio.new_event_loop()`, имя вида `controller-<port>`. Qt-слот `run(True/False)` блокирует GUI только до готовности или таймаута (ориентир 5 с на старт и 5 с на join), как короткий `start()` у `PrinterEmul`, а не на всё время работы. Ошибка старта: откат (если сервер уже слушает — остановить его), кнопка возвращается в «остановлено», поля снова доступны, порт свободен. Сообщения только через `logging.getLogger`, без `print` и без журнала на карточке.

Реестр контроллеров — **отдельный** `dict`, не `_device_widgets`. Иначе `TransporterWidget.get_data_models` добавит контроллер в combo «откуда»: туда попадают все значения `_device_data`, фильтр `CameraWidget | ScannerWidget` стоит только на «куда». Генератор и так берёт только камеру и сканер, но общий реестр устройств для перевозчика нельзя расширять.

`qasync` в `requirements.txt` не добавлять. Добавить только `pymodbus==3.12.1`.

## Подзадачи

### 1. Ядро Modbus и Doypack в core/controller

- **ID**: 1
- **Стек**: backend
- **Описание**: Установить `pymodbus==3.12.1` в `venv` и дописать одну строку в `requirements.txt` (только этот пакет, без транзитивных зависимостей). Скопировать и адаптировать исходники, не импортируя `ControllerServerEmulator` и не меняя его файлы. Не переносить `MainWindow`, `ModbusEmulatorWithSimulation`, `__main__`, демо-клиент и `print`.

  Целевая раскладка:

  - `core/controller/__init__.py` — пакет, без побочных импортов Qt.
  - `core/controller/dmc_modbus/exceptions.py` — `LineControllerException`.
  - `core/controller/dmc_modbus/helpers.py` — `get_modbus` (логика `DmcModBus/helpers.py`; `get_async_modbus_advanced` не обязателен).
  - `core/controller/dmc_modbus/base.py` — `DmcModbusBase` из `BaseModbusProxy.py`, импорты относительные, `slave_id: int = 0`.
  - `core/controller/dmc_modbus/__init__.py` — реэкспорт `DmcModbusBase`, `get_modbus`, `LineControllerException`.
  - `core/controller/modbus_server.py` — `ModbusEmulator`: размеры datastore, `setup_datastore`, `setup_device_info`, методы read/write coil и holding как в исходнике. Конструктор по-прежнему принимает host/port; host по умолчанию `"0.0.0.0"`. Создание `ModbusTcpServer` и жизненный цикл — в подзадаче #2; здесь достаточно фабрики контекста и identity и тонкой обёртки, которая умеет `async start()` / `async stop()` на **уже текущем** loop: `start` делает `ModbusTcpServer(context, identity=..., address=(self.host, self.port))` и `create_task(serve_forever())`, ждёт `is_active()` (или успешного listen); `stop` вызывает `await server.shutdown()` и дожидается задачи. Не использовать `StartAsyncTcpServer` и `ServerAsyncStop`.
  - `core/controller/doypack.py` — `DoypackEmulation` с теми же адресами, шагом, `q_end` и телом цикла. `print` заменить на `getLogger`. Параметр адреса остаётся строкой `IP:PORT`, чтобы цикл не знал про карточку.

  Логгер: в `libs/loggers.py` константа `CONTROLLER_LOGGER = "CTL"` и добавление в кортеж `LOGGERS` (его обходит `main.setup_logging`). В ядре — `getLogger(CONTROLLER_LOGGER)`. Уровни: ERROR с `exc_info=True` на исключениях цикла и старта; INFO — старт/стоп (порт, режим, тип, `q_start`–`q_end`); DEBUG — поадресные чтения, если вообще логировать. Не логировать дампы datastore.

  В `CHANGES.LOG` — строка в начало (зависимость pymodbus, пакет `core/controller`). `VERSION` в этой подзадаче не менять.

- **Файлы/модули**: `requirements.txt`, `libs/loggers.py`, `core/controller/**`, `CHANGES.LOG`, `tests/test_core/test_controller_modbus.py`, `tests/test_core/test_controller_doypack.py`
- **Критерии готовности**:
  - `.\venv\Scripts\python.exe -c "import pymodbus; assert pymodbus.__version__ == '3.12.1'"` проходит; в `requirements.txt` есть ровно `pymodbus==3.12.1`, `qasync` нет.
  - Импорт `core.controller` не тянет PySide и не ссылается на каталог ControllerServerEmulator.
  - Тесты `tests/test_core/test_controller_doypack.py`: Xinje/Delta × Simplex/Duplex дают те же `q_start`, `can_start_work`, `step`, `q_end`, что формула исходника (очередь 10: Xinje simplex `q_end=20+11=31`, Delta duplex `q_end=4146+22=4168`). Один цикл с подменённым клиентом: holding `1` становится `3`, `0` становится `4`, прочие значения не пишутся; перед чтением coil `can_start_work` пишется `False`. `slave_id` у `DmcModbusBase()` равен 0.
  - Тесты `tests/test_core/test_controller_modbus.py` на реальном сокете (свободный порт > 1024, не 502): после `start` внешний `AsyncModbusTcpClient("127.0.0.1", port=...)` читает holding; после `stop` `bind(("", port))` без `SO_REUSEADDR` успешен. Повторный `start` на том же порту успешен. Два эмулятора на двух портах работают одновременно; остановка одного не закрывает второй и не использует `ServerStop`. Размеры блоков: запись coil по адресу 5000 и holding по адресу 10000 не выходит за блок (адрес внутри размера принимается).
  - В скопированном коде нет `print(`.
- **Зависимости**: нет
- **Оценка**: M

### 2. Поток карточки: старт сервера, затем Doypack, и обратный стоп

- **ID**: 2
- **Стек**: backend
- **Описание**: Класс `ControllerRuntime` в `core/controller/runtime.py`. Им владеет виджет (подзадача #4); сам класс Qt не импортирует.

  `start(port, queue_size, duplex, xinje) -> None` из потока Qt:

  1. Поднимает не-daemon `Thread` с новым event loop.
  2. В loop: `ModbusEmulator(host="0.0.0.0", port=port).start()`, дождаться listen.
  3. Затем `DoypackEmulation(f"127.0.0.1:{port}", queue_size, duplex=duplex, xinje=xinje).start()` — клиент только на loopback, не на адрес поля карточки (поля IP нет).
  4. Сигналит готовность. При исключении или таймауте ожидания (5 с): внутри loop остановить то, что успело подняться (сначала Doypack, если клиент уже создан, затем сервер), выставить ошибку, завершить поток. `start` пробрасывает исходное исключение вызывающему. Повторный `start` при уже запущенном runtime — ошибка или no-op с логом; виджет сам не вызывает старт дважды.

  `stop() -> None` идемпотентен:

  1. Если loop жив — `call_soon_threadsafe`: остановить Doypack (`running=False`, cancel задачи цикла, `await`, `disconnect`), затем `ModbusEmulator.stop()` (`shutdown` + ожидание `serve_forever`).
  2. `thread.join` с таймаутом. После join закрыть loop.
  3. Проверить, что порт принимается `bind(("", port))`. Если нет — залогировать ERROR (это дефект stop, не повод молча оставлять кнопку «запущено»; виджет в #4 всё равно переводит UI в остановлено).

  Фоновый цикл Doypack живёт в том же loop, что и сервер. Исключения итерации не роняют поток: лог и `sleep(0.5)`, как в исходнике.

  В `CHANGES.LOG` — строка про runtime. `VERSION` не менять.

- **Файлы/модули**: `core/controller/runtime.py`, `core/controller/modbus_server.py`, `core/controller/doypack.py`, `CHANGES.LOG`, `tests/test_core/test_controller_runtime.py`
- **Критерии готовности**:
  - `tests/test_core/test_controller_runtime.py`: `start` на свободном порту; TCP-connect на `127.0.0.1:port` успешен; отдельный сокет на адрес машины (`gethostbyname` / `0.0.0.0` через connect к `127.0.0.1` уже покрывает loopback — дополнительно connect к LAN не обязателен в CI, достаточно факта `address=("0.0.0.0", port)` и успешного listen на всех интерфейсах: клиент к `127.0.0.1` ходит в этот сокет). После `stop` bind того же порта успешен в пределах 2 с.
  - Два `ControllerRuntime` на разных портах: stop первого освобождает только его порт, второй по-прежнему принимает соединение.
  - Старт, когда порт уже занят чужим `socket.bind`+`listen`: `start` бросает исключение, поток завершён, чужой сокет жив, повторный bind после закрытия чужого сокета возможен (runtime не удержал порт).
  - Если сервер поднялся, а `DoypackEmulation.start` падает (подмена `connect`): `start` бросает, порт после возврата свободен (сервер откатился).
  - Порядок при штатном `stop`: disconnect клиента раньше `server.shutdown()` (проверка моком/обёрткой с метками времени или флагами).
  - `qasync` не импортируется.
- **Зависимости**: после #1
- **Оценка**: M

### 3. Секция controllers в JSON-конфиге

- **ID**: 3
- **Стек**: backend
- **Описание**: Модель `core/controller/data.py` по образцу `core/printing/data.py` (`ConfigDict(strict=True)`, `field_validator(..., mode="before")` для enum-строк, иначе strict-режим Pydantic отвергнет JSON-строки).

  - `ControllerMode(str, Enum)`: `simplex = "simplex"`, `duplex = "duplex"`.
  - `ControllerType(str, Enum)`: `delta = "delta"`, `xinje = "xinje"`.
  - `ControllerConfig`: `name: str`, `port: int`, `queue_size: int = 10`, `mode: ControllerMode = simplex`, `controller_type: ControllerType = delta`.

  В `ConfigFile` (`core/main_ui/data.py`) поле `controllers: list[ControllerConfig] = Field(default=[])` — тот же приём, что у `scanners`/`generators`: отсутствие ключа в старом JSON даёт `[]` и не валит `model_validate_json`. Сохранение через существующий `model_dump_json` подхватит поле само, когда #5 начнёт его заполнять. В этой подзадаче `line_emul.py` не менять.

  `CHANGES.LOG` — строка про секцию `controllers`. `VERSION` не менять.

- **Файлы/модули**: `core/controller/data.py`, `core/main_ui/data.py`, `CHANGES.LOG`, `tests/test_core/test_controller_config.py`
- **Критерии готовности**:
  - Тест: JSON только с `printers` (как старый конфиг) валидируется, `controllers == []`.
  - Round-trip `ControllerConfig` и `ConfigFile` для обеих пар mode/type; `queue_size` по умолчанию 10, mode simplex, type delta, если полей нет в объекте контроллера.
  - Неизвестный `mode`/`controller_type` и не-строка дают `ValidationError`.
  - Существующие тесты `tests/test_core/test_printer_config.py` и `test_scanner_config.py` проходят без правок фикстур (новое поле с default).
- **Зависимости**: нет
- **Оценка**: S

### 4. Карточка ControllerWidget

- **ID**: 4
- **Стек**: backend
- **Описание**: Форма и виджет по образцу `PrinterWidget` / `forms/ui/Printer.ui`, без списка кодов, журнала и строки статуса.

  `forms/ui/Controller.ui` — `QWidget` шириной до 260 px (как принтер), высота меньше принтера (ориентир 180–220, без `QListView`). Стили кнопок, полей, spin и combo скопировать из `Printer.ui` (те же цвета `#226091` / `#f0b321`, шрифт DejaVu Sans Mono), чтобы карточка не выпадала из темы линии. Объекты:

  | Объект | Тип | Смысл |
  |--------|-----|--------|
  | `leName` | `QLineEdit` | имя |
  | `lePort` | `QLineEdit` | порт (как `leConnetionStr` у принтера, не отдельное поле IP) |
  | `spQueueSize` | `QSpinBox` | минимум 1, максимум 1000, значение 10 |
  | `cbMode` | `QComboBox` | пункты `Simplex`, `Duplex` (индекс 0 — Simplex) |
  | `cbType` | `QComboBox` | пункты `Delta`, `Xinje` (индекс 0 — Delta) |
  | `tbRun` | `QToolButton` checkable | подписи R/S выставляет код, как у принтера |
  | `tbDelete` | `QToolButton` 28×28 | после `tbRun`, как на остальных карточках |

  Сгенерировать `forms/Controller.py` прямым вызовом (обёртка `venv\Scripts\pyside6-uic.exe` в этом окружении ненадёжна, см. `docs/line_emulator/frontend/widget-backgrounds.md`):

  ```text
  .\venv\Lib\site-packages\PySide6\uic.exe -g python --rc-prefix forms/ui/Controller.ui -o forms/Controller.py
  ```

  `ControllerWidget(QWidget, Ui_Form)` в `core/controller/controller_widget.py`:

  - Сигнал `delete_requested`. Слот удаления как у `PrinterWidget._on_delete_clicked`: если `tbRun` включён — `QMessageBox.warning` «Остановите виджет перед удалением»; иначе вопрос «Удалить виджет «имя»?» и при Yes — `delete_requested`.
  - `tbRun.toggled` → `run` и `_setup_icon` (R зелёный / S красный — те же stylesheet-строки, что в `printer_widget._setup_icon`).
  - `run(True)`: прочитать имя, порт (`int`, иначе снять галку как принтер при `ValueError`), очередь, mode, type; заблокировать `leName`, `lePort`, `spQueueSize`, `cbMode`, `cbType`; вызвать `ControllerRuntime.start`. При исключении: `stop()` runtime (идемпотентно), разблокировать поля, `tbRun.setChecked(False)` чтобы кнопка вернулась в остановлено (повторный вход в `run(False)` должен быть безопасен), ERROR в лог. `QMessageBox` на ошибку старта не показывать — у принтера его нет, текст только в логе.
  - `run(False)`: `runtime.stop()`, разблокировать те же поля. `clear_data` не добавлять: очереди кодов нет, меню очистки контроллер не вызывает.
  - Пока запущен, поля недоступны. `tbDelete` не прятать (предупреждение при работающей карточке — как у принтера).
  - `options() -> ControllerConfig` читает текущие поля. Конструктор принимает `name`, `port`, `queue_size=10`, `mode=simplex`, `controller_type=delta` и выставляет виджеты.
  - Лог виджета: `getLogger(CONTROLLER_LOGGER)`.

  `CHANGES.LOG` — строка про карточку. `VERSION` не менять. Холст и меню — подзадача #5, виджет пока никуда не встраивать.

- **Файлы/модули**: `forms/ui/Controller.ui`, `forms/Controller.py`, `core/controller/controller_widget.py`, `CHANGES.LOG`, `tests/test_core/test_controller_widget.py`
- **Критерии готовности**:
  - Тесты с `QApplication` по образцу `tests/test_core/test_printer_config.py` (`TestPrinterWidgetOptions`): конструктор выставляет имя, порт, очередь 10, combo Simplex и Delta; `options()` следует за combo и spin; смена combo меняет `ControllerMode`/`ControllerType`.
  - `run(True)` при занятом/падающем runtime (мок `ControllerRuntime.start` бросает) оставляет `tbRun` выключенным, поля снова enabled, `stop` вызван.
  - Успешный `run(True)` (мок start) disables пять полей; `run(False)` включает их и вызывает `runtime.stop`.
  - `_on_delete_clicked` при включённом `tbRun` не эмитит `delete_requested` (патч `QMessageBox`, как `tests/test_core/test_widget_delete.py`).
  - На форме нет виджета лога и статус-бара.
- **Зависимости**: после #2, #3
- **Оценка**: M

### 5. Холст, меню, сохранение и массовый пуск

- **ID**: 5
- **Стек**: backend
- **Описание**: Встроить карточку в `MainLineField`, не отдавая её перевозчикам и генераторам.

  Реестр `self._controller_widgets: dict[int, ControllerWidget]`. Метод `controller_port_generator` по образцу `printer_port_generator`: старт **5020**, шаг 1, пока порт `< 21100`. Генератор **не** синхронизировать с уже загруженными портами — у принтера той же схемы нет (`_sync_*` есть только у имён сканера). Имя новой карточки: `CTL_{port}` (как `PRN_{port}` / `CAM_{port}`).

  `add_controller(name, port, queue_size=10, mode=..., controller_type=...)` кладёт виджет в `_devices_layout` (холст устройств, не `transporters_layout`), пишет в `_controller_widgets`, соединяет `delete_requested` с обработчиком. **Не** вызывать `setup_models` из-за контроллера и **не** класть виджет в `_device_widgets`. Удаление: `_remove_controller` — выкинуть из реестра, `setParent(None)`, `run(False)`, `deleteLater`. В `_on_widget_delete_requested` добавить ветку `ControllerWidget`. `clear_ui` и `closeEvent` вызывают `run(False)` и для контроллеров (в `clear_ui` ещё `deleteLater`, как для устройств). Удаление с холста только через подтверждение на остановленной карточке (#4); `clear_ui` по-прежнему гасит все карточки при открытии другого файла.

  Меню `forms/ui/Main.ui`, затем регенерация `forms/Main.py` тем же `uic.exe -g python --rc-prefix`:

  - «Добавить»: `acAddController`, текст «Контроллер», сразу после `acAddScanner` и до первого `separator` (группа устройств: Камера, Принтер, Сканер, Контроллер).
  - «Управление → Запустить»: `acControlStartControllers`, текст «Контроллеры», после `acControlStartScanners` и до `separator`.
  - «Управление → Остановить»: `acControlStopControllers`, текст «Контроллеры», в том же месте.
  - В «Очистить данные» пункта нет.

  Слоты в `line_emul.py`: `acAddController` → следующий порт и `add_controller`. Bulk: `_iter_controllers`, `_bulk_start_controllers`, `_bulk_stop_controllers`. «Всё»:

  - Старт (`_bulk_start_all`): устройства (принтеры → камеры → сканеры) → **контроллеры** → перевозчики → генераторы.
  - Стоп (`_bulk_stop_all`): генераторы (reversed) → перевозчики (reversed) → **контроллеры (reversed)** → устройства (reversed, как сейчас).

  `_bulk_clear_*` не обходит контроллеры. `isinstance`-кортежи в `transporter_widget.get_data_models` и `generator_widget.get_data_models` не расширять.

  `save_configuration_to_file`: список `controllers=[dev.options() for ...]`. `process_config`: `_load_controllers` после сканеров и до перевозчиков; id контроллеров в словарь `devices` для перевозчиков **не** класть (перевозчик ищет узлы по имени принтера/камеры/сканера).

  Обновить ожидаемый порядок в `tests/test_core/test_bulk_control.py` (`test_bulk_start_all_order`, `test_bulk_stop_all_reverse_order`) — сейчас там жёсткие списки без контроллера. Добавить кейсы: старт/стоп только контроллеров; clear all не вызывает методов контроллера. В `tests/test_core/test_widget_delete.py`: `_remove_controller` убирает виджет из реестра и layout; `clear_ui` вызывает `run(False)`. Отдельный тест: после `add_controller` combo перевозчика «откуда» не содержит имя контроллера, combo генератора тоже.

  `CHANGES.LOG` — строка про меню и JSON load/save. `VERSION` не менять (бамп в #6).

- **Файлы/модули**: `forms/ui/Main.ui`, `forms/Main.py`, `core/main_ui/line_emul.py`, `CHANGES.LOG`, `tests/test_core/test_bulk_control.py`, `tests/test_core/test_widget_delete.py`, `tests/test_core/test_controller_line.py`
- **Критерии готовности**:
  - `tests/test_core/test_controller_line.py`: `add_controller` даёт порты 5020, затем 5021; `options()` попадает в `ConfigFile.controllers` при `save_configuration_to_file` на временный файл; `process_config` восстанавливает имя, порт, очередь, mode, type; JSON без ключа `controllers` открывается логикой `ConfigFile` и не создаёт карточек.
  - Bulk-тесты: порядок старта `printer, camera, scanner, controller, transporter, generator`; стоп — обратный; «Очистить данные → Всё» не трогает контроллер.
  - Тест перевозчика/генератора: контроллер отсутствует в моделях combo.
  - `clear_ui` / remove вызывают `run(False)`.
  - Существующие тесты `test_bulk_control.py` и `test_widget_delete.py` обновлены и проходят, а не заскипаны.
- **Зависимости**: после #4
- **Оценка**: M

### 6. Сборка PyInstaller и версия

- **ID**: 6
- **Стек**: backend
- **Описание**: `pymodbus` подтягивает фреймеры и datastore динамически. В `build/spec/main.spec` добавить в `hiddenimports` результат `collect_submodules("pymodbus")` (импорт `PyInstaller.utils.hooks.collect_submodules` в spec, рядом с уже существующим списком). Точечного списка `pymodbus.client` недостаточно: без подмодулей framer замороженный exe падает на старте сервера.

  Поднять `client_info.VERSION` с `1.0.0.1.b0008` до `1.0.0.1.b0009` (последний разряд, префикс `b`). Это единственный бамп на всю фичу: подзадачи #1–#5 отдельно не выпускаются. `DB_VERSION` не трогать.

  `CHANGES.LOG` — строка про hiddenimports и версию. Полный прогон PyInstaller в критерии не требуется (долгий); достаточно, чтобы spec импортировался и список hiddenimports содержал `pymodbus.server`, `pymodbus.client`, `pymodbus.datastore`, `pymodbus.framer`.

- **Файлы/модули**: `build/spec/main.spec`, `client_info.py`, `CHANGES.LOG`, `tests/test_core/test_controller_freeze_spec.py` (или короткий кейс в существующем `tests/test_core/test_build_project.py`, если там уже читают spec — не ломая текущие проверки deb/linux)
- **Критерии готовности**:
  - Тест читает `build/spec/main.spec` как текст и проверяет наличие `collect_submodules` и `pymodbus`, либо исполняет кусок сбора hiddenimports в venv и проверяет, что в списке есть перечисленные модули.
  - `client_info.VERSION == "1.0.0.1.b0009"`.
  - `DB_VERSION` в diff этой фичи не менялся.
- **Зависимости**: после #5
- **Оценка**: S

### 7. Техническая документация линии

- **ID**: 7
- **Стек**: backend
- **Описание**: Документация в `docs/line_emulator/` (каталог эмулятора линии; `ClientTypes` для `main.py` отдельной папкой не задан, актуальные документы лежат здесь). Пишет `tech-writer` после ревью. Пользовательские инструкции и `WHATSNEW.md` этой подзадачей не подменять: их после всех `- [x]` пишет `user-doc-writer` (фаза 3 цикла).

  Обновить:

  - `docs/line_emulator/line_emulator.md` — абзац назначения (контроллер Modbus/Doypack), строка версии `1.0.0.1.b0009`, mermaid-схема (`ControllerWidget` → runtime → сервер `0.0.0.0` + клиент `127.0.0.1`), таблица модулей, таблица полей `ConfigFile` (`controllers`, default `[]`, старые файлы открываются), пример JSON одной карточки.
  - Новый `docs/line_emulator/controller.md` — карта адресов Xinje/Delta, simplex/duplex и формула `q_end`; размеры datastore; один `tbRun` и порядок старт/стоп; отдельный asyncio-поток на карточку; почему stop — это `ModbusTcpServer.shutdown()`, а не `cancel` и не `ServerStop` (несколько карточек); блокировка полей; удаление только на стопе; отсутствие в перевозчиках, генераторах и «Очистить данные»; логгер `CTL`.
  - `docs/line_emulator/bulk-control.md` — пункт «Контроллеры» в Запустить/Остановить, место в порядке «Всё», явное отсутствие в «Очистить данные».
  - Раздел сборки в `line_emulator.md` — `hiddenimports` pymodbus через `collect_submodules`.

  `CHANGES.LOG` — строка про документы.

- **Файлы/модули**: `docs/line_emulator/line_emulator.md`, `docs/line_emulator/controller.md`, `docs/line_emulator/bulk-control.md`, `CHANGES.LOG`
- **Критерии готовности**:
  - В `line_emulator.md` есть секция `controllers` и модуль `core/controller`.
  - В `controller.md` указаны константы адресов, порт по умолчанию 5020, bind `0.0.0.0`, клиент `127.0.0.1`, запрет `qasync` и запрет правки ControllerServerEmulator.
  - `bulk-control.md` описывает новый пункт и не добавляет контроллер в очистку.
  - Нет инструкции вида «импортируйте пакет из ControllerServerEmulator».
- **Зависимости**: после #6
- **Оценка**: S

## Чеклист выполнения

- [x] 1. Ядро Modbus и Doypack в core/controller
- [x] 2. Поток карточки: старт сервера, затем Doypack, и обратный стоп
- [x] 3. Секция controllers в JSON-конфиге
- [x] 4. Карточка ControllerWidget
- [x] 5. Холст, меню, сохранение и массовый пуск
- [x] 6. Сборка PyInstaller и версия
- [x] 7. Техническая документация линии

## Волны выполнения

- **Волна 1:** #1 (ядро Modbus/Doypack) и #3 (модель JSON) — общих файлов нет (`core/controller/data.py` создаёт #3, ядро его не импортирует; `requirements.txt` и `libs/loggers.py` только у #1; `core/main_ui/data.py` только у #3). `CHANGES.LOG` обеим можно дописывать.
- **Волна 2:** #2 — после #1 (runtime вызывает `ModbusEmulator` и `DoypackEmulation`).
- **Волна 3:** #4 — после #2 и #3 (виджет зависит от runtime и `ControllerConfig`).
- **Волна 4:** #5 — после #4 (`line_emul`, `Main.ui`, bulk/delete-тесты).
- **Волна 5:** #6 — после #5 (spec и единственный бамп `VERSION`).
- **Волна 6:** #7 — после #6 (документы ссылаются на версию и hiddenimports).

После волны 6 оркестратор запускает `user-doc-writer`: `docs/line_emulator/user-guides/controller.md` (добавить карточку, порт, очередь, Simplex/Duplex, Delta/Xinje, кнопка R/S, что IP вводить не нужно, DataManager подключается на IP машины и порт карточки), правка `user-guides/bulk-control.md` и `user-guides/README.md`, запись в `WHATSNEW.md`.

## Процесс выполнения

**Обязательно:** каждая подзадача проходит цикл по полю **Стек**:

- `backend` → `developer → code-review → tech-writer`
- `frontend` → `frontend-developer → frontend-code-review → frontend-tech-writer`
- `mixed` → разбей на отдельные подзадачи со своим стеком, если возможно

Все семь подзадач — `backend`. Ревью frontend не подключать.

**Параллельно:** подзадачи **без общих файлов** и **без зависимостей** друг от друга — в одной **волне** (волна 1: #1 и #3). Остальные волны строго по зависимостям.

Оркестратор (основная сессия) **не пишет код сам** — skill `/execute-plan` или `/execute-development-cycle`.

```text
/execute-plan .plans/backlog/2026-11-06-line-controller-device.md
```

При **Build** в Plan mode агент следует тем же правилам (см. `.cursor/rules/plan-execution-orchestration.mdc`).

Интерпретатор команд и тестов: `.\venv\Scripts\python.exe` из корня репозитория. Тесты подзадач: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_controller_modbus tests.test_core.test_controller_doypack` и аналогично для остальных новых модулей; на #5 дополнительно `tests.test_core.test_bulk_control` и `tests.test_core.test_widget_delete`.

## Риски и открытые вопросы

- `ModbusBaseServer.active_server` — одно классовое поле на процесс. Любой вызов `ServerStop()` погасит «последний» сервер и сломает соседнюю карточку. Критерий #1 это ловит двумя одновременными портами.
- `serve_forever` в pymodbus 3.12 глотает `CancelledError` и не закрывает слушающий сокет. Стоп только через `shutdown()` экземпляра. Тест bind после stop — обязательный, не заменять проверкой флага `running`.
- На Windows сокет в `TIME_WAIT` после внешнего клиента может на короткое время мешать bind. Штатный стоп сначала рвёт клиент Doypack. Если bind в тесте флапает, ждать до 2 с в цикле, не включать `SO_REUSEADDR` на проверочном сокете (он маскирует занятый порт).
- Генератор портов, как у принтера, не смотрит занятые порты загруженного JSON: после открытия файла с портом 5020 следующее «Добавить → Контроллер» снова предложит 5020, пока генератор не сдвинут добавлениями в этой сессии. Это принятое сходство с `printer_port_generator`, не отдельная задача.
- `collect_submodules("pymodbus")` раздувает hiddenimports (simulator и прочее). Это приемлемо: точечный список уже приводил к падениям frozen-импорта у pymodbus. Исключать пакеты вручную в этой задаче не нужно.
- Двойной вход `run(False)` при `setChecked(False)` из неудачного `run(True)` должен быть идемпотентен (`runtime.stop()` безопасен до успешного старта).
- Блокировка GUI на время `start`/`stop` (до ~5 с) на карточку. Массовый «Всё» стартует контроллеры последовательно через `tbRun.setChecked`, каждый `start` дожидается listen. Не уводить старт в «выстрелил и забыл»: иначе кнопка станет S до того, как порт слушает, и откат при ошибке разъедется с состоянием кнопки.
- ControllerServerEmulator и его venv не редактировать. Сверка API pymodbus 3.12.1 — чтение установленного пакета в том venv или в venv линии после `pip install`, не копирование site-packages в репозиторий.

## Следующий шаг

Волна 1, параллельно: `developer` на подзадачу #1 (ядро `core/controller` и `pymodbus==3.12.1`) и `developer` на подзадачу #3 (`ControllerConfig` и поле `ConfigFile.controllers`).

## Журнал изменений плана

| Дата | Изменение |
|------|-----------|
| 2026-11-06 | Создан план |
| 2026-11-06 | Выполнено: #5–#7, перенос в `.plans/complete/` |
