---
title: Типизированные значения регистров на карточке контроллера
created: 2026-11-06
updated: 2026-11-09
status: completed
priority: high
estimated_subtasks: 3
---

# Типизированные значения регистров на карточке контроллера

## Контекст и цель

Карточка контроллера уже опрашивает локальный datastore каждые 500 мс, но колонка «Значение» умеет только holding: текст `str(int)`, без coil и без цвета. Внешний ModbusPoller (`C:\emulators\ModbusPoller`, пример `для тестов.json` хранит `"variables"` строками, в том числе `"2801"`) показывает holding целым числом, coil как `True`/`False`, успешное чтение зелёным, ошибку чтения красным. Пользователь зафиксировал этот вариант. Исходника `app/utils/modbus.py` в поставке поллера нет (exe/zip без `.py`); правила ниже — контракт задачи, им нужно совпасть.

Успех: пользователь по-прежнему сам вводит адреса. В ячейке «Переменная» сохраняется введённый текст (`D100`, `M100`, `2801`, `4146`). При запущенном `tbRun` колонка «Значение» обновляется с локального datastore (не вторым Modbus-клиентом): holding — `4` / `0` / `3`, coil — `True` / `False`, успех — зелёный текст, ошибка чтения — красный. Старый JSON с `register_addresses: list[int]` открывается; число разбирается теми же правилами (4146 — holding, 2801 — coil). Цикл Doypack (coil `False`, holding `1→3`, `0→4`) не меняется. `client_info.DB_VERSION` не менять.

Предшественник `.plans/complete/2026-11-06-controller-register-table.md` не переписывать: там coil/bool и зелёная раскраска сознательно отложены.

## Обзор подхода

Один чистый разбор адреса, одно новое чтение datastore, одна правка опроса виджета. Источник значений — `ModbusEmulator.get_holding_register` / `get_coil` на цикле воркера, как сейчас `read_holding_registers`.

Фактические пределы datastore (`core/controller/modbus_server.py`): `holding_registers_size = 10002`, `coils_size = 5002`. pymodbus 3.x адресует блок как `address + 1`, поэтому допустимы holding **0…10000** и coil **0…5000** (`size - 2`). Это уже проверяет `tests/test_core/test_controller_modbus.py`: coil 5000 и holding 10000 проходят, 5001 и 10001 — нет.

### Правила адреса (зафиксированы)

После `strip` токен целиком:

| Форма | Тип | Адрес | Пример |
|-------|-----|-------|--------|
| `D`/`d` + десятичные цифры | holding | `4096 + int(цифры)` | `D100` → holding 4196; `d0` → holding 4096 |
| `M`/`m` + десятичные цифры | coil | `2048 + int(цифры)` | `M100` → coil 2148; `m100` хранится как `m100` |
| строка только из цифр, число **2048…4095** включительно | coil | само число | `2801` → coil 2801; `2567` → coil 2567; `2048` и `4095` → coil |
| строка только из цифр вне этого диапазона | holding | само число | `4146` → holding 4146; `0`, `2047`, `4096`, `5000`, `5001`, `11`, `20` → holding |

Дальше проверка диапазона **уже выбранного** типа:

- holding: адрес в **0…10000**, иначе ошибка. `D5904` → 10000, ок; `D5905` → 10001, ошибка; голое `10001` — ошибка; голое `5001` — **валидный holding** (не coil).
- coil: адрес в **0…5000**, иначе ошибка. `M2952` → 5000, ок; `M2953` → 5001, ошибка. Полоса голых чисел 2048…4095 целиком внутри 0…5000, отдельный отсев там не нужен.

Не совпало с тремя формами (`abc`, `X100`, `D`, `M`, `D100a`, `+1`, `-1`, пустая строка после strip) — ошибка. Регистр префикса только `D`/`d`/`M`/`m`. Пробелы внутри токена не допускаются (`D 100` — ошибка). Ведущие нули в цифрах допустимы (`D0100` → holding 4196), в JSON хранится введённый текст после `strip`, не каноническое число.

Ошибки:

- **Сохранение (`options()`):** `ValueError` с текстом `Строка N: недопустимый адрес переменной`. **N** — номер строки таблицы с единицы (пустые строки тоже считаются, как сейчас: плохой текст во второй строке при пустой первой — «Строка 2»). Пустая после `strip` строка в список не входит и исключения не даёт.
- **Опрос:** невалидный или пустой адрес **не** бросает исключение: текст «Значение» очищается, цвет текста сбрасывается в умолчание (не красный и не зелёный). Строка в запрос рантайма не попадает.
- **Модель JSON:** тот же разбор; при ошибке — `ValidationError`. Номера строки UI в pydantic нет.

Отображение (зафиксировано):

- Успех holding: текст `str(int)` (`"4"`, `"0"`, `"3"`). `0` — это значение, ячейка не пустая.
- Успех coil: `str(bool)` → `"True"` или `"False"`. В виджете `bool` проверять **раньше** `int` (`bool` — подкласс `int`).
- Успех: `setForeground(QColor(0, 128, 0))` только у колонки «Значение».
- Ошибка чтения точки (`None` из рантайма, в том числе таймаут 0.25 с, который API отдаёт как `None`, и исключение `get_coil` / `get_holding_register` по одной точке): `setText("")` и `setForeground(QColor(128, 0, 0))`. Отдельную надпись «Ошибка» не добавлять.
- Сбой **всего** вызова (метод бросил, длина ответа не равна числу точек): DEBUG в лог `CTL` без traceback, ячейки не менять, исключение в Qt не выпускать.
- Остановка `tbRun`: как сейчас, очистить только тексты «Значение» и дополнительно сбросить `ForegroundRole` (`item.setData(Qt.ItemDataRole.ForegroundRole, None)`). Не вызывать `setForeground(QBrush())` — пустая кисть может спрятать текст. Колонку адресов не красить и не очищать.
- Интервал **500** мс, `QTimer` с GUI-потока, первый тик сразу после успешного `start`. Второй `ModbusTcpClient` из карточки не создавать.

JSON (зафиксировано):

- Поле остаётся `register_addresses`. Элемент — **`str | int`** (не `bool`, не `float`).
- `str` — токен пользователя после `strip`, регистр префикса сохраняется.
- `int` — старый файл. При загрузке число проверяется теми же правилами и **остаётся int** в модели (повторное сохранение без карточки не переписывает числа в строки). `4146` и `"4146"` — один и тот же holding; `2801` и `"2801"` — coil.
- Карточка в `options()` пишет **строки** (то, что в ячейке). После сохранения линии с карточки префиксы не теряются, старые голые числа уходят в JSON как строки `"4146"`.
- Нет ключа → `[]`. Явный `null` — ошибка. `true`/`false` и float по-прежнему ошибка (strict).
- Адреса из полосы **2048…4095** в старых файлах раньше читались как holding. Теперь это coil. Так и должно быть (`2801` → `True`/`False`). `4146`, `20`, `11` остаются holding. Coil Xinje `can_start_work = 11` этой грамматикой как coil не задать: голое `11` — holding 11. Отдельную форму для адреса 11 не вводить.

Что не делать: не заполнять таблицу очередью Doypack, не менять `DoypackEmulation` (`0→4`, `1→3`, пауза 0.1 с), не подключать клиент из карточки, не менять `DB_VERSION`, не бампить `VERSION` больше одного раза.

## Подзадачи

### 1. Разбор адреса и JSON `register_addresses`

- **ID**: 1
- **Стек**: backend
- **Описание**:

  Новый модуль `core/controller/addresses.py` без Qt и без pymodbus. Константы: holding **0…10000**, coil **0…5000**, базы `4096` / `2048`, полоса голого coil **2048…4095**. Функции с аннотациями и docstring:

  - `parse_register_token(raw: str) -> ParsedRegister` — `strip`, таблица правил выше. Успех: тип (`holding` | `coil`), числовой адрес, `token` (строка после `strip`, исходный регистр). Любая ошибка формата или диапазона — `ValueError("недопустимый адрес переменной")` без номера строки.
  - `normalize_register_token(value: object) -> str | int` — `str` → разобрать и вернуть `token`; `int`, но не `bool` → `parse_register_token(str(value))` и вернуть **тот же int**; `bool`, `float`, `None` и прочее — `ValueError`.

  `ControllerConfig` в `core/controller/data.py`: заменить `RegisterAddress = Annotated[int, Field(ge=0, le=10_000)]` на элемент `str | int`. `ConfigDict(strict=True)` оставить. `field_validator("register_addresses", mode="before")` на весь список: `None` — ошибка; не список — отдать pydantic как есть; иначе `[normalize_register_token(item) for item in value]`. `default_factory=list` не трогать. Валидатор mode/type не менять.

  Виджет в этой подзадаче **не** менять: `options()` по-прежнему отдаёт `list[int]` в конструктор модели, валидатор принимает эти int. Существующие тесты виджета и линии, которые сравнивают `register_addresses` с `[4146, 4150]`, должны остаться зелёными.

  Developer: строка в начало `CHANGES.LOG` (разбор D/M/чисел, `str | int`, старые int открываются). `VERSION` и `DB_VERSION` не менять. `docs/` не править.

  **Документация (tech-writer после ревью):** `docs/line_emulator/config_controllers.md` — тип поля `list[str | int]`, правила D/M/голое число, диапазоны holding 0…10000 и coil 0…5000, отсутствие ключа → `[]`, `null`/bool/float по-прежнему ошибка, повтор адреса допустим, значения регистров в модель не входят. Пример: старый фрагмент с числами `[4146, 4148, 4150]` всё ещё валиден; рядом пример строк `"D100"`, `"M100"`, `"2801"`, `"4146"`. В `docs/line_emulator/line_emulator.md` поправить только пример `register_addresses` карточки контроллера (или одну фразу-отсылку, если пример сознательно не дублируют — тогда оставить числа и написать, что строки допустимы, полный контракт в `config_controllers.md`). `WHATSNEW.md` и `user-guides/` не трогать.

- **Файлы/модули**: `core/controller/addresses.py`, `core/controller/data.py`, `tests/test_core/test_controller_config.py`, `CHANGES.LOG`
- **Критерии готовности**:
  - Векторы `parse_register_token` (тип, адрес, token): `D100` → holding 4196 / `"D100"`; `d0` → holding 4096 / `"d0"`; `D0100` → holding 4196 / `"D0100"`; `D5904` → holding 10000; `M100` → coil 2148; `m100` → coil 2148 / token `"m100"`; `M0` → coil 2048; `M2952` → coil 5000; `2801`, `2567`, `2048`, `4095` → coil с тем же адресом; `4146`, `0`, `2047`, `4096`, `5000`, `5001`, `11`, `20`, `10000` → holding; `"  D100  "` → token `"D100"`.
  - Ошибки parse: `D5905`, `M2953`, `10001`, `-1`, `abc`, `X100`, `D`, `M`, `D100a`, `D 100`, `+4146`, `""`, `"   "`.
  - `normalize_register_token(4146) == 4146`, `normalize_register_token(2801) == 2801`, `normalize_register_token("D100") == "D100"`. `True`, `False`, `4146.0` — `ValueError`.
  - `ControllerConfig.model_validate({"name": "CTL_1", "port": 5020})` → `register_addresses == []`. `null` вместо списка — `ValidationError`.
  - Раунд-трип чисел `[4146, 5000, 4146]` сохраняет **int** и порядок. Раунд-трип `["D100", "m100", "2801", "4146"]` сохраняет строки. Смешанный список `[4146, "D100"]` после `model_dump_json` → `model_validate_json` даёт тот же смешанный список.
  - Границы JSON: int `0` и `10000` ок; `-1` и `10001` — `ValidationError`; int `2801` ок (это coil, но в модели остаётся int). Строка `"4146"` теперь **валидна** (старый тест `test_register_addresses_string_element_raises` заменить на допуск строк). Bool и float по-прежнему `ValidationError`.
  - Прогон: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_controller_config tests.test_core.test_controller_widget tests.test_core.test_controller_line`.
  - В diff этой подзадачи нет правок `client_info.py`.
- **Зависимости**: нет
- **Оценка**: M

### 2. Чтение holding и coil с цикла рантайма

- **ID**: 2
- **Стек**: backend
- **Описание**:

  В `ControllerRuntime` добавить `read_points(self, points: Sequence[tuple[str, int]]) -> list[int | bool | None]`. `read_holding_registers` не менять (сигнатура, диапазон, таймаут, тексты DEBUG, тесты).

  Контракт `read_points`, по тому же каркасу, что `read_holding_registers` (`asyncio.run_coroutine_threadsafe` на цикл воркера, `fut.result(timeout=0.25)`, пустой вход → `[]`, рантайм не запущен / поток мёртв / цикл закрыт → `[None] * n`):

  - Элемент `("holding", address)`: не `bool`, `int`, **0…10000** → `int(modbus.get_holding_register(address))` (результат не `bool`). Иначе слот `None`, datastore не трогать.
  - Элемент `("coil", address)`: не `bool`, `int`, **0…5000** → `bool(modbus.get_coil(address))`. Иначе слот `None`, datastore не трогать.
  - Иной тип первого элемента — слот `None`.
  - Исключение одной точки — DEBUG `CTL`, эта точка `None`, остальные читаются.
  - Таймаут, сбой планирования, исключение `fut.result` — DEBUG и `[None] * n` на весь запрос.
  - Импортов `AsyncModbusTcpClient`, PySide, qasync в `runtime.py` нет. `doypack.py` не менять.

  Константы 10000 и 5000 в этом методе можно записать литералами с комментарием, что они равны `holding_registers_size - 2` и `coils_size - 2`. Общий импорт `addresses.py` не обязателен: подзадача идёт параллельно с #1 и не должна от неё зависеть.

  Один проход по списку точек за один вызов (виджет не будет делать два таймаута).

  Developer: строка в начало `CHANGES.LOG`. `VERSION` не менять. `docs/` не править.

  **Документация (tech-writer после ревью):** `docs/line_emulator/controller_core.md` — раздел про `read_points` рядом с `read_holding_registers`: источник `get_holding_register` / `get_coil`, диапазоны, таймаут 0.25 с, `None` на слот и на весь запрос, без второго клиента. Раздел про `read_holding_registers` не переписывать, только не утверждать, что карточка по-прежнему зовёт только его (это сделает #3; здесь достаточно описать новый метод). Версию в шапке на `b0012` не ставить — бамп в #3. `WHATSNEW.md` и `user-guides/` не трогать.

- **Файлы/модули**: `core/controller/runtime.py`, `tests/test_core/test_controller_runtime.py`, `CHANGES.LOG`
- **Критерии готовности**:
  - После `start` внешний клиент пишет holding `4146 = 3` и coil `2567 = True`. `read_points([("holding", 4146), ("coil", 2567), ("coil", 5001), ("holding", 10001), ("discrete", 0)])` → `[3, True, None, None, None]`. Тип coil — `bool`, holding — `int` и не `bool`.
  - Coil `5000` и holding `10000` читаются (записать клиентом `True` и `7`). Coil `5001` и holding `10001` — `None`, метод не бросает.
  - `read_points([])` → `[]` на запущенном рантайме. До `start` и после `stop` непустой список → все `None`.
  - Существующие тесты `read_holding_registers` без правок ожиданий: `[4, 0, None, None]` на `[4146, 4150, 10001, -1]`.
  - Цикл Doypack виден через datastore: после `start` (Delta, simplex, `queue_size` 10) клиент пишет в holding `4146` значение `1`; в цикле до **3 с** `read_points([("holding", 4146)])` становится `[3]`. Логику `doypack.py` не менять. Если за 3 с тройка не появилась — тест падает (слот с `1` цикл переписывает в `3` и дальше не трогает).
  - В тексте `runtime.py` нет `AsyncModbusTcpClient`, `PySide`, `qasync`.
  - Прогон: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_controller_runtime`.
  - В diff этой подзадачи нет правок `client_info.py` и `doypack.py`.
- **Зависимости**: нет
- **Оценка**: M

### 3. Опрос карточки: текст, цвет, строки в JSON

- **ID**: 3
- **Стек**: backend
- **Описание**:

  `ControllerWidget` (`core/controller/controller_widget.py`):

  - Импорт разбора из `addresses.py` и `QColor` из `PySide6.QtGui`. Интервал `_REGISTER_POLL_INTERVAL_MS = 500` не менять.
  - Конструктор: позиционные аргументы `name, port, queue_size, mode, controller_type` не ломать. `register_addresses` остаётся keyword-only, тип расширить до `Sequence[str | int] | None`. В таблицу: `int` (не `bool`) → десятичный `str`, `str` → текст как есть. Колонка значений пустая, без цвета.
  - `load_options`: то же отображение из `config.register_addresses` (`4146` → ячейка `"4146"`, `"D100"` → `"D100"`). Рантайм не стартовать.
  - `options()`: пустые строки пропускать. Непустую — `parse_register_token`. Успех: в список класть **`parsed.token`** (строка, не числовой адрес: `"D100"`, не `4196`). Ошибка — `raise ValueError(f"Строка {row + 1}: недопустимый адрес переменной") from exc`. Колонка «Значение» на список не влияет. Порт — как сейчас.
  - `_poll_register_values` только с GUI-потока. Ранний выход, если `_runtime is None` или `tbRun` выключен. По строкам: пусто или `parse_register_token` бросил — очистить текст значения и `ForegroundRole`, в запрос не класть. Иначе накопить `("holding"|"coil", address)` и индекс строки. Один вызов `read_points` (не `read_holding_registers`). Исключение или неверная длина — DEBUG `CTL`, `return`, ячейки не трогать. Иначе по слотам: `bool` → `"True"`/`"False"` и зелёный `QColor(0, 128, 0)`; `int` → `str(int)` и тот же зелёный; `None` → `""` и красный `QColor(128, 0, 0)`. Item колонки 1 не подменять, если он есть: только текст и foreground, флаги «только чтение» не сбрасывать. Колонку 0 не перезаписывать.
  - `run(False)`: порядок как сейчас (стоп таймера, `runtime.stop()`, `_runtime = None`), затем очистка текстов **и** `ForegroundRole`. `run(True)` при успешном `start` по-прежнему сразу один тик. При исключении `start` таймер не запускать.
  - `_set_fields_enabled` не расширять на таблицу и «Добавить переменную»: их можно менять и на запущенной карточке.

  Тултип `tblRegisters` в `forms/ui/Controller.ui` (сейчас только holding 0…10000 и старт очереди) заменить на короткий текст: `D`/`d` — holding `4096+N`, `M`/`m` — coil `2048+N`, голое число `2048…4095` — coil, иначе holding `0…10000`, coil datastore `0…5000`, очередь Delta с 4146, Xinje с 20. Перегенерировать `forms/Controller.py` прямым вызовом (обёртка `venv\Scripts\pyside6-uic.exe` в этом окружении ненадёжна):

  ```text
  .\venv\Lib\site-packages\PySide6\uic.exe -g python --rc-prefix forms/ui/Controller.ui -o forms/Controller.py
  ```

  Макет, `maximumHeight`, stretch и набор виджетов не менять. `line_emul.py` не менять: загрузка идёт через `load_options`.

  Developer: строка в начало `CHANGES.LOG`. Единственный бамп `client_info.VERSION` с `1.0.0.1.b0011` на `1.0.0.1.b0012` (префикс `b`). `DB_VERSION` не менять. `docs/` не править.

  **Документация (tech-writer после ревью):**

  - `docs/line_emulator/controller_widget.md` — таблица больше не «только holding»: синтаксис адреса, `options()` пишет строки и `ValueError` «Строка N: недопустимый адрес переменной», опрос `read_points` 500 мс, цвета `QColor(0, 128, 0)` / `QColor(128, 0, 0)`, очистка текста и цвета при **R**, невалидный адрес на тике очищает значение без красного. Шапка версии — `1.0.0.1.b0012`.
  - `docs/line_emulator/controller.md` — абзац про таблицу: holding и coil, JSON-токены, цвета, источник — локальный datastore через `read_points`. Формулу `q_start` / `step` не дублировать. Версия сборки внизу файла — `b0012`.
  - `docs/line_emulator/controller_core.md` — только шапка версии на `b0012`, если раздел `read_points` уже написан в #2.
  - `WHATSNEW.md` и `user-guides/` не заполнять.

- **Файлы/модули**: `core/controller/controller_widget.py`, `forms/ui/Controller.ui`, `forms/Controller.py`, `tests/test_core/test_controller_widget.py`, `tests/test_core/test_controller_line.py`, `client_info.py`, `CHANGES.LOG`
- **Критерии готовности**:
  - `options()` для ячеек `D100`, пусто, `M100`, `2801`, `4146` (и мусор в колонке «Значение») даёт `register_addresses == ["D100", "M100", "2801", "4146"]`.
  - `"abc"`, `"10001"`, `"M2953"`, `"X100"` в `options()` — `ValueError`, в тексте есть `Строка 1` (для единственной строки).
  - `load_options` со списком `["D100", "20"]` — две строки, тексты `D100` и `20`, значения пустые. `ControllerConfig.model_validate` со старым `[4146, 2801]` через `load_options` показывает `"4146"` и `"2801"`.
  - Успешный `run(True)` с моком `ControllerRuntime`: таймер активен, в `read_points` уходит список точек. Для строк `4146` и `2801` мок возвращает `[4, False]` — тексты `"4"` и `"False"`, foreground `(0, 128, 0)`. Отдельный тик с `[0, True]` даёт `"0"` и `"True"` (ноль не пустая ячейка), тоже зелёный. Тик с `[None, False]` — первая ячейка `""` и `(128, 0, 0)`, вторая `"False"` зелёная.
  - Строка `"abc"` на тике: значение пустое, `ForegroundRole is None`, этой строки нет в аргументе `read_points`.
  - `read_points` бросает или возвращает список другой длины: предыдущий текст ячейки остаётся, виджет не падает.
  - `run(False)` останавливает таймер, вызывает `stop`, очищает тексты и `ForegroundRole`, адреса на месте, имя/порт и «Добавить переменную» снова enabled. Если `start` бросает — таймер не активен, `tbRun` выключен.
  - `tests/test_core/test_controller_line.py`: раунд-трип карточки ждёт строки `["4146", "4150"]` (или с добавленным `"D100"`, если сценарий расширен). Отдельный сценарий: JSON с числовым `"register_addresses": [4146, 2801]` → `process_config` → в таблице `"4146"` и `"2801"`, значения пустые. `add_controller` / `_load_controllers` не переписывать.
  - В `forms/Controller.py` после uic тот же тултип, что в `Controller.ui`. `maximumHeight` формы не откатывается к 220.
  - Прогон: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_controller_widget tests.test_core.test_controller_line tests.test_core.test_controller_config tests.test_core.test_controller_runtime`.
  - `client_info.VERSION == "1.0.0.1.b0012"`. В diff `DB_VERSION` не менялся.
- **Зависимости**: после #1, #2
- **Оценка**: M

## Чеклист выполнения

- [x] 1. Разбор адреса и JSON `register_addresses`
- [x] 2. Чтение holding и coil с цикла рантайма
- [x] 3. Опрос карточки: текст, цвет, строки в JSON

## Волны выполнения

- **Волна 1:** #1 (схема и разбор) и #2 (`read_points`) — общих файлов нет (`addresses.py` / `data.py` только у #1, `runtime.py` только у #2). `CHANGES.LOG` обеим можно дописывать в начало. `VERSION` не бампать.
- **Волна 2:** #3 — после #1 и #2 (виджет зовёт `parse_register_token` и `read_points`; здесь единственный бамп `VERSION` на `1.0.0.1.b0012`).

## Процесс выполнения

**Обязательно:** каждая подзадача — backend:

```text
developer → code-review → tech-writer
```

Developer пишет код, тесты и `CHANGES.LOG` (версию — только #3). Tech-writer после «no issues» правит только перечисленные в подзадаче markdown в `docs/line_emulator/`. `user-guides/` и `WHATSNEW.md` в этих подзадачах не писать.

**Параллельно:** волна 1 (#1 и #2). Волна 2 только после обеих.

Оркестратор код сам не пишет. После всех `- [x]` он запускает `user-doc-writer`: поведение таблицы для пользователя изменилось (синтаксис `D`/`M`/число, `True`/`False`, зелёный/красный, в файле линии сохраняется введённый текст, старые числовые списки открываются). Ожидаемые места: `docs/line_emulator/user-guides/controller.md`, `WHATSNEW.md`. В пользовательском тексте прямо сказать, что число от 2048 до 4095 — катушка (`True`/`False`), а адрес очереди вроде 4146 или 20 — целое; при **S** успешное значение зелёное, сбой чтения — красная пустая ячейка; после **R** колонка значений пустая.

```text
/execute-plan .plans/backlog/2026-11-06-controller-register-typed-values.md
```

## Риски и открытые вопросы

Открытых вопросов нет: вариант отображения, цвета, источник datastore и грамматика адреса зафиксированы в разделах выше.

- Coil Xinje `11` этими правилами как coil не вводится: голое `11` — holding 11. Coil Delta `2567` вводится числом `2567` (полоса 2048…4095). Отдельную запись для адреса 11 не добавлять.
- Повторное сохранение линии с карточки переписывает старые JSON-числа в строки (`4146` → `"4146"`). Смысл голого числа тот же. Пока файл только читают и не сохраняют с карточки, в модели элементы остаются `int`.
- Любой сохранённый адрес **2048…4095** (в том числе `2801` и `2567`) после этой задачи читается как coil, не как holding. Адреса очереди `4146` и `20` остаются holding.
- Пустая красная ячейка не рисует глиф: автотест проверяет `foreground()`, отдельное слово в ячейку не пишем.
- `fut.result(0.25)` по-прежнему блокирует GUI на время одного чтения. Опрос может попасть в середину шага Doypack; на экране фактическое содержимое datastore.
- Удаление строки таблицы по-прежнему нет. Пустая строка не попадает в JSON.

## Следующий шаг

Волна 1: параллельно `developer` для #1 и `developer` для #2. После ревью и tech-writer обеих — `developer` для #3.

## Журнал изменений плана

| Дата | Изменение |
|------|-----------|
| 2026-11-06 | Создан план |
