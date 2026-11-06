# Карточка «Контроллер» (Modbus / Doypack)

| Параметр | Значение |
|----------|----------|
| Виджет | `core/controller/controller_widget.py` → `ControllerWidget` |
| Форма | `forms/ui/Controller.ui`, `forms/Controller.py` |
| Поток / asyncio | `core/controller/runtime.py` → `ControllerRuntime` (отдельный не-daemon `threading.Thread`, свой `asyncio` loop на карточку) |
| Сервер Modbus | `core/controller/modbus_server.py` → `ModbusEmulator`; слушает **`0.0.0.0:<порт>`** (все IPv4), как принтер/камера |
| Клиент Doypack | `core/controller/doypack.py` → `DoypackEmulation`; подключается только к **`127.0.0.1:<тот же порт>`** — поле IP на карточке не вводится |
| Логгер | `CTL` (`libs/loggers.py` → `CONTROLLER_LOGGER`); в ядре — `logging.getLogger(CONTROLLER_LOGGER)` |

## Назначение и границы

Карточка воспроизводит поведение отдельного приложения ControllerServerEmulator (Modbus TCP + цикл Doypack), **без** импорта его кода и **без** `qasync`: главный цикл приложения остаётся `QApplication.exec()`.

| Где контроллер участвует | Где нет |
|--------------------------|---------|
| Холст устройств, JSON `controllers[]`, меню «Запустить/Остановить» (в т.ч. «Всё») | Перевозчик и генератор (combo «ИЗ» / «В» не перечисляют контроллер даже в списке «откуда») |
| Внешний Modbus-клиент к IP машины и порту карточки | Меню «Очистить данные» (нет очередей кодов — смысла нет) |

## Адреса Doypack (Xinje / Delta)

Очередь: регистры holding, шаг адреса **2** при Duplex (**simplex** — шаг **1**). Катушка старта работы — coil.

| Тип (`controller_type`) | `q_start` | `can_start_work` (coil) |
|-------------------------|-----------|-------------------------|
| **xinje** | 20 | 11 |
| **delta** | 4146 | 2567 |

Формула конца очереди: `q_end = q_start + (queue_size + 1) * step`, где `step = 2` если режим **duplex**, иначе `1`. Пример при `queue_size = 10`: Xinje simplex → `20 + 11 = 31`; Delta duplex → `4146 + 22 = 4168`.

## Datastore Modbus (размеры блоков)

Как в ядре `ModbusEmulator`: coils до **5000**, discrete inputs до **100**, holding registers до **10000**, input registers до **100** (индексация pymodbus — см. `controller_core.md`).

## Один `tbRun` и порядок старт / стоп

- **Старт:** в фоновом loop сначала listen **Modbus** на `0.0.0.0`, затем **Doypack** к `127.0.0.1`.
- **Стоп:** сначала отключение клиента Doypack, затем **`await server.shutdown()`** у экземпляра `ModbusTcpServer`. Не использовать «глобальный» `ServerStop` pymodbus — при нескольких карточках он трогает только последний сервер.
- Отмена `serve_forever` **без** предварительного `shutdown()` оставляет порт в `LISTEN` — поэтому каноничный путь стопа именно `shutdown()` (см. pymodbus 3.12).

## UI

- Порт — одно число (по умолчанию следующий из генератора линии, с **5020**).
- При **Run** поля имени, порта, очереди и режимов блокируются; при ошибке старта — откат, только запись в лог (`ERROR` + `exc_info`), без `QMessageBox`.
- Удаление кнопкой «X» — только на остановленной карточке (как у принтера).

**Таблица holding на карточке** (`tblRegisters`, кнопка «Добавить переменную»): пользователь задаёт **адреса** наблюдаемых holding-регистров (0…10000); список сериализуется в JSON как **`register_addresses`** (подробнее — [config_controllers.md](config_controllers.md)). При **включённом** `tbRun` значения в колонке «Значение» обновляются **каждые 500** мс из локального datastore сервера через `ControllerRuntime.read_holding_registers` (см. [controller_core.md](controller_core.md)); при остановке колонка значений очищается. Типовые адреса очереди Doypack и формула границы очереди — в разделе «Адреса Doypack» выше; наблюдаемые адреса в таблице могут быть любыми в допустимом диапазоне holding. Поведение UI, `load_options`/`options()` и `ValueError` при сохранении — [controller_widget.md](controller_widget.md).

## Сборка PyInstaller

В `build/spec/main.spec` к `hiddenimports` добавляется **`collect_submodules("pymodbus")`** — иначе в frozen exe не подтягиваются framer и вспомогательные подпакеты.

## Версия

Функциональность карточки входит в сборку с `client_info.VERSION` **`1.0.0.1.b0011`** и новее (таблица регистров и опрос — с этой версии).

## Связанные документы

- [controller_widget.md](controller_widget.md) — виджет карточки, таблица регистров, таймер опроса.
- [controller_core.md](controller_core.md) — детали `ModbusEmulator`, `get_modbus`, тесты.
- [config_controllers.md](config_controllers.md) — поля `ControllerConfig` в JSON.
- [bulk-control.md](bulk-control.md) — пункты меню «Контроллеры» и порядок «Всё».
