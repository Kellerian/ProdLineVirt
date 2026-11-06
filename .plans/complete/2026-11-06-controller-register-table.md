---
title: Таблица регистров на карточке контроллера
created: 2026-11-06
updated: 2026-11-06
status: completed
priority: medium
estimated_subtasks: 3
---

# Таблица регистров на карточке контроллера

## Контекст и цель

Карточка «Контроллер» (`ControllerWidget`, `forms/ui/Controller.ui`, ширина 260) уже есть на холсте линии. Сейчас у формы `maximumSize` высота **220**, `minimumSize` высота **180**, вертикальная политика **Minimum**, а в `verticalLayout` нет stretch. Лишняя высота делится между строками «Очередь» (`spQueueSize`), «Режим» (`cbMode`) и «Тип» (`cbType`): у них вертикальная политика **Minimum**, поэтому спинбокс и комбобоксы тянутся. У принтера (`forms/ui/Printer.ui`) `maximumSize` высота **16777215**, `verticalLayout` `stretch="0,0,1"`, область значений — `QListView` `lstData`. Холст кладёт виджет по `sizeHint()` (`core/main_ui/flow_layout.py`, `item.setGeometry(..., item.sizeHint())`), поэтому «рост вниз» — это больший `sizeHint` карточки, а не растягивание родителя.

Успех: верхние блоки остаются в одну строку по своему `sizeHint`; под ними на всю ширину 260 — таблица holding-регистров (колонки «Переменная» и «Значение», номера строк, вертикальный скролл). Кнопка «Добавить переменную» добавляет пустую строку; адрес пользователь вписывает сам. Колонка «Значение» только для чтения и заполняется из datastore **запущенного** контроллера. В JSON уходят только адреса (`ControllerConfig.register_addresses`). Пока `tbRun` выключен, значения пустые, адреса на месте. Окно «Поллер контроллеров» в репозиторий не переносится: в коде нет «Поллер», IP, периода, Старт/Стоп поллера, Загрузить/Сохранить, «Готово» и «Опрос запущен». `tbRun` (R/S) остаётся единственным пуском контроллера.

Вне scope: удаление строки, запись в регистры из таблицы, coil/bool и зелёный `False`, автозаполнение адресов очереди, поле периода в UI, правка `line_emul.py` (сохранение уже вызывает `options()`, загрузка — `load_options`), `DB_VERSION`, Alembic, `requirements.txt`.

Стек всех подзадач — **backend** (PySide6 на Python, не React): `developer` → `code-review` → `tech-writer`. Пользовательскую документацию пишет оркестратор через `user-doc-writer` после всех `- [x]`, отдельной подзадачей её нет.

## Обзор подхода

Адреса — новое поле схемы, виджет и опрос от него не зависят по файлам, поэтому модель и API чтения делаются параллельно. Виджет собирает оба результата.

Чтение значений — **не** второй `AsyncModbusTcpClient` и **не** `DoypackEmulation.get_status`. `get_status` берёт тот же `DmcModbusBase`, что цикл очереди, захватывает `_queue_lock` и делает TCP (`timeout=0.3` в `get_modbus`). Опрос списка адресов раз в 500 мс застопорит шаг очереди (`sleep(0.1)` в `_step_queue_iteration`). Прямой доступ уже есть: `ModbusEmulator.get_holding_register` (`core/controller/modbus_server.py`) читает holding через `context[0].getValues(3, address, count=1)`. Функция 3 и смещение `address + 1` внутри pymodbus 3.x уже учтены этим методом — в новый код адрес передавать как есть, без `+ 1`. Допустимый holding — **0…10000** включительно (`holding_registers_size = 10002`; тест `test_out_of_range_coil_and_holding_rejected`: 10000 принимается, 10001 — ошибка).

Datastore живёт в потоке рантайма. GUI его не трогает. `ControllerRuntime.read_holding_registers` один раз планирует короткую корутину через `asyncio.run_coroutine_threadsafe` на цикл воркера (тот же приём, что `stop()`), внутри вызывает `get_holding_register` и возвращает список той же длины. Виджет опрашивает это **с GUI-потока** таймером `QTimer` 500 мс и тут же пишет ячейки. Отдельный Qt-сигнал из воркера не нужен: слот таймера и есть GUI-поток. `setItem` / `setText` из потока `controller-<port>` запрещены.

Интервал **500 мс** в UI не показывается. Константа `_REGISTER_POLL_INTERVAL_MS = 500` в `controller_widget.py`. Так стоит период на скрине поллера; цикл Doypack и так спит 0.1 с на слот, а чтение datastore дешевле этого шага. Таймаут `fut.result` — **0.25 с**, меньше интервала, чтобы слот не копился.

Очередь Doypack (для подсказки и тестов, **не** для автозаполнения таблицы): Delta `q_start=4146`, Xinje `q_start=20`, `step=2` при duplex и `1` при simplex, `q_end = q_start + (queue_size + 1) * step` (`core/controller/doypack.py`). Примеры 4146, 4148, 4150 — слоты Delta duplex. Это holding-целые (цикл пишет 3 или 4, иначе оставляет прочитанное, старт блока — 0).

`client_info.VERSION` сейчас `1.0.0.1.b0009`. Один бамп на всю фичу — в подзадаче #3, до `1.0.0.1.b0010`. Подзадачи #1 и #2 версию не меняют. `DB_VERSION` не трогать.

## Подзадачи

### 1. Поле `register_addresses` в ControllerConfig

- **ID**: 1
- **Стек**: backend
- **Описание**: В `ControllerConfig` (`core/controller/data.py`) добавить поле адресов holding-регистров, которые карточка показывает в таблице. Значения регистров в модель не входят.

  Поле: `register_addresses: list[int] = Field(default_factory=list)`. Не `default=[]` (общий список на экземпляры). `ConfigDict(strict=True)` сохранить.

  Правила значения:

  - ключ отсутствует в JSON объекта контроллера → `[]` (старые файлы линии открываются);
  - элементы — целые **0…10000** включительно, порядок сохраняется, повторы разрешены;
  - `bool` не принимается как int (strict Pydantic так и делает — зафиксировать тестом);
  - число вне диапазона, не-int, `null` вместо списка — `ValidationError`.

  Отдельный `field_validator` нужен только если strict-тип сам не отсекает диапазон: тогда `Field` не выражает «каждый элемент 0…10000», и валидатор по элементам обязателен. Не подменять отсутствие ключа пустым списком через `mode="before"` так, чтобы явный `null` стал `[]`.

  `core/main_ui/data.py` и `line_emul.py` не менять: `ConfigFile.controllers` уже `list[ControllerConfig]`, сохранение — `model_dump_json`.

  Developer: строка в начало `CHANGES.LOG` (поле `register_addresses`, значения регистров не сериализуются). `VERSION` не менять. Markdown в `docs/` не править — это зона tech-writer после ревью.

  **Документация (tech-writer после ревью):** `docs/line_emulator/config_controllers.md` — строка в таблице `ControllerConfig`, диапазон 0…10000, default `[]`, обратная совместимость при отсутствии ключа, пример JSON с `"register_addresses": [4146, 4148, 4150]`. Убрать устаревшую фразу, что виджет «может подключаться позже»: карточка уже на холсте; редактирование адресов с карточки появится в #3, в этом документе достаточно схемы. В `docs/line_emulator/line_emulator.md` в примере карточки контроллера добавить тот же ключ (или явная отсылка, что полный пример в `config_controllers.md`, если пример не дублируют). `WHATSNEW.md` и `docs/line_emulator/user-guides/` не трогать.

- **Файлы/модули**: `core/controller/data.py`, `tests/test_core/test_controller_config.py`, `CHANGES.LOG`
- **Критерии готовности**:
  - `ControllerConfig.model_validate({"name": "CTL_1", "port": 5020})` даёт `register_addresses == []`.
  - Round-trip `model_dump_json` → `model_validate_json` сохраняет порядок `[4146, 4148, 2801, 0, 10000]`.
  - `10001`, `-1`, `true`, `"4146"`, `null` на месте списка — `ValidationError`.
  - Существующий `tests/test_core/test_controller_line.py` (round-trip `options()` без адресов) проходит без правки `line_emul.py`: в дампе есть `"register_addresses": []`.
  - Прогон: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_controller_config tests.test_core.test_controller_line`.
- **Зависимости**: нет
- **Оценка**: S

### 2. Чтение holding с цикла рантайма

- **ID**: 2
- **Стек**: backend
- **Описание**: Добавить в `ControllerRuntime` синхронный метод для GUI. Qt в `runtime.py` не импортировать.

  Сигнатура:

  ```python
  def read_holding_registers(self, addresses: Sequence[int]) -> list[int | None]:
  ```

  Поведение:

  1. Под `_state_lock` снять ссылки на `_loop` и `_modbus`. Если поток не запущен, цикл `None` или закрыт, `modbus is None` — вернуть список `None` той же длины, не бросать.
  2. Иначе одна корутина на этом цикле через `asyncio.run_coroutine_threadsafe` (как `_shutdown` в `stop`). Внутри, для каждого адреса по порядку:
     - не `int`, `bool`, либо не `0 <= address <= 10000` → `None` (datastore не звать);
     - иначе `int(modbus.get_holding_register(address))`;
     - любое исключение на адресе (`RuntimeError` без context, ошибка pymodbus, индекс) → `None` и `logger.debug` (`CTL`), без `exc_info` на INFO и без ERROR на каждый адрес (опрос раз в 500 мс).
  3. `fut.result(timeout=0.25)`. При `TimeoutError` или ошибке планирования — DEBUG и список `None` той же длины (виджет в #3 на таком ответе не падает).
  4. Длина результата всегда равна длине `addresses`, порядок тот же. Пустой вход → `[]` сразу, без похода в цикл.

  Не вызывать `DoypackEmulation.get_status` / `set_status`, не создавать `AsyncModbusTcpClient`, не читать coils (`get_coil`). Метод только читает.

  Гонка со `stop`: после `stop` context уже `None`, метод возвращает `None`, а не исключение наружу. Не держать datastore-ссылку дольше корутины.

  Developer: строка в начало `CHANGES.LOG`. `VERSION` не менять. `docs/` не править.

  **Документация (tech-writer после ревью):** раздел `ControllerRuntime` в `docs/line_emulator/controller_core.md` — метод `read_holding_registers`, почему чтение на цикле воркера через `get_holding_register`, а не клиент Doypack, диапазон 0…10000, таймаут 0.25 с, результат `None` на остановленном рантайме и на плохом адресе. Упомянуть в списке тестов `test_controller_runtime.py`.

- **Файлы/модули**: `core/controller/runtime.py`, `tests/test_core/test_controller_runtime.py`, `CHANGES.LOG`
- **Критерии готовности**:
  - После `start` на свободном порту внешний тестовый `AsyncModbusTcpClient` делает `write_register(4146, 4)` и `write_register(4150, 0)`; `read_holding_registers([4146, 4150, 10001, -1])` возвращает `[4, 0, None, None]`. Клиент теста закрыть в `finally`. Это не образец для виджета — у виджета своего клиента нет.
  - `read_holding_registers([])` на запущенном рантайме → `[]`.
  - После `stop()` тот же вызов с непустым списком → все `None`, исключения нет.
  - Вызов до `start` → все `None`.
  - В `runtime.py` нет импорта PySide, `qasync` и `AsyncModbusTcpClient`.
  - Прогон: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_controller_runtime`.
- **Зависимости**: нет
- **Оценка**: S

### 3. Компактные блоки, таблица адресов и опрос на карточке

- **ID**: 3
- **Стек**: backend
- **Описание**: Собрать UI и поведение. `forms/Controller.py` не править руками: после правки `forms/ui/Controller.ui` регенерировать из корня репозитория:

  ```text
  .\venv\Lib\site-packages\PySide6\uic.exe -g python --rc-prefix forms/ui/Controller.ui -o forms/Controller.py
  ```

  #### Форма (`Controller.ui`)

  Ширина карточки остаётся **260** (`minimumSize` и `maximumSize` по ширине). Высоту разжать как у принтера:

  - `maximumSize` высота **16777215** (снять потолок 220);
  - `minimumSize` высота **280** (было 180), чтобы `sizeHint` на холсте вмещал компактные контролы и несколько строк таблицы;
  - `sizePolicy`: горизонталь Preferred, вертикаль **Expanding** (как `Printer.ui`);
  - `geometry` height можно выставить 280, на рантайм влияет связка minimum/maximum и layout.

  `verticalLayout` — пять участников, `stretch="0,0,0,0,1"`:

  1. уже существующая строка имени/порта/`tbRun`/`tbDelete`;
  2. строка «Очередь» (`horizontalLayoutQueue`);
  3. строка «Режим» / «Тип» (`horizontalLayoutModeType`);
  4. `QPushButton` `btnAddRegister`, текст **«Добавить переменную»**, на всю ширину (прямой item `verticalLayout`, не вложенный в колонку);
  5. `QTableWidget` `tblRegisters`, stretch **1**.

  Чтобы лишняя высота не возвращалась в спинбокс и комбобоксы (вертикальный **Minimum** как раз разрешает рост):

  - у `spQueueSize`, `cbMode`, `cbType`, подписей `labelQueue` / `labelMode` / `labelType`, а также у `leName` и `lePort` вертикальная `sizePolicy` = **Fixed** (горизонталь spin/combo оставить Expanding);
  - пиксельный `maximumHeight` на эти контролы **не** ставить: высота строки = `sizeHint` (шрифт 10pt и кнопки spin 20px из stylesheet не обрезать);
  - `tbRun` / `tbDelete` уже 28×28, не трогать;
  - у `btnAddRegister` вертикальная политика **Fixed**. В stylesheet формы добавить правило `QPushButton` теми же цветами, что `QToolButton` (`#226091`, текст `#FFFFFF`, hover/checked `#f0b321`, шрифт **10pt** «DejaVu Sans Mono», чтобы длинная подпись влезала в 260). Отдельное серое окно поллера не копировать.

  Таблица `tblRegisters` — обычный `QTableWidget`, не `QListView`:

  - 2 колонки, заголовки **«Переменная»** и **«Значение»**;
  - вертикальный заголовок виден (номера строк);
  - вертикальный скролл `ScrollBarAsNeeded`; горизонтальный скролл выключен (`ScrollBarAlwaysOff`);
  - оба столбца `QHeaderView.Stretch`, чтобы занять ширину 260 вместе с номерами строк;
  - `alternatingRowColors` true, сетка включена, перенос слов выключен;
  - шрифт ячеек «DejaVu Sans Mono» 8pt (как `lstData`);
  - без drag-and-drop;
  - tooltip таблицы: адреса holding 0…10000; очередь Delta с 4146 шагом 2 при Duplex (1 при Simplex), Xinje с 20. Это подсказка, не автозаполнение;
  - `minimumHeight` таблицы около **120**, чтобы при minimum формы 280 строки были видны. Верхнего потолка высоты у таблицы нет.

  Колонку «Значение» в `.ui` сделать нередактируемой нельзя построчно — флаги ячеек выставляет код виджета при добавлении строки.

  #### Виджет (`controller_widget.py`)

  Константа `_REGISTER_POLL_INTERVAL_MS = 500`. В `__init__` создать `QTimer(self)`, интервал 500, `timeout` → `_poll_register_values`. Таймер **не** `singleShot`. Пока рантайм не запущен, таймер не активен.

  Конструктор: существующие позиционные аргументы не ломать; в конец добавить `register_addresses: Sequence[int] | None = None`. Если список передан — заполнить строки (колонка значений пустая). По умолчанию строк нет.

  `btnAddRegister.clicked` → одна новая строка в конец:

  - колонка 0: пустой редактируемый item (`ItemIsEnabled | ItemIsSelectable | ItemIsEditable`);
  - колонка 1: пустой item **без** `ItemIsEditable` (`ItemIsEnabled | ItemIsSelectable`).

  Кнопку и колонку адресов **не** блокировать в `_set_fields_enabled`. По-прежнему при запуске недоступны только `leName`, `lePort`, `spQueueSize`, `cbMode`, `cbType`. Удаления строки нет: ни кнопки, ни обработчика Delete.

  `load_options`: таблицу очистить (`setRowCount(0)`) и заново добавить по строке на каждый `config.register_addresses` (текст адреса — десятичный `str`, значение пустое). Рантайм не трогать и не запускать. `options()` по-прежнему собирает `ControllerConfig` и дополнительно передаёт адреса:

  - обход сверху вниз;
  - пустая ячейка или строка из пробелов — пропуск (в JSON не пишется, на экране остаётся, пока файл не перезагрузят);
  - непустой текст, который не является целым, или целое вне **0…10000** — `ValueError` с номером строки (1-based) и понятным русским текстом, по тому же принципу, что неверный порт (`from exc`, если был `ValueError` от `int()`). Сохранение линии тогда падает явно, а не теряет опечатку;
  - в конфиг попадает только `list[int]`. Тексты колонки «Значение» не читать.

  `run(True)` после успешного `runtime.start`: запустить таймер и сразу один раз вызвать `_poll_register_values` (не ждать первые 500 мс). Если `start` бросил исключение — таймер не запускать, значения не заполнять, откат кнопки как сейчас.

  `_poll_register_values` выполняется только как слот таймера / прямой вызов с GUI-потока:

  1. Если `_runtime is None` или `tbRun` не включён — выйти.
  2. Собрать адреса по строкам. Пустая, нецелая или вне 0…10000 ячейка: значение этой строки очистить, в запрос её не класть, **не** бросать (исключение только в `options()`).
  3. `values = self._runtime.read_holding_registers(addrs)`.
  4. Если метод бросил (не должен, но слот не имеет права ронять Qt) — DEBUG в лог `CTL` и выйти, предыдущие числа оставить.
  5. Если вернулся список `None` целиком из-за таймаута/остановки внутри API — записать пустые значения только когда рантайм ещё считается запущенным и длина совпала; не падать при несовпадении длины (DEBUG и выход, ячейки не двигать).
  6. В совпавшие строки колонки 1 записать `str(value)` для `int` и `""` для `None`. Колонку 0 не перезаписывать (пользователь может редактировать адрес). Item колонки 1 не заменять, если он уже есть: только `setText`, чтобы флаги «только чтение» не сбрасывались. Цвет не менять, строки `True`/`False` не подставлять.

  `run(False)`: сначала `timer.stop()`, затем существующий `runtime.stop()` и сброс `_runtime`, затем очистить **только** тексты колонки «Значение» (`setText("")`), строки и адреса не удалять. Идемпотентно, если таймер уже остановлен и `_runtime is None`. `clear_ui` / `closeEvent` уже вызывают `run(False)` — `line_emul.py` не менять.

  Пока контроллер остановлен, колонка «Значение» пустая, даже если в ячейках остался старый текст от прошлого сеанса: очистка в `run(False)` это гарантирует. Повторный старт заполняет её следующим опросом.

  Запись регистров из таблицы не добавлять. `set_status` не вызывать.

  Developer: строка в начало `CHANGES.LOG`; единственный бамп `client_info.VERSION` с `1.0.0.1.b0009` на `1.0.0.1.b0010` (префикс `b`). `DB_VERSION` не менять. `docs/` не править.

  **Документация (tech-writer после ревью):**

  - `docs/line_emulator/controller_widget.md` — снять пометку, что виджет ещё не на холсте (она уже устарела). Описать снятие потолка 220, stretch таблицы, `btnAddRegister`, `tblRegisters`, что блокируется при R/S, опрос 500 мс только на запущенном рантайме, очистку значений при стопе, `options()` / `load_options` для адресов, `ValueError` на плохом адресе. Версию в шапке документа поставить `1.0.0.1.b0010`.
  - `docs/line_emulator/controller.md` — короткий абзац: таблица holding на карточке, адреса в JSON, значения только при запущенном `tbRun`, чтение через runtime, не второй клиент. Формулу `q_start` / `step` не дублировать заново, дать ссылку.
  - `controller_core.md` не переписывать, если #2 уже описал `read_holding_registers`; достаточно ссылки из виджета.
  - `WHATSNEW.md` и `user-guides/` не заполнять — их после всех подзадач пишет `user-doc-writer` (ожидаемые места: `docs/line_emulator/user-guides/controller.md`, `WHATSNEW.md`).

- **Файлы/модули**: `forms/ui/Controller.ui`, `forms/Controller.py`, `core/controller/controller_widget.py`, `tests/test_core/test_controller_widget.py`, `tests/test_core/test_controller_line.py`, `client_info.py`, `CHANGES.LOG`
- **Критерии готовности**:
  - В сгенерированном `forms/Controller.py` есть `btnAddRegister` и `tblRegisters`; у формы `maximumHeight()` равен 16777215, ширина maximum 260; вертикальная политика `spQueueSize`, `cbMode`, `cbType` — `QSizePolicy.Fixed`; stretch-фактор item-а таблицы в `verticalLayout` равен 1, у строки очереди — 0.
  - Клик по «Добавить переменную» увеличивает `rowCount` на 1; колонка 0 редактируема, колонка 1 — нет (`flags` без `ItemIsEditable`).
  - `options()` после адресов `4146` и `4150` (и пустой строки между ними) возвращает `register_addresses == [4146, 4150]`. Текст `"abc"` и `10001` дают `ValueError`. Значение в колонке 1 на список не влияет.
  - `load_options` с `register_addresses=[20, 22]` строит две строки, колонка значений пустая.
  - Успешный `run(True)` с моком `ControllerRuntime`: таймер активен, `read_holding_registers` можно вызвать через `_poll_register_values`; мок возвращает `[4, 0]` — в колонке 1 тексты `"4"` и `"0"`, без зелёного stylesheet и без `"False"`. `run(False)` останавливает таймер, вызывает `stop`, очищает значения, адреса остаются, поля имени/порта/очереди/режима/типа снова enabled, кнопка добавления тоже enabled.
  - `run(True)`, если `start` бросает: таймер не активен, `tbRun` выключен (как текущий тест отката).
  - В `tests/test_core/test_controller_line.py` один сценарий: две строки адресов на карточке, `ConfigFile` → `process_config` → у нового виджета те же `register_addresses` и пустые значения. `add_controller` / `_load_controllers` не переписывать, если хватает уже существующего `load_options`.
  - Прогон: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_controller_widget tests.test_core.test_controller_line tests.test_core.test_controller_config`.
  - `client_info.VERSION == "1.0.0.1.b0010"`. В diff фичи `DB_VERSION` не менялся.
- **Зависимости**: после #1, #2
- **Оценка**: M

## Чеклист выполнения

- [x] 1. Поле `register_addresses` в ControllerConfig
- [x] 2. Чтение holding с цикла рантайма
- [x] 3. Компактные блоки, таблица адресов и опрос на карточке

## Волны выполнения

- **Волна 1:** #1 (схема JSON) и #2 (API рантайма) — общих файлов нет (`data.py` только у #1, `runtime.py` только у #2). `CHANGES.LOG` обеим можно дописывать.
- **Волна 2:** #3 — после #1 и #2 (виджет сериализует поле и зовёт `read_holding_registers`; здесь же единственный бамп `VERSION`).

## Процесс выполнения

**Обязательно:** каждая подзадача — backend:

```text
developer → code-review → tech-writer
```

Developer пишет код, тесты и `CHANGES.LOG` (версию — только #3). Tech-writer после «no issues» правит только перечисленные в подзадаче markdown в `docs/line_emulator/` и строку `CHANGES.LOG` про документацию. `user-guides/` и `WHATSNEW.md` в этих подзадачах не писать.

**Параллельно:** волна 1 (#1 и #2). Волна 2 только после обеих.

Оркестратор код сам не пишет. После всех `- [x]` он запускает `user-doc-writer` (карточка: кнопка «Добавить переменную», таблица, адреса в файле линии, значения только пока контроллер запущен).

```text
/execute-plan .plans/backlog/2026-11-06-controller-register-table.md
```

## Риски и открытые вопросы

- На скрине поллера адрес **2801** показан как **False** зелёным, остальные ячейки — целые `4` / `0`. В `doypack.py` регистра 2801 нет. Именованные адреса очереди — holding (`q_start` 4146 или 20). Coil в эмуляторе — только `can_start_work` (Delta **2567**, Xinje **11**), и таблица его как coil не читает. Адрес 2801 попадает в holding-блок 0…10000, поэтому чтение вернёт **целое** (по умолчанию 0), не `False`. Поддержку coil/bool и зелёную раскраску не делать. Если позже выяснится, что 2801 — катушка внешнего поллера, это отдельная задача.
- Тот же номер на другой функции Modbus — другой блок. Пользователь, вписавший 2567, увидит holding 2567, а не coil `can_start_work`. Tooltip это не расписывает по каждому coil; в документации tech-writer одной фразой говорит, что колонка — holding (fc 3).
- Удаление строки не делаем. Пустая строка не попадает в JSON, но висит на карточке до перезагрузки файла. Ошибочный адрес пользователь может стереть вручную; пока текст непустой и невалидный, `options()` бросает `ValueError` и сохранение линии не проходит.
- `FlowLayout` не растягивает карточку выше `sizeHint`. Снятие потолка 220 и minimum 280 задают высоту на холсте; внутри неё stretch 1 отдаёт избыток таблице. Отдельного ресайза карточки мышью на холсте нет и в этой задаче не появляется.
- `fut.result(0.25)` блокирует GUI на время чтения. Чтение — память на том же loop, между `await` цикла Doypack, поэтому укладка обычно много меньше 0.25 с. Если цикл занят дольше таймаута, ячейки этого тика не обновляются, карточка не падает.
- Опрос не сериализуется с `_queue_lock` клиента Doypack и может прочитать holding в середине `_step_queue_iteration` (до или после записи 3/4). Для таблицы это нормально: на экране фактическое содержимое datastore.

## Следующий шаг

Волна 1: одновременно `developer` для #1 и `developer` для #2. После ревью и tech-writer обеих — `developer` для #3.

## Журнал изменений плана

| Дата | Изменение |
|------|-----------|
| 2026-11-06 | Выполнены подзадачи #1 и #2 (схема `register_addresses`, `read_holding_registers`, документация tech-writer) |
| 2026-11-06 | Выполнена подзадача #3 (UI таблица, опрос, тесты, tech-writer, user-doc-writer) |
| 2026-11-06 | Создан план |
