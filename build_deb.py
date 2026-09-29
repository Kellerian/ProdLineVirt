"""Build a Debian package from the Linux PyInstaller onedir.

On Linux, ``--deb`` / this script always re-run the same PyInstaller onedir
freeze as ``build_project.py --linux``, then stage the tree and call
``dpkg-deb --build``. The resulting ``.deb`` is also copied next to the
onedir under ``build/install/dmcLineEmulator/``.

On Windows, ``--deb`` / this script orchestrate the same native Linux path
inside the **default** WSL distro (``wsl.exe`` without ``-d``): sync sources
to a Linux ``/tmp`` workdir, create a venv, run ``build_project.py --deb``,
copy the ``.deb`` to ``build/install/dmcLineEmulator/``, then remove the
temp tree. ``--linux`` (freeze-only) on Windows still exits with an error.

After freeze on Linux (before ``dpkg-deb``), ``smoke_check_linux_onedir``
runs ``ldd`` on the frozen ELF and fails if any shared library is
``not found``. That step is a no-op on non-Linux hosts.

Use the project venv:

    python build_deb.py
    python build_project.py --deb
"""
from __future__ import annotations

import os
import platform
import re
import shlex
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
DEBIAN_PACKAGING_DOCS: str = "docs/line_emulator/debian_packaging.md"
WSL_SYNC_EXCLUDES: tuple[str, ...] = (
    "venv",
    "build/install",
    "build/tmp",
    "__pycache__",
    ".git",
    ".idea",
    "*.pyc",
)

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
    no ELF). Windows ``--deb`` never reaches it: the host routes through
    ``build_deb_via_wsl`` instead of the local freeze path.

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


def copy_deb_to_install_dir(
    deb_path: Path,
    *,
    install_dir: Path | None = None,
) -> Path:
    """Copy a built ``.deb`` next to the PyInstaller onedir.

    Args:
        deb_path: Source ``.deb`` file (typically under ``build/deb/``).
        install_dir: Parent of ``dmcLineEmulator`` (default ``INSTALL_DIR``).

    Returns:
        Destination path ``…/dmcLineEmulator/<name>.deb``.

    Raises:
        FileNotFoundError: If ``deb_path`` is not a file.
    """
    if not deb_path.is_file():
        raise FileNotFoundError(f"Debian package not found: {deb_path}")
    parent = INSTALL_DIR if install_dir is None else install_dir
    dest_dir = parent / ONEDIR_DIR_NAME
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / deb_path.name
    shutil.copy2(deb_path, dest)
    print(f"Copied Debian package to {dest}")
    return dest


def find_wsl_executable() -> str | None:
    """Locate ``wsl`` / ``wsl.exe`` on PATH.

    Returns:
        Absolute or PATH-resolved executable name, or ``None`` if missing.
    """
    return shutil.which("wsl") or shutil.which("wsl.exe")


def wsl_argv(wsl: str, *remote_args: str) -> list[str]:
    """Build a ``wsl`` argv that never selects a distro via ``-d``.

    Args:
        wsl: Path or name of the WSL launcher.
        *remote_args: Arguments after ``--`` (for example ``bash``, ``-lc``,
            command).

    Returns:
        Full argv for ``subprocess`` (``[wsl, "--", …]``).
    """
    return [wsl, "--", *remote_args]


def run_wsl_captured(
    wsl: str,
    *remote_args: str,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a WSL command and capture combined text output.

    Args:
        wsl: Path or name of the WSL launcher.
        *remote_args: Arguments after ``--``.
        check: When True, raise ``CalledProcessError`` on non-zero exit.

    Returns:
        Completed process with ``text=True`` stdout/stderr streams.
    """
    return subprocess.run(
        wsl_argv(wsl, *remote_args),
        capture_output=True,
        text=True,
        check=check,
    )


def run_wsl_bash_streaming(wsl: str, bash_command: str) -> int:
    """Run ``bash -lc`` in default WSL and print stdout/stderr lines.

    Args:
        wsl: Path or name of the WSL launcher.
        bash_command: Shell script passed to ``bash -lc``.

    Returns:
        Process exit code (``0`` on success).
    """
    proc = subprocess.Popen(
        wsl_argv(wsl, "bash", "-lc", bash_command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="")
    return int(proc.wait())


def resolve_windows_path_in_wsl(wsl: str, windows_path: Path) -> str:
    """Convert a Windows path to a WSL path via ``wslpath -a``.

    Args:
        wsl: Path or name of the WSL launcher.
        windows_path: Absolute or relative Windows path.

    Returns:
        Absolute path as seen inside the default WSL distro.

    Raises:
        SystemExit: If ``wslpath`` fails.
    """
    absolute = windows_path.resolve()
    completed = run_wsl_captured(
        wsl,
        "wslpath",
        "-a",
        str(absolute),
    )
    path_text = (completed.stdout or "").strip()
    if completed.returncode != 0 or not path_text:
        detail = (completed.stderr or completed.stdout or "").strip()
        print(
            "Failed to convert Windows path to WSL via wslpath: "
            f"{absolute}. {detail}",
            file=sys.stderr,
        )
        sys.exit(1)
    return path_text


def preflight_wsl_tools(wsl: str) -> None:
    """Ensure default WSL has ``python3`` and ``dpkg-deb``.

    Args:
        wsl: Path or name of the WSL launcher.

    Raises:
        SystemExit: When either tool is missing (code ``1``).
    """
    completed = run_wsl_captured(
        wsl,
        "bash",
        "-lc",
        "command -v python3 && command -v dpkg-deb",
    )
    if completed.returncode != 0:
        print(
            "Default WSL is missing python3 and/or dpkg-deb. "
            "Install the documented prerequisites "
            f"({DEBIAN_PACKAGING_DOCS}) inside the default distro, "
            "then retry. Do not use docker-desktop; wsl is invoked "
            "without -d.",
            file=sys.stderr,
        )
        sys.exit(1)


def create_wsl_temp_dir(wsl: str) -> str:
    """Create a temporary directory on the Linux filesystem (``/tmp``).

    Args:
        wsl: Path or name of the WSL launcher.

    Returns:
        Absolute Linux path of the new empty directory.

    Raises:
        SystemExit: If ``mktemp`` fails.
    """
    completed = run_wsl_captured(wsl, "mktemp", "-d")
    remote = (completed.stdout or "").strip()
    if completed.returncode != 0 or not remote:
        detail = (completed.stderr or completed.stdout or "").strip()
        print(
            f"Failed to create a WSL temp directory under /tmp: {detail}",
            file=sys.stderr,
        )
        sys.exit(1)
    return remote


def sync_project_to_wsl(
    wsl: str,
    project_root: Path,
    remote_dir: str,
) -> None:
    """Copy project sources into a WSL temp dir, excluding heavy trees.

    Uses a single ``tar`` pipe inside WSL so Windows ``venv/`` and
    ``build/install/`` are never written into from Linux.

    Args:
        wsl: Path or name of the WSL launcher.
        project_root: Windows (or host) repository root.
        remote_dir: Destination directory on the Linux FS.

    Raises:
        SystemExit: If the sync command fails.
    """
    src_wsl = resolve_windows_path_in_wsl(wsl, project_root)
    exclude_args = " ".join(
        f"--exclude={shlex.quote(pattern)}" for pattern in WSL_SYNC_EXCLUDES
    )
    command = (
        f"tar -C {shlex.quote(src_wsl)} {exclude_args} -cf - . "
        f"| tar -C {shlex.quote(remote_dir)} -xf -"
    )
    completed = run_wsl_captured(wsl, "bash", "-lc", command)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        print(
            f"Failed to sync project sources into WSL temp: {detail}",
            file=sys.stderr,
        )
        sys.exit(1)


def run_remote_deb_build(wsl: str, remote_dir: str) -> None:
    """Create a Linux venv in ``remote_dir`` and run ``build_project.py --deb``.

    Args:
        wsl: Path or name of the WSL launcher.
        remote_dir: Synced project copy on the Linux FS.

    Raises:
        SystemExit: If venv/pip/freeze/pack returns non-zero.
    """
    command = (
        f"cd {shlex.quote(remote_dir)} && "
        "python3 -m venv venv && "
        "venv/bin/pip install -U pip && "
        "venv/bin/pip install -r requirements.txt && "
        "venv/bin/python build_project.py --deb"
    )
    exit_code = run_wsl_bash_streaming(wsl, command)
    if exit_code != 0:
        print(
            "WSL Debian build failed "
            f"(exit {exit_code}). See output above and "
            f"{DEBIAN_PACKAGING_DOCS}.",
            file=sys.stderr,
        )
        sys.exit(exit_code if exit_code else 1)


def find_remote_deb(wsl: str, remote_dir: str) -> str:
    """Locate the built ``.deb`` under ``remote_dir/build/deb/``.

    Args:
        wsl: Path or name of the WSL launcher.
        remote_dir: Synced project copy on the Linux FS.

    Returns:
        Absolute Linux path of the ``.deb`` file.

    Raises:
        SystemExit: If no matching artifact is found.
    """
    # Quote only the directory; leave the glob unquoted so bash expands `*`.
    deb_glob = (
        f"{shlex.quote(remote_dir)}/build/deb/"
        f"{PACKAGE_NAME}_*_amd64.deb"
    )
    completed = run_wsl_captured(
        wsl,
        "bash",
        "-lc",
        f"ls -1 {deb_glob} 2>/dev/null | head -n 1",
    )
    remote_deb = (completed.stdout or "").strip()
    if completed.returncode != 0 or not remote_deb:
        print(
            "WSL build finished but no .deb was found under "
            f"{remote_dir}/build/deb/ "
            f"(expected {PACKAGE_NAME}_*_amd64.deb).",
            file=sys.stderr,
        )
        sys.exit(1)
    return remote_deb


def copy_remote_deb_to_install(
    wsl: str,
    remote_deb: str,
    *,
    install_dir: Path | None = None,
) -> Path:
    """Copy a WSL-built ``.deb`` into ``build/install/dmcLineEmulator/``.

    Args:
        wsl: Path or name of the WSL launcher.
        remote_deb: Absolute Linux path of the ``.deb``.
        install_dir: Parent of ``dmcLineEmulator`` (default ``INSTALL_DIR``).

    Returns:
        Destination path on the Windows host.

    Raises:
        SystemExit: If the copy fails or the destination file is missing.
    """
    parent = INSTALL_DIR if install_dir is None else install_dir
    dest_dir = parent / ONEDIR_DIR_NAME
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_wsl = resolve_windows_path_in_wsl(wsl, dest_dir)
    deb_name = Path(remote_deb).name
    command = (
        f"mkdir -p {shlex.quote(dest_wsl)} && "
        f"cp {shlex.quote(remote_deb)} {shlex.quote(dest_wsl)}/"
    )
    completed = run_wsl_captured(wsl, "bash", "-lc", command)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        print(
            f"Failed to copy .deb from WSL to {dest_dir}: {detail}",
            file=sys.stderr,
        )
        sys.exit(1)
    dest = dest_dir / deb_name
    if not dest.is_file():
        print(
            f"Expected .deb at {dest} after WSL copy, but the file is missing.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Copied Debian package to {dest}")
    return dest


def cleanup_wsl_temp(wsl: str, remote_dir: str) -> None:
    """Remove a WSL temporary directory (best-effort).

    Args:
        wsl: Path or name of the WSL launcher.
        remote_dir: Absolute Linux path previously created under ``/tmp``.
    """
    if not remote_dir:
        return
    try:
        completed = run_wsl_captured(
            wsl,
            "bash",
            "-lc",
            f"rm -rf {shlex.quote(remote_dir)}",
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            print(
                f"Warning: failed to remove WSL temp {remote_dir}: {detail}",
                file=sys.stderr,
            )
    except OSError as exc:
        print(
            f"Warning: failed to remove WSL temp {remote_dir}: {exc}",
            file=sys.stderr,
        )


def build_deb_via_wsl(
    *,
    project_root: Path | None = None,
    install_dir: Path | None = None,
) -> Path:
    """Build a ``.deb`` on Windows through the default WSL distro.

    Discovers ``wsl`` without ``-d``, checks ``python3`` / ``dpkg-deb``,
    syncs sources to a Linux ``/tmp`` workdir (excluding ``venv/``,
    ``build/install/``, etc.), runs the native ``build_project.py --deb``
    path inside a fresh venv, copies the artifact to
    ``build/install/dmcLineEmulator/``, and always deletes the temp tree.

    Args:
        project_root: Repository root to sync (default ``ROOT_DIR``).
        install_dir: Windows install parent for the copied ``.deb``
            (default ``INSTALL_DIR``).

    Returns:
        Path of the ``.deb`` on the Windows host.

    Raises:
        SystemExit: On missing WSL/tools, sync/build/copy failure.
    """
    wsl = find_wsl_executable()
    if wsl is None:
        print(
            "wsl.exe not found on PATH. Install WSL2, set a Linux default "
            "distro (not docker-desktop), and meet the prerequisites in "
            f"{DEBIAN_PACKAGING_DOCS}.",
            file=sys.stderr,
        )
        sys.exit(1)
    preflight_wsl_tools(wsl)
    root = ROOT_DIR if project_root is None else project_root
    remote_tmp: str | None = None
    try:
        remote_tmp = create_wsl_temp_dir(wsl)
        print(f"WSL build workspace: {remote_tmp}")
        sync_project_to_wsl(wsl, root, remote_tmp)
        run_remote_deb_build(wsl, remote_tmp)
        remote_deb = find_remote_deb(wsl, remote_tmp)
        return copy_remote_deb_to_install(
            wsl,
            remote_deb,
            install_dir=install_dir,
        )
    finally:
        if remote_tmp is not None:
            cleanup_wsl_temp(wsl, remote_tmp)


def run(argv: list[str] | None = None) -> None:
    """Freeze Linux onedir, then stage and pack a ``.deb``.

    On Linux this always re-runs PyInstaller before packaging. On Windows
    it delegates to ``build_deb_via_wsl`` via ``build_project.main``.

    Args:
        argv: Extra arguments after the implicit ``--deb`` flag.
            ``None`` uses ``sys.argv[1:]``.
    """
    extra = sys.argv[1:] if argv is None else argv
    main(["--deb", *extra])


if __name__ == "__main__":
    run()
