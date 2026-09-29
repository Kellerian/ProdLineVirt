# Сборка и установка `.deb` (dmcLineEmulator)

Пошаговая инструкция для разработчика: собрать установочный пакет **dmclineemulator** на **Linux** (native Debian 12 / Ubuntu 22.04+) или с **Windows** через **default WSL2** и установить его через `dpkg`, не читая исходники приложения.

Версия приложения и пакета берётся из `client_info.VERSION` (актуально: `1.0.0.1.b0007`).

## Ограничения

| Среда | Что можно |
|-------|-----------|
| **Linux** (native) | `venv` → PyInstaller onedir → smoke `ldd` → `dpkg-deb` → `.deb` в `build/deb/` **и** копия в `build/install/dmcLineEmulator/` |
| **Windows** + **default WSL** | `.\venv\Scripts\python.exe build_project.py --deb` (или `build_deb.py`) оркестрирует тот же Linux-путь внутри default-дистрибутива (`wsl` / `wsl.exe` **без** `-d`); итоговый `.deb` на Windows — в `build/install/dmcLineEmulator/` |
| **Windows**, флаг `--linux` | Отказ: stderr + exit `1` до freeze (freeze-only **не** идёт через WSL) |
| **Windows**, без флагов | Обычная сборка exe/onedir: `.\venv\Scripts\python.exe build_project.py` |

PyInstaller **не** кросс-компилирует Windows → Linux ELF. Честный `.deb` получается только на Linux (native или внутри WSL). Скрипт **не** вызывает `sudo apt` / `apt-get install` — пакеты предусловий ставятся вручную в целевом дистрибутиве (в т.ч. в default WSL).

**Default WSL:** используется только дистрибутив по умолчанию. Не указывайте `-d`, не ориентируйтесь на `docker-desktop`. Проверка: `wsl -l -v` — нужный Linux-дистр должен быть `Default`.

**glibc:** бинарь привязан к поколению хоста сборки. Собирайте на целевом дистрибутиве (Debian 12 / Ubuntu 22.04+). Пакет с Ubuntu 24.04 может не запуститься на Debian 12.

Apt-репозиторий, GPG-подпись и CI в этом документе не описаны.

Связь с Windows: краткий контракт freeze и ссылка сюда — в [line_emulator.md](line_emulator.md) (раздел «Сборка onedir»).

## Версия пакета

| Источник | Пример |
|----------|--------|
| `client_info.VERSION` | `1.0.0.1.b0007` |
| Поле `Version` в `.deb` | `1.0.0.1~b0007-1` |

Формула (`normalize_debian_version` в `build_deb.py`): числовой префикс, затем канал `a` / `b` / `r` через `~` (pre-release для dpkg), ревизия пакета `-1`.

Имя файла артефакта:

```text
dmclineemulator_1.0.0.1~b0007-1_amd64.deb
```

(подставьте актуальную Debian-версию из `VERSION`).

| Хост сборки | Где лежит файл |
|-------------|----------------|
| Native Linux | `build/deb/…` (основной путь после `dpkg-deb`) **и** копия `build/install/dmcLineEmulator/…` (`copy_deb_to_install_dir`) |
| Windows → WSL | на Windows-хосте: `build/install/dmcLineEmulator/…` (после копирования из temp WSL); каталог `build/deb/` на Windows **не обязателен** |

## Предусловия (хост)

Нужны: **WSL2 с Ubuntu 22.04+** или **Debian 12** (amd64), доступ в интернет для `apt` / `pip` / Git (зависимость `pylibdmtx` ставится с GitHub).

Для сборки с Windows через WSL дополнительно:

- `wsl` / `wsl.exe` на `PATH`;
- в **default** distro доступны `python3` и `dpkg-deb` (скрипт проверяет `command -v`; при отсутствии — exit `1` со ссылкой на этот документ);
- apt-пакеты из раздела ниже установлены **вручную внутри WSL** (скрипт их не ставит).

### Пакеты для venv и сборки `.deb`

```bash
sudo apt-get update
sudo apt-get install -y \
  python3 python3-venv python3-dev \
  build-essential binutils dpkg-dev \
  git \
  libpq-dev \
  libdmtx-dev \
  libc-bin
```

| Пакет / группа | Зачем |
|----------------|--------|
| `python3-venv`, `python3-dev` | виртуальное окружение и сборка расширений |
| `build-essential` | компилятор для `psycopg-c` и нативных wheel |
| `binutils` | утилиты линковки (часто нужны PyInstaller) |
| `dpkg-dev` | `dpkg-deb` |
| `git` | установка `pylibdmtx` из Git-URL в `requirements.txt` |
| `libpq-dev` | сборка `psycopg-c` |
| `libdmtx-dev` | заголовки/библиотека для `pylibdmtx` при сборке venv и (по возможности) попадание libdmtx в onedir |
| `libc-bin` | `ldd` для smoke-проверки после freeze |

Опционально для краткого старта ELF в smoke (после `ldd`): `xvfb` (`xvfb-run`) или рабочий `DISPLAY`.

Runtime-зависимости GUI (xcb, GL, fontconfig и т.д.) подтянет `dpkg` из поля `Depends` пакета при установке; на машине **сборки** они часто уже есть в desktop-образе. Если smoke/`ldd` сообщит `not found` — установите недостающий пакет и повторите сборку.

## Подготовка репозитория и venv

### Native Linux

Из корня клона репозитория:

```bash
cd /path/to/ProdLineVirt

python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Дальше все команды сборки — только через `venv/bin/python` (или при активированном venv).

### Windows → default WSL

На Windows достаточно проектного venv для запуска оркестратора (`build_project.py` / `build_deb.py`). Скрипт **не** использует Windows `venv/` для freeze Linux: внутри WSL создаётся отдельный temp-каталог на Linux FS (`mktemp -d`, обычно под `/tmp`), туда копируются исходники, затем в temp — свой `python3 -m venv` и `pip install -r requirements.txt`.

Исключения при sync (`WSL_SYNC_EXCLUDES` в `build_deb.py`): `venv`, `build/install`, `build/tmp`, `__pycache__`, `.git`, `.idea`, `*.pyc`. Windows `venv/` и `build/install/` не затираются Linux-freeze. Временный каталог WSL удаляется в `finally` и при успехе, и при ошибке.

### Риск: Windows-only пакеты в `requirements.txt`

В `requirements.txt` есть `pefile` и `pywin32-ctypes` (нужны Windows / PyInstaller на Windows). На Linux `pip install -r requirements.txt` обычно проходит, но возможны предупреждения или сбои установки. **Не меняйте** `requirements.txt` ради Linux без отдельной задачи: при блокере зафиксируйте ошибку pip и обходите точечно (платформенные маркеры — вне объёма этой инструкции).

## Сборка `.deb`

### Native Linux

Одна команда (всегда заново freeze onedir → smoke `ldd` → `dpkg-deb` → копия в install):

```bash
venv/bin/python build_project.py --deb
```

Эквивалент:

```bash
venv/bin/python build_deb.py
```

Что происходит:

1. Генерация UI (`pyside6-uic`) и PyInstaller по `build/spec/main.spec` → `build/install/dmcLineEmulator/`.
2. Smoke: `ldd` по ELF `build/install/dmcLineEmulator/dmcLineEmulator`. Любая строка `=> not found` — **сборка падает**, `.deb` не создаётся.
3. Staging и `dpkg-deb --build --root-owner-group` → `build/deb/…`.
4. `copy_deb_to_install_dir`: тот же файл копируется в `build/install/dmcLineEmulator/`.

Артефакты:

```text
build/deb/dmclineemulator_<debian_ver>_amd64.deb
build/install/dmcLineEmulator/dmclineemulator_<debian_ver>_amd64.deb
```

Пример при `VERSION = 1.0.0.1.b0007`:

```text
build/deb/dmclineemulator_1.0.0.1~b0007-1_amd64.deb
build/install/dmcLineEmulator/dmclineemulator_1.0.0.1~b0007-1_amd64.deb
```

Только freeze без пакета (отладка onedir; **только Linux**):

```bash
venv/bin/python build_project.py --linux
```

### Windows (оркестрация через default WSL)

Из корня репозитория на Windows (интерпретатор из проектного `venv`):

```powershell
.\venv\Scripts\python.exe build_project.py --deb
```

Эквивалент:

```powershell
.\venv\Scripts\python.exe build_deb.py
```

Поведение (`build_deb.build_deb_via_wsl`):

1. Найти `wsl` / `wsl.exe` на `PATH`; вызов **без** `-d` (`wsl -- …`).
2. Preflight: в default distro есть `python3` и `dpkg-deb`.
3. `mktemp -d` на Linux FS → sync исходников через `tar` с исключениями выше.
4. В temp: `python3 -m venv` → `pip install -r requirements.txt` → `venv/bin/python build_project.py --deb` (нативный Linux-путь: freeze → smoke → pack).
5. Найти `.deb` в temp (`…/build/deb/dmclineemulator_*_amd64.deb`) и скопировать на Windows в `build/install/dmcLineEmulator/`.
6. Удалить temp WSL (`cleanup_wsl_temp` в `finally`).

Итоговый файл на Windows-хосте:

```text
build/install/dmcLineEmulator/dmclineemulator_<debian_ver>_amd64.deb
```

(рядом с `dmcLineEmulator.exe`, если ранее собирали Windows-onedir). Локальный Windows-freeze при `--deb` **не** выполняется.

### Содержимое пакета

| Элемент | Значение |
|---------|----------|
| Имя пакета | `dmclineemulator` |
| Файлы приложения | `/opt/dmclineemulator/` (PyInstaller onedir) |
| Запуск | `/opt/dmclineemulator/dmcLineEmulator` |
| Меню | `/usr/share/applications/dmclineemulator.desktop` (`Exec=/opt/dmclineemulator/dmcLineEmulator`, `Icon=dmclineemulator`) |
| Иконка | `/usr/share/pixmaps/dmclineemulator.png` (из `media/logo.png`) |

Шаблоны: `build/debian/control.in`, `build/debian/dmclineemulator.desktop`.

### `Depends` и runtime (кратко)

Актуальный список — в `build/debian/control.in`. Важно:

- В `Depends` — **хостовые** shared libraries для Qt6 xcb GUI (glib, GL/EGL, fontconfig, dbus, X11/xcb/…), плюс `libdmtx*` (альтернативы имён) и `libpq5`.
- Пакетов **`libQt6*` в Depends нет** — Qt6 обычно уже внутри onedir.
- `Recommends: fonts-dejavu-core`.
- Serial (pyserial): нужен доступ к `/dev/tty*`, отдельного apt-Depends нет (часто группа `dialout`).
- Фактический `ldd` на Windows-хосте разработки **не прогонялся**; список Depends — известный набор для Debian 12 / Ubuntu 22.04+, не dump с конкретной Windows-машины.

## Установка

На Linux-машине (подставьте имя файла из `build/deb/` или из `build/install/dmcLineEmulator/`):

```bash
sudo dpkg -i build/deb/dmclineemulator_1.0.0.1~b0007-1_amd64.deb
```

Если dpkg пожалуется на незакрытые зависимости:

```bash
sudo apt-get install -f
```

Запуск из меню (пункт **dmcLineEmulator**) или:

```bash
/opt/dmclineemulator/dmcLineEmulator
```

Для эмулятора сканера по COM: пользователь должен иметь доступ к нужному `/dev/tty*` (например `sudo usermod -aG dialout "$USER"`, затем перелогин).

## Удаление

```bash
sudo apt remove dmclineemulator
```

или:

```bash
sudo dpkg -r dmclineemulator
```

## Быстрая проверка артефакта (опционально)

```bash
dpkg-deb -I build/deb/dmclineemulator_*.deb
dpkg-deb -c build/deb/dmclineemulator_*.deb | head
```

После сборки с Windows путь к тому же файлу:

```powershell
Get-ChildItem build\install\dmcLineEmulator\*.deb
```

В control должны быть `Package: dmclineemulator`, `Version` с `~` и `-1`, `Architecture: amd64`. В списке файлов — пути под `./opt/dmclineemulator/` и `.desktop` / pixmap.

## Чеклист «с нуля»

### Native Linux / вручную внутри WSL

1. Установить пакеты из раздела «Предусловия» (вручную, не из скрипта сборки).
2. Клонировать репозиторий, создать `venv`, `pip install -r requirements.txt`.
3. `venv/bin/python build_project.py --deb`.
4. Убедиться, что `.deb` есть в `build/deb/` и копия в `build/install/dmcLineEmulator/`.
5. `sudo dpkg -i …` и запуск `/opt/dmclineemulator/dmcLineEmulator`.
6. При необходимости — `sudo apt remove dmclineemulator`.

### Windows → default WSL

1. Установить WSL2, назначить Linux default (не `docker-desktop`); вручную поставить apt-пакеты из «Предусловий» **внутри** default distro.
2. На Windows: проектный `venv`, из корня репозитория `.\venv\Scripts\python.exe build_project.py --deb`.
3. Убедиться, что на Windows появился `build/install/dmcLineEmulator/dmclineemulator_*_amd64.deb`.
4. Перенести `.deb` на целевой Debian/Ubuntu и установить через `dpkg` (см. выше).
