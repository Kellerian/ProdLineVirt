# Layout, docking и persistence

| Параметр | Значение |
|----------|----------|
| План | Line Emulator UI modernization, подзадачи **#6–#9**, **#12**, **#14** |
| Главное окно | `core/main_ui/line_emul.py` → `MainLineField` |
| Оболочка `.ui` | [layout-shell.md](layout-shell.md) — `dockSidebar`, central canvas, меню «Вид» |
| Sidebar reorder | [sidebar-layout.md](sidebar-layout.md) — `SidebarLayout` |
| Canvas reorder | [canvas-layout.md](canvas-layout.md) — `CanvasDeviceArea` / `FlowLayout` |
| Save/load оркестрация | [mainlinefield-layout.md](mainlinefield-layout.md) |
| Drag chrome | [device-card.md](device-card.md) — grip «≡», mime, zone guards |
| Project JSON | [config.md](../config.md), migration — [config_migration.md](../config_migration.md) |
| Theme (не project) | [user_settings.md](../user_settings.md), [qt_theme.md](../qt_theme.md) |
| Тесты | `test_sidebar_layout.py`, `test_canvas_area.py`, `test_line_emul_layout.py` (**#13**) |

## Назначение

Сводный документ для разработчиков: **как устроены зоны устройств**, **dock-оболочка**, **drag-reorder**, **сброс layout**, **что сохраняется в project JSON**, а что — в user settings. Детали API — в профильных файлах по ссылкам выше.

## Архитектура окна

```text
┌─ QMainWindow (MainLineField) ────────────────────────────────────────────┐
│ menuBar: Файл | Добавить | Управление | Вид                              │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌─ QDockWidget dockSidebar ────┐  ┌─ centralwidget ───────────────────┐ │
│ │ scrollAreaSidebar            │  │ scrollAreaCanvas                  │ │
│ │   scaTransporters            │  │   scaDevices (FlowLayout)         │ │
│ │     SidebarLayout            │  │     CanvasDeviceArea              │ │
│ │       Transporter, Generator │  │       Printer, Camera, Scanner    │ │
│ └──────────────────────────────┘  └───────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

| Зона | Dock / widget | Типы устройств | Reorder-контейнер |
|------|---------------|----------------|-------------------|
| **Sidebar** | `dockSidebar` → `scaTransporters` | Transporter, Generator | `SidebarLayout` |
| **Canvas** | central → `scaDevices` | Printer, Camera, Scanner | `CanvasDeviceArea` + `FlowLayout` |

По умолчанию sidebar — **слева** (`LeftDockWidgetArea`); canvas — **central widget** (не отдельный dock). Sidebar можно float, tab и переносить в left/right dock areas.

## Строгое разделение зон

| Тип | Зона | Drag target |
|-----|------|-------------|
| Transporter, Generator | Sidebar only | `SidebarLayout` |
| Printer, Camera, Scanner | Canvas only | `CanvasDeviceArea` |

Cross-zone drop **отклоняется**: transporter на canvas или camera в sidebar не перемещаются. Проверка — `DeviceZone` в mime payload ([device-card.md](device-card.md)).

## Drag-reorder (только grip «≡»)

| Правило | Реализация |
|---------|------------|
| Единственный drag handle | `DeviceGripHandle` в `DeviceCardHeader` |
| Не draggable | body карточки, кнопки Run/Stop, combo, списки кодов |
| Mime | `application/x-line-emulator-device-id` — `device_id` + `DeviceZone` |
| Sidebar | вертикальный список, drop indicator между карточками |
| Canvas | auto-wrap `FlowLayout`, insert-before по hit-testing rects |

DnD очередей кодов (`text/plain` и др.) **не** перехватывается layout-контейнерами canvas/sidebar.

## Меню «Вид»

| Пункт | `QAction` | Эффект | Persistence |
|-------|-----------|--------|-------------|
| Сбросить расположение | `acResetLayout` | default dock area + default device order | **не** пишет project JSON до File→Save |
| Как в системе | `acThemeSystem` | `apply_theme(SYSTEM)` | `line_emulator_user.json` |
| Светлая | `acThemeLight` | `apply_theme(LIGHT)` | user settings |
| Тёмная | `acThemeDark` | `apply_theme(DARK)` | user settings |

Сброс layout: `_on_reset_layout` → `_apply_default_layout()` — sidebar слева, порядок устройств по умолчанию (transporters → generators; printers → cameras → scanners). Подробности save/load — [mainlinefield-layout.md](mainlinefield-layout.md).

## Project JSON vs user settings

| Аспект | Project JSON (`ConfigFile`) | User settings (`UserSettings`) |
|--------|----------------------------|----------------------------------|
| Файл | путь Open/Save | `line_emulator_user.json` |
| Расположение | произвольный | `%APPDATA%/DataMatrixControl/` или `WORKDIR` |
| Когда сохраняется | **только File → Save** | при смене «Вид → тема» |
| Layout | `sidebar_order[]`, `canvas_order[]`, `dock_state` (base64) | — |
| Устройства | списки `*Config`, `device_id`, `advanced_expanded` | — |
| Тема | **не** входит | `theme_preference`: `system` / `light` / `dark` |

Drag-reorder и изменения dock **без Save** живут только в памяти до перезапуска или reload конфига.

### Поля layout в project JSON

| Поле | Тип | Содержимое |
|------|-----|------------|
| `sidebar_order` | `list[str]` | `device_id` transporter/generator сверху вниз |
| `canvas_order` | `list[str]` | `device_id` printer/camera/scanner (visual flow order) |
| `dock_state` | `str \| null` | base64 `QMainWindow.saveState()` |
| `advanced_expanded` | `bool` per `*Config` | состояние «Дополнительно» на карточке |

Save: `_encode_dock_state()` + `get_sidebar_device_order()` / `get_canvas_device_order()` + `widget.options()` per device. Load: `process_config` → `_apply_device_layout` → `_restore_dock_state`.

## Migration legacy JSON

Файлы без `device_id`, `sidebar_order`, `canvas_order`, `dock_state` — `core/main_ui/config_migration.py`:

- `migrate_legacy_config` / `enrich_legacy_config` — assign `device_id`, построить order из порядка списков в JSON;
- default dock: sidebar слева, `dock_state=None` → defaults при restore;
- `advanced_expanded=False` для всех устройств.

См. [config_migration.md](../config_migration.md) и тесты `test_config_layout_migration.py`.

## Связанные модули (PyInstaller)

Явные `hiddenimports` в `build/spec/main.spec` (**#14**):

- `core.main_ui.device_card`, `config_migration`, `sidebar_layout`, `canvas_area`, `user_settings`, `flow_layout`
- `libs.qt_theme`

`datas`: `media/themes/` для `load_stylesheet()`. Обзор сборки — [line_emulator.md](../line_emulator.md) («Сборка exe»).

## Критерии готовности (#14)

- [x] Dock sidebar + central canvas; меню «Вид» (reset + theme).
- [x] Grip-only reorder; zone guards.
- [x] Layout в project JSON on Save; theme в user settings.
- [x] Legacy JSON opens via migration.
- [x] Consolidated doc + cross-links; `VERSION` `1.0.0.1.b0006`.

## Связанная документация

- [layout-shell.md](layout-shell.md) — `Main.ui`, `dockSidebar`, меню actions.
- [mainlinefield-layout.md](mainlinefield-layout.md) — `_apply_default_layout`, iterators, save/load flow.
- [sidebar-layout.md](sidebar-layout.md), [canvas-layout.md](canvas-layout.md) — reorder API.
- [device-card.md](device-card.md) — grip, mime, collapsible advanced.
- [theme-system.md](theme-system.md) — design system слои.
- [line_emulator.md](../line_emulator.md) — обзор приложения.
