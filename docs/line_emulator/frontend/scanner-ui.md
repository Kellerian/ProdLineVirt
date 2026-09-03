# UI-форма виджета сканера (Scanner)

| Параметр | Значение |
|----------|----------|
| План | serial-barcode-scanner-bulk-control, подзадача **#3** |
| Макет (Qt Designer) | `forms/ui/Scanner.ui` |
| Сгенерированный класс | `forms/Scanner.py` → `Ui_Form` |
| Потребитель (подзадача #4) | `core/barcode_scanner/scanner_widget.py` → `ScannerWidget` |

## Назначение

Статический макет PySide6 для виджета эмулятора ручного сканера штрихкодов на линии. Форма задаёт компоновку, имена виджетов, стили и режимы drag-and-drop; бизнес-логика (COM-порт, очередь отправки, `CodeScheduler`) реализована в `ScannerWidget` — см. [scanner-widget.md](scanner-widget.md).

Макет наследует общую сетку виджетов линии (как `Printer.ui`): chrome-шапка **название | Run/Stop | delete** (через `DeviceCardHeader`), always-visible блок (ручной ввод + очередь), кнопка **«Дополнительно»**, скрытая панель COM (**#10** UI modernization).

## Макет (ASCII)

```text
┌──────────────────────────────────────────────────┐  QWidget#Form, фон #f3e5f5
│ [≡] [Название]                          [R] [X]  │  DeviceCardHeader (после mount)
│ [Ручной ввод текста...........] [▶]             │  horizontalLayout_2 (1:0)
│ ┌──────────────────────────────────────────────┐ │
│ │  lstData — очередь (DropOnly)                │ │  verticalLayout stretch
│ └──────────────────────────────────────────────┘ │
│ [Дополнительно]                                  │  tbAdvanced (collapsed)
│ ┌ wAdvanced (hidden): [COM ▼] [↻] ─────────────┐ │  раскрывается по toggle
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

Размеры корневого виджета: ширина 200–260 px, минимальная высота 250 px; `sizePolicy` по вертикали — `Expanding` (виджет растягивается в `FlowLayout` главного окна).

## Компоненты и свойства

| objectName | Тип | Роль в UI | Ключевые свойства |
|------------|-----|-----------|-------------------|
| `leName` | `QLineEdit` | Отображаемое имя сканера на линии | `maxLength` 25; placeholder «Название»; в `title_layout` после mount |
| `tbRun` | `QToolButton` | Запуск / остановка эмулятора | Текст «R»; `checkable`, 28×28 px; в `title_layout` |
| `tbDelete` | `QToolButton` | Запрос удаления (legacy в `.ui`) | Заменяется кнопкой `DeviceCardHeader` при mount (**#5**) |
| `leManualInput` | `QLineEdit` | Ручной ввод кода для отправки | Placeholder «Ручной ввод текста»; always visible |
| `btnSend` | `QToolButton` | Отправка текста из ручного ввода | Tooltip «Отправить»; always visible |
| `lstData` | `QListView` | Очередь кодов (приём drag-and-drop) | `DropOnly`; always visible |
| `tbAdvanced` | `QToolButton` | Toggle секции «Дополнительно» | `checkable`, default unchecked (**#10**) |
| `wAdvanced` | `QWidget` | Панель COM-порта | `visible=false` по умолчанию |
| `cbxComPort` | `QComboBox` | Выбор COM-порта | Внутри `wAdvanced`; placeholder «Выберите порт» |
| `tbRefreshPorts` | `QToolButton` | Обновление списка COM | Внутри `wAdvanced`; tooltip «Обновить список COM-портов» |

### Строка header (после mount #5)

Горизонтальный layout `horizontalLayout` содержит `DeviceCardHeader`:

1. **grip «≡»** — единственный drag handle для reorder.
2. **`leName`**, **`tbRun`** — в `title_layout`.
3. **delete** — кнопка header (legacy `tbDelete` из `.ui` удаляется).

COM-элементы **`cbxComPort`** и **`tbRefreshPorts`** перенесены в **`wAdvanced`** (**#10**); при collapsed advanced они скрыты, но порт по-прежнему обязателен перед Run (валидация в `ScannerWidget`).

### Ручной ввод и отправка

Вторая строка (`horizontalLayout_2`, stretch **1 : 0**) — отличие от `Printer.ui`, где вместо неё блок «Буфер» + `spAmount`:

- **`leManualInput`** — строка для ввода кода с клавиатуры.
- **`btnSend`** — триггер отправки; обработчик `clicked` подключается в `ScannerWidget`.

### Список очереди `lstData`

| Свойство | Значение | Смысл |
|----------|----------|--------|
| `dragDropMode` | `DropOnly` | Список только **принимает** перетаскивание; сам не является источником drag (в отличие от принтера — `DragOnly`) |
| `defaultDropAction` | `MoveAction` | При drop код **переносится** из источника, а не копируется |
| `editTriggers` | `NoEditTriggers` | Редактирование ячеек отключено |
| `selectionMode` | `ExtendedSelection` | Множественный выбор (Ctrl/Shift) |

Модель данных (`QStandardItemModel` или аналог) и включение приёма MIME назначаются в `ScannerWidget`; в `.ui` задан только вид списка.

## Визуальное оформление

### Фон виджета

В `styleSheet` корневого `QWidget#Form` задан светло-фиолетовый фон:

```css
QWidget#Form {
    background-color: #f3e5f5;
    border: 1px solid #17365D;
    border-radius: 3px;
}
```

Цвет сканера — `#f3e5f5` (purple 50). Полная палитра фонов всех типов виджетов на холсте описана в [widget-backgrounds.md](widget-backgrounds.md) (подзадача #7).

### Общие стили

Таблица стилей совпадает с семейством форм линии (`Printer.ui`, `Camera.ui`): шрифт **DejaVu Sans Mono**; кнопки и combo — тёмно-синий фон `#226091`, акцент `#f0b321`; скроллбар без стрелок.

## Placeholder COM-порта

В `Scanner.ui` в `cbxComPort` добавлен один элемент с текстом «Выберите порт». После генерации `forms/Scanner.py` для этого элемента выполняется:

```python
_com_port_placeholder = self.cbxComPort.model().item(0)
if _com_port_placeholder is not None:
    _com_port_placeholder.setEnabled(False)
```

Пользователь не может выбрать placeholder как рабочий порт; при заполнении списка реальными COM-именами placeholder остаётся первой строкой до выбора порта.

## Генерация Python из `.ui`

`forms/Scanner.py` — автогенерация **Qt User Interface Compiler** (PySide6). Редактировать вручную не следует: изменения вносятся в `forms/ui/Scanner.ui`, затем пересборка:

```powershell
.\venv\Scripts\pyside6-uic.exe forms/ui/Scanner.ui -o forms/Scanner.py
```

Класс `Ui_Form.setupUi(self, Form)` создаёт иерархию layout и виджетов; `retranslateUi` задаёт локализуемые строки (window title «Scanner», placeholders, tooltips).

## Сравнение с `Printer.ui`

| Аспект | Printer | Scanner |
|--------|---------|---------|
| Подключение | `leConnetionStr` в `wAdvanced` (TCP) | `cbxComPort` + `tbRefreshPorts` в `wAdvanced` (COM) |
| Always visible | `lstData` (буфер) | `leManualInput` + `btnSend`, `lstData` |
| Collapsible | `tbAdvanced` / `wAdvanced` | то же (**#10**) |
| `lstData` drag | `DragOnly` (источник) | `DropOnly` (приёмник) |
| Фон `#Form` | `#fff3e0` | `#f3e5f5` |

См. также [widget-backgrounds.md](widget-backgrounds.md) — светлые фоны всех типов виджетов (#7).

## Граница ответственности подзадачи #3 (форма) и последующих правок

**Исходная #3 (макет сканера) — реализовано:**

- Макет, objectName, размеры, stretch, tooltips, placeholders.
- Режим `lstData` DropOnly и визуальный стиль.
- Placeholder «Выберите порт» с `setEnabled(False)` в сгенерированном коде.

**Добавлено в ту же форму позже (реализовано):**

| Элемент | План / подзадача | Документация |
|---------|------------------|--------------|
| `tbRefreshPorts` | widget-delete-com-refresh **#1**; перенос в `wAdvanced` — UI modernization **#10** | [scanner-widget.md](scanner-widget.md), [device-card.md](device-card.md) |
| `tbDelete` | widget-delete-com-refresh **#2**; mount в `DeviceCardHeader` — **#5** | [widget-delete.md](widget-delete.md) |
| `tbAdvanced` / `wAdvanced` | UI modernization **#10** | [device-card.md](device-card.md) |

**Реализовано вне формы (логика / главное окно):**

| Поведение | Подзадача (serial barcode scanner) | Документация |
|-----------|-------------------------------------|--------------|
| Пункт меню «Добавить → Сканер» | #5 | [line_emulator.md](../line_emulator.md) |
| Участие в Transport / Generator | #6 | [scanner-widget.md](scanner-widget.md) |

Логика `ScannerWidget` (модели, DnD, COM, `CodeScheduler`, ручная отправка, transport/generator) — подзадачи **#4** и **#6**, см. [scanner-widget.md](scanner-widget.md).

## Связанная документация

- [scanner-widget.md](scanner-widget.md) — `ScannerWidget`: DnD, `CodeScheduler`, COM / `tbRefreshPorts`, `tbDelete` / `delete_requested`, transport/generator (#6), `clear_data()`, `options` (подзадача #4).
- [widget-delete.md](widget-delete.md) — `tbDelete` и `delete_requested` на всех пяти виджетах; Remove API; тесты (план widget-delete-com-refresh, #2–#5).
- [widget-backgrounds.md](widget-backgrounds.md) — палитра фонов `QWidget#Form` для всех типов виджетов на холсте (подзадача #7).
- [line_emulator.md](../line_emulator.md) — обзор приложения; wiring transport/generator (#6); удаление виджетов; COM refresh.
- План формы: `.plans/in_progress/2026-07-10-serial-barcode-scanner-bulk-control.md` — подзадачи #3 (форма), #4 (`ScannerWidget`), #6 (transport/generator).
- План удаления/COM: `.plans/in_progress/2026-07-13-line-emulator-widget-delete-com-refresh.md`.
