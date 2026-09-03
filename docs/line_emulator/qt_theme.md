# Design system и Qt theme (`libs/qt_theme.py`)

| Параметр | Значение |
|----------|----------|
| Модуль | `libs/qt_theme.py` |
| QSS | `media/themes/theme_light.qss`, `media/themes/theme_dark.qss` |
| План | UI modernization Line Emulator, подзадачи **#3**, **#11**, **#12**, **#14** |
| User settings | `core/main_ui/user_settings.py` → `theme_preference` (подзадача **#2**, см. [user_settings.md](user_settings.md)) |
| Точка входа | `main.py` → `load_user_settings()` + `apply_theme(app, ThemeMode(...))` (**#12**) |
| Меню переключения | `MainLineField` → «Вид» → «Как в системе» / «Светлая» / «Тёмная» (**#12**) |
| Архитектура UI | [frontend/theme-system.md](frontend/theme-system.md) |
| Тесты | `tests/test_libs/test_qt_theme.py` (**9** тестов, **#12** + **#13** ✓) |

## Назначение

Централизованная **design system** для Line Emulator:

- Python-tokens (`DesignTokens`, константы `LIGHT` / `DARK`) — палитра, типографика, фоны карточек по типу устройства;
- QSS-файлы в `media/themes/` — правила для controls, меню, combo popup, dock/scroll, `deviceType` backgrounds;
- API загрузки и применения темы (`load_stylesheet`, `apply_theme`, `apply_light_theme`, `resolve_effective_mode`, `apply_qt_style`).

Подзадача **#3** создала скелет tokens и QSS. **#11** удалила duplicate QSS из `forms/ui/*.ui`, подключила глобальный QSS и bundling `media/themes/` в PyInstaller. **#12** заменила hardcoded light на `UserSettings.theme_preference`, добавила тёмную тему в runtime, меню «Вид» и polish shell (`QMainWindow`, `QDockWidget`, `QScrollArea`).

## Два источника палитры

Hex-значения дублируются в Python и QSS **намеренно** (Qt QSS не читает Python-константы):

| Слой | Файл | Роль |
|------|------|------|
| Tokens | `libs/qt_theme.py` → `LIGHT`, `DARK` | Программный доступ (`get_tokens`), тесты, runtime-логика без парсинга QSS |
| Стили | `media/themes/theme_<mode>.qss` | Глобальный `app.setStyleSheet(...)` — **активен** для light и dark (**#11**, **#12**) |

При изменении цвета обновляй **оба** места. Комментарии в `.qss` ссылаются на соответствующий `DesignTokens.*`. Per-form QSS в `.ui` **не используется** с **#11**.

## Design tokens

### Общие токены

| Token | Light | Dark | Назначение |
|-------|-------|------|------------|
| `accent` | `#f0b321` | `#f0b321` | Выделение, hover, selected item |
| `border` | `#17365D` | `#5a8ab0` | Рамка карточки, меню, combo, inputs |
| `button_bg` | `#226091` | `#1e4d73` | Кнопки, combo (closed), spinbox |
| `button_pressed_bg` | `#19466a` | `#163a57` | Pressed / checked |
| `combo_popup_bg` | `#19466a` | `#163a57` | Popup `QComboBox` |
| `menu_bar_bg` | `#ffffff` | `#2d2d2d` | `QMenuBar` |
| `menu_bg` | `#f5f5f5` | `#3c3c3c` | `QMenu` dropdown |
| `text_primary` | `#17365D` | `#e0e0e0` | Основной текст на светлых / тёмных поверхностях |
| `text_on_button` | `#FFFFFF` | `#e8e8e8` | Подписи на filled controls |
| `text_on_dark` | `#FFFFFF` | `#e0e0e0` | Текст на тёмных popup / accent-поверхностях |

### Фоны карточек по типу устройства

| Token | Light | Dark | Тип |
|-------|-------|------|-----|
| `device_printer` | `#fff3e0` | `#3d3528` | Принтер |
| `device_camera` | `#e8f5e9` | `#2a3d2c` | Камера |
| `device_scanner` | `#f3e5f5` | `#352a3d` | Сканер |
| `device_transporter` | `#e3f2fd` | `#283545` | Перевозчик |
| `device_generator` | `#fff9c4` | `#3d3a28` | Генератор |

Палитра совпадает с grilling-решением плана UI modernization и [frontend/widget-backgrounds.md](frontend/widget-backgrounds.md).

### Типографика

| Token | Значение | Область QSS |
|-------|----------|-------------|
| `font_ui` | `"Segoe UI", "SF Pro Text", "Helvetica Neue", sans-serif` | `QLabel`, `QToolButton`, `QPushButton`, `QCheckBox`, `QComboBox` |
| `font_mono` | `"Cascadia Mono", "Consolas", "DejaVu Sans Mono", monospace` | `QListView#lstData`, `QLineEdit#leConnetionStr`, `QLineEdit#leManualInput` |

Per-widget `font` (DejaVu Sans Mono) удалены из device `.ui` (**#11**).

## Device card backgrounds (QSS)

Фон карточки задаётся динамическим свойством `deviceType` на `QWidget#Form` (устанавливается в `DeviceCardMixin`, подзадача **#5**; API chrome — [frontend/device-card.md](frontend/device-card.md)):

```css
QWidget#Form[deviceType="printer"]     { background-color: /* device_printer */; }
QWidget#Form[deviceType="camera"]      { background-color: /* device_camera */; }
QWidget#Form[deviceType="scanner"]     { background-color: /* device_scanner */; }
QWidget#Form[deviceType="transporter"] { background-color: /* device_transporter */; }
QWidget#Form[deviceType="generator"]   { background-color: /* device_generator */; }
```

Общая рамка: `border: 1px solid <border>`; `border-radius: 3px`.

## Структура QSS-файлов

Оба файла (`theme_light.qss`, `theme_dark.qss`) содержат одинаковые секции:

| Секция | Селекторы | Примечание |
|--------|-----------|------------|
| Typography | sans-serif controls; monospace `#lstData`, tech line edits | единственный источник шрифтов (**#11**) |
| Device cards | `QWidget#Form`, `QWidget#Form[deviceType=…]` | 5 типов |
| Buttons | `QToolButton`, `QPushButton` (+ hover / pressed / `:checked`) | |
| Labels & inputs | `QLabel`, `QCheckBox`, `QLineEdit` | dark: фон `#2a2a2a` у `QLineEdit` |
| Spin boxes | `QSpinBox`, subcontrols | |
| Combo boxes | closed, popup `QAbstractItemView`, `::item`, `#cbxProduct` min-width | fix-qt-light-theme **#4** |
| Code queues | `QListView#lstData` | dark: цвет и фон списка |
| Scroll bars | `QScrollBar` | |
| Menu bar & menus | `QMenuBar`, `QMenu` | fix-qt-light-theme **#3** |
| Tabs (Camera) | `QTabWidget::pane`, `QTabWidget::tab-bar` | **#11** |
| Shell | `QMainWindow`, `QDockWidget`, `QScrollArea` | polish sidebar/canvas (**#12**) |

Загрузка: `load_stylesheet("light" | "dark")` через `libs.media.get_path_to_media("themes/theme_<mode>.qss")`.

## Типы и API

### `ThemeMode`

Пользовательское предпочтение (enum, значения для JSON user settings):

```python
class ThemeMode(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"
```

### `ResolvedTheme`, `DeviceType`

```python
ResolvedTheme = Literal["light", "dark"]
DeviceType = Literal["printer", "camera", "scanner", "transporter", "generator"]
```

### `DesignTokens`

Frozen dataclass; экземпляры `LIGHT`, `DARK`. Методы:

- `device_background(device_type: DeviceType) -> str`
- `device_backgrounds -> dict[DeviceType, str]`

### `get_tokens(mode: ResolvedTheme) -> DesignTokens`

Возвращает `LIGHT` или `DARK` по resolved mode.

### `load_stylesheet(mode: ResolvedTheme) -> str`

Читает `media/themes/theme_<mode>.qss`. Raises `FileNotFoundError` если файл отсутствует; `ValueError` если mode не `light`/`dark`.

### `resolve_effective_mode(preference, app=None) -> ResolvedTheme`

| Preference | Результат |
|------------|-----------|
| `LIGHT` | `"light"` |
| `DARK` | `"dark"` |
| `SYSTEM` | 1) `QStyleHints.colorScheme()` через `app` (PySide6 6.7+), если передан `QApplication`; 2) иначе Windows registry `HKCU\...\Themes\Personalize` → `AppsUseLightTheme` (0 = dark); 3) fallback `"light"` |

Аргумент `app` опционален — без него для `SYSTEM` используется OS heuristic (`_detect_system_theme`).

### `apply_qt_style(app, effective_mode) -> None`

| Платформа | Light | Dark |
|-----------|-------|------|
| Windows | `app.setStyle("windowsvista")` | первый доступный из `windows11`, `Windows`, `Fusion` |
| Linux / macOS | no-op | no-op |

Light: workaround для Qt 6.7 popup при `QT_QPA_PLATFORM=windows:darkmode=0`. Dark: сброс с `windowsvista` на platform style, чтобы popup оставались читаемыми после переключения из светлой темы.

### `apply_theme(app, preference=ThemeMode.LIGHT) -> ResolvedTheme`

Цепочка: `resolve_effective_mode(preference, app=app)` → `apply_qt_style` → `app.setStyleSheet(load_stylesheet(...))`. Возвращает resolved mode (`"light"` / `"dark"`).

**Production path:** `main.py` после `QApplication`; повторный вызов из `MainLineField._on_theme_preference_changed` при смене меню «Вид».

### `apply_light_theme(app)`

Convenience wrapper: `apply_theme(app, ThemeMode.LIGHT)`. Сохранён для тестов и обратной совместимости; **не** используется в `main.py` с **#12**.

## Startup (`main.py`, #12)

```text
setup_pathes()
setup_logging()
QApplication(sys.argv)
user_settings = load_user_settings()
apply_theme(app, ThemeMode(user_settings.theme_preference))
MainLineField().show()
app.exec()
```

| Платформа | `QT_QPA_PLATFORM` | Зачем |
|-----------|-------------------|-------|
| Linux | `xcb` | явный backend |
| Windows | `windows:darkmode=0` | отключить native dark title bars — глобальный QSS контролирует menu/combo popups |
| macOS | не задаётся | platform default |

Порядок важен: `apply_theme` **до** `MainLineField()`, чтобы menu bar и dock получили QSS при построении окна.

## Меню «Вид» и persistence (#12)

| Пункт UI | `QAction` | `ThemeMode` |
|----------|-----------|-------------|
| «Как в системе» | `acThemeSystem` | `SYSTEM` |
| «Светлая» | `acThemeLight` | `LIGHT` |
| «Тёмная» | `acThemeDark` | `DARK` |

Wiring в `MainLineField` (`core/main_ui/line_emul.py`):

- `_setup_theme_connections()` — слоты на `triggered`, `_sync_theme_menu_from_settings()` при старте;
- `_on_theme_preference_changed(mode)` — `save_user_settings(UserSettings(theme_preference=...))`, затем `apply_theme(app, mode)`;
- `themeActionGroup` (exclusive) в `Main.ui` — radio-поведение checkable actions.

Файл настроек: `line_emulator_user.json` — путь см. [user_settings.md](user_settings.md). **Не** входит в project JSON.

## PyInstaller (frozen-сборка)

Runtime читает QSS с диска относительно `media/` через `get_path_to_media()`. PyInstaller не включает `media/themes/` автоматически — каталог задаётся явно в `build/spec/main.spec`:

```python
datas=[
    ('..\\..\\media\\logo.ico', 'media'),
    ('..\\..\\media\\themes', 'media/themes'),
    ...
]
```

Без этой записи frozen `dmcLineEmulator.exe` вызовет `FileNotFoundError` в `load_stylesheet()`. Обзор сборки — [line_emulator.md](line_emulator.md) («Сборка exe»).

## Windows popup workaround

| Условие | Действие |
|---------|----------|
| Windows + light | `windowsvista` + `theme_light.qss` |
| Windows + dark | `windows11` / `Windows` / `Fusion` + `theme_dark.qss` |
| Linux / macOS | Qt style не меняется; QSS применяется |

QSS для `QMenuBar`, `QMenu`, `QComboBox QAbstractItemView` — в `theme_*.qss`. Контекст бага Qt 6.7 — [frontend/widget-backgrounds.md](frontend/widget-backgrounds.md).

## Тестирование

`tests/test_libs/test_qt_theme.py` (**9** тестов, **#12** + **#13** ✓). Smoke-тесты без GUI-assertions; для `SYSTEM` и `apply_theme` требуется singleton `QApplication`.

| Класс / тест | Покрытие |
|--------------|----------|
| `TestResolveEffectiveMode.test_light_and_dark_preferences` | Explicit `LIGHT` / `DARK` без OS |
| `test_system_preference_uses_os_heuristic` | `SYSTEM` → registry fallback (mock) |
| `test_system_preference_prefers_qt_hints` | `SYSTEM` + `QApplication` → `QStyleHints` (mock) |
| `test_system_falls_back_to_os_when_qt_unavailable` | `QStyleHints` → `None`, fallback на OS heuristic |
| `TestDesignTokens.test_get_tokens_returns_light_and_dark_singletons` | `get_tokens("light"|"dark")` → `LIGHT` / `DARK` |
| `test_device_backgrounds_match_device_type_keys` | Пять типов устройств, distinct hex per type |
| `TestLoadStylesheet.test_load_light_and_dark_stylesheets` | Оба QSS на диске; селекторы `deviceType`, `QMenuBar`, `QDockWidget` |
| `test_invalid_mode_raises_value_error` | Неизвестный mode → `ValueError` до чтения файла |
| `TestApplyTheme.test_apply_theme_sets_stylesheet_for_light_and_dark` | `apply_theme` → resolved mode + `app.styleSheet()` содержит QSS |

```powershell
.\venv\Scripts\python.exe -m unittest tests.test_libs.test_qt_theme -v
```

## Критерии готовности

### Подзадача #3

- [x] `media/themes/theme_light.qss`, `theme_dark.qss` — deviceType, menu, combo, typography.
- [x] `libs/qt_theme.py` — `ThemeMode`, `DesignTokens`, API.
- [x] `windowsvista` workaround для light на Windows.

### Подзадача #11

- [x] Duplicate QSS удалён из `forms/ui/*.ui`.
- [x] Глобальный QSS, PyInstaller `media/themes/`.

### Подзадача #12

- [x] `main.py` — `load_user_settings` + `apply_theme(ThemeMode(...))` до `MainLineField`.
- [x] Меню «Вид» — persist + live re-apply QSS.
- [x] `resolve_effective_mode` — `QStyleHints.colorScheme()` + registry fallback.
- [x] Dark Qt style reset на Windows (`windows11` / `Windows` / `Fusion`).
- [x] QSS shell: `QMainWindow`, `QDockWidget`, `QScrollArea`.
- [x] Unit-тесты `test_qt_theme.py`.

## Связанная документация

- [frontend/theme-system.md](frontend/theme-system.md) — архитектура UI-темы для разработчиков.
- [user_settings.md](user_settings.md) — персистентность `theme_preference`, пути, load/save.
- [frontend/layout-shell.md](frontend/layout-shell.md) — меню «Вид», `acTheme*` в `Main.ui`.
- [frontend/mainlinefield-layout.md](frontend/mainlinefield-layout.md) — theme actions vs project JSON layout.
- [frontend/layout-and-docking.md](frontend/layout-and-docking.md) — project JSON vs user settings (theme).
- [frontend/widget-backgrounds.md](frontend/widget-backgrounds.md) — палитра фонов, menu/combo fix, «Тема Windows».
- [line_emulator.md](line_emulator.md) — обзор приложения, PyInstaller.

## Roadmap

| Подзадача | Статус | Что добавляет |
|-----------|--------|---------------|
| **#5** | ✓ | `deviceType` property на карточках |
| **#11** | ✓ | Централизация QSS, PyInstaller `media/themes/` |
| **#12** | ✓ | Runtime light/dark/system, меню «Вид», user settings wiring |
| **#13** | ✓ | Расширены `test_qt_theme.py` (tokens, system fallback, `apply_theme` smoke); см. также `test_user_settings.py`, `test_config_layout_migration.py`, `test_line_emul_layout.py` |
| **#14** | ✓ | Финал документации API (`apply_theme` production path), consolidated [layout-and-docking.md](frontend/layout-and-docking.md), `hiddenimports` UI-модулей в `main.spec`, `VERSION` `1.0.0.1.b0006` |
