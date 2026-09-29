---
title: Сборка dmcLineEmulator в Debian-пакет (.deb)
created: 2026-09-29
updated: 2026-09-29
status: completed
priority: medium
estimated_subtasks: 6
---

# Сборка dmcLineEmulator в Debian-пакет (.deb)

## Контекст и цель

Нужна воспроизводимая возможность собрать проект **ProdLineVirt / dmcLineEmulator** (точка входа `main.py`, версия `client_info.VERSION`) в установочный **`.deb`**, не ломая существующую Windows-сборку через `build_project.py` → PyInstaller (`build/spec/main.spec` → `build/install/dmcLineEmulator/`).

**Успех:** на Linux-хосте (или WSL2) одной командой получается `.deb`, который после `sudo dpkg -i` ставит приложение, создаёт пункт меню (`.desktop`) и запускает GUI-эмулятор линии. Версия пакета берётся из `client_info.VERSION`. Документация описывает, где и как собирать.

**Вне объёма:** apt-репозиторий, GPG-подпись пакета, CI/CD, macOS, изменение `client_info.DB_VERSION` (в этом репозитории константы нет — не вводить).

## Обзор подхода

### Выбранный формат упаковки (зафиксировано)

**Один `.deb` с PyInstaller onedir для Linux + `.desktop` entry + `Depends` на системные shared libraries.**

Почему не «системный Python + Depends на python3-*»:

1. Текущая Windows-сборка уже onedir через PyInstaller — Linux-пакет зеркалит тот же контракт артефакта.
2. В `requirements.txt` есть `pylibdmtx` с Git-URL и жёсткие пины PySide6 — пакет на системном Python хрупкий и плохо воспроизводится через apt.
3. Bundled onedir изолирует приложение от версии Python дистрибутива.

Почему не собирать `.deb` на чистом Windows:

- PyInstaller не кросс-компилирует Windows → Linux ELF. Честный Linux-бинарь только на Linux (native / WSL2 / CI-раннер).

### Где собирается `.deb`

| Среда | Что допускается |
|-------|-----------------|
| **Linux / WSL2** (целевая) | Полный цикл: venv → PyInstaller → `dpkg-deb` → `.deb` |
| **Windows** | Только существующий `build_project.py` (exe); скрипт `.deb` **отказывается** с понятным сообщением |

Рекомендуемый хост для локальной сборки: **WSL2 Ubuntu 22.04+** или **Debian 12 / Ubuntu 22.04+**. `.deb` привязан к glibc build-хоста (это нормально для локального пакета без multi-arch CI).

### Целевой дистрибутив

**Debian 12 (bookworm) / Ubuntu 22.04+** (amd64). В `control` — `Architecture: amd64`, `Depends` на runtime shared libs (xcb/Qt-host, libGL, fontconfig, libdmtx при необходимости, опционально libpq5). Точный список Depends уточняется на этапе упаковки по `ldd` / документации PySide6 Linux.

### Архитектура артефактов

```text
build/install/dmcLineEmulator/     # PyInstaller onedir (как сейчас на Windows)
        ↓  (только Linux)
build/deb/dmclineemulator_…/      # staging tree для dpkg
  DEBIAN/control
  opt/dmclineemulator/...         # содержимое onedir
  usr/share/applications/*.desktop
  usr/share/pixmaps/...           # иконка из media/
        ↓
build/deb/dmclineemulator_<ver>_amd64.deb
```

Версия Debian: нормализация `client_info.VERSION` вида `1.0.0.1.b0006` → `1.0.0.1~b0006-1` (`~` — pre-release сортировка в dpkg). Функция нормализации — в скрипте сборки, с docstring и типами.

Существующий `build/spec/main.spec` с путями `..\..\` остаётся для Windows; для Linux — отдельный spec или тот же файл с **кроссплатформенными** путями (`os.path.join` / `Path`), без поломки Windows.

## Подзадачи

### 1. Кроссплатформенный PyInstaller spec для Linux (без поломки Windows)

- **ID**: 1
- **Стек**: backend
- **Описание**: Сделать сборку onedir возможной на Linux: либо поправить `build/spec/main.spec` на платформонезависимые пути к `main.py`, `media/logo.ico`, qtawesome fonts и `pylibdmtx.EXTERNAL_DEPENDENCIES`, либо добавить `build/spec/main_linux.spec` и оставить Windows-spec без изменений. Сохранить `hiddenimports` (`pylibdmtx`, `psycopg`, `serial`, `qtawesome`, …), `COLLECT` name `dmcLineEmulator`, `console=False`. На Linux убедиться, что бинарные зависимости `pylibdmtx` (libdmtx) попадают в bundle или явно документируются в Depends.
- **Файлы/модули**: `build/spec/main.spec` и/или `build/spec/main_linux.spec`
- **Критерии готовности**: на Linux `PyInstaller` по spec создаёт `build/install/dmcLineEmulator/dmcLineEmulator` (ELF); на Windows существующая команда `build_project.py` по-прежнему собирает onedir (регрессия не допускается — пути для win работают).
- **Зависимости**: нет
- **Оценка**: M

### 2. Точка входа сборки Linux onedir (расширение build_project или отдельный скрипт)

- **ID**: 2
- **Стек**: backend
- **Описание**: Добавить воспроизводимую сборку Linux-артефакта PyInstaller, не ломая Windows-поток `build_project.py`. Предпочтительно: параметр/подкоманда (например `build_project.py --linux` или отдельный `build_deb.py`, который вызывает общий helper) — на `platform.system() != "Linux"` печать ошибки и exit ≠ 0. Переиспользовать `generate_ui_files()`, `TMP_DIR` / `INSTALL_DIR`. Декодирование stdout в `run_external`: на Linux приоритет utf-8 (сейчас cp866/cp1251 — Windows-first; расширить без поломки Windows). Python только из `venv`.
- **Файлы/модули**: `build_project.py` и/или `build_deb.py` (новый), при необходимости общий helper в `build/`
- **Критерии готовности**: на Linux одна команда из venv собирает onedir в `build/install/dmcLineEmulator/`; на Windows вызов deb/linux-режима даёт понятный отказ; обычный `build_project.py` на Windows без флагов работает как раньше.
- **Зависимости**: после #1
- **Оценка**: M

### 3. Staging `.deb`: control, desktop, иконка, dpkg-deb

- **ID**: 3
- **Стек**: backend
- **Описание**: Реализовать упаковку onedir в `.deb`:
  - `Package`: `dmclineemulator` (lowercase, допустимое Debian-имя)
  - `Version`: из нормализованного `client_info.VERSION`
  - `Architecture`: `amd64`
  - `Maintainer`: разумное значение (например проект/организация; зафиксировать в control-шаблоне)
  - `Depends`: минимальный набор runtime libs для PySide6/xcb GUI + то, что не уехало в bundle (`libdmtx0a`/`libdmtx0` — уточнить по дистрибутиву; при необходимости `libpq5` если libpq не bundled)
  - `Section`: utils / science — на усмотрение, зафиксировать
  - Установка в `/opt/dmclineemulator/`
  - `usr/share/applications/dmclineemulator.desktop`: `Exec=/opt/dmclineemulator/dmcLineEmulator`, `Icon=dmclineemulator`, `Categories=Utility;`, `Terminal=false`
  - Иконка из `media/logo.png` (или конвертация) → `usr/share/pixmaps/`
  - Сборка через `dpkg-deb --build` (или `dpkg-deb -b`), артефакт в `build/deb/`
  - Строгая типизация + docstrings; для CLI `print` допустим (как в `build_project.py`)
- **Файлы/модули**: шаблоны в `build/debian/` (например `control.in`, `dmclineemulator.desktop`), логика в `build_deb.py` / helper; вывод в `build/deb/`
- **Критерии готовности**: на Linux после сборки существует `.deb`; `dpkg-deb -I` / `-c` показывают control с версией из `client_info.VERSION`, `.desktop` и дерево `/opt/dmclineemulator/`; `sudo dpkg -i` на той же машине ставит пакет без ошибки зависимостей (или с документированным `apt-get install -f` только если Depends намеренно минимальны — лучше закрыть Depends сразу).
- **Зависимости**: после #2
- **Оценка**: M

### 4. Runtime-зависимости и smoke-проверка запуска

- **ID**: 4
- **Стек**: backend
- **Описание**: По факту Linux-сборки уточнить `Depends`/`Recommends` (xcb, libxkbcommon, libegl/libgl, libglib, fonts, libdmtx, serial не требует пакета кроме доступа к `/dev/tty*`). Добавить короткий smoke: после установки или из staging — запуск бинаря с таймаутом / проверкой, что ELF стартует (GUI может требовать DISPLAY — в headless достаточно `ldd` без missing и `--help`/exit без ImportError, либо запуск под `xvfb-run` если доступен). Зафиксировать в комментариях/docs список проверенных Depends для Ubuntu 22.04 или Debian 12.
- **Файлы/модули**: `build/debian/control.in` (или генератор), при необходимости `build/debian/smoke_check.sh` / функция в `build_deb.py`
- **Критерии готовности**: Depends согласованы с `ldd` onedir; smoke-скрипт/команда описана и проходит на build-хосте с DISPLAY или xvfb; нет «missing .so» при старте на чистой VM того же поколения (если VM недоступна — минимум ldd + документированный список).
- **Зависимости**: после #3
- **Оценка**: S

### 5. Документация сборки `.deb`

- **ID**: 5
- **Стек**: backend
- **Описание**: Документ в `docs/line_emulator/` (в этом репозитории нет `ClientTypes` — канон docs уже `docs/line_emulator/`): предусловия (WSL2/Ubuntu/Debian, пакеты `python3-venv`, `binutils`, `dpkg-dev`, build-deps для `psycopg-c`/`libdmtx` при сборке venv), создание venv, `pip install -r requirements.txt`, команда сборки `.deb`, установка `dpkg -i`, удаление `apt remove`/`dpkg -r`, ограничение «только Linux», связь с Windows `build_project.py`. Обновить раздел «Сборка» в `docs/line_emulator/line_emulator.md` ссылкой на новый документ. Не описывать apt-repo/подпись/CI.
- **Файлы/модули**: `docs/line_emulator/debian_packaging.md` (новый), `docs/line_emulator/line_emulator.md`
- **Критерии готовности**: по документу разработчик на WSL/Debian без знания внутреннего кода может собрать и установить `.deb`; указана версия из `client_info.VERSION`.
- **Зависимости**: после #3 (можно параллелить с #4 после #3, если control стабилен; предпочтительно после #4, чтобы Depends в docs были финальными)
- **Оценка**: S

### 6. CHANGES.LOG и инкремент VERSION

- **ID**: 6
- **Стек**: backend
- **Описание**: Запись в начало `CHANGES.LOG` о возможности сборки `.deb`; увеличить последний разряд `client_info.VERSION` (префикс `b` сохранить, если билд ещё бета). `DB_VERSION` не трогать / не вводить. Не коммитить без запроса пользователя.
- **Файлы/модули**: `CHANGES.LOG`, `client_info.py`
- **Критерии готовности**: VERSION увеличен; запись в CHANGES.LOG сверху; смысл совпадает с поставленной возможностью deb-сборки.
- **Зависимости**: после #2, #3, #5 (логически после готовности фичи и docs)
- **Оценка**: XS

## Чеклист выполнения

- [x] 1. Кроссплатформенный PyInstaller spec для Linux (без поломки Windows)
- [x] 2. Точка входа сборки Linux onedir (расширение build_project или отдельный скрипт)
- [x] 3. Staging `.deb`: control, desktop, иконка, dpkg-deb
- [x] 4. Runtime-зависимости и smoke-проверка запуска
- [x] 5. Документация сборки `.deb`
- [x] 6. CHANGES.LOG и инкремент VERSION

## Волны выполнения

- **Волна 1:** #1 — spec (база для всего)
- **Волна 2:** #2 — Linux onedir entrypoint (после #1)
- **Волна 3:** #3 — deb staging / dpkg-deb (после #2)
- **Волна 4:** #4 и при готовности control — подготовка #5; фактически #4 → #5 → #6 последовательно
- **Волна 5:** #5 — docs (после #4)
- **Волна 6:** #6 — CHANGES + VERSION (после #5)

Параллелизм ограничен: все подзадачи трогают смежную цепочку сборки; параллелить почти нечего без конфликта файлов. #4 и черновик docs теоретически пересекаются по `control.in` — держать строго последовательно.

## Процесс выполнения

**Обязательно:** каждая подзадача проходит цикл по полю **Стек**:

- `backend` → `developer → code-review → tech-writer`
- `frontend` → `frontend-developer → frontend-code-review → frontend-tech-writer`
- `mixed` → разбей на отдельные подзадачи со своим стеком, если возможно

**Параллельно:** подзадачи **без общих файлов** и **без зависимостей** друг от друга — в одной **волне**. Здесь волны в основном последовательные.

Оркестратор (основная сессия) **не пишет код сам** — skill `/execute-plan` или `/execute-development-cycle`.

```text
/execute-plan .plans/backlog/2026-09-29-debian-deb-packaging.md
```

При **Build** в Plan mode агент следует тем же правилам (см. `.cursor/rules/plan-execution-orchestration.mdc`).

## Риски и открытые вопросы

- **glibc build-хоста:** `.deb`, собранный на Ubuntu 24.04, может не запуститься на Debian 12 — документировать «собирать на целевом поколении».
- **`pylibdmtx` / libdmtx:** на Linux нужна системная `libdmtx` при сборке и, возможно, в Depends, если не в bundle.
- **`psycopg-c`:** для сборки venv на Linux могут понадобиться `libpq-dev`, компилятор; runtime — `libpq5` или bundled.
- **`pywin32-ctypes` / `pefile` в requirements.txt:** на Linux pip может ругаться или ставить no-op; не чистить список в рамках этой задачи без необходимости — при блокере сборки Linux вынести в optional/platform notes в docs, не ломая Windows.
- **Headless smoke:** без DISPLAY GUI не стартует — использовать `xvfb-run` или ограничить smoke проверкой `ldd` + существования ELF.
- **Имя пакета vs имя бинаря:** пакет `dmclineemulator`, бинарь/каталог `dmcLineEmulator` — сохранить узнаваемость Windows-артефакта внутри `/opt`.

Открытых вопросов, блокирующих старт, нет — формат и среда сборки зафиксированы выше.

## Следующий шаг

Запустить `developer` для **подзадачи #1**: кроссплатформенный / Linux PyInstaller spec без регрессии Windows-сборки.

## Журнал изменений плана

| Дата | Изменение |
|------|-----------|
| 2026-09-29 | Создан план: PyInstaller onedir + .deb, сборка только на Linux/WSL |
