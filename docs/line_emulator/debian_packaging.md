# Сборка и установка `.deb` (dmcLineEmulator)

Пошаговая инструкция для разработчика: собрать установочный пакет **dmclineemulator** на **WSL2 Ubuntu 22.04+** или **Debian 12** (amd64) и установить его через `dpkg`, не читая исходники приложения.

Версия приложения и пакета берётся из `client_info.VERSION` (актуально: `1.0.0.1.b0007`).

## Ограничения

| Среда | Что можно |
|-------|-----------|
| **Linux / WSL2** (целевая) | venv → PyInstaller onedir → `dpkg-deb` → `.deb` |
| **Windows** | Только обычная сборка: `.\venv\Scripts\python.exe build_project.py` (exe/onedir). Флаги `--linux`, `--deb` и скрипт `build_deb.py` печатают ошибку и завершаются с кодом `1` |

PyInstaller **не** кросс-компилирует Windows → Linux ELF. Честный `.deb` получается только на Linux.

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
build/deb/dmclineemulator_1.0.0.1~b0007-1_amd64.deb
```

(подставьте актуальную Debian-версию из `VERSION`).

## Предусловия (хост)

Нужны: **WSL2 с Ubuntu 22.04+** или **Debian 12**, архитектура **amd64**, доступ в интернет для `apt` / `pip` / Git (зависимость `pylibdmtx` ставится с GitHub).

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

Из корня клона репозитория:

```bash
cd /path/to/ProdLineVirt

python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Дальше все команды сборки — только через `venv/bin/python` (или при активированном venv).

### Риск: Windows-only пакеты в `requirements.txt`

В `requirements.txt` есть `pefile` и `pywin32-ctypes` (нужны Windows / PyInstaller на Windows). На Linux `pip install -r requirements.txt` обычно проходит, но возможны предупреждения или сбои установки. **Не меняйте** `requirements.txt` ради Linux без отдельной задачи: при блокере зафиксируйте ошибку pip и обходите точечно (платформенные маркеры — вне объёма этой инструкции).

## Сборка `.deb`

Одна команда (всегда заново freeze onedir → smoke `ldd` → `dpkg-deb`):

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
3. Staging и `dpkg-deb --build --root-owner-group`.

Артефакт:

```text
build/deb/dmclineemulator_<debian_ver>_amd64.deb
```

Пример при `VERSION = 1.0.0.1.b0007`:

```text
build/deb/dmclineemulator_1.0.0.1~b0007-1_amd64.deb
```

Только freeze без пакета (отладка onedir):

```bash
venv/bin/python build_project.py --linux
```

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

```bash
sudo dpkg -i build/deb/dmclineemulator_1.0.0.1~b0007-1_amd64.deb
```

Подставьте имя файла из `build/deb/`. Если dpkg пожалуется на незакрытые зависимости:

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

В control должны быть `Package: dmclineemulator`, `Version` с `~` и `-1`, `Architecture: amd64`. В списке файлов — пути под `./opt/dmclineemulator/` и `.desktop` / pixmap.

## Чеклист «с нуля на WSL/Debian»

1. Установить пакеты из раздела «Предусловия».
2. Клонировать репозиторий, создать `venv`, `pip install -r requirements.txt`.
3. `venv/bin/python build_project.py --deb`.
4. Убедиться, что в `build/deb/` появился `.deb` с версией из `client_info.VERSION`.
5. `sudo dpkg -i …` и запуск `/opt/dmclineemulator/dmcLineEmulator`.
6. При необходимости — `sudo apt remove dmclineemulator`.
