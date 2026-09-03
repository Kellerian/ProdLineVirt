# Визуальные фоны виджетов на холсте

| Параметр | Значение |
|----------|----------|
| План | serial-barcode-scanner-bulk-control **#7**; централизация QSS — UI modernization **#11** |
| Область | Layout в `forms/ui/*.ui`; все стили — `media/themes/theme_*.qss` + `libs/qt_theme.py` |
| Потребители | `*Widget` в `core/*/` — наследуют `Ui_Form` и отображаются в `FlowLayout` главного окна |

## Назначение

На холсте `MainLineField` одновременно могут находиться десятки виджетов разных типов (принтер, камера, сканер, перевозчик, генератор). У каждого типа задан **светлый фон** корневой формы, чтобы оператор быстро отличал роль узла без чтения подписи.

Фоны не влияют на бизнес-логику: это только QSS корневого `QWidget` с `objectName` **Form** и dynamic property **`deviceType`**.

> **UI modernization (#11–#12):** per-form QSS удалён из `forms/ui/*.ui`; палитра и селекторы `QWidget#Form[deviceType=…]` — единственный источник в `media/themes/theme_*.qss` и `libs/qt_theme.py`. Property `deviceType` задаёт `DeviceCardMixin` (**#5**). Глобальный QSS подключается через `apply_theme(app, ThemeMode(...))` → `theme_light.qss` или `theme_dark.qss` (**#12**); предпочтение — user settings + меню «Вид». См. [theme-system.md](theme-system.md), [qt_theme.md](../qt_theme.md), [layout-and-docking.md](layout-and-docking.md).

## Реализация

Цвет задаётся в `media/themes/theme_light.qss` / `theme_dark.qss` селекторами по dynamic property `deviceType` (рамка — общий `QWidget#Form`, фон — `QWidget#Form[deviceType="…"]`):

```css
QWidget#Form {
    border: 1px solid #17365D;
    border-radius: 3px;
}

QWidget#Form[deviceType="printer"] {
    background-color: #fff3e0;
}
/* … camera, scanner, transporter, generator … */
```

| Аспект | Деталь |
|--------|--------|
| Селектор | `QWidget#Form[deviceType=…]` — только корневой виджет формы |
| Property | `deviceType` — `printer` / `camera` / `scanner` / `transporter` / `generator`; устанавливает `DeviceCardMixin.apply_device_type` |
| Рамка | `#17365D` (light), `#5a8ab0` (dark), радиус 3 px |
| Элементы управления | Кнопки, combo, menu, scrollbar — в том же `theme_*.qss` (**#11**) |
| Шрифт UI | sans-serif (`font_ui`); monospace — только `QListView#lstData`, tech `QLineEdit` |

Каждый виджет-потребитель создаётся как `QWidget` с `objectName` `Form` через `Ui_Form.setupUi(self)`; после `mount_device_card_header` на корне есть `deviceType` для QSS.

## Палитра по типам виджетов

| Тип виджета | Класс | Макет Qt Designer | Сгенерированный модуль | Цвет фона | Примечание |
|-------------|-------|-------------------|------------------------|-----------|------------|
| Принтер | `PrinterWidget` | `forms/ui/Printer.ui` | `forms/Printer.py` | `#fff3e0` | тёплый оранжевый (orange 50) |
| Камера | `CameraWidget` | `forms/ui/Camera.ui` | `forms/Camera.py` | `#e8f5e9` | светло-зелёный (green 50) |
| Сканер ШК | `ScannerWidget` | `forms/ui/Scanner.ui` | `forms/Scanner.py` | `#f3e5f5` | светло-фиолетовый (purple 50); задан ещё в подзадаче #3 |
| Перевозчик | `TransporterWidget` | `forms/ui/Transporter.ui` | `forms/Transporter.py` | `#e3f2fd` | светло-голубой (blue 50) |
| Генератор | `GeneratorWidget` | `forms/ui/Generator.ui` | `forms/Generator.py` | `#fff9c4` | янтарный (amber 100) |

**Различимость Generator и Printer:** изначально для генератора планировался `#fffde7` (yellow 50), близкий к `#fff3e0` принтера. В design system принят **`#fff9c4`** (`device_generator` / `deviceType="generator"`) — более насыщенный жёлтый.

## Визуальная схема на холсте

```text
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  #fff3e0    │  │  #e8f5e9    │  │  #f3e5f5    │
│  Printer    │  │  Camera     │  │  Scanner    │
└─────────────┘  └─────────────┘  └─────────────┘

┌─────────────┐  ┌─────────────┐
│  #e3f2fd    │  │  #fff9c4    │
│ Transporter │  │  Generator  │
└─────────────┘  └─────────────┘
```

Контраст текста и кнопок на светлом фоне обеспечивается глобальным theme QSS (**#11**): тёмные кнопки на светлой подложке формы.

## Изменение цвета

1. Обновить token в `libs/qt_theme.py` (`LIGHT` / `DARK` → `device_*`).
2. Синхронно обновить hex в `media/themes/theme_light.qss` и `theme_dark.qss` (селектор `QWidget#Form[deviceType="…"]`).
3. Перезапустить приложение — `forms/ui/*.ui` и `forms/*.py` **не** содержат фонов; регенерация UIC не требуется.

**Источник истины** — `libs/qt_theme.py` + `media/themes/*.qss`.

## Критерии готовности (подзадача #7)

- [x] Светлый фон `QWidget#Form` для принтера, камеры, сканера, перевозчика и генератора.
- [x] Типы визуально различимы на холсте при типичном количестве виджетов.
- [x] Читаемость подписей, placeholders и кнопок R/S на фоне формы сохранена.

## QSS меню главного окна (fix-qt-light-theme, подзадача **#3**)

| Параметр | Значение |
|----------|----------|
| План | fix-qt-light-theme, подзадача **#3** |
| Макет | `forms/ui/Main.ui` → `QMainWindow` |
| Сгенерированный модуль | `forms/Main.py` |
| Потребитель | `MainLineField` в `core/main_ui/line_emul.py` |

### Назначение

Строка меню (`QMenuBar`) и выпадающие подменю (`QMenu`) главного окна **без QSS** на Windows 11 с системной тёмной темой рендерятся нативно и остаются тёмными при светлых формах на холсте. Правила `QMenuBar` и `QMenu` в **`media/themes/theme_light.qss`** (и `theme_dark.qss`) принудительно задают палитру и акцентные цвета.

> **#11:** inline QSS удалён из `forms/ui/Main.ui`; правила перенесены в theme QSS.

### Структура меню

| Пункт `QMenuBar` | `objectName` | Вложенные подменю |
|------------------|--------------|-------------------|
| **Добавить** | `menu` | — (плоский список действий: камера, принтер, сканер, перевозчик, генератор) |
| **Файл** | `menu_2` | — (открыть, сохранить, закрыть) |
| **Управление** | `menuControl` | **Запустить** (`menuControlStart`), **Остановить** (`menuControlStop`), **Очистить данные** (`menuControlClear`) |

Все перечисленные `QMenu` наследуют один набор QSS-селекторов `QMenu` / `QMenu::item` — отдельные правила по `objectName` не требуются.

### Палитра

| Элемент | Состояние | Фон | Текст / линия |
|---------|-----------|-----|----------------|
| `QMenuBar` | обычное | `#ffffff` | `#17365D` |
| `QMenuBar::item` | обычное | прозрачный | `#17365D` |
| `QMenuBar::item` | `:selected`, `:pressed` | `#226091` | `#f0b321` |
| `QMenu` | обычное | `#f5f5f5` | `#17365D`; рамка `1px solid #17365D` |
| `QMenu::separator` | — | линия `#17365D`, высота 1 px | отступы `4px 8px` |
| `QMenu::item` | обычное | прозрачный | `#17365D` |
| `QMenu::item` | `:selected` | `#226091` | `#f0b321` |

Цвета `#17365D`, `#226091` и `#f0b321` совпадают с рамкой `QWidget#Form`, фоном кнопок/combo и акцентом выделения на виджетах устройств (см. таблицу «Элементы управления» выше).

### Фрагмент QSS (источник истины — `media/themes/theme_light.qss`)

```css
QMenuBar {
    background-color: #ffffff;
    color: #17365D;
}

QMenuBar::item {
    background-color: transparent;
    color: #17365D;
    padding: 2px 8px;
}

QMenuBar::item:selected {
    background-color: #226091;
    color: #f0b321;
}

QMenuBar::item:pressed {
    background-color: #226091;
    color: #f0b321;
}

QMenu {
    background-color: #f5f5f5;
    color: #17365D;
    border: 1px solid #17365D;
}

QMenu::separator {
    height: 1px;
    background: #17365D;
    margin: 4px 8px;
}

QMenu::item {
    background-color: transparent;
    color: #17365D;
    padding: 4px 24px 4px 8px;
}

QMenu::item:selected {
    background-color: #226091;
    color: #f0b321;
}
```

Селектор `QMenuBar::item:pressed` и `QMenu::separator` добавлены по итогам code-review: без `:pressed` подсветка пункта строки меню при нажатии могла отличаться от `:selected`; без `::separator` разделители в подменю наследовали системный тёмный рендер.

### Изменение стилей меню

1. Отредактировать блок `QMenuBar` / `QMenu` в `media/themes/theme_light.qss` и/или `theme_dark.qss`.
2. Синхронизировать tokens в `libs/qt_theme.py` при смене hex.

`forms/ui/Main.ui` не содержит QSS; `forms/Main.py` не редактируют вручную.

### Критерии готовности (подзадача #3)

- [x] Меню **Добавить**, **Файл**, **Управление** и вложенные подменю читаемы при системной тёмной теме Windows 11.
- [x] Светлый фон строки меню и выпадающих списков; текст `#17365D`; выделение `#226091` / `#f0b321`.
- [x] Разделители в подменю видимы на светлом фоне (`QMenu::separator`).

### Связь с Qt-стилем приложения

QSS меню дополняет смену Qt-стиля через `apply_theme` / `apply_qt_style` (подзадачи **#1–#2**, **#11**, **#12**). На Windows light — `windowsvista` + `theme_light.qss`; dark — platform style + `theme_dark.qss`. Стиль приложения влияет на отрисовку popup в целом; глобальный QSS фиксирует `QMenuBar`/`QMenu`. Подробности — [qt_theme.md](../qt_theme.md).

QSS popup `QComboBox` в формах устройств — подзадача **#4** (раздел ниже). Сводка всех слоёв фикса — раздел [«Тема Windows»](#тема-windows) ниже.

## QSS popup QComboBox в device-формах (fix-qt-light-theme, подзадача **#4**)

| Параметр | Значение |
|----------|----------|
| План | fix-qt-light-theme, подзадача **#4** |
| Макеты | `forms/ui/{Camera,Printer,Scanner,Transporter,Generator}.ui` |
| Сгенерированные модули | `forms/{Camera,Printer,Scanner,Transporter,Generator}.py` |
| Потребители | `CameraWidget`, `PrinterWidget`, `ScannerWidget`, `TransporterWidget`, `GeneratorWidget` |

### Назначение

На Windows 11 с системной тёмной темой popup `QComboBox` мог отрисовываться нативно (тёмный фон, нечитаемый текст), даже при светлом QSS закрытого поля combo. Селектор `QComboBox QListView { ... }` в Qt 6.7 **не всегда применяется** к выпадающему списку.

Правки в **`media/themes/theme_*.qss`** (ранее — в `styleSheet` пяти device-форм) принудительно задают светлую читаемую палитру popup и отдельных пунктов списка. Закрытое поле combo (фон `#226091`, текст `#f0b321`) и остальные стили кнопок — в том же theme QSS (**#11**).

### Затронутые combo

| Макет | Файл | Combo с popup | Примечание |
|-------|------|---------------|------------|
| Камера | `forms/ui/Camera.ui` | общие правила | `cbxProduct` — расширенная ширина popup |
| Принтер | `forms/ui/Printer.ui` | общие правила | `cbxProduct` — расширенная ширина popup |
| Сканер | `forms/ui/Scanner.ui` | `cbxComPort` | только общие правила popup |
| Перевозчик | `forms/ui/Transporter.ui` | `cbxFrom`, `cbxTo` | `cbxProduct` — расширенная ширина popup |
| Генератор | `forms/ui/Generator.ui` | `cbxCodeType`, `cbxTo` | `cbxProduct` — расширенная ширина popup |

### Изменение селекторов

**Было:** `QComboBox QListView { ... }` — стили popup не гарантированы в Qt 6.7.

**Стало:** `QComboBox QAbstractItemView { ... }` плюс псевдо-селекторы пунктов:

```css
QComboBox QAbstractItemView {
    selection-background-color: #f0b321;
    selection-color: #19466a;
    color: #f0b321;
    background-color: #19466a;
    border: 2px solid #f0b321;
}

QComboBox::item {
    color: #f0b321;
    background-color: #19466a;
}

QComboBox::item:hover {
    background-color: #226091;
}

QComboBox::item:selected {
    background-color: #f0b321;
    color: #19466a;
}
```

| Состояние popup | Фон | Текст |
|-----------------|-----|-------|
| Список (по умолчанию) | `#19466a` | `#f0b321` |
| Пункт при наведении (`::item:hover`) | `#226091` | `#f0b321` |
| Выбранный пункт (`::item:selected`) | `#f0b321` | `#19466a` |
| Рамка списка | — | `2px solid #f0b321` |

Селектор `QAbstractItemView` охватывает view popup независимо от внутренней реализации (`QListView` и др.). Псевдо-селекторы `::item`, `::item:hover`, `::item:selected` задают цвета **отдельных строк** — без них Qt 6.7 может отдать нативную тёмную отрисовку пунктов.

### Ширина popup продукта

В `media/themes/theme_*.qss` — правило для combo с `objectName` **cbxProduct** (формы `Camera`, `Printer`, `Transporter`, `Generator`):

```css
QComboBox#cbxProduct QAbstractItemView {
    min-width: 800px;
}
```

В `Scanner.ui` отдельного `cbxProduct` нет — для `cbxComPort` действуют только общие правила popup.

### Изменение стилей popup combo

1. Отредактировать блок `QComboBox QAbstractItemView` / `QComboBox::item` в `media/themes/theme_light.qss` и/или `theme_dark.qss`.
2. Синхронизировать tokens в `libs/qt_theme.py` при смене hex.

`forms/ui/{Camera,Printer,Scanner,Transporter,Generator}.ui` не содержат QSS; `forms/*.py` не редактируют вручную.

### Критерии готовности (подзадача #4)

- [x] В пяти device-формах `QComboBox QListView` заменён на `QComboBox QAbstractItemView`.
- [x] Добавлены `QComboBox::item`, `QComboBox::item:hover`, `QComboBox::item:selected`.
- [x] Popup combo: золотой текст `#f0b321` на фоне `#19466a`; выделение `#f0b321` / `#19466a`.
- [x] Правило `QComboBox#cbxProduct QAbstractItemView { min-width: 800px; }` сохранено где было.

### Связь с Qt-стилем приложения

QSS popup combo дополняет смену Qt-стиля через `apply_theme` / `apply_qt_style` (подзадачи **#1–#2**, **#11**, **#12**). Стиль приложения влияет на отрисовку popup в целом; глобальный QSS из `theme_*.qss` фиксирует выпадающие списки `QComboBox`. Подробности — [qt_theme.md](../qt_theme.md).

## Регенерация Python-модулей форм

| Параметр | Значение |
|----------|----------|
| Планы | fix-qt-light-theme **#5** (синхронизация UIC); UI modernization **#11** (удаление QSS из `.ui`) |
| Компилятор | Qt User Interface Compiler **6.7.1** (PySide6) |
| Источник layout | `forms/ui/*.ui` — geometry, widgets, `objectName`; **без** `styleSheet` |
| Стили | `media/themes/theme_*.qss` — не проходят через UIC |
| Сгенерированные модули | `forms/{Main,Camera,Printer,Scanner,Transporter,Generator}.py` |

### Назначение

После правок **layout** в Qt Designer Python-модули форм **перегенерируются** из `.ui`. Ручные правки в `forms/*.py` запрещены — при регенерации они теряются (заголовок файла: *«WARNING! All changes made in this file will be lost when recompiling UI file!»*).

С **#11** per-form `styleSheet` удалён из всех device `.ui`; `Main.ui` не содержал inline QSS. Регенерация UIC **не** переносит QSS — стили задаются только глобальным theme QSS через `apply_theme()`.

### Синхронизированные модули

| Сгенерированный модуль | Макет | Содержимое `.ui` |
|------------------------|-------|------------------|
| `forms/Main.py` | `forms/ui/Main.ui` | layout shell, меню, docks — без QSS |
| `forms/Camera.py` … `forms/Generator.py` | `forms/ui/{Camera,…,Generator}.ui` | layout device-карточек, `objectName` `Form` — без QSS |

Исторически QSS menu/combo переносились через `.ui` (fix-qt-light-theme **#3–#4**); с **#11** единственный источник — `theme_*.qss`.

### Инструмент и обёртка `pyside6-uic`

Рабочий компилятор в venv проекта:

```powershell
$UIC = ".\venv\Lib\site-packages\PySide6\uic.exe"
```

Проверка версии: `& $UIC --version` → `uic 6.7.1`.

**Обёртка `.\venv\Scripts\pyside6-uic.exe` в текущем venv неработоспособна** (завершается с кодом ошибки без вывода). До восстановления entry point используйте прямой вызов `$UIC` (команды ниже).

Флаги совпадают с `build_project.py` → `generate_ui_files()`:

| Флаг | Назначение |
|------|------------|
| `-g python` | генератор Python (по умолчанию для `pyside6-uic`, для `uic.exe` указывать явно) |
| `--rc-prefix` | импорт ресурсов как `rc_<file>`, а не `<file>_rc` |
| `-o <path>` | выходной `forms/<Name>.py` |

### Команды (все формы линии)

Из корня репозитория, PowerShell:

```powershell
$UIC = ".\venv\Lib\site-packages\PySide6\uic.exe"

& $UIC forms/ui/Main.ui -o forms/Main.py -g python --rc-prefix
& $UIC forms/ui/Camera.ui -o forms/Camera.py -g python --rc-prefix
& $UIC forms/ui/Printer.ui -o forms/Printer.py -g python --rc-prefix
& $UIC forms/ui/Scanner.ui -o forms/Scanner.py -g python --rc-prefix
& $UIC forms/ui/Transporter.ui -o forms/Transporter.py -g python --rc-prefix
& $UIC forms/ui/Generator.ui -o forms/Generator.py -g python --rc-prefix
```

Для одной формы достаточно одной строки с нужным `.ui`.

### Альтернатива: `build_project.py`

`generate_ui_files()` в `build_project.py` обходит все `**/*.ui` в каталогах с именем `ui` и запускает `pyside6-uic` из **PATH** shell-процесса:

```python
command = f"pyside6-uic {file_to_convert} -o {output_file} --rc-prefix"
```

Из-за неработающей обёртки в `venv\Scripts` и возможного другого `pyside6-uic` в системном PATH полная сборка **может не перегенерировать** формы линии. Для правок только UI форм эмулятора надёжнее команды с `$UIC` выше.

Точечный вызов без PyInstaller-сборки (с тем же ограничением по PATH):

```powershell
.\venv\Scripts\python.exe -c "from build_project import generate_ui_files; generate_ui_files()"
```

### Критерии готовности

- [x] Шесть модулей `forms/{Main,Camera,Printer,Scanner,Transporter,Generator}.py` синхронны с `forms/ui/*.ui` (fix-qt-light-theme **#5**).
- [x] Per-form `styleSheet` удалён из device `.ui`; `forms/*.py` не содержат QSS (**#11**).
- [x] Ручных правок в сгенерированных `.py` нет; заголовок — Qt UIC 6.7.1.

## Тема Windows

| Параметр | Значение |
|----------|----------|
| План | fix-qt-light-theme (**#1–#6**); runtime light/dark/system — UI modernization **#12**, **#14** |
| Версия | `1.0.0.1.b0006` (`client_info.VERSION`; UI modernization release) |
| Платформа | Windows 11 + `QT_QPA_PLATFORM=windows:darkmode=0` в `main.py` |
| Точка входа | `main.py` → `load_user_settings()` + `apply_theme(app, ThemeMode(...))` до `MainLineField()` |

### Проблема

Светлые фоны `QWidget#Form` (разделы выше) и кастомный QSS кнопок/combo задают **внешний вид форм на холсте**, но при дефолтном стиле **Windows 11** (Qt 6.7 / PySide6 6.7.1) popup-элементы рендерятся нативно и остаются тёмными:

- строка меню и подменю `QMenuBar` / `QMenu` главного окна;
- выпадающие списки `QComboBox` на виджетах устройств.

Поведение совпадает с [известным багом Qt 6.7](https://forum.qt.io/topic/156611/qt6-7-0-force-light-mode-has-incorrect-rendering-when-system-is-dark-mode). Переменная `windows:darkmode=0` отключает тёмную рамку окна, но **не** устраняет битый рендер popup.

### Многослойный фикс

Фикс состоит из смены Qt-стиля на уровне `QApplication` и дополнительного QSS там, где нативный рендер всё ещё проскакивает:

| Слой | Подзадача | Модуль / макет | Что делает |
|------|-----------|----------------|------------|
| **1. Qt-стиль + QSS** | #1–#2, **#11**, **#12** | `libs/qt_theme.py`, `main.py` | `apply_theme(app, ThemeMode(...))` → `apply_qt_style` + `theme_light.qss` или `theme_dark.qss` |
| **2. QSS меню** | #3, **#11**, **#12** | `media/themes/theme_*.qss` | `QMenuBar` / `QMenu` — [раздел выше](#qss-меню-главного-окна-fix-qt-light-theme-подзадача-3) |
| **3. QSS popup combo + device cards** | #4, **#11**, **#12** | `media/themes/theme_*.qss` | `QAbstractItemView` + `::item` + `deviceType` фоны — [разделы выше](#qss-popup-qcombobox-в-device-формах-fix-qt-light-theme-подзадача-4) |
| **Синхронизация `.py`** | #5, **#11** | `forms/*.py` ← `forms/ui/*.ui` | UIC только layout/geometry; QSS не в `.ui` |
| **User preference** | **#12** | `user_settings.py`, меню «Вид» | `theme_preference` в `line_emulator_user.json`, не в project JSON |

Слои **дополняют** друг друга: стиль `windowsvista` задаёт базовую отрисовку popup; QSS фиксирует палитру конкретных виджетов, которые иначе наследуют системную тёмную тему.

```text
main.py
  ├─ QT_QPA_PLATFORM=windows:darkmode=0
  ├─ setup_logging()
  ├─ QApplication(sys.argv)
  ├─ load_user_settings()
  ├─ apply_theme(app, ThemeMode(...))   ← apply_qt_style + theme_*.qss (#12)
  └─ MainLineField()
       └─ device widgets             ← deviceType → фон из theme QSS
```

Подробности API `apply_theme`, контекст бага и полный порядок вызова — в [qt_theme.md](../qt_theme.md). Разделение theme vs project layout — [layout-and-docking.md](layout-and-docking.md).

### Порядок запуска (`main.py`)

| Шаг | Действие |
|-----|----------|
| 1 | `os.environ['QT_QPA_PLATFORM'] = "windows:darkmode=0"` (только Windows) |
| 2 | `setup_logging()` — инициализация логгеров до GUI |
| 3 | `app = QApplication(sys.argv)` |
| 4 | `load_user_settings()` |
| 5 | `apply_theme(app, ThemeMode(user_settings.theme_preference))` — до создания главного окна |
| 6 | `MainLineField()` → `show()` → `app.exec()` |

На Linux `apply_qt_style` для light/dark — no-op (стиль не меняется); QSS применяется. На macOS переменная `QT_QPA_PLATFORM` не задаётся.

### Регенерация форм

После правок `.ui` пересоберите `forms/*.py` — [раздел «Регенерация Python-модулей форм»](#регенерация-python-модулей-форм-fix-qt-light-theme-подзадача-5) (подзадача **#5**): прямой `PySide6\uic.exe`, флаги `-g python --rc-prefix`, примечание о неработающей обёртке `pyside6-uic` в venv.

### Проверка (Windows 11, системная тёмная тема)

1. `.\venv\Scripts\python.exe main.py`
2. Меню **Добавить / Файл / Управление** — светлый фон, текст `#17365D`, выделение `#226091` / `#f0b321`
3. Popup `QComboBox` (COM-порт сканера, продукт, from/to) — золотой текст `#f0b321` на фоне `#19466a`
4. Светлые фоны виджетов на холсте без регрессии

### Вне scope (исторически)

- Нативные `QFileDialog` в `core/main_ui/line_emul.py` — при необходимости отдельная задача (`QFileDialog.DontUseNativeDialog`)

С **#12** полная тёмная тема UI (menu, combo, device cards, dock shell) реализована через `theme_dark.qss` + `apply_theme(DARK)`.

### Критерии готовности (план fix-qt-light-theme + #11–#12)

- [x] `libs/qt_theme.py` — `apply_theme` + `apply_qt_style` + `theme_*.qss` на Windows (**#11**, **#12**)
- [x] `main.py` — `load_user_settings` + `apply_theme` после `QApplication`, до `MainLineField`
- [x] Menu / combo / device backgrounds — в `media/themes/theme_*.qss`, не в `.ui` (**#11**)
- [x] Пять device-форм — popup через `QAbstractItemView` + `::item` (исторически **#4**, сейчас theme QSS)
- [x] `forms/*.py` синхронны с `.ui` (layout only)
- [x] `build/spec/main.spec` — `media/themes` в `datas` (**#11**); UI-модули в `hiddenimports` (**#14**)

### Критерии готовности (UI modernization #11–#12)

- [x] Per-form QSS и per-widget DejaVu fonts удалены из `forms/ui/{Printer,Camera,Scanner,Transporter,Generator}.ui`.
- [x] `deviceType` backgrounds, controls, typography — глобальный theme QSS.
- [x] `apply_theme()` загружает `theme_light.qss` или `theme_dark.qss` по resolved mode.

## Связанная документация

- [qt_theme.md](../qt_theme.md) — модуль `libs/qt_theme.py`, `apply_theme`, API и контекст бага Qt 6.7.
- [layout-and-docking.md](layout-and-docking.md) — theme в user settings vs layout в project JSON.
- [theme-system.md](theme-system.md) — централизованная design system (#3, **#11–#12**), слои QSS.
- [scanner-ui.md](scanner-ui.md) — макет и стиль формы сканера (`#f3e5f5`), сравнение с `Printer.ui`; popup `cbxComPort` (подзадача #4); генерация `Scanner.py` — см. также [регенерацию форм](#регенерация-python-модулей-форм-fix-qt-light-theme-подзадача-5) (подзадача #5).
- [line_emulator.md](../line_emulator.md) — обзор приложения и размещение виджетов на холсте; меню **Управление** и массовые операции.
