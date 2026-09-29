"""Build a Debian package from the Linux PyInstaller onedir.

On a non-Linux host the process prints an error and exits with status 1.
``dpkg-deb`` is invoked only on Linux when the command is on PATH.

Freeze policy (``--deb`` / this script): always re-run the same PyInstaller
onedir freeze as ``build_project.py --linux``, then stage the tree and call
``dpkg-deb --build``. ``--linux`` remains freeze-only.

After freeze on Linux (before ``dpkg-deb``), ``smoke_check_linux_onedir``
runs ``ldd`` on the frozen ELF and fails if any shared library is
``not found``. That step is a no-op on Windows (never reached: the
``--linux`` / ``--deb`` guards exit first; the function also returns
immediately if ``platform.system()`` is not Linux).

Use the project venv:

    python build_deb.py
    python build_project.py --deb
"""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from build_project import BUILD_DIR, INSTALL_DIR, ROOT_DIR, main

DEBIAN_TEMPLATES_DIR: Path = BUILD_DIR / "debian"
DEB_OUTPUT_DIR: Path = BUILD_DIR / "deb"
ONEDIR_DIR_NAME: str = "dmcLineEmulator"
ONEDIR_BINARY_NAME: str = "dmcLineEmulator"
PACKAGE_NAME: str = "dmclineemulator"
OPT_INSTALL_DIR: str = "opt/dmclineemulator"
PIXMAP_NAME: str = "dmclineemulator.png"
DESKTOP_NAME: str = "dmclineemulator.desktop"
CONTROL_TEMPLATE_NAME: str = "control.in"
VERSION_PLACEHOLDER: str = "@VERSION@"

_PROJECT_VERSION_RE = re.compile(
    r"^(?P<numeric>(?:\d+\.)*\d+)\.(?P<tag>[abr]\d+)$",
)
_LDD_NOT_FOUND_RE = re.compile(
    r"^\s+(?P<soname>\S+)\s+=>\s+not found\s*$",
    re.MULTILINE | re.IGNORECASE,
)
_ELF_START_TIMEOUT_SEC: float = 8.0
_LDD_TIMEOUT_SEC: float = 30.0


def normalize_debian_version(
    project_version: str,
    *,
    revision: str = "1",
) -> str:
    """Convert ``client_info.VERSION`` to a Debian version string.

    Project versions look like ``1.0.0.1.b0006``: a dotted numeric prefix,
    then a one-letter channel (``a`` / ``b`` / ``r``) and a zero-padded
    build number. Debian sorts ``~`` as a pre-release marker, so
    ``1.0.0.1~b0006`` is strictly less than ``1.0.0.1``. The Debian
    revision is appended after a hyphen.

    Args:
        project_version: Value of ``client_info.VERSION``.
        revision: Debian package revision (default ``1``).

    Returns:
        String such as ``1.0.0.1~b0006-1``.

    Raises:
        ValueError: If ``project_version`` does not match the expected shape
            or ``revision`` is empty.
    """
    if not revision:
        raise ValueError("Debian revision must be a non-empty string")
    match = _PROJECT_VERSION_RE.fullmatch(project_version.strip())
    if match is None:
        raise ValueError(
            "Unsupported project version for Debian packaging: "
            f"{project_version!r}. Expected e.g. '1.0.0.1.b0006'.",
        )
    numeric = match.group("numeric")
    tag = match.group("tag")
    return f"{numeric}~{tag}-{revision}"


def debian_staging_dir(debian_version: str) -> Path:
    """Return the staging root for one package version.

    Args:
        debian_version: Output of ``normalize_debian_version``.

    Returns:
        Path under ``build/deb/``.
    """
    return DEB_OUTPUT_DIR / f"{PACKAGE_NAME}_{debian_version}"


def debian_deb_path(debian_version: str) -> Path:
    """Return the ``.deb`` artifact path for one package version.

    Args:
        debian_version: Output of ``normalize_debian_version``.

    Returns:
        Path ``build/deb/dmclineemulator_<ver>_amd64.deb``.
    """
    return DEB_OUTPUT_DIR / f"{PACKAGE_NAME}_{debian_version}_amd64.deb"


def strip_control_comments(control_text: str) -> str:
    """Drop ``#`` comment lines from a Debian control template.

    Args:
        control_text: Raw ``control.in`` contents.

    Returns:
        Control file text without full-line comments, ready for ``dpkg-deb``.
    """
    lines: list[str] = []
    for raw_line in control_text.splitlines():
        stripped = raw_line.lstrip()
        if stripped.startswith("#"):
            continue
        lines.append(raw_line)
    return "\n".join(lines).rstrip() + "\n"


def render_control(template_text: str, debian_version: str) -> str:
    """Fill the control template and strip comments.

    Args:
        template_text: Contents of ``build/debian/control.in``.
        debian_version: Output of ``normalize_debian_version``.

    Returns:
        Binary-package ``DEBIAN/control`` text.

    Raises:
        ValueError: If the version placeholder is missing from the template.
    """
    if VERSION_PLACEHOLDER not in template_text:
        raise ValueError(
            f"control template must contain {VERSION_PLACEHOLDER}",
        )
    filled = template_text.replace(VERSION_PLACEHOLDER, debian_version)
    return strip_control_comments(filled)


def parse_ldd_missing_libraries(ldd_output: str) -> list[str]:
    """Extract sonames marked ``not found`` in ``ldd`` output.

    Pure text parsing so unit tests can run on Windows without an ELF
    binary and without the ``ldd`` tool.

    Args:
        ldd_output: Combined stdout (and optionally stderr) of ``ldd``.

    Returns:
        Unique library names in first-seen order.
    """
    missing: list[str] = []
    seen: set[str] = set()
    for match in _LDD_NOT_FOUND_RE.finditer(ldd_output):
        soname = match.group("soname")
        if soname not in seen:
            seen.add(soname)
            missing.append(soname)
    return missing


def linux_onedir_elf_path(onedir: Path) -> Path:
    """Return the frozen Linux ELF path inside an onedir.

    Args:
        onedir: ``build/install/dmcLineEmulator`` (or a test substitute).

    Returns:
        Path to ``dmcLineEmulator`` (no ``.exe`` suffix).

    Raises:
        FileNotFoundError: If the ELF file is missing.
    """
    elf_path = onedir / ONEDIR_BINARY_NAME
    if not elf_path.is_file():
        raise FileNotFoundError(
            f"Linux freeze ELF not found: {elf_path}",
        )
    return elf_path


def _try_brief_elf_start(elf_path: Path) -> None:
    """Optionally start the ELF under xvfb or DISPLAY to catch ImportError.

    A timeout is treated as success (GUI likely blocked on the event loop).
    Missing DISPLAY and missing ``xvfb-run`` skip this step after ``ldd``.

    Args:
        elf_path: Frozen ``dmcLineEmulator`` binary.

    Raises:
        SystemExit: If the process reports ``ImportError`` / ``ModuleNotFoundError``.
    """
    use_xvfb = shutil.which("xvfb-run") is not None
    display = os.environ.get("DISPLAY", "").strip()
    if use_xvfb:
        argv: list[str] = ["xvfb-run", "-a", str(elf_path), "--help"]
    elif display:
        argv = [str(elf_path), "--help"]
    else:
        print(
            "ldd smoke passed; skipping ELF start "
            "(no DISPLAY and no xvfb-run).",
        )
        return
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=_ELF_START_TIMEOUT_SEC,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(
            "ELF start timed out (GUI likely running); smoke treats this "
            "as a pass.",
        )
        return
    combined = f"{completed.stdout or ''}{completed.stderr or ''}"
    if "ImportError" in combined or "ModuleNotFoundError" in combined:
        print(
            "Frozen ELF reported an import error during smoke start:\n"
            f"{combined}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(
        f"ELF start exited {completed.returncode} without ImportError "
        f"(command: {argv[0]}).",
    )


def smoke_check_linux_onedir(install_dir: Path | None = None) -> None:
    """Fail the Linux freeze if ``ldd`` reports missing shared libraries.

    Call site: ``build_project.main`` after PyInstaller (``build_modules``)
    and ``cleanup_build_dir``, **before** ``package_frozen_onedir`` /
    ``dpkg-deb``. That way a broken onedir is not packed.

    On a non-Linux host this function returns immediately (no ``ldd``,
    no ELF). Windows ``--deb`` never reaches it because ``require_linux``
    exits first.

    Args:
        install_dir: PyInstaller dist parent (default ``build/install``).

    Raises:
        SystemExit: If ``ldd`` is missing, the ELF is missing, ``ldd``
            fails, the file is not a dynamic executable, or any line
            is ``=> not found``.
    """
    if platform.system() != "Linux":
        return
    resolved_install = INSTALL_DIR if install_dir is None else install_dir
    try:
        onedir = resolve_onedir(resolved_install)
        elf_path = linux_onedir_elf_path(onedir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    ldd_bin = shutil.which("ldd")
    if ldd_bin is None:
        print(
            "ldd is required on Linux for the freeze smoke check "
            "(package libc-bin).",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        completed = subprocess.run(
            [ldd_bin, str(elf_path)],
            capture_output=True,
            text=True,
            timeout=_LDD_TIMEOUT_SEC,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(
            f"ldd timed out after {_LDD_TIMEOUT_SEC}s on {elf_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    ldd_text = f"{completed.stdout or ''}{completed.stderr or ''}"
    if completed.returncode != 0:
        print(
            f"ldd failed with exit {completed.returncode}:\n{ldd_text}",
            file=sys.stderr,
        )
        sys.exit(1)
    if "not a dynamic executable" in ldd_text.lower():
        print(
            f"ldd: {elf_path} is not a dynamic executable (expected ELF).",
            file=sys.stderr,
        )
        sys.exit(1)
    missing = parse_ldd_missing_libraries(ldd_text)
    if missing:
        names = ", ".join(missing)
        print(
            "ldd reported missing shared libraries (install matching "
            f"Debian Depends or rebuild the onedir): {names}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"ldd smoke OK for {elf_path} (no 'not found' libraries).")
    _try_brief_elf_start(elf_path)


def resolve_onedir(install_dir: Path) -> Path:
    """Return the PyInstaller onedir that will be packed.

    Args:
        install_dir: ``build/install`` (or a test substitute).

    Returns:
        Directory ``…/dmcLineEmulator`` containing the frozen payload.

    Raises:
        FileNotFoundError: If the onedir or its main binary is missing.
    """
    onedir = install_dir / ONEDIR_DIR_NAME
    linux_binary = onedir / ONEDIR_BINARY_NAME
    windows_binary = onedir / f"{ONEDIR_BINARY_NAME}.exe"
    if not onedir.is_dir():
        raise FileNotFoundError(
            f"PyInstaller onedir not found: {onedir}",
        )
    if not linux_binary.is_file() and not windows_binary.is_file():
        raise FileNotFoundError(
            f"Frozen binary not found in {onedir} "
            f"(expected {ONEDIR_BINARY_NAME} or {ONEDIR_BINARY_NAME}.exe)",
        )
    return onedir


def stage_debian_tree(
    *,
    onedir_src: Path,
    staging_root: Path,
    debian_version: str,
    icon_src: Path,
    control_template: Path,
    desktop_src: Path,
) -> Path:
    """Lay out a dpkg staging tree (no ``dpkg-deb``).

    Creates ``DEBIAN/control``, copies the onedir to
    ``opt/dmclineemulator/``, installs the ``.desktop`` file and pixmap.

    Args:
        onedir_src: Frozen ``dmcLineEmulator`` directory.
        staging_root: Destination staging directory (replaced if present).
        debian_version: Output of ``normalize_debian_version``.
        icon_src: Source image (typically ``media/logo.png``).
        control_template: Path to ``control.in``.
        desktop_src: Path to ``dmclineemulator.desktop``.

    Returns:
        ``staging_root`` after the tree is written.

    Raises:
        FileNotFoundError: If a required source file or directory is missing.
    """
    if not onedir_src.is_dir():
        raise FileNotFoundError(f"onedir source not found: {onedir_src}")
    if not icon_src.is_file():
        raise FileNotFoundError(f"icon not found: {icon_src}")
    if not control_template.is_file():
        raise FileNotFoundError(f"control template not found: {control_template}")
    if not desktop_src.is_file():
        raise FileNotFoundError(f"desktop file not found: {desktop_src}")

    if staging_root.exists():
        shutil.rmtree(staging_root)

    debian_dir = staging_root / "DEBIAN"
    opt_dir = staging_root / OPT_INSTALL_DIR
    apps_dir = staging_root / "usr" / "share" / "applications"
    pixmaps_dir = staging_root / "usr" / "share" / "pixmaps"
    debian_dir.mkdir(parents=True)
    apps_dir.mkdir(parents=True)
    pixmaps_dir.mkdir(parents=True)

    control_text = render_control(
        control_template.read_text(encoding="utf-8"),
        debian_version,
    )
    control_path = debian_dir / "control"
    control_path.write_text(control_text, encoding="utf-8")

    shutil.copytree(onedir_src, opt_dir, dirs_exist_ok=True)
    shutil.copy2(desktop_src, apps_dir / DESKTOP_NAME)
    shutil.copy2(icon_src, pixmaps_dir / PIXMAP_NAME)
    return staging_root


def dpkg_deb_is_available() -> bool:
    """Return whether ``dpkg-deb`` can be invoked on this host.

    Returns:
        True only when the OS is Linux and ``dpkg-deb`` is on PATH.
    """
    return platform.system() == "Linux" and shutil.which("dpkg-deb") is not None


def run_dpkg_deb(staging_root: Path, output_deb: Path) -> None:
    """Build a ``.deb`` with ``dpkg-deb --build``.

    Args:
        staging_root: Directory produced by ``stage_debian_tree``.
        output_deb: Destination ``.deb`` path.

    Raises:
        SystemExit: If the host is not Linux or ``dpkg-deb`` is missing.
        subprocess.CalledProcessError: If ``dpkg-deb`` returns non-zero.
    """
    current = platform.system()
    if current != "Linux" or shutil.which("dpkg-deb") is None:
        print(
            "dpkg-deb is only invoked on Linux when the command is on PATH. "
            f"Current OS: {current}.",
            file=sys.stderr,
        )
        sys.exit(1)
    output_deb.parent.mkdir(parents=True, exist_ok=True)
    if output_deb.exists():
        output_deb.unlink()
    subprocess.run(
        [
            "dpkg-deb",
            "--root-owner-group",
            "--build",
            str(staging_root),
            str(output_deb),
        ],
        check=True,
    )


def package_frozen_onedir(
    *,
    install_dir: Path | None = None,
    templates_dir: Path | None = None,
    icon_src: Path | None = None,
    project_version: str | None = None,
    output_dir: Path | None = None,
    run_dpkg: bool = True,
) -> Path:
    """Stage the onedir and optionally run ``dpkg-deb``.

    Args:
        install_dir: PyInstaller ``--distpath`` parent (default
            ``build/install``).
        templates_dir: Directory with ``control.in`` and the desktop file
            (default ``build/debian``).
        icon_src: PNG icon (default ``media/logo.png``).
        project_version: Override for tests; default is
            ``client_info.VERSION``.
        output_dir: Parent of the staging tree and ``.deb`` (default
            ``build/deb``).
        run_dpkg: When True, call ``dpkg-deb`` (Linux + tool present).
            Unit tests on Windows pass False.

    Returns:
        Staging root if ``run_dpkg`` is False, otherwise the ``.deb`` path.

    Raises:
        FileNotFoundError: If freeze output or templates are missing.
        ValueError: If ``project_version`` cannot be normalized.
        SystemExit: If ``run_dpkg`` is True but ``dpkg-deb`` cannot run.
    """
    from client_info import VERSION

    resolved_install = INSTALL_DIR if install_dir is None else install_dir
    resolved_templates = (
        DEBIAN_TEMPLATES_DIR if templates_dir is None else templates_dir
    )
    resolved_icon = (
        ROOT_DIR / "media" / "logo.png" if icon_src is None else icon_src
    )
    resolved_output = DEB_OUTPUT_DIR if output_dir is None else output_dir
    version = VERSION if project_version is None else project_version
    debian_version = normalize_debian_version(version)
    onedir = resolve_onedir(resolved_install)
    staging_root = resolved_output / f"{PACKAGE_NAME}_{debian_version}"
    resolved_output.mkdir(parents=True, exist_ok=True)
    stage_debian_tree(
        onedir_src=onedir,
        staging_root=staging_root,
        debian_version=debian_version,
        icon_src=resolved_icon,
        control_template=resolved_templates / CONTROL_TEMPLATE_NAME,
        desktop_src=resolved_templates / DESKTOP_NAME,
    )
    print(f"Staged Debian tree at {staging_root}")
    if not run_dpkg:
        return staging_root
    deb_path = resolved_output / f"{PACKAGE_NAME}_{debian_version}_amd64.deb"
    run_dpkg_deb(staging_root, deb_path)
    print(f"Built Debian package {deb_path}")
    return deb_path


def run(argv: list[str] | None = None) -> None:
    """Freeze Linux onedir, then stage and pack a ``.deb``.

    Always re-runs PyInstaller (same path as ``build_project.py --linux``)
    before packaging so the embedded ``client_info.VERSION`` matches the
    Debian ``Version`` field.

    Args:
        argv: Extra arguments after the implicit ``--deb`` flag.
            ``None`` uses ``sys.argv[1:]``.
    """
    extra = sys.argv[1:] if argv is None else argv
    main(["--deb", *extra])


if __name__ == "__main__":
    run()
