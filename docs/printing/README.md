# Справочники языков принтера (эмулятор линии)

| Параметр | Значение |
|----------|----------|
| Дата актуализации | 2026-09-16 |
| План реализации | [`.plans/complete/2026-09-16-printer-language-emulation.md`](../../.plans/complete/2026-09-16-printer-language-emulation.md) |
| Ядро эмулятора | [`core/printing/printer_core.py`](../../core/printing/printer_core.py) |
| Контракт PSM (ожидается) | [`.plans/PRINTER_INTEGRATION_EMULATOR.md`](../../.plans/PRINTER_INTEGRATION_EMULATOR.md) |

## Назначение

Каталог собирает **официальные мануалы** производителей для языков, которые эмулятор принтера на производственной линии должен понимать в режимах **TSPL2**, **EZPL**, **ZPL** и **SAVEMA SPPL**. Локальные копии PDF складываются в [`manuals/`](manuals/). Режим **Legacy** (CHW, старые `~S` / `~HS` без отдельного vendor-мануала) в этом разделе не дублируется — поведение задаётся текущим кодом и планом эмуляции.

Цель эмуляции по плану: Print Station Mini проходит identity/status/queue на TSPL2/EZPL/ZPL; SAVEMA-клиент получает ответы `~SPGRES{…}^`; GS1 из нативных полей и очередей попадает в буфер линии; растровые задания не роняют TCP; старые JSON без `language` остаются на Legacy.

## Мануалы PDF

| Язык | Локальный файл (`manuals/`) | Официальный источник | Статус |
|------|-----------------------------|----------------------|--------|
| **TSPL2** (TSC) | `tspl_tspl2_programming_3_0.pdf` | [TSPL/TSPL2 Programming Manual v3.0 (PDF)](https://fs.tscprinters.com/system/files/31-0000001-00_tspl_tspl2_programming_3_0.pdf) | **pending download** — положить PDF в `manuals/` |
| **EZPL** (GoDEX) | `ezpl_o4_en.pdf` | [EZPL Programming Manual O.4 EN (PDF)](https://godex.com.ua/components/com_jshopping/files/demo_products/EZPL_O.4_EN.pdf) | **pending download** — положить PDF в `manuals/` |
| **ZPL** (Zebra) | `zpl-zbi2-pg-en.pdf` | [ZPL/ZBI2 Programming Guide (PDF)](https://www.zebra.com/content/dam/support-dam/en/documentation/unrestricted/guide/software/zpl-zbi2-pg-en.pdf) | **pending download** — положить PDF в `manuals/` |
| **SAVEMA SPPL** | не качаем отдельно | [SPPL Rev.11 (PDF в репозитории)](../SPPL%20-%20Rev11.pdf) | использовать существующий файл в `docs/` |

Скачивание TSC/GoDEX/Zebra в `manuals/` выполняется **только после явного разрешения** (см. подзадачу #1 плана). Пока файлов нет — разработка опирается на URL выше и на перечень команд ниже; отсутствие PDF не блокирует остальные волны плана.

## Эмулируемые команды и кадры (scope плана)

Ниже — **не полный** перечень из мануалов, а минимальный набор, зафиксированный в плане эмуляции. Детали полей и синтаксиса — в соответствующих PDF.

### TSPL2

| Категория | Команды / поведение |
|-----------|---------------------|
| Запрос статуса | `ESC !?` (байты `1B 21 3F`, без CR/LF) → **один байт** флагов (ready = `0x00`; маски head/jam/paper/ribbon/pause/printing/other) |
| Счётчик / PSM | `OUT NET "PSM_LABEL=";STR$(LABEL)\r\n` → ответ `PSM_LABEL={odometer}\r\n` |
| Задание на печать | Кадр `BITMAP x,y,B,H,mode,` + ровно `B×H` байт растра + `\r\nPRINT` (framing не ищет команды внутри bitmap) |
| Извлечение GS1 | `DMATRIX`, `BARCODE "content"`; префиксы `~1`, `~dNNN`, `~~` |
| Не эмулировать в TSPL2-режиме | Ответы на `~HI`, `~S,STATUS` (это другие языки) |

### EZPL (GoDEX)

| Категория | Команды / поведение |
|-----------|---------------------|
| Identity | `~HI` → `\x02EZ2350i,V1.151p,12,1014KB\x03\r\n` |
| Очередь / busy | `~S,STATUS\r\n` → `aa,nnnnn\r\n` (в т.ч. `50` printing, `60` processing, затем `00` idle); `~S,LABEL\r\n` → 3–5 цифр остатка (`015`, не `15`) |
| Задание на печать | Конверт `^Q/^W/^P1/^C1/^R0/~R200/^L` + `Q0,0,B,H\r\n` + `B×H` байт + `\r\nE\r\n` |
| Извлечение GS1 | `XRB…,length` + следующие `length` байт; `BR,…` |

### ZPL (Zebra)

| Категория | Команды / поведение |
|-----------|---------------------|
| Identity | `~HI` → STX/ETX (не строка GoDEX), напр. `\x02ZEBRA-EMU,1.0,8\x03\r\n` |
| Host status | `~HS` → **три** кадра STX/ETX (12 полей, 11 полей, непустой третий) |
| Odometer | SGD `! U1 getvar "odometer.total_label_count"\r\n` → `"123"\r\n` (инкремент по завершению печати) |
| Задание на печать | `^XA` … `^GFA,N,N,B,` + `2×N` hex + `^FS^PQ1^XZ\r\n` |
| Извлечение GS1 | `^FD` / `^FH^FD` (в т.ч. `_7e`); не брать hex из `^GFA` |

### SAVEMA SPPL (Rev.11)

Кадры: команды `~…^`, цепочки через `|`; framing не режет внутри `{…}`.

| Команда | Ответ / эффект (кратко) |
|---------|-------------------------|
| `SPLAMQ` / `SPLAQD` | `~SPGRES{SPLAMQ:OK}^` / `SPLAQD:OK`; FIFO по полям; GS1 длиной ≥13 во все коды линии |
| `SPLGMQ` / `SPLGQC` | `~SPGRES{SPLGMQ:F1=n<F2=n}^` (имя **запрошенной** команды) |
| `SPLCMQ` / `SPLCQD` | `~SPGRES{SPLCMQ:OK}^` + очистка указанных FIFO и кодов линии |
| `SPMC2D` / `SPMCBV` / `SPMCSV` / `SPMCTV` | `~SPGRES{CMD:OK}^` + код в буфер при длине ≥13 |
| `SPPSAP` / `SPPSTP` / `SPPSLQ` | OK/FAIL; SAP→RUNNING, STP→WAITING; разбор `\|` |
| `SPPSTA` | `~SPGRES{SPPSTA:RUNNING<}^` без `<WORKING` |
| `SPGGFV` / `SPGGFW` (алиас) | `~SPGRES{SPGGFV:…}^` |
| `SPGGTP` / `SPGGCP` | числа в SPGRES |
| `SPLGSD` | `~SPGRES{SPLGSD:a.csv<b.csv}^` |
| `SPLDDF` | `~SPGRES{SPLDDF:OK}^` |
| `SPLTDS` / `SPLLTF` / `SPLCDF` | OK-заглушки |
| Прочие `~SP[CLMPGT]…^` | `~SPGRES{CMD:OK}^` (get — правдоподобный пустой payload) |

Извлечение GS1: пары `Field~gt~rows` из `SPLAMQ`/`SPLAQD`; значения ≥13 не только в поле `barcode`; `SPMC2D`/`SPMCBV`/`SPMCSV`; XML `SPLTDS` `<Data>` для 2D/Barcode.

Полная спецификация: [`../SPPL - Rev11.pdf`](../SPPL%20-%20Rev11.pdf). Вне scope плана: полная таблица 100+ config/traverse SPPL; команды PSM §12 (`~K1`, `~HQOD`).

## Связанные модули

| Модуль | Назначение |
|--------|------------|
| `core/printing/data.py` | `PrinterLanguage`, поле `PrinterConfig.language` |
| `core/printing/framing.py` | Сборка бинарных кадров BITMAP / Q…E / ^GFA / SPPL |
| `core/printing/extract.py` | Извлечение GS1 по языку |
| `core/printing/dialects/*.py` | Логика TSPL2, EZPL, ZPL, SPPL, Legacy |

## Каталог `manuals/`

Положите сюда локальные копии PDF из таблицы выше с **именами файлов как в колонке «Локальный файл»**. После появления файлов обновите колонку «Статус» в этом README (вручную или в отдельной doc-задаче).
