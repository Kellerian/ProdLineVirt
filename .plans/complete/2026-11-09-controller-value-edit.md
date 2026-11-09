---
title: Редактируемое значение регистра на карточке контроллера
created: 2026-11-09
updated: 2026-11-09
status: completed
priority: high
estimated_subtasks: 2
---

# Редактируемое значение регистра на карточке контроллера

## Контекст и цель

Колонка «Значение» на карточке контроллера только для чтения. `_append_register_row` в `core/controller/controller_widget.py` ставит ячейке флаги `ItemIsEnabled | ItemIsSelectable` без `ItemIsEditable`. Клавиша не открывает редактор: `QTableWidget` уходит в `keyboardSearch` и перескакивает на другую строку с тем же текстом. Опрос `_poll_register_values` каждые 500 мс делает `setText` из `ControllerRuntime.read_points` и затирал бы ввод. `itemChanged` срабатывает и на этот программный `setText`, поэтому запись из слота без защиты зациклится.

Успех: при **S** (`tbRun` включён, рантайм запущен) ячейку «Значение» можно править с клавиатуры и двойным щелчком. Введённое число пишется в локальный datastore запущенного контроллера одним вызовом с цикла воркера. Holding остаётся целым `0…65535`, coil по-прежнему показывается как `True`/`False`, успех — зелёный `QColor(0, 128, 0)`. Мусор в ячейку datastore не попадает и не красится в красную пустую. В файл линии по-прежнему уходят только адреса. После **R** колонка пустая и снова не редактируется. Колонка «Переменная» редактируется и на запущенной карточке, как сейчас.

Предшественник `.plans/complete/2026-11-06-controller-register-typed-values.md` не переписывать. `client_info.DB_VERSION` не менять. Грамматику `core/controller/addresses.py` не менять. `DoypackEmulation` не менять.

## Обзор подхода

Два слоя, тот же каркас, что у чтения.

1. **`ControllerRuntime.write_point`** — один синхронный метод с GUI-потока. Внутри одна корутина на цикле воркера через `asyncio.run_coroutine_threadsafe` и `fut.result(timeout=0.25)`. На цикле вызываются уже существующие `ModbusEmulator.update_holding_register(address, int)` и `update_coil(address, bool)` (`core/controller/modbus_server.py`). Второй `ModbusTcpClient` / `AsyncModbusTcpClient` не создавать. `read_points` и `read_holding_registers` не менять.
2. **Виджет** включает `ItemIsEditable` у колонки 1 только пока карточка запущена, по `itemChanged` разбирает текст и зовёт `write_point`. Программные `setText` / `setForeground` / `UserRole` опроса идут под счётчиком защиты, чтобы не писать в datastore повторно. Пока редактор этой ячейки открыт, тик опроса её не трогает.

Это живая правка datastore. `options()` / `register_addresses` по смыслу те же: только токены адресов. Значения в JSON не добавлять.

Адреса очереди Doypack (Delta с **4146**, Xinje с **20**, шаг и `can_start_work` в `core/controller/doypack.py`) **не** особый случай. Запись в них разрешена. Цикл Doypack может перезаписать регистр следующим шагом. Это ожидаемо, логику цикла не трогать и тестом «значение обязано удержаться на 4146» не закреплять.

### Разбор текста «Значение» (зафиксирован)

После `strip` вся строка — только ASCII-цифры (`0-9`), без знака, точки, запятой и букв. `str.isdigit()` само по себе не годится: оно пропускает юникодные цифры. Пустая строка, пробелы, `+1`, `-1`, `1.5`, `1,5`, `True` / `False` / `true` / `TRUE` — отказ.

| Тип строки | Допустимый ввод | Что уходит в `write_point` | Что видно после успеха |
|------------|-----------------|----------------------------|------------------------|
| holding | целое **0…65535** включительно (`0`, `0007`, `65535`) | `int` (ведущие нули схлопываются: `0007` → `7`) | `str(int)`, зелёный `QColor(0, 128, 0)` |
| coil | целое **0** и любое **> 0** (верхней границы нет) | `False` если 0, иначе `True`. Слова `True`/`False` не принимаются | `"False"` или `"True"`, тот же зелёный |

Диапазон **значения** holding `0…65535` — это 16-битный регистр Modbus. Он не равен диапазону **адреса** holding `0…10000` из `addresses.py`. Адрес по-прежнему берётся из колонки «Переменная» через `parse_register_token` (`parsed.kind`, `parsed.address`).

Отказ (мусор, пусто, holding вне `0…65535`, неразобранный адрес в колонке 0, `write_point` вернул `False` или бросил): datastore **не** менять, `QMessageBox` **не** показывать. Вернуть ячейке последний успешно показанный текст (см. ниже) и зелёный цвет. Если такого текста ещё не было — пустая ячейка и сброс `ForegroundRole` (`setData(..., None)`), не красная пустая.

Успешная запись сразу ставит канонический текст и зелёный под защитой от `itemChanged`. Следующий тик опроса по-прежнему показывает holding как `str(int)`, coil как `True`/`False`, успех зелёный, сбой чтения точки — пустая красная `QColor(128, 0, 0)`. Отдельный путь отображения кроме «канон после записи» и уже существующего опроса не добавлять.

### Последний успешный текст

Хранить на item колонки 1 в `Qt.ItemDataRole.UserRole` строку канонического показа (`"4"`, `"0"`, `"True"`, `"False"`). Не словарь по номеру строки: вставка строк не должна сдвигать память.

- Успешный слот опроса (`bool` или `int`) и успешная запись — записать эту строку в `UserRole`.
- Слот `None` (красная пустая) — `UserRole` **не** затирать. Отказ ввода тогда вернёт прежний успешный текст, а не красную пустую. Следующий тик, если чтение снова `None`, снова покажет красную пустую — это обычный опрос, не реакция на мусор.
- Пустой или невалидный адрес на тике — как сейчас очистить текст и `ForegroundRole` и **сбросить** `UserRole` (для этого токена успешного чтения нет).
- `run(False)` — очистить текст, `ForegroundRole` и `UserRole`.

`setData(UserRole)` тоже шлёт `itemChanged`. Только вместе с `setText` / `setForeground` и под тем же счётчиком.

### Защита от цикла записи

`QTableWidget.itemChanged` подключен один раз (не вместе с `cellChanged` — будет двойная запись). Слот сразу выходит, если глубина `_register_cell_guard > 0`.

Любая программная правка item колонки 1 (`setText`, `setForeground`, `setData` роли `ForegroundRole` и `UserRole`) увеличивает счётчик на время вызова и на это время делает `tblRegisters.blockSignals(True)`. Счётчик, а не один `bool`: `_clear_value_row` вложенно зовёт текст и цвет. Снимать блок и уменьшать счётчик в `finally`.

Без этой защиты тик опроса делает `setText("4")` → `itemChanged` → `write_point` → следующий тик снова пишет. Смена адреса в колонке 0 при незащищённом `setText` значения записала бы старое число уже в новый регистр. Колонку 0 слот не откатывает и в datastore из неё не пишет.

Пока карточка не запущена (`tbRun` выключен или `_runtime is None`), слот выходит **не** меняя текст. Иначе сломаются текущие тесты, которые на остановленной карточке кладут в «Значение» `"999"` / `"junk"` / `"keep"` и ждут, что `options()` это игнорирует, а ячейка не очищается.

### Редактор и опрос

`editTriggers` таблицы не менять и `keyboardSearch` не выключать. У `QTableWidget` по умолчанию есть `AnyKeyPressed | EditKeyPressed | DoubleClicked`. Когда у ячейки есть `ItemIsEditable`, клавиша открывает редактор и поиск по строкам не забирает фокус. Отдельный `keyPressEvent` и делегат не писать: проверка ввода — на коммите (`itemChanged`), чтобы `True` можно было ввести и тут же откатить.

Пока редактор открыт, тик **не** вызывает `setText`, `setForeground`, сброс цвета и `setData` у **этой** строки (ни успех, ни красная пустая, ни очистка из-за плохого адреса). Остальные строки тика обновляются. Чтение `read_points` для редактируемой строки можно не исключать: пропускается только применение результата. Редактор не закрывать из таймера.

Открытый редактор колонки 1: `tblRegisters.state() == QAbstractItemView.State.EditingState` и `currentIndex()` валиден, его `row()` совпадает, `column() == 1`. Редактор колонки 0 на значение не влияет — колонку 1 в этом случае опрос обновляет.

### Флаги колонки «Значение»

- Остановлено (конструктор, `load_options`, неудачный `start`, после `run(False)`): `ItemIsEnabled | ItemIsSelectable`.
- После успешного `start`, пока `tbRun` включён и `_runtime is not None`: те же флаги плюс `ItemIsEditable` у всех уже существующих строк и у строки, добавленной «Добавить переменную».
- `_value_table_item`, если создаёт item по ходу опроса, ставит флаги по этому же правилу.
- Колонка 0 всегда `ItemIsEnabled | ItemIsSelectable | ItemIsEditable`. `_set_fields_enabled` таблицу и `btnAddRegister` по-прежнему не трогает.

Порядок `run(False)` не ломать: стоп таймера, `runtime.stop()`, `_runtime = None`, затем очистка колонки значений (текст, цвет, `UserRole`, снятие `ItemIsEditable`).

### Контракт `write_point`

```text
write_point(self, kind: str, address: int, value: int | bool) -> bool
```

Один вызов = одна корутина на цикле воркера = один `run_coroutine_threadsafe`. Не очередь, не слияние с тиком `read_points`, не пакет точек. Таймаут **0.25** с на весь вызов. Пустого списка нет: метод всегда про одну точку.

Возврат `True` только если запись в datastore на цикле воркера выполнилась. Иначе `False`, исключение наружу не бросать (виджет всё равно ловит его).

На цикле, до вызова `update_*`:

- `"holding"`: `address` — `int` и не `bool`, **0…10000**; `value` — `int` и не `bool`, **0…65535**. Иначе `False`, `update_holding_register` не звать.
- `"coil"`: `address` — `int` и не `bool`, **0…5000**; `value` — именно `bool` (`True`/`False`). Целые `0`/`1` отклонять: виджет уже превратил число в `bool`. Иначе `False`, `update_coil` не звать.
- Иной `kind` — `False`, datastore не трогать.
- Исключение `update_*` — DEBUG `CTL` без traceback, `False`.

Рантайм не запущен, поток мёртв, цикл закрыт, `modbus is None`, сбой планирования, `TimeoutError`, иное исключение `fut.result` — DEBUG в том же стиле, что у `read_points` (`schedule failed` / `timed out after 0.25s` / `result failed`), вернуть `False`. Невалидные аргументы без исключения не логировать (как невалидный адрес в `read_points`).

`update_holding_register` / `update_coil` не расширять проверками и не вызывать с GUI-потока. Импортов PySide, qasync и `AsyncModbusTcpClient` в `runtime.py` не добавлять.

## Подзадачи

### 1. Запись точки в datastore с цикла рантайма

- **ID**: 1
- **Стек**: backend
- **Описание**:

  В `ControllerRuntime` добавить `write_point` по контракту выше. Образец каркаса — `read_points` в том же файле (`_state_lock`, снимок `loop` / `modbus` / `thread`, вложенная корутина, `asyncio.run_coroutine_threadsafe`, `fut.result(timeout=0.25)`, отдельный `except concurrent.futures.TimeoutError`). `read_points` и `read_holding_registers` не менять. `modbus_server.py`, `doypack.py`, `addresses.py` не менять.

  Developer: строка в начало `CHANGES.LOG` (запись holding/coil в datastore через `write_point`, таймаут 0.25 с). `VERSION` и `DB_VERSION` не менять. `docs/` не править.

  **Документация (tech-writer после ревью):** `docs/line_emulator/controller_core.md` — раздел про `write_point` рядом с `read_points`: один `run_coroutine_threadsafe`, таймаут 0.25 с, `update_holding_register` / `update_coil`, адрес holding 0…10000 и значение 0…65535 (`bool` отклонён), адрес coil 0…5000 и значение только `bool`, `False` без исключения, без второго клиента. Разделы `read_points` и `read_holding_registers` не переписывать. Шапку версии на `b0013` не ставить — бамп в #2. `WHATSNEW.md` и `user-guides/` не трогать.

- **Файлы/модули**: `core/controller/runtime.py`, `tests/test_core/test_controller_runtime.py`, `CHANGES.LOG`
- **Критерии готовности**:
  - После `start` (Delta, simplex, `queue_size` 10 — очередь Doypack занимает holding **4146…4156**, адрес **100** вне неё): `write_point("holding", 100, 65535)` → `True`, `read_points([("holding", 100)]) == [65535]`, тип `int`. Внешний `AsyncModbusTcpClient.write` не нужен для этой записи; один `read_holding_registers` клиента видит **65535** (datastore сервера, не только локальный снимок).
  - `write_point("holding", 100, 0)` → `True`, чтение `[0]`. `write_point("holding", 100, 7)` после ведущего смысла «7», чтение `[7]`.
  - `write_point("holding", 100, 65536)`, `write_point("holding", 100, -1)`, `write_point("holding", 100, True)` → `False`, в регистре остаётся прежнее значение. `True` не проходит как `int`.
  - `write_point("coil", 100, True)` → `True`, `read_points([("coil", 100)]) == [True]`, тип `bool`. Затем `False` → чтение `[False]`. `write_point("coil", 100, 1)` и `write_point("coil", 100, 0)` → `False`, coil не меняется (остаётся `False` после предыдущего шага).
  - `write_point("holding", 10001, 1)`, `write_point("coil", 5001, True)`, `write_point("discrete", 0, 1)`, `write_point("holding", True, 1)` → `False`, метод не бросает.
  - `write_point("holding", 4146, 9)` → `True`. Не ждать, что 9 удержится: цикл Doypack может записать своё. `doypack.py` не менять.
  - До `start` и после `stop` вызов → `False`.
  - Существующие тесты `read_points` / `read_holding_registers` без смены ожиданий, включая Doypack «1 на 4146 становится 3 за 3 с».
  - В тексте `runtime.py` нет `AsyncModbusTcpClient`, `PySide`, `qasync`.
  - Прогон: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_controller_runtime`.
  - В diff этой подзадачи нет правок `client_info.py`, `doypack.py`, `addresses.py`, `controller_widget.py`.
- **Зависимости**: нет
- **Оценка**: S

### 2. Редактируемая колонка «Значение» на карточке

- **ID**: 2
- **Стек**: backend
- **Описание**:

  `ControllerWidget` (`core/controller/controller_widget.py`):

  - Сигнал `tblRegisters.itemChanged` в `_connect_ui`. Слот по правилам раздела «Защита от цикла записи».
  - Флаги колонки 1 по разделу «Флаги». После успешного `start` выставить `ItemIsEditable` всем текущим ячейкам значения. В `_append_register_row` и `_value_table_item` — те же флаги, если карточка уже запущена. `run(False)` снимает `ItemIsEditable` вместе с очисткой текста, `ForegroundRole` и `UserRole`.
  - Слот колонки 1 при запущенной карточке: адрес строки через `parse_register_token`. Не разобрался — отказ без записи. Иначе разбор значения по таблице выше. Holding: `write_point("holding", parsed.address, number)`. Coil: `write_point("coil", parsed.address, number > 0)`. Успех: под защитой канонический текст, зелёный `QColor(0, 128, 0)`, `UserRole`. Отказ или `False`/исключение из `write_point`: DEBUG `CTL` без traceback при сбое вызова, откат к `UserRole` (зелёный) или пусто без красного, без `QMessageBox`.
  - `_poll_register_values`: применение к строке пропустить, если открыт редактор её колонки 1 (раздел «Редактор и опрос»). Успешный слот по-прежнему пишет канонический текст, зелёный и `UserRole`. `None` — пусто и красный, `UserRole` не трогать. Пустой/плохой адрес — очистка текста и цвета и сброс `UserRole`, но не у строки с открытым редактором значения. Исключение или неверная длина `read_points` — как сейчас, ячейки не менять. Все программные правки item — под `_register_cell_guard`.
  - `options()` не читать колонку 1 и не добавлять полей в `ControllerConfig`. Адреса 4146, 20 и прочие валидные токены писать так же, как любой другой адрес. `forms/ui/Controller.ui`, `forms/Controller.py`, `addresses.py`, `doypack.py`, `line_emul.py` не менять.

  Developer: строка в начало `CHANGES.LOG`. Единственный бамп `client_info.VERSION` с `1.0.0.1.b0012` на `1.0.0.1.b0013` (префикс `b`). `DB_VERSION` не менять. `docs/` не править.

  **Документация (tech-writer после ревью):**

  - `docs/line_emulator/controller_widget.md` — колонка «Значение» редактируется только при запущенном рантайме; разбор holding `0…65535` и coil `0` / `>0`; отказ откатывает последний успешный текст без message box и без красной пустой; опрос не делает `setText` открытому редактору; `itemChanged` опроса не пишет в datastore; `options()` по-прежнему только токены адресов; колонка «Переменная» редактируема и на **S**. Шапка версии — `1.0.0.1.b0013`.
  - `docs/line_emulator/controller.md` — абзац таблицы: правка значения при **S** пишется в локальный datastore, в JSON не сохраняется, очередь Doypack может перезаписать регистр. Строку версии сборки дополнить: редактирование «Значения» — с **`1.0.0.1.b0013`**. Формулу `q_start` не дублировать.
  - `docs/line_emulator/controller_core.md` — только шапка версии на `b0013`, если раздел `write_point` уже написан в #1.
  - `docs/line_emulator/config_controllers.md` не менять: схема `register_addresses` та же.
  - `WHATSNEW.md` и `user-guides/` не заполнять (это фаза `user-doc-writer` после всех подзадач).

- **Файлы/модули**: `core/controller/controller_widget.py`, `tests/test_core/test_controller_widget.py`, `client_info.py`, `CHANGES.LOG`
- **Критерии готовности**:
  - Остановленная карточка: колонка 0 с `ItemIsEditable`, колонка 1 без него (текущий `test_add_register_row_editable_flags` остаётся верен). `setText("999")` / `"junk"` в значении не вызывает запись и не стирает текст; `options()` по-прежнему только адреса.
  - Успешный `run(True)` с моком `ControllerRuntime`: у колонки 1 появляется `ItemIsEditable`, у колонки 0 он остаётся. `editTriggers` содержат `AnyKeyPressed`. После `run(False)` колонка 1 снова без `ItemIsEditable`, текст пустой, `ForegroundRole is None`. Неудачный `start` не включает редактирование значения и не запускает таймер.
  - Строка, добавленная при уже включённом **S**, имеет редактируемое значение.
  - Мок `read_points` → `[4]` на holding `"100"`, затем `item.setText("15")`: ровно один `write_point("holding", 100, 15)`, текст `"15"`, foreground `(0, 128, 0)`. `options().register_addresses == ["100"]`.
  - `"65535"` → `write_point(..., 65535)` и текст `"65535"`. `"65536"`, `"-1"`, `"1.5"`, `"1,5"`, `""`, `"   "`, `"abc"`, `"+3"`, `"True"`, `"False"` → `write_point` не вызывается, текст возвращается к `"4"` (последний успешный опрос), цвет зелёный, не красный, `QMessageBox.warning` / `information` / `critical` не вызываются.
  - `"0007"` на holding → `write_point(..., 7)` и текст `"7"`.
  - Coil `"2801"`: после опроса `"False"` ввод `"0"` → `write_point("coil", 2801, False)`, текст `"False"`. Ввод `"2"` и `"0007"` → `write_point(..., True)`, текст `"True"`. Ввод `"True"` откатывает к последнему успеху, записи нет.
  - Адреса `"4146"` и `"20"`: ввод `"9"` вызывает `write_point("holding", 4146, 9)` и `write_point("holding", 20, 9)`. Отдельной блокировки нет.
  - Адрес `"abc"` при запущенной карточке: `setText("1")` в значении не вызывает `write_point`.
  - Смена текста колонки 0 при **S** не вызывает `write_point` и не откатывает адрес.
  - После опроса сбросить мок `write_point` и вызвать `_poll_register_values` ещё раз (и `setForeground` внутри тика): `write_point` не вызывается.
  - Две строки со значением `"4"`, виджет `show()`, фокус на `(0, 1)`, `QTest.keyClick` клавиши `4`: `state() == EditingState`, `currentRow() == 0` (поиск не перескакивает на вторую четвёрку), `write_point` ещё не вызван. `Escape` закрывает редактор и тоже не пишет. В `finally` закрыть виджет.
  - Редактор строки 0 открыт (`edit(index)` после `show()`), мок чтения меняется на другое число и на `None`: текст и цвет строки 0 не меняются, соседняя строка обновляется. Если `edit()` вернул `False`, тест падает.
  - В `controller_widget.py` нет `ModbusTcpClient` и `AsyncModbusTcpClient`.
  - Прогон: `.\venv\Scripts\python.exe -m unittest tests.test_core.test_controller_widget tests.test_core.test_controller_line tests.test_core.test_controller_runtime`.
  - `client_info.VERSION == "1.0.0.1.b0013"`. В diff `DB_VERSION` не менялся.
- **Зависимости**: нет (сигнатура `write_point` зафиксирована выше; тесты виджета мокают `ControllerRuntime`)
- **Оценка**: M

## Чеклист выполнения

- [x] 1. Запись точки в datastore с цикла рантайма
- [x] 2. Редактируемая колонка «Значение» на карточке

## Волны выполнения

- **Волна 1:** #1 (`runtime.py`) и #2 (`controller_widget.py`, `client_info.py`) — общих файлов нет, сигнатура `write_point` задана в этом плане. `CHANGES.LOG` обеим можно дописывать в начало. `VERSION` бампает только #2.

## Процесс выполнения

**Обязательно:** каждая подзадача — `backend` → `developer` → `code-review` → `tech-writer`.

Оркестратор код сам не пишет. После всех пунктов чеклиста — один `user-doc-writer` (фаза 3 `execute-development-cycle`): `docs/line_emulator/user-guides/controller.md` и `WHATSNEW.md`.

Что сказать в пользовательской документации, без имён методов:

- При **S** ячейку «Значение» можно изменить. Числовой регистр — целое от 0 до 65535. Катушка — 0 выключена, любое число больше нуля включено. Слова True и False вводить нельзя.
- После успеха на экране снова целое или True/False, зелёным. Мусор, минус, дробь, пустая строка и число регистра вне 0…65535 не записываются: ячейка возвращается к последнему успешно показанному тексту, без окна с ошибкой и без красной пустой.
- В файл линии по-прежнему сохраняются только адреса из «Переменной».
- Адреса очереди (Delta с 4146, Xinje с 20) править можно; эмуляция очереди может записать своё значение следующим шагом.
- Пока ячейка открыта для ввода, опрос её не перезаписывает. После **R** колонка пустая и не редактируется. Колонку «Переменная» по-прежнему можно менять и на запущенной карточке.

```text
/execute-plan .plans/backlog/2026-11-09-controller-value-edit.md
```

## Риски и открытые вопросы

- Открытых вопросов нет: решения пользователя зафиксированы в разделах выше.
- `edit()` и `QTest.keyClick` в тесте виджета требуют `show()`. Без видимого виджета Qt не открывает редактор — тест должен это требовать, а не пропускать.
- Запись в holding 4146 / 20 гоняется с циклом Doypack. Критерий рантайма для 4146 — `write_point` вернул `True`, а не «девятка осталась в регистре».
- `bool` — подкласс `int`. И holding-значение `True`, и coil-значение `1` обязаны отвергаться в `write_point`, иначе в datastore уедет не то.

## Следующий шаг

Волна 1: параллельно `developer` для #1 (`write_point`) и `developer` для #2 (колонка «Значение»). Ревью и документация — внутри каждой подзадачи, до перехода к `user-doc-writer`.

## Журнал изменений плана

| Дата | Изменение |
|------|-----------|
| 2026-11-09 | Создан план |
