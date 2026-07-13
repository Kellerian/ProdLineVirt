---
title: Удаление виджетов Line Emulator и обновление COM-портов сканера
created: 2026-07-13
updated: 2026-07-13
status: completed
priority: medium
estimated_subtasks: 5
---

# Удаление виджетов Line Emulator и обновление COM-портов сканера

## Контекст и цель

В Line Emulator (`main.py` → `MainLineField` в `core/main_ui/line_emul.py`) виджеты добавляются через меню «Добавить», но **удалить отдельный виджет с холста нельзя** — только bulk-очистка при загрузке конфига через `clear_ui()`. Нужна кнопка удаления на каждом типе виджета (Printer, Camera, Scanner, Transporter, Generator) с проверкой «только остановленный» и диалогом подтверждения.

Во виджете сканера список COM-портов заполняется один раз в `__init__` через уже существующий `_refresh_com_ports()`. Нужна UI-кнопка обновления рядом с `cbxComPort`, чтобы оператор мог пересканировать порты без перезапуска приложения.

**Успех:** на каждом виджете есть `tbDelete`; удаление остановленного виджета с подтверждением убирает его с холста и из реестра; combo у transporters/generators не содержат stale id; сканер умеет обновить список COM; `clear_ui`/`closeEvent` корректно обрабатывают generators; unit-тесты и docs в `docs/line_emulator/`.

**Ограничения:** не трогать Manager/Monitor и другие клиенты; стек — Python + PySide6 (не React); документация — `docs/line_emulator/`.

## Обзор подхода

1. **`tbDelete`** (`QToolButton`, 28×28, после `tbRun`) во всех пяти `.ui`; после правок — регенерация `forms/*.py` через `pyside6-uic`.
2. В каждом `*_widget.py`: сигнал `delete_requested`, слот `_on_delete_clicked` — если `tbRun.isChecked()` → `QMessageBox.warning` («Остановите виджет перед удалением»); иначе `QMessageBox.question` («Удалить виджет «{name}»?») → при Yes emit `delete_requested`.
3. **`MainLineField`**: при `_add_*` подключать `delete_requested` к единому `_on_widget_delete_requested(widget)`; remove из соответствующего dict, `setParent(None)` + `run(False)` + `deleteLater()` (как в `clear_ui`); для device — обновить combo transporters/generators и `_sync_scanner_name_generator()` при удалении Scanner.
4. **`setup_models`**: заменить `self._device_data.update(...)` на полную замену словаря (`self._device_data = dict(device_widgets)`); словарь обновлять **всегда**, пересборку combo пропускать только если `tbRun.isChecked()` (чтобы при удалении device у running transporter не оставался stale id в `_device_data`).
5. **Баг рядом:** в `clear_ui()` и `closeEvent` добавить остановку/удаление `_generator_widgets` (сейчас generators не очищаются и не останавливаются при закрытии).
6. **COM refresh:** `tbRefreshPorts` между `cbxComPort` и `tbRun` в `Scanner.ui`; connect → `_refresh_com_ports(select_port=current)`; в `run()` disable вместе с `cbxComPort`.

Переиспользуем: `_refresh_com_ports`, `list_available_ports`, паттерн `clear_ui`, тесты с mock как в `tests/test_core/test_bulk_control.py`.

## Подзадачи

### 1. Кнопка обновления COM-портов в сканере

- **ID**: 1
- **Стек**: backend
- **Описание**: В `forms/ui/Scanner.ui` добавить `QToolButton` `tbRefreshPorts` (28×28) между `cbxComPort` и `tbRun`; обновить stretch шапки при необходимости (`4,1,0,0` или аналог). Регенерировать `forms/Scanner.py`. В `ScannerWidget._connect_ui` подключить `tbRefreshPorts.clicked` к обработчику, который вызывает `_refresh_com_ports(select_port=self._get_port_name() or None)` (если порт не выбран — `None`, остаётся placeholder). В `run()`: `self.tbRefreshPorts.setDisabled(toggled)` рядом с `cbxComPort.setDisabled(toggled)`. Иконка: `qtawesome` (например `fa5s.sync` / `fa5s.redo`) или текст «↻» — в стиле `btnSend`. Unit-тест: mock `list_available_ports`, вызвать refresh, проверить состав combo и сохранение текущего выбора.
- **Файлы/модули**: `forms/ui/Scanner.ui`, `forms/Scanner.py`, `core/barcode_scanner/scanner_widget.py`, `tests/test_core/test_scanner_com_refresh.py` (новый) или расширение `tests/test_core/test_scanner_emul.py`
- **Критерии готовности**: кнопка видна между combo и Run; клик перечитывает порты без сброса выбранного (если порт ещё в списке); при running кнопка disabled вместе с combo; тест зелёный.
- **Зависимости**: нет
- **Оценка**: S

### 2. Кнопка удаления и сигнал на всех виджетах

- **ID**: 2
- **Стек**: backend
- **Описание**: Во всех пяти UI-формах добавить `tbDelete` сразу после `tbRun` (28×28, tooltip «Удалить», текст «X» или иконка `fa5s.times`). Layouts: Printer/Camera/Scanner — `horizontalLayout` (шапка); Transporter/Generator — `horizontalLayout_6` (рядом с `tbRun`). Регенерировать `forms/{Printer,Camera,Scanner,Transporter,Generator}.py`. В каждом виджете:
  - `delete_requested = Signal()` (PySide6 `Signal` без аргументов; sender = виджет);
  - в `_connect_ui`: `tbDelete.clicked.connect(self._on_delete_clicked)`;
  - `_on_delete_clicked`: если `tbRun.isChecked()` → warning и return; иначе question с именем из `leName` / `self.name`; при Yes — `self.delete_requested.emit()`.
  Одинаковый UX на всех пяти классах; без общего mixin (копирование короткого слота допустимо, чтобы не раздувать архитектуру).
- **Файлы/модули**: `forms/ui/Printer.ui`, `forms/ui/Camera.ui`, `forms/ui/Scanner.ui`, `forms/ui/Transporter.ui`, `forms/ui/Generator.ui`, соответствующие `forms/*.py`, `core/printing/printer_widget.py`, `core/scanning/camera_widget.py`, `core/barcode_scanner/scanner_widget.py`, `core/transporting/transporter_widget.py`, `core/generator/generator_widget.py`
- **Критерии готовности**: у каждого виджета есть `tbDelete` и `delete_requested`; running → warning без emit; stopped + Yes → emit; No → виджет остаётся.
- **Зависимости**: нет (частичное пересечение с #1 по `Scanner.ui` / `scanner_widget.py` — выполнять **после** или **в одной волне с merge**: если параллельно, сначала #1, затем #2 на Scanner, либо одна сессия правит Scanner целиком; оркестратору: **не параллелить #1 и #2** из‑за общего `Scanner.ui` / `scanner_widget.py`)
- **Оценка**: M

### 3. Remove API в MainLineField, fix clear_ui/closeEvent и setup_models

- **ID**: 3
- **Стек**: backend
- **Описание**: В `MainLineField`:
  1. При `_add_device` / `_add_transport` / `_add_generator` подключить `widget.delete_requested` → `_on_widget_delete_requested`.
  2. Реализовать `_remove_device` / `_remove_transporter` / `_remove_generator` (или один метод с ветвлением по типу): pop из реестра, `run(False)`, `setParent(None)`, `deleteLater()`.
  3. После удаления device: для всех transporters/generators вызвать `setup_models(self._device_widgets)`; если удалён `ScannerWidget` — `_sync_scanner_name_generator()`.
  4. Исправить `TransporterWidget.setup_models` и `GeneratorWidget.setup_models`: **всегда** `self._device_data = dict(device_widgets)` (полная замена, не `update`); если `tbRun.isChecked()` — return **после** замены словаря, без пересборки combo (или пересобирать combo всегда — предпочтительно полная замена + пересборка, если UI combo можно трогать на running; минимум — словарь без stale id).
  5. `clear_ui()`: добавить цикл по `_generator_widgets` (stop + delete), аналогично transporters.
  6. `closeEvent`: добавить `run(False)` для всех generators.
- **Файлы/модули**: `core/main_ui/line_emul.py`, `core/transporting/transporter_widget.py`, `core/generator/generator_widget.py`
- **Критерии готовности**: удаление через сигнал убирает виджет с холста и из dict; combo не содержат удалённый id; `clear_ui` удаляет generators; `closeEvent` останавливает generators; загрузка конфига после удаления не оставляет «призраков».
- **Зависимости**: после #2
- **Оценка**: M

### 4. Unit-тесты remove API и регрессии clear_ui

- **ID**: 4
- **Стек**: backend
- **Описание**: Тесты по образцу `tests/test_core/test_bulk_control.py` (`QApplication`, mock COM/icons):
  - удаление остановленного printer/camera/scanner из `_device_widgets` и layout;
  - удаление transporter/generator из соответствующих dict;
  - отказ/не-вызов remove при running (через `_on_delete_clicked` с mock `QMessageBox`, либо прямой вызов remove API только для happy-path + отдельный тест слота с patch warning/question);
  - после удаления device — `_device_data` transporter/generator не содержит stale key;
  - `clear_ui()` очищает и `_generator_widgets`.
  Патчить `QMessageBox.question` / `warning` где нужно для неинтерактивного прогона.
- **Файлы/модули**: `tests/test_core/test_widget_delete.py` (новый), при необходимости правки `tests/test_core/test_bulk_control.py`
- **Критерии готовности**: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_widget_delete` (и связанные) — OK.
- **Зависимости**: после #3
- **Оценка**: S

### 5. Документация и CHANGES.LOG

- **ID**: 5
- **Стек**: backend
- **Описание**: Обновить docs Line Emulator:
  - `docs/line_emulator/line_emulator.md` — удаление виджетов, fix `clear_ui`/`closeEvent` для generators, refresh COM;
  - `docs/line_emulator/frontend/scanner-ui.md` / `scanner-widget.md` — `tbRefreshPorts`, `tbDelete`;
  - `docs/line_emulator/user-guides/scanner-widget.md` — шаг «обновить список COM», «удалить виджет»;
  - краткая user-guide заметка об удалении любого виджета (можно секция в `line_emulator.md` или `user-guides/README.md` + короткий файл / абзац в bulk-control соседстве);
  - `CHANGES.LOG` — запись в начало;
  - инкремент `client_info.VERSION` — при сборке/релизе по соглашению проекта (если в рамках задачи делается build — поднять последний разряд; иначе зафиксировать в CHANGES и поднять VERSION вместе с реализацией фичи, как в предыдущих планах Line Emulator).
- **Файлы/модули**: `docs/line_emulator/**`, `CHANGES.LOG`, `client_info.py`
- **Критерии готовности**: docs отражают UX удаления и refresh COM; CHANGES.LOG обновлён; VERSION согласован с записью в логе.
- **Зависимости**: после #1–#4
- **Оценка**: S

## Чеклист выполнения

- [x] 1. Кнопка обновления COM-портов в сканере
- [x] 2. Кнопка удаления и сигнал на всех виджетах
- [x] 3. Remove API в MainLineField, fix clear_ui/closeEvent и setup_models
- [x] 4. Unit-тесты remove API и регрессии clear_ui
- [x] 5. Документация и CHANGES.LOG

## Волны выполнения

- **Волна 1:** #1 (COM refresh) — отдельно; **затем** #2 (delete UI+сигналы). Не параллелить #1 и #2: оба правят `Scanner.ui` / `scanner_widget.py`.
- **Волна 2:** #3 — после #2 (нужен сигнал `delete_requested`).
- **Волна 3:** #4 — после #3.
- **Волна 4:** #5 — после #1–#4 (tech-writer в конце каждой подзадачи по циклу; финальная сверка user-facing — в #5 / `user-doc-writer` оркестратора).

Примечание: внутри каждой подзадачи цикл `developer → code-review → tech-writer`. Подзадача #5 может быть целиком на tech-writer после кода, либо developer правит CHANGES/VERSION, tech-writer — docs.

## Процесс выполнения

**Обязательно:** каждая подзадача проходит цикл по полю **Стек**:

- `backend` → `developer → code-review → tech-writer`
- `frontend` → `frontend-developer → frontend-code-review → frontend-tech-writer`
- `mixed` → разбей на отдельные подзадачи со своим стеком, если возможно

**Параллельно:** подзадачи **без общих файлов** и **без зависимостей** друг от друга — в одной **волне**. Здесь #1 и #2 пересекаются по Scanner — **последовательно**.

Оркестратор (основная сессия) **не пишет код сам** — skill `/execute-plan` или `/execute-development-cycle`.

```text
/execute-plan .plans/backlog/2026-07-13-line-emulator-widget-delete-com-refresh.md
```

При **Build** в Plan mode агент следует тем же правилам (см. `.cursor/rules/plan-execution-orchestration.mdc`).

## Риски и открытые вопросы

- **Пересечение Scanner:** #1 и #2 нельзя делать двумя параллельными агентами — риск конфликтов merge в `.ui` / виджете.
- **Running transporter со ссылкой на удалённый device:** после полной замены `_device_data` combo при running может не обновиться до stop — зафиксировать в #3: словарь всегда чистый; при stop/`setup_models` combo пересоберётся. При желании можно дополнительно сбрасывать selection, если id исчез — не блокер MVP.
- **FlowLayout:** удаление через `setParent(None)` уже используется в `clear_ui` — повторять тот же паттерн, не изобретать `removeWidget`, если текущий путь стабилен.
- Открытых продуктовых вопросов нет: UX и имена кнопок зафиксированы выше.

## Следующий шаг

Запустить `developer` для подзадачи **#1** (COM refresh в сканере) — минимальный независимый кусок с готовым `_refresh_com_ports`.

## Журнал изменений плана

| Дата | Изменение |
|------|-----------|
| 2026-07-13 | Создан план |
