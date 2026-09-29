from argparse import ArgumentParser, Namespace
from multiprocessing import Pool, cpu_count
from pathlib import Path
from shutil import rmtree
from subprocess import PIPE, STDOUT, Popen
import platform
import sys

import PyInstaller.__main__ as make_exe


ROOT_DIR = Path(__file__).parent
BUILD_DIR = Path(ROOT_DIR, "build")
SPEC_DIR = Path(BUILD_DIR, "spec")
INSTALL_DIR = Path(BUILD_DIR, "install")
TMP_DIR = Path(BUILD_DIR, "tmp")
PROJECT_FILES: list[tuple[str, str]] = [
    ("", "main.spec"),
]


def generate_ui_files() -> None:
    """Convert Qt Designer ``.ui`` files under ``ui/`` dirs to Python."""
    commands: list[str] = []
    for path_object in ROOT_DIR.glob("**/*.ui"):
        if path_object.is_file() and path_object.parent.name == "ui":
            file_to_convert = path_object.absolute()
            file_dir = file_to_convert.parent
            file_name = path_object.stem
            output_file = file_dir.parents[0].joinpath(file_name + ".py")
            print(f"Generating .py file for {file_to_convert}")
            command = (
                f"pyside6-uic {file_to_convert} -o {output_file} "
                f"--rc-prefix"
            )
            commands.append(command)
    with Pool(processes=cpu_count()) as p_pool:
        p_pool.map(run_external, commands)


def del_tree(dir_path: Path) -> None:
    """Remove ``dir_path`` if it exists; ignore a missing directory."""
    try:
        rmtree(dir_path)
    except FileNotFoundError:
        pass


def cleanup_previous_installation_files() -> None:
    """Delete leftover install trees that this script used to produce."""
    del_tree(Path(INSTALL_DIR, "dmcServer"))


def cleanup_build_dir() -> None:
    """Remove the PyInstaller work directory."""
    del_tree(TMP_DIR)


def build_app(install_dir: str, spec_file: str) -> None:
    """Run PyInstaller for one spec into ``INSTALL_DIR / install_dir``.

    Args:
        install_dir: Extra dist subdirectory under ``INSTALL_DIR``. Empty
            string writes COLLECT output (``dmcLineEmulator/``) directly
            under ``INSTALL_DIR``.
        spec_file: Spec filename inside ``SPEC_DIR``.
    """
    make_exe.run([
        "-y",
        "--workpath", str(TMP_DIR),
        "--distpath", str(Path(INSTALL_DIR, install_dir)),
        "--clean",
        str(Path(SPEC_DIR, spec_file)),
    ])


def build_modules() -> None:
    """Freeze every entry in ``PROJECT_FILES`` via PyInstaller."""
    with Pool(processes=cpu_count()) as p_pool:
        p_pool.starmap(build_app, PROJECT_FILES)


def stdout_decode_encodings() -> tuple[str, ...]:
    """Return encodings to try when decoding subprocess stdout.

    Linux prefers UTF-8. Windows keeps the historical order ``cp866``,
    then ``cp1251``, then UTF-8.

    Returns:
        Ordered encoding names for ``bytes.decode``.
    """
    if platform.system() == "Linux":
        return ("utf-8", "cp866", "cp1251")
    return ("cp866", "cp1251", "utf-8")


def decode_subprocess_output(raw: bytes) -> str:
    """Decode a subprocess stdout chunk for display on the current OS.

    Args:
        raw: One line of bytes from the child process.

    Returns:
        Decoded text. If no encoding in ``stdout_decode_encodings``
        succeeds, UTF-8 with replacement characters is used.
    """
    for encoding in stdout_decode_encodings():
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def run_external(command: str) -> None:
    """Run a shell command and print its combined stdout/stderr.

    Args:
        command: Command line passed to the system shell.
    """
    proc = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
    while proc.poll() is None:
        if proc.stdout is None:
            continue
        line = proc.stdout.readline().strip()
        if line:
            print(decode_subprocess_output(line))


def require_linux() -> None:
    """Abort with a non-zero exit code unless the host OS is Linux.

    Used for freeze-only ``--linux``. Windows ``--deb`` does not call this;
    it uses default-WSL orchestration instead.

    Raises:
        SystemExit: Always with code 1 when ``platform.system()`` is not
            ``Linux``. Does not return on that path.
    """
    current = platform.system()
    if current != "Linux":
        print(
            "Linux onedir build (--linux) is only supported on Linux "
            f"(native or inside WSL). Current OS: {current}. "
            "To build a .deb from Windows, use --deb (default WSL).",
            file=sys.stderr,
        )
        sys.exit(1)


def parse_cli_args(argv: list[str]) -> Namespace:
    """Parse CLI flags for this build script.

    Args:
        argv: Argument list without the program name (like
            ``sys.argv[1:]``). An empty list is the default Windows
            onedir path with no Linux-only flags.

    Returns:
        Parsed namespace. ``linux`` is True when ``--linux`` or
        ``--deb`` was given. ``deb`` is True only for ``--deb``
        (freeze plus ``.deb`` packaging).
    """
    parser = ArgumentParser(
        description=(
            "Build dmcLineEmulator with PyInstaller. "
            "Default (no flags) is the existing Windows onedir flow."
        ),
    )
    parser.add_argument(
        "--linux",
        action="store_true",
        dest="linux",
        help=(
            "Build Linux onedir into build/install/dmcLineEmulator/. "
            "Must run on Linux; on Windows exits with an error "
            "(freeze-only is not orchestrated via WSL)."
        ),
    )
    parser.add_argument(
        "--deb",
        action="store_true",
        dest="deb",
        help=(
            "On Linux: re-freeze the onedir (same as --linux), stage a "
            "Debian tree, run dpkg-deb, and copy the .deb next to the "
            "onedir under build/install/dmcLineEmulator/. "
            "On Windows: run the same path inside the default WSL distro "
            "(wsl.exe without -d) and copy the .deb to that install dir. "
            "Freeze-only: use --linux (Linux host only)."
        ),
    )
    args = parser.parse_args(argv)
    args.linux = bool(args.linux or args.deb)
    return args


def main(argv: list[str] | None = None) -> None:
    """Run UI generation, PyInstaller freeze, and optional ``.deb`` packing.

    Calling ``main()`` or ``main([])`` without Linux flags keeps the
    historical pipeline: cleanup leftovers, ``generate_ui_files``,
    ``build_modules``, then ``cleanup_build_dir``.

    ``--linux`` is freeze-only and requires a Linux host. ``--deb`` on
    Linux re-freezes, smoke-checks with ``ldd``, packs with ``dpkg-deb``,
    and copies the ``.deb`` to ``build/install/dmcLineEmulator/``. On
    Windows ``--deb`` delegates to ``build_deb.build_deb_via_wsl`` (default
    WSL, no local freeze).

    Args:
        argv: CLI arguments without the program name. ``None`` is treated
            as an empty list so importing and calling ``main()`` is not
            affected by pytest or other ``sys.argv`` values. Pass
            ``sys.argv[1:]`` from the ``__main__`` entry.
    """
    args = parse_cli_args([] if argv is None else argv)
    if args.deb and platform.system() == "Windows":
        from build_deb import build_deb_via_wsl

        build_deb_via_wsl()
        return
    if args.linux:
        require_linux()
    cleanup_previous_installation_files()
    generate_ui_files()
    build_modules()
    cleanup_build_dir()
    if args.linux:
        from build_deb import smoke_check_linux_onedir

        smoke_check_linux_onedir()
    if args.deb:
        from build_deb import copy_deb_to_install_dir, package_frozen_onedir

        deb_path = package_frozen_onedir()
        copy_deb_to_install_dir(deb_path)


if __name__ == "__main__":
    main(sys.argv[1:])
    # generate_ui_files()
