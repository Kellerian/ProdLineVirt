# UI-форма виджета сканера (Scanner)

| Параметр | Значение |
|----------|----------|
| План | serial-barcode-scanner-bulk-control, подзадача **#3** |
| Макет (Qt Designer) | `forms/ui/Scanner.ui` |
| Сгенерированный класс | `forms/Scanner.py` → `Ui_Form` |
| Потребитель (подзадача #4) | `core/barcode_scanner/scanner_widget.py` → `ScannerWidget` |

## Назначение

Статический макет PySide6 для виджета эмулятора ручного сканера штрихкодов на линии. Форма задаёт компоновку, имена виджетов, стили и режимы drag-and-drop; бизнес-логика (COM-порт, очередь отправки, `CodeScheduler`) реализована в `ScannerWidget` — см. [scanner-widget.md](scanner-widget.md).

Макет наследует общую сетку виджетов линии (как `Printer.ui`): верхняя строка **название | подключение | Run/Stop**, средняя — дополнительные элементы управления, нижняя — список данных на всю оставшуюся высоту.

## Макет (ASCII)

```text
┌─────────────────────────────────────────┐  QWidget#Form, фон #f3e5f5
│ [Название]  [Выберите порт ▼]  [R]      │  horizontalLayout (4:1:0)
│ [Ручной ввод текста........] [▶]        │  horizontalLayout_2 (1:0)
│ ┌─────────────────────────────────────┐ │
│ │  lstData — очередь (DropOnly)       │ │  verticalLayout stretch 0,0,1
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

Размеры корневого виджета: ширина 200–260 px, минимальная высота 250 px; `sizePolicy` по вертикали — `Expanding` (виджет растягивается в `FlowLayout` главного окна).

## Компоненты и свойства

| objectName | Тип | Роль в UI | Ключевые свойства |
|------------|-----|-----------|-------------------|
| `leName` | `QLineEdit` | Отображаемое имя сканера на линии | `maxLength` 25; placeholder «Название» |
| `cbxComPort` | `QComboBox` | Выбор COM-порта | Первый элемент «Выберите порт» (placeholder); tooltip «COM-порт»; шрифт bold 10 pt |
| `tbRun` | `QToolButton` | Запуск / остановка эмулятора | Текст «R» (иконка Run/Stop задаётся в виджете); `checkable`, 28×28 px |
| `leManualInput` | `QLineEdit` | Ручной ввод кода для отправки | Placeholder «Ручной ввод текста»; `clearButtonEnabled` |
| `btnSend` | `QToolButton` | Отправка текста из ручного ввода | Текст «▶»; tooltip «Отправить»; 28×28 px |
| `lstData` | `QListView` | Очередь кодов (приём drag-and-drop) | `DropOnly`, `MoveAction`, `NoEditTriggers`, `ExtendedSelection`, чередующиеся строки; tooltip «Список очереди (перетащите коды сюда)» |

### Строка name | COM | R/S

Горизонтальный layout `horizontalLayout` с пропорциями stretch **4 : 1 : 0**:

1. **`leName`** — узкое поле имени (как у принтера/камеры).
2. **`cbxComPort`** — вместо `QLineEdit` порта у принтера (`leConnetionStr`) используется выпадающий список портов. Список портов заполняется в рантайме из `serial.tools.list_ports` (подзадача #4), не в `.ui`.
3. **`tbRun`** — переключаемая кнопка Run/Stop; в покое отображает «R»; при включении виджет меняет текст/иконку на «S» (логика в `ScannerWidget`, по аналогии с `PrinterWidget._setup_icon`).

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
| Подключение | `leConnetionStr` (порт TCP) | `cbxComPort` (COM combo) |
| Средняя строка | «Буфер» + `spAmount` | `leManualInput` + `btnSend` |
| `lstData` drag | `DragOnly` (источник) | `DropOnly` (приёмник) |
| Фон `#Form` | `#fff3e0` | `#f3e5f5` |

См. также [widget-backgrounds.md](widget-backgrounds.md) — светлые фоны всех типов виджетов (#7).

## Граница ответственности подзадачи #3

**Входит в #3 (реализовано в форме):**

- Макет, objectName, размеры, stretch, tooltips, placeholders.
- Режим `lstData` DropOnly и визуальный стиль.
- Placeholder «Выберите порт» с `setEnabled(False)` в сгенерированном коде.

**Не входит (последующие подзадачи):**

| Поведение | Подзадача |
|-----------|-----------|
| Пункт меню «Добавить → Сканер» | #5 |
| Участие в Transport / Generator | #6 (реализовано — см. [scanner-widget.md](scanner-widget.md)) |

Логика `ScannerWidget` (модели, DnD, COM, `CodeScheduler`, ручная отправка, transport/generator) — подзадачи **#4** и **#6**, см. [scanner-widget.md](scanner-widget.md).

## Связанная документация

- [scanner-widget.md](scanner-widget.md) — `ScannerWidget`: DnD, `CodeScheduler`, COM, transport/generator (#6), `clear_data()`, `options` (подзадача #4).
- [widget-backgrounds.md](widget-backgrounds.md) — палитра фонов `QWidget#Form` для всех типов виджетов на холсте (подзадача #7).
- [line_emulator.md](../line_emulator.md) — обзор приложения; wiring transport/generator (#6).
- План: `.plans/in_progress/2026-07-10-serial-barcode-scanner-bulk-control.md` — подзадачи #3 (форма), #4 (`ScannerWidget`), #6 (transport/generator).
