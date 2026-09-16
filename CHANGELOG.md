# Журнал изменений (разработка)

Хронология существенных изменений в репозитории **Эмулятора производственной линии** (`main.py`). Пользовательские release notes — в [`WHATSNEW.md`](WHATSNEW.md); построчный журнал разработки — в [`CHANGES.LOG`](CHANGES.LOG).

Новые секции — сверху.

---

## [2026-09-16] Эмуляция языков принтера

Эмулятор TCP-принтера (`core/printing/printer_core.py`) переведён на **диалекты** по выбранному языку: запросы статуса и задания печати обрабатываются в протоколе клиента (Print Station Mini, SAVEMA и legacy CHW), извлечённые GS1-коды попадают в буфер линии `_print_buffer`.

### Контракт и конфигурация

- `core/printing/data.py`: перечисление `PrinterLanguage` (`legacy`, `tspl2`, `ezpl`, `zpl`, `sppl`); поле `PrinterConfig.language` с default `legacy` — старые JSON без `language` загружаются без ошибок.
- Сохранение/загрузка: `PrinterWidget.options()` → `ConfigFile.printers[]`; `MainLineField.add_printer` / `_load_printers` прокидывают `language`.

### Ядро и вспомогательные модули

- `core/printing/framing.py`: накопительный бинарный framing кадров TSPL2 (`BITMAP` + `PRINT`), EZPL (`Q…E`), ZPL (`^GFA`), SPPL (`~…^`).
- `core/printing/extract.py`: извлечение штрихкодов/GS1 по языку; `libs/template_parsers.py` делегирует сюда (обратная совместимость импортов).
- `core/printing/printer_core.py`: приём **bytes** на соединение, dispatch по `PrinterLanguage`, ответы query через `sendall`, отложенные фазы busy (EZPL/ZPL/TSPL), состояние устройства не сбрасывается на reconnect; удалён монолитный `_process_status_requests`.

### Диалекты (`core/printing/dialects/`)

| Модуль | Режим | Кратко |
|--------|--------|--------|
| `base.py` | — | `PrinterDialect`, `PrinterDeviceState`, callback `on_codes` |
| `tspl2.py` | TSPL2 | `ESC !?` (1 байт), `PSM_LABEL`, BITMAP/PRINT |
| `ezpl.py` | EZPL | `~HI` GoDEX, `~S,STATUS` / `~S,LABEL`, busy 50→00 |
| `zpl.py` | ZPL | `~HI`, `~HS` (3 кадра STX/ETX), SGD odometer, `^GFA` |
| `sppl.py` | SAVEMA | `~SP…^`, `~SPGRES{…}^`, очереди SPLAMQ и др. (Rev.11) |
| `legacy.py` | Legacy | CHW, старые `~S`/`~HS`; кадры `~SP` делегируются в `sppl` |

Справочник команд и мануалы: [`docs/printing/README.md`](docs/printing/README.md).

### UI Line Emulator

- `forms/ui/Printer.ui`: `QComboBox` `cbLanguage` — **Legacy**, **TSPL2**, **EZPL**, **ZPL**, **SAVEMA** (значение `sppl` в JSON).
- `core/printing/printer_widget.py`: чтение/запись combo; блокировка вместе с именем и портом при Run; `PrinterProxy.start(..., language=)`.

### Тесты (без живого TCP)

- `tests/test_core/test_printer_framing.py`, `test_printer_extract.py`, `test_printer_tspl2.py`, `test_printer_zpl.py`, `test_printer_sppl.py`, `test_printer_config.py`.

### Документация

- Карта модулей: [`index.md`](index.md) (раздел `core/printing`).
- План и контракт PSM: [`.plans/complete/2026-09-16-printer-language-emulation.md`](.plans/complete/2026-09-16-printer-language-emulation.md).
