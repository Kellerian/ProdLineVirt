# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for dmcLineEmulator onedir (Windows and Linux).

Paths are resolved from this file's directory (``SPECPATH`` / ``__file__``)
so the same spec works with ``build_project.py`` on Windows and with
PyInstaller on Linux. Do not use backslash-only relative strings.

pylibdmtx native library:
    Windows — ``EXTERNAL_DEPENDENCIES`` is ``libdmtx-*.dll`` from the wheel;
    it is collected into the onedir.
    Linux — ctypes loads system ``libdmtx`` via ``find_library('dmtx')``.
    If that file exists when the spec is evaluated, it is collected as BINARY.
    If libdmtx is not installed at freeze time, nothing is bundled; the
    Debian package must then Depends on ``libdmtx0`` or ``libdmtx0a``
    (exact name per distro).
"""
from pathlib import Path
import sys

import qtawesome


block_cipher = None

try:
    _SPEC_DIR = Path(SPECPATH).resolve()
except NameError:
    _SPEC_DIR = Path(__file__).resolve().parent

_REPO_ROOT = _SPEC_DIR.parent.parent
_MAIN_PY = str(_REPO_ROOT / 'main.py')
_LOGO_ICO = str(_REPO_ROOT / 'media' / 'logo.ico')

_qtawesome_fonts = (
    str(Path(qtawesome.__file__).parent / 'fonts'),
    'qtawesome/fonts',
)


def _resolve_linux_shared_lib(soname: str) -> Path | None:
    """Resolve a Linux soname (or ``find_library`` result) to an existing file.

    Args:
        soname: Library name from ``CDLL._name`` or ``find_library``.

    Returns:
        Absolute path if the file exists, otherwise ``None``.
    """
    from ctypes.util import find_library
    import subprocess

    candidate = Path(soname)
    if candidate.is_file():
        return candidate
    needles = {Path(soname).name}
    found = find_library('dmtx')
    if found:
        found_path = Path(found)
        if found_path.is_file():
            return found_path
        needles.add(Path(found).name)
    try:
        proc = subprocess.run(
            ['ldconfig', '-p'],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        if '=>' not in line:
            continue
        name_part, abs_part = line.split('=>', 1)
        tokens = name_part.split()
        if not needles.intersection(tokens):
            continue
        abs_path = Path(abs_part.strip())
        if abs_path.is_file():
            return abs_path
    return None


def _pylibdmtx_binary_toc():
    """Collect libdmtx shared libraries from pylibdmtx for the frozen bundle.

    On Windows every ``EXTERNAL_DEPENDENCIES`` entry is added as BINARY
    using ``CDLL._name`` as-is (PyInstaller fails if the file is missing).
    On Linux a BINARY is added only when the shared object exists on disk
    (``_name`` as a path, or soname resolved via ``find_library`` / ``ldconfig``).

    Returns:
        TOC: BINARY entries, or empty if the native library is unavailable
        (typical on Linux without ``libdmtx-dev`` / ``libdmtx0`` at freeze).
    """
    try:
        from pylibdmtx import pylibdmtx
    except (ImportError, OSError) as exc:
        if sys.platform.startswith('win'):
            raise
        print(
            'WARNING: pylibdmtx import failed '
            f'({exc!r}); native libdmtx not bundled'
        )
        return TOC([])
    items = []
    is_win = sys.platform.startswith('win')
    for dep in pylibdmtx.EXTERNAL_DEPENDENCIES:
        src = getattr(dep, '_name', None) or ''
        if not src:
            continue
        path = Path(src)
        if is_win:
            items.append((path.name, src, 'BINARY'))
            continue
        resolved = path if path.is_file() else _resolve_linux_shared_lib(src)
        if resolved is not None and resolved.is_file():
            items.append((resolved.name, str(resolved), 'BINARY'))
    if not items:
        print(
            'WARNING: pylibdmtx native library was not collected into the bundle'
        )
    return TOC(items)


a = Analysis(
    [_MAIN_PY],
    pathex=[],
    binaries=[],
    datas=[
        (_LOGO_ICO, 'media'),
        _qtawesome_fonts,
    ],
    hiddenimports=[
        'pylibdmtx',
        'psycopg',
        'psycopg_c',
        'shortuuid',
        'serial',
        'serial.tools.list_ports',
        'qtawesome',
        'qtawesome.iconic_font',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)


a.binaries += _pylibdmtx_binary_toc()


pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='dmcLineEmulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_LOGO_ICO,
)


coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='dmcLineEmulator',
)
