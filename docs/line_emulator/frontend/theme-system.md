# Design system Line Emulator (frontend)

| Параметр | Значение |
|----------|----------|
| План | UI modernization, подзадачи **#3**, **#11**, **#12** |
| Модуль | `libs/qt_theme.py` |
| QSS | `media/themes/theme_light.qss`, `media/themes/theme_dark.qss` |
| Runtime | `main.py` → `load_user_settings()` + `apply_theme(app, ThemeMode(...))` (**#12**) |
| Меню | «Вид» → «Как в системе» / «Светлая» / «Тёмная» → `UserSettings` + re-apply (**#12**) |

## Назначение

Единая тема оформления desktop UI Line Emulator: светлая и тёмная палитра, различимые фоны карточек по типу устройства, согласованные menu/combo popup, shell (dock, scroll) и разделение шрифтов (sans-serif UI / monospace для очередей кодов и tech-полей).

Документ для разработчиков UI. Полное описание API, tokens, PyInstaller, Windows workaround и тестов — [qt_theme.md](../qt_theme.md). Per-form фоны и многослойный fix Qt 6.7 — [widget-backgrounds.md](widget-backgrounds.md).

## Слои оформления (после #12)

```text
main.py
  ├─ setup_pathes() / setup_logging()
  ├─ QApplication(sys.argv)
  ├─ load_user_settings()                    → theme_preference (system/light/dark)
  └─ apply_theme(app, ThemeMode(...))        → resolve + apply_qt_style + theme_*.qss
       └─ MainLineField
            ├─ deviceType property → фон карточки из QSS (#5)
            ├─ «Вид» → acTheme* → save_user_settings + apply_theme (live)
            └─ controls / menu / combo / dock / scroll — глобальный theme QSS
```

| Слой | Источник | Статус |
|------|----------|--------|
| Qt platform style | `apply_qt_style` | Light: `windowsvista` (Windows); dark: `windows11`/`Windows`/`Fusion` |
| Глобальный QSS | `media/themes/theme_*.qss` | **Активен** для light и dark (**#11**, **#12**) |
| Per-form QSS | `forms/ui/*.ui` | **Удалён** (**#11**) |
| Per-widget fonts | `forms/ui/*.ui` | **Удалены**; типографика из theme QSS (**#11**) |

## Файлы и ответственность

| Файл | Роль |
|------|------|
| `libs/qt_theme.py` | `ThemeMode`, `DesignTokens`, `resolve_effective_mode`, `apply_theme`, `apply_qt_style` |
| `media/themes/theme_light.qss` | Светлая тема — controls, menu, combo, shell, `deviceType` |
| `media/themes/theme_dark.qss` | Тёмная тема (те же секции + dark palette) |
| `main.py` | `load_user_settings()` + `apply_theme` после `QApplication`, до `MainLineField()` |
| `core/main_ui/user_settings.py` | `theme_preference` в JSON; load/save API (**#2**) |
| `core/main_ui/line_emul.py` | Меню «Вид» theme actions, persist, re-apply (**#12**) |
| `forms/ui/Main.ui` | `acThemeSystem`, `acThemeLight`, `acThemeDark`, `themeActionGroup` (**#8**) |
| `core/main_ui/device_card.py` | Chrome карточки, `deviceType` (**#5**) — [device-card.md](device-card.md) |

## Device card: `deviceType`

Общий chrome карточки — [device-card.md](device-card.md) (**#5**).

QSS выбирает фон корневой формы карточки по dynamic property:

```css
QWidget#Form[deviceType="printer"] { background-color: …; }
```

| `deviceType` | Виджет | Token |
|--------------|--------|-------|
| `printer` | `PrinterWidget` | `device_printer` |
| `camera` | `CameraWidget` | `device_camera` |
| `scanner` | `ScannerWidget` | `device_scanner` |
| `transporter` | `TransporterWidget` | `device_transporter` |
| `generator` | `GeneratorWidget` | `device_generator` |

Программный доступ:

```python
from libs.qt_theme import get_tokens

tokens = get_tokens("light")
bg = tokens.device_background("scanner")
```

## Типографика

| Класс элементов | Шрифт | QSS-селекторы |
|-----------------|-------|---------------|
| UI controls | sans-serif (`font_ui`) | `QLabel`, `QToolButton`, `QPushButton`, `QCheckBox`, `QComboBox` |
| Очереди кодов | monospace (`font_mono`) | `QListView#lstData` |
| Tech fields | monospace | `QLineEdit#leConnetionStr`, `QLineEdit#leManualInput` |

## Menu, combo, shell

Правила `QMenuBar` / `QMenu`, `QComboBox QAbstractItemView`, кнопок, spinbox, scrollbar, `QTabWidget`, `QMainWindow`, `QDockWidget`, `QScrollArea` — в `media/themes/theme_*.qss`. Исторический контекст fix Qt 6.7 — [widget-backgrounds.md](widget-backgrounds.md).

## Theme preference

| `ThemeMode` | JSON (`theme_preference`) | Resolved | QSS |
|-------------|---------------------------|----------|-----|
| `system` | `"system"` (default) | OS: `QStyleHints` → registry → `"light"` | `theme_light.qss` или `theme_dark.qss` |
| `light` | `"light"` | `"light"` | `theme_light.qss` |
| `dark` | `"dark"` | `"dark"` | `theme_dark.qss` |

### Меню «Вид» и persistence

| Пункт | `QAction` | При выборе |
|-------|-----------|------------|
| «Как в системе» | `acThemeSystem` | `save_user_settings` + `apply_theme(SYSTEM)` |
| «Светлая» | `acThemeLight` | `save_user_settings` + `apply_theme(LIGHT)` |
| «Тёмная» | `acThemeDark` | `save_user_settings` + `apply_theme(DARK)` |

Файл: `line_emulator_user.json` — см. [user_settings.md](../user_settings.md). Статическая разметка меню — [layout-shell.md](layout-shell.md); wiring в `MainLineField` — [mainlinefield-layout.md](mainlinefield-layout.md) (раздел «Theme preference»).

## PyInstaller

QSS загружается через `get_path_to_media("themes/theme_<mode>.qss")`. Каталог `media/themes/` в `build/spec/main.spec` → `datas` (**#11**). Подробности — [qt_theme.md](../qt_theme.md#pyinstaller-frozen-сборка).

## Изменение палитры

1. Обновить `LIGHT` / `DARK` в `libs/qt_theme.py`.
2. Синхронно обновить hex в `theme_light.qss` и/или `theme_dark.qss`.
3. Перезапустить приложение или переключить тему в меню «Вид».

## Критерии готовности

### #11

- [x] Per-form QSS удалён; глобальный light QSS; PyInstaller `media/themes/`.

### #12

- [x] `main.py` — `apply_theme` по `UserSettings.theme_preference`.
- [x] Меню «Вид» — persist + live switch light/dark/system.
- [x] Dark QSS + shell (`QDockWidget`, `QScrollArea`) в runtime.
- [x] `tests/test_libs/test_qt_theme.py`.

## Связанная документация

- [device-card.md](device-card.md) — `DeviceCardMixin`, `deviceType` (#5).
- [qt_theme.md](../qt_theme.md) — полный API, startup, тесты.
- [widget-backgrounds.md](widget-backgrounds.md) — палитра, menu/combo fix Qt 6.7.
- [user_settings.md](../user_settings.md) — хранение `theme_preference`, пути.
- [layout-shell.md](layout-shell.md) — `menuView`, `acTheme*` в `.ui`.
- [mainlinefield-layout.md](mainlinefield-layout.md) — theme vs layout persistence.
- [line_emulator.md](../line_emulator.md) — обзор приложения.
