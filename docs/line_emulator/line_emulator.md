# Эмулятор производственной линии

| Параметр | Значение |
|----------|----------|
| Точка входа | `main.py` |
| Версия | `client_info.VERSION` (например `1.0.0.1.b0005`) |
| Главное окно | `core/main_ui/line_emul.py` → `MainLineField` |
| UI-форма | `forms/Main.py` → `Ui_MainWindow` |
| Конфигурация | JSON через `core/main_ui/data.py` → `ConfigFile` |
| Сборка exe | `build_project.py` → `build/spec/main.spec` → `build/install/dmcLineEmulator/` |

## Назначение

Desktop-приложение на PySide6 для визуальной эмуляции производственной линии маркировки: камеры сканирования, эмулятор ручного сканера ШК (COM), транспортёры, генераторы кодов и принтеры. Виджеты устройств размещаются на холсте (`FlowLayout`), связываются по ID и настраиваются из JSON-конфига.

## Архитектура

```mermaid
flowchart TB
    main["main.py"] --> mlf["MainLineField"]
    mlf --> cam["CameraWidget"]
    mlf --> trn["TransporterWidget"]
    mlf --> gen["GeneratorWidget"]
    mlf --> prn["PrinterWidget"]
    mlf --> scn["ScannerWidget"]
    cam --> proxy["CameraProxy / CameraEmul"]
    scn --> sproxy["ScannerProxy / ScannerEmul"]
    prn --> pemul["PrinterEmul"]
    sproxy --> serial["libs/serial_port / COM"]
    cam --> mp["libs/model_processing"]
    trn --> mp
    gen --> mp
    cam --> cs["libs/code_scheduler"]
    trn --> cs
    gen --> cs
    cs --> mp
```

| Модуль | Роль |
|--------|------|
| `core/scanning/camera_widget.py` | Очередь отправки (`model_in`), результаты (`model_out`); `CodeScheduler` + per-code batch (`spInterval`, `spSize`); `tbDelete` / `delete_requested` |
| `core/barcode_scanner/scanner_widget.py` | Очередь отправки (`model_in`), подтверждённые коды (`model_out`); `CodeScheduler` + COM через `ScannerProxy`; `tbRefreshPorts` — повторное `_refresh_com_ports`; `tbDelete` / `delete_requested` |
| `core/transporting/transporter_widget.py` | Перенос кодов между связанными виджетами (`cbxFrom` → `model_out` источника, `cbxTo` → `model_in` приёмника); источник — камера/принтер/сканер, приёмник — камера/сканер; `CodeScheduler` + per-code FIFO; `tbDelete` / `delete_requested` |
| `core/generator/generator_widget.py` | Генерация кодов в `model_in` камеры или сканера (`cbxTo`); `CodeScheduler` + `_last_generated_at` (~`spInterval` между генерациями), `create_code_item`; `tbDelete` / `delete_requested` |
| `core/printing/printer_widget.py` | Отображение буфера принтера (сокет); `tbDelete` / `delete_requested` |
| `core/barcode_scanner/scanner_core.py` | Эмулятор сканера ШК: очередь кодов, запись в COM (фоновый поток) |
| `core/barcode_scanner/scanner_proxy.py` | Qt-мост: `Signal scanned`, опрос ядра 250 мс |
| `libs/serial_port.py` | pyserial: перечисление портов, `SerialPortConfig`, open/write с суффиксом `\r\n` |
| `libs/model_processing.py` | Модели очередей Qt, хелперы per-code timing |
| `libs/code_scheduler.py` | Периодический тик (~10 мс) для проверки готовности кодов |

## Очереди кодов и per-code timing

Коды в pipeline представлены элементами `QStandardItem` в `QStandardItemModel`. Для моделирования времени прохождения кода через узел линии каждый элемент несёт метку прибытия в `Qt.UserRole` (см. `ARRIVAL_TIME_ROLE`).

Инфраструктура меток и проверки готовности реализована в `libs/model_processing.py` и описана в [model_processing_timing.md](model_processing_timing.md). Все точки входа кодов в pipeline (drop, загрузка модели, генератор, камера, транспортёр) создают элементы через `create_code_item` — см. раздел «Точки входа» в той же документации.

Периодический опрос готовности выполняет `CodeScheduler` (`libs/code_scheduler.py`): внутренний тик **10 мс** (`SCHEDULER_TICK_MS`, `Qt.TimerType.PreciseTimer`), callback виджета на каждом тике проверяет очередь через хелперы `model_processing`. Подробности — в [code_scheduler.md](code_scheduler.md).

Поле `spInterval` в UI виджетов (и поле `interval` в JSON-конфиге) задаёт требуемое время ожидания **для каждого конкретного кода** в очереди узла, а не период тика планировщика.

## Конфигурация JSON (`ConfigFile`)

Корневая Pydantic-модель — `core/main_ui/data.py` → `ConfigFile` (`strict=True`). Загрузка и сохранение выполняются в `MainLineField` (`open_config`, `save_configuration_to_file`) через `model_validate_json()` / `model_dump_json(indent=4)`.

| Поле | Тип | По умолчанию | Назначение |
|------|-----|--------------|------------|
| `printers` | `list[PrinterConfig]` | `[]` | принтеры (TCP) |
| `cameras` | `list[CameraConfig]` | `[]` | камеры сканирования (TCP) |
| `scanners` | `list[ScannerConfig]` | `[]` | эмуляторы ручного сканера ШК (COM) |
| `transporters` | `list[TransporterConfig]` | `[]` | перевозчики между виджетами |
| `generators` | `list[GeneratorConfig]` | `[]` | генераторы кодов |

**Обратная совместимость:** поля со значением по умолчанию `[]` (в том числе `scanners`) могут отсутствовать в старых JSON-файлах — при десериализации подставляется пустой список, ошибки валидации не возникает.

### Модель конфигурации сканера (`ScannerConfig`)

Модуль: `core/barcode_scanner/data.py`. План: serial barcode scanner, подзадача **#2** (модель конфигурации).

| Класс | Роль |
|-------|------|
| `ScannerParams` | Параметры линии COM и суффикс штрихкода |
| `ScannerConfig` | Сохраняемое состояние одного виджета сканера |
| `ScannerConfig.to_serial_port_config()` | Преобразование в `libs/serial_port.SerialPortConfig` для `ScannerEmul` |

```mermaid
flowchart LR
    JSON["JSON scanners[]"] --> SC["ScannerConfig"]
    SC --> SP["ScannerParams config"]
    SC -->|"to_serial_port_config()"| SPC["SerialPortConfig"]
    SPC --> Emul["ScannerEmul / libs/serial_port"]
```

#### `ScannerParams`

Вложенный объект `config` внутри элемента `scanners[]`. Значения по умолчанию совпадают с `SerialPortConfig` в `libs/serial_port.py`.

| Поле | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `baud_rate` | `int` | `9600` | Скорость порта |
| `bytesize` | `int` | `8` | Размер символа (5–8) |
| `parity` | `str` | `"N"` | Чётность: `N`, `E`, `O`, `M`, `S` |
| `stopbits` | `float` | `1` | Стоп-биты: `1`, `1.5`, `2` |
| `suffix` | `str` | `"\r\n"` | Суффикс после кода при записи в COM |

#### `ScannerConfig`

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `name` | `str` | да | Имя виджета на холсте |
| `port_name` | `str` | да | Имя COM-порта ОС (например, `COM3`) |
| `config` | `ScannerParams` | да | Параметры линии и суффикс |

Метод `to_serial_port_config()` собирает `SerialPortConfig`: переносит `port_name` с верхнего уровня и поля `baud_rate`, `bytesize`, `parity`, `stopbits`, `suffix` из вложенного `config`. Используется при старте эмулятора, чтобы UI-слой не зависел напрямую от dataclass `libs/serial_port`.

#### Пример фрагмента JSON

```json
{
    "scanners": [
        {
            "name": "SCN_COM3",
            "port_name": "COM3",
            "config": {
                "baud_rate": 9600,
                "bytesize": 8,
                "parity": "N",
                "stopbits": 1,
                "suffix": "\r\n"
            }
        }
    ]
}
```

Файлы без секции `scanners` (например, `configs/test.json`) по-прежнему загружаются; список сканеров остаётся пустым.

#### Пример конфигурации `configs/scanner_example.json`

Готовый JSON для отладки цепочки **генератор → сканер (COM) → перевозчик → камера** (подзадача **#9**). Файл можно открыть через меню конфигурации в `MainLineField.open_config`.

| Секция | Содержание | Связь на холсте |
|--------|------------|-----------------|
| `scanners[]` | `SCAN_1`, `port_name`: `COM5`, 9600 8N1, суффикс `\r\n` | Эмулятор ручного сканера; порт — одна сторона пары com0com (см. [com0com_setup.md](com0com_setup.md)) |
| `generators[]` | `give_to`: `SCAN_1`, `interval`: 500 мс | Коды попадают в `ScannerWidget.model_in` |
| `transporters[]` | `take_from`: `SCAN_1`, `give_to`: `CAM_23`, `interval`: 250 мс | После записи в COM коды снимаются с `model_out` сканера и передаются в камеру |
| `cameras[]` | `CAM_23`, TCP-порт `23` | Приёмник перевозчика |

Перед запуском замените `port_name` на фактический COM из пары com0com или физического адаптера. Секции `printers` в примере нет — для минимального сценария сканера достаточно перечисленных полей.

Для отладки COM без физического адаптера см. [com0com_setup.md](com0com_setup.md).

Восстановление виджетов при `open_config`, запись в `save_configuration_to_file` и пункт меню «Добавить → Сканер» реализованы в `MainLineField` — см. раздел **«Интеграция сканера в главное окно»** ниже (подзадача **#5**).

## Интеграция сканера в главное окно (#5)

Модуль: `core/main_ui/line_emul.py` → `MainLineField`. UI главного окна: `forms/ui/Main.ui`, `forms/Main.py`.

### Меню «Добавить → Сканер»

| Элемент | Значение |
|---------|----------|
| QAction | `acAddScanner` (текст «Сканер») |
| Подключение | `setup_connections()` → `acAddScanner.triggered` → `_ac_add_scanner` |
| Порядок в меню | после «Принтер», перед разделителем и «Перевозчик» |

```mermaid
flowchart LR
    Menu["Добавить → Сканер"] --> AC["_ac_add_scanner"]
    AC --> Name["next(scanner_name)"]
    Name --> Add["add_scanner(name)"]
    Add --> Dev["_add_device(ScannerWidget)"]
```

### Имена по умолчанию (`scanner_name_generator`)

Генератор имён — статический метод `scanner_name_generator(start=1)`: `SCAN_1`, `SCAN_2`, …

| Ситуация | Поведение |
|----------|-----------|
| Ручное добавление через меню | `_ac_add_scanner` берёт `next(self.scanner_name)` и создаёт виджет |
| После `open_config` / `clear_ui` | `_sync_scanner_name_generator()` находит максимальный суффикс среди существующих виджетов с именами `SCAN_<число>` и сбрасывает итератор на `max_index + 1`, чтобы новые сканеры не пересекались с загруженными |

Произвольные имена (не `SCAN_N`) при загрузке JSON не влияют на итератор — учитываются только совпадающие с шаблоном `SCAN_<digits>`.

### Добавление на холст (`add_scanner`)

```python
def add_scanner(self, name: str, port_name: str = "") -> ScannerWidget:
    scn_w = ScannerWidget(name, port_name)
    self._add_device(scn_w)
    return scn_w
```

- Виджет попадает в `_device_widgets` и на холст `scaDevices` (`FlowLayout`).
- `_add_device` после вставки вызывает `setup_models(self._device_widgets)` у **всех** существующих `TransporterWidget` и `GeneratorWidget`, чтобы combo «откуда» / «куда» увидели новый сканер без перезапуска приложения.

### Сохранение и загрузка JSON

| Операция | Метод | Сканеры |
|----------|-------|---------|
| Сохранить | `save_configuration_to_file` | `scanners=[dev.options() for dev in _device_widgets if isinstance(dev, ScannerWidget)]` |
| Открыть | `open_config` → `clear_ui` → `process_config` | `_load_scanners(config.scanners, devices)` |

Порядок восстановления в `process_config`: принтеры → камеры → **сканеры** → перевозчики → генераторы. Для каждого элемента `scanners[]`:

1. `add_scanner(scn.name, scn.port_name)`
2. `scn_w.load_options(scn.config)` — параметры линии COM (`ScannerParams`)
3. `devices[scn_w.name] = id(scn_w)` — регистрация для привязки transport/generator
4. После цикла — `_sync_scanner_name_generator()`

`options()` / `load_options()` описаны в [frontend/scanner-widget.md](frontend/scanner-widget.md).

### Остановка при закрытии (`closeEvent`) и очистка (`clear_ui`)

При закрытии главного окна `closeEvent` вызывает `run(False)` для **перевозчиков**, **генераторов** и всех устройств на холсте (камеры, принтеры, **сканеры**). Это останавливает `CodeScheduler`, закрывает COM через `ScannerProxy` / `ScannerEmul` и снимает флаг Run в UI.

`clear_ui` (перед загрузкой другого JSON) останавливает и удаляет (`setParent(None)` + `deleteLater`) виджеты из `_device_widgets`, `_transporter_widgets` и **`_generator_widgets`**, затем снова синхронизирует `scanner_name` через `_sync_scanner_name_generator()`.

## Удаление виджета (`tbDelete` + Remove API, #2–#4)

План widget-delete-com-refresh (docs — **#5**). На всех пяти виджетах (Printer, Camera, Scanner, Transporter, Generator):

| Элемент | Описание |
|---------|----------|
| `tbDelete` | `QToolButton` 28×28, текст «X», tooltip «Удалить», сразу после `tbRun` в шапке формы |
| `delete_requested` | `Signal()` без аргументов |
| `_on_delete_clicked` | если `tbRun` включён → `QMessageBox.warning` без emit; иначе `question` → при Yes — `emit` |

Имя в диалоге: у устройств — `leName` (fallback `self.name`); у перевозчика/генератора — `self.name`.

`MainLineField` при `_add_*` подключает `delete_requested` → `_on_widget_delete_requested` → `_remove_device` / `_remove_transporter` / `_remove_generator` (pop из реестра, `run(False)`, `deleteLater`). После удаления device — `setup_models(self._device_widgets)` у всех transporters/generators; при удалении `ScannerWidget` — `_sync_scanner_name_generator()`.

Подробности — [frontend/widget-delete.md](frontend/widget-delete.md), шаги оператора — [user-guides/widget-delete.md](user-guides/widget-delete.md).

## Связь виджетов: Transport и Generator (#6)

`TransporterWidget` и `GeneratorWidget` подключают устройства линии через комбобоксы и ссылки на модели очередей (`QStandardItemModel`). После подзадачи **#6** в списках участвует `ScannerWidget` наравне с `CameraWidget`.

### Правила wiring

| Виджет | Combo | Допустимые устройства | Привязка модели |
|--------|-------|----------------------|-----------------|
| `TransporterWidget` | `cbxFrom` (источник) | камера, принтер, сканер | `model_in` ← `widget.model_out` |
| `TransporterWidget` | `cbxTo` (приёмник) | камера, сканер | `model_out` ← `widget.model_in` |
| `GeneratorWidget` | `cbxTo` (приёмник) | камера, сканер | `model_out` ← `widget.model_in` |

Сканер **не** фигурирует в `cbxTo` транспортёра как промежуточный «только приёмник без исходящей очереди» — у него есть и `model_in`, и `model_out`; как **источник** транспортёр читает `model_out` сканера (коды, подтверждённые записью в COM).

```mermaid
flowchart LR
    subgraph sources["Источник cbxFrom"]
        CamOut["CameraWidget.model_out"]
        PrnOut["PrinterWidget.model_out"]
        ScnOut["ScannerWidget.model_out"]
    end
    TR["TransporterWidget"]
  subgraph sinks["Приёмник cbxTo / Generator.cbxTo"]
        CamIn["CameraWidget.model_in"]
        ScnIn["ScannerWidget.model_in"]
    end
    CamOut --> TR
    PrnOut --> TR
    ScnOut --> TR
    TR --> CamIn
    TR --> ScnIn
    GEN["GeneratorWidget"] --> CamIn
    GEN --> ScnIn
```

### Обновление списков (`setup_models`)

`MainLineField` передаёт в `setup_models(device_widgets)` словарь `{id(widget): widget}` всех устройств на холсте (в т.ч. после `_add_device` и `_remove_device`).

1. Виджет **всегда** выполняет полную замену: `_device_data = dict(device_widgets)` (не `update`) — удалённые id не остаются в реестре.
2. Если `tbRun` включён — return **без** пересборки combo (защита от смены маршрута во время работы).
3. Если остановлен — перестраивает модели combo:
   - **Транспортёр** — `get_data_models()` → `from_model` (все устройства), `to_model` (только `CameraWidget` и `ScannerWidget`).
   - **Генератор** — `get_data_models()` → `to_model` (только `CameraWidget` и `ScannerWidget`).

### Null guards

| Метод | Условие | Реакция |
|-------|---------|---------|
| `TransporterWidget.set_from_model` / `set_to_model` | виджет не найден в combo (`data is None` или нет в `_device_data`) | `warning` в `UI_LOGGER`, привязка не меняется |
| `TransporterWidget.send_data` | `model_in is None` или `model_out is None` | `warning` «Не заданы источники», выход |
| `GeneratorWidget.set_to_model` | виджет не выбран | `warning` «Не выбран приёмник», выход |
| `GeneratorWidget.send_data` | `model_out is None` | `warning` «Не задан приёмник», выход |

При старте Run транспортёр вызывает `set_from_model()` и `set_to_model()`; генератор — `set_to_model()` для актуализации ссылок после смены combo.

Подробности callback и `CodeScheduler` — в [code_scheduler.md](code_scheduler.md) (разделы TransporterWidget, GeneratorWidget). Контракт `model_in` / `model_out` сканера — в [frontend/scanner-widget.md](frontend/scanner-widget.md).

## Массовое управление виджетами (#10)

Меню **«Управление»** (`menuControl` в `forms/ui/Main.ui`) — массовый запуск, остановка и очистка очередей по типам виджетов. Реализация в `MainLineField`: `_setup_bulk_control_connections()`, `_bulk_start_*`, `_bulk_stop_*`, `_bulk_clear_*`.

| Подменю | Пункты | Действие |
|---------|--------|----------|
| Запустить | Всё, Принтеры, Камеры, Сканеры, Перевозчики, Генераторы | `tbRun.setChecked(True)` только для остановленных |
| Остановить | те же | `tbRun.setChecked(False)` только для запущенных |
| Очистить данные | Всё, Принтеры, Камеры, Сканеры | `clear_data()` без остановки Run |

**Порядок «Всё»:** запуск — устройства (принтеры → камеры → сканеры) → перевозчики → генераторы; остановка — в обратном порядке (внутри группы устройств — `reversed`).

Публичный `clear_data()` на `PrinterWidget`, `CameraWidget`, `ScannerWidget` сбрасывает UI-модели и буферы ядра (`PrinterProxy.clear_buffer`, `CameraProxy.clear_queues`, `ScannerProxy.clear_queues`). Перевозчики и генераторы в «Очистить» не входят.

Подробности, таблицы QAction, диаграммы pipeline и тесты — в [bulk-control.md](bulk-control.md).

## Запуск

```powershell
.\venv\Scripts\python.exe main.py
```

Логирование инициализируется в `setup_logging()`; рабочие каталоги — `client_info.WORKDIR`, `client_info.RUNDIR`.

## Сборка exe (PyInstaller)

Подзадача **#9** плана эмулятора сканера: зависимости сканера (`pyserial`, `QtAwesome`) должны попадать в собранный дистрибутив.

### Команда сборки

```powershell
.\venv\Scripts\python.exe build_project.py
```

Скрипт пересобирает UI из `forms/ui/*.ui`, затем вызывает PyInstaller по `build/spec/main.spec`. Итоговый каталог:

`build/install/dmcLineEmulator/dmcLineEmulator.exe`

### Spec-файл `build/spec/main.spec`

| Элемент | Назначение |
|---------|------------|
| Точка входа | `main.py` |
| Имя exe | `dmcLineEmulator` |
| `hiddenimports` | `serial`, `serial.tools.list_ports` — перечисление и открытие COM (`libs/serial_port`); `qtawesome`, `qtawesome.iconic_font` — иконки `btnSend` и `tbRefreshPorts` в `ScannerWidget` |
| `datas` | Каталог шрифтов QtAwesome (`qtawesome/fonts`) — без него иконки в frozen-сборке не отображаются |
| Прочие `hiddenimports` | `pylibdmtx`, `psycopg`, `shortuuid` — уже использовались эмулятором до сканера |

Зависимости в `requirements.txt`:

| Пакет | Версия | Где используется |
|-------|--------|------------------|
| `pyserial` | `3.5` | `libs/serial_port.py`, ядро `ScannerEmul` |
| `QtAwesome` | `1.3.1` | `core/barcode_scanner/scanner_widget.py` (`btnSend`, `tbRefreshPorts`) |

PyInstaller не всегда подхватывает подмодули `serial.tools.list_ports` и ресурсы QtAwesome статическим анализом — поэтому они указаны явно в `hiddenimports` и `datas`.

### Версия приложения

Номер сборки — `client_info.VERSION` в корне репозитория. Текущая версия: `1.0.0.1.b0005` (удаление виджетов + COM refresh); ранее `1.0.0.1.b0004` (Remove API), `1.0.0.1.b0003` (`tbDelete` / `delete_requested`), `1.0.0.1.b0002` (fix-qt-light-theme), `1.0.0.1.b0001` (релиз с эмулятором сканера ШК). Последний разряд увеличивается по соглашениям версионирования проекта.

## Связанная документация

- [model_processing_timing.md](model_processing_timing.md) — метки времени, FIFO-готовность, API хелперов, точки входа pipeline (#1, #3 плана per-code interval).
- [code_scheduler.md](code_scheduler.md) — `CodeScheduler`, тик 10 мс, API `start`/`stop`; интеграция в `CameraWidget` (#4), `TransporterWidget` (#5) и `GeneratorWidget` (#6).
- Раздел «Связь виджетов: Transport и Generator» выше — `ScannerWidget` в combo, wiring `model_in`/`model_out`, null guards (подзадача #6 плана serial barcode scanner).
- Раздел «Интеграция сканера в главное окно» выше — `acAddScanner`, save/load `scanners`, `closeEvent`, `_sync_scanner_name_generator`, `setup_models` при `_add_device` (подзадача #5 плана serial barcode scanner).
- Раздел «Конфигурация JSON» выше — `ScannerParams`, `ScannerConfig`, секция `scanners` в `ConfigFile`, `to_serial_port_config()` (подзадача #2 плана serial barcode scanner).
- [frontend/scanner-widget.md](frontend/scanner-widget.md) — `ScannerWidget`, COM refresh (`tbRefreshPorts`), `tbDelete` / `delete_requested`, интеграция с transport/generator (#6).
- [frontend/scanner-ui.md](frontend/scanner-ui.md) — макет `Scanner.ui` (в т.ч. `tbRefreshPorts`, `tbDelete`).
- [frontend/widget-delete.md](frontend/widget-delete.md) — `tbDelete` / `delete_requested`, Remove API в `MainLineField`, unit-тесты `test_widget_delete.py` (план widget-delete-com-refresh, #2–#5).
- Раздел «Удаление виджета» выше — UI, сигнал и снятие с холста; `clear_ui`/`closeEvent` для generators; `setup_models` с полной заменой `_device_data`.
- [scanner_serial.md](scanner_serial.md) — инфраструктура Serial (`libs/serial_port`), `ScannerEmul`, `ScannerProxy`, `SCANNER_LOGGER` (подзадача #1 плана эмулятора сканера).
- [scanner_unit_tests.md](scanner_unit_tests.md) — unit-тесты подсистемы сканера: mock COM, `ScannerEmul` без Qt, `ConfigFile.scanners`, wiring в transport/generator; COM refresh — `test_scanner_com_refresh.py`; Remove API — см. [frontend/widget-delete.md](frontend/widget-delete.md).
- [com0com_setup.md](com0com_setup.md) — настройка виртуальных COM-портов com0com для тестирования сканера (подзадача #9).
- [bulk-control.md](bulk-control.md) — меню «Управление», массовый start/stop/clear, `clear_data()` API, порядок pipeline (подзадача #10 плана serial barcode scanner).
- Раздел «Сборка exe (PyInstaller)» выше — `main.spec`, hiddenimports `pyserial`/`qtawesome`, `scanner_example.json`, `VERSION` (подзадача #9).
- [user-guides/scanner-widget.md](user-guides/scanner-widget.md) — пользовательские шаги: выбор COM, обновление списка портов (`tbRefreshPorts`), Run/Stop, удаление (`tbDelete`).
- [user-guides/widget-delete.md](user-guides/widget-delete.md) — удаление любого виджета кнопкой «X» с холста.
