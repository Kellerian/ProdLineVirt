"""Unit tests for Debian staging (no ``dpkg-deb`` required)."""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import subprocess

from build_deb import (
    DEBIAN_PACKAGING_DOCS,
    DEBIAN_TEMPLATES_DIR,
    PACKAGE_NAME,
    PIXMAP_NAME,
    _try_brief_elf_start,
    build_deb_via_wsl,
    copy_deb_to_install_dir,
    dpkg_deb_is_available,
    find_remote_deb,
    normalize_debian_version,
    package_frozen_onedir,
    parse_ldd_missing_libraries,
    render_control,
    resolve_onedir,
    run_dpkg_deb,
    smoke_check_linux_onedir,
    stage_debian_tree,
    strip_control_comments,
    wsl_argv,
)
from build_project import main, parse_cli_args
from client_info import VERSION


class TestNormalizeDebianVersion(unittest.TestCase):
    """Project VERSION → Debian upstream~tag-revision."""

    def test_beta_example_from_plan(self) -> None:
        self.assertEqual(
            normalize_debian_version("1.0.0.1.b0006"),
            "1.0.0.1~b0006-1",
        )

    def test_alpha_and_release_channels(self) -> None:
        self.assertEqual(
            normalize_debian_version("1.0.4.7.a0001"),
            "1.0.4.7~a0001-1",
        )
        self.assertEqual(
            normalize_debian_version("1.0.4.7.r0103", revision="2"),
            "1.0.4.7~r0103-2",
        )

    def test_current_client_info_version(self) -> None:
        debian = normalize_debian_version(VERSION)
        self.assertRegex(debian, r"^\d+(?:\.\d+)*~[abr]\d+-\d+$")
        self.assertTrue(debian.endswith("-1"))

    def test_rejects_unknown_shape(self) -> None:
        with self.assertRaises(ValueError):
            normalize_debian_version("1.0.0")
        with self.assertRaises(ValueError):
            normalize_debian_version("1.0.0.1.c0001")
        with self.assertRaises(ValueError):
            normalize_debian_version("1.0.0.1.b0006", revision="")


class TestControlTemplate(unittest.TestCase):
    """control.in placeholders and comment stripping."""

    def test_render_substitutes_version_and_drops_comments(self) -> None:
        template = (DEBIAN_TEMPLATES_DIR / "control.in").read_text(
            encoding="utf-8",
        )
        rendered = render_control(template, "1.0.0.1~b0006-1")
        self.assertIn("Package: dmclineemulator\n", rendered)
        self.assertIn("Version: 1.0.0.1~b0006-1\n", rendered)
        self.assertIn("Architecture: amd64\n", rendered)
        self.assertIn("Section: utils\n", rendered)
        self.assertIn("Maintainer: DataMatrixControl", rendered)
        self.assertIn("libdmtx0t64 | libdmtx0a | libdmtx0", rendered)
        self.assertIn("libpq5", rendered)
        self.assertIn("libdbus-1-3", rendered)
        self.assertIn("libglib2.0-0 | libglib2.0-0t64", rendered)
        self.assertIn("libxcb-randr0", rendered)
        self.assertIn("Recommends: fonts-dejavu-core", rendered)
        self.assertNotIn("@VERSION@", rendered)
        self.assertNotIn("Runtime Depends", rendered)
        self.assertNotIn("Windows development host", rendered)
        self.assertTrue(rendered.endswith("\n"))

    def test_strip_control_comments_keeps_fields(self) -> None:
        text = "Package: x\n# comment\nArchitecture: amd64\n"
        self.assertEqual(
            strip_control_comments(text),
            "Package: x\nArchitecture: amd64\n",
        )


class TestLddSmoke(unittest.TestCase):
    """``ldd`` parser (Windows-safe) and Linux-only smoke guard."""

    def test_parse_missing_unique_order(self) -> None:
        sample = (
            "\tlinux-vdso.so.1 (0x00007ffe)\n"
            "\tlibdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x1)\n"
            "\tlibxcb.so.1 => not found\n"
            "\tlibfoo.so.0 => not found\n"
            "        libxcb.so.1 => not found\n"
            "\t/lib64/ld-linux-x86-64.so.2 (0x2)\n"
        )
        self.assertEqual(
            parse_ldd_missing_libraries(sample),
            ["libxcb.so.1", "libfoo.so.0"],
        )

    def test_parse_empty_when_all_resolved(self) -> None:
        sample = "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x1)\n"
        self.assertEqual(parse_ldd_missing_libraries(sample), [])

    def test_smoke_noop_on_windows(self) -> None:
        with patch("build_deb.platform.system", return_value="Windows"):
            with patch("build_deb.subprocess.run") as run_mock:
                smoke_check_linux_onedir(Path("."))
        run_mock.assert_not_called()

    def _write_fake_elf(self, parent: Path) -> Path:
        onedir = parent / "dmcLineEmulator"
        onedir.mkdir(parents=True)
        elf = onedir / "dmcLineEmulator"
        elf.write_bytes(b"\x7fELFfake")
        return parent

    def test_smoke_fails_when_ldd_reports_not_found(self) -> None:
        ldd_out = "\tlibxcb.so.1 => not found\n"
        completed = subprocess.CompletedProcess(
            args=["ldd", "dmcLineEmulator"],
            returncode=0,
            stdout=ldd_out,
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            install = self._write_fake_elf(Path(tmp))
            with patch("build_deb.platform.system", return_value="Linux"):
                with patch("build_deb.shutil.which", return_value="/usr/bin/ldd"):
                    with patch(
                        "build_deb.subprocess.run",
                        return_value=completed,
                    ):
                        with patch("build_deb._try_brief_elf_start") as start:
                            with self.assertRaises(SystemExit) as raised:
                                smoke_check_linux_onedir(install)
        self.assertEqual(raised.exception.code, 1)
        start.assert_not_called()

    def test_smoke_ok_when_ldd_clean(self) -> None:
        ldd_out = "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x1)\n"
        completed = subprocess.CompletedProcess(
            args=["ldd", "dmcLineEmulator"],
            returncode=0,
            stdout=ldd_out,
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            install = self._write_fake_elf(Path(tmp))
            with patch("build_deb.platform.system", return_value="Linux"):
                with patch("build_deb.shutil.which", return_value="/usr/bin/ldd"):
                    with patch(
                        "build_deb.subprocess.run",
                        return_value=completed,
                    ):
                        with patch("build_deb._try_brief_elf_start") as start:
                            smoke_check_linux_onedir(install)
        start.assert_called_once()

    def test_smoke_fails_when_not_dynamic_executable(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["ldd", "dmcLineEmulator"],
            returncode=0,
            stdout="\tnot a dynamic executable\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            install = self._write_fake_elf(Path(tmp))
            with patch("build_deb.platform.system", return_value="Linux"):
                with patch("build_deb.shutil.which", return_value="/usr/bin/ldd"):
                    with patch(
                        "build_deb.subprocess.run",
                        return_value=completed,
                    ):
                        with self.assertRaises(SystemExit) as raised:
                            smoke_check_linux_onedir(install)
        self.assertEqual(raised.exception.code, 1)

    def test_brief_start_fails_on_import_error(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["xvfb-run", "-a", "bin", "--help"],
            returncode=1,
            stdout="",
            stderr="ImportError: No module named 'PySide6'\n",
        )
        with patch("build_deb.shutil.which", return_value="/usr/bin/xvfb-run"):
            with patch("build_deb.subprocess.run", return_value=completed):
                with self.assertRaises(SystemExit) as raised:
                    _try_brief_elf_start(Path("dmcLineEmulator"))
        self.assertEqual(raised.exception.code, 1)

    def test_brief_start_skips_without_display_or_xvfb(self) -> None:
        with patch("build_deb.shutil.which", return_value=None):
            with patch.dict("os.environ", {"DISPLAY": ""}, clear=False):
                with patch("build_deb.subprocess.run") as run_mock:
                    _try_brief_elf_start(Path("dmcLineEmulator"))
        run_mock.assert_not_called()


class TestStageDebianTree(unittest.TestCase):
    """Layout of DEBIAN/control, /opt, desktop, pixmap."""

    def _make_onedir(self, parent: Path, *, windows_exe: bool = False) -> Path:
        onedir = parent / "dmcLineEmulator"
        onedir.mkdir(parents=True)
        name = "dmcLineEmulator.exe" if windows_exe else "dmcLineEmulator"
        (onedir / name).write_bytes(b"fake-bin")
        (onedir / "_internal").mkdir()
        (onedir / "_internal" / "payload.txt").write_text("x", encoding="utf-8")
        return onedir

    def test_resolve_onedir_accepts_linux_or_exe_binary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_onedir(root)
            self.assertEqual(
                resolve_onedir(root),
                root / "dmcLineEmulator",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_onedir(root, windows_exe=True)
            self.assertEqual(
                resolve_onedir(root),
                root / "dmcLineEmulator",
            )

    def test_resolve_onedir_missing_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                resolve_onedir(Path(tmp))

    def test_stage_layout_and_control_version(self) -> None:
        templates = DEBIAN_TEMPLATES_DIR
        icon = Path(__file__).resolve().parents[2] / "media" / "logo.png"
        self.assertTrue(icon.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            onedir = self._make_onedir(root / "install")
            staging = root / "stage"
            debian_version = "1.0.0.1~b0006-1"
            stage_debian_tree(
                onedir_src=onedir,
                staging_root=staging,
                debian_version=debian_version,
                icon_src=icon,
                control_template=templates / "control.in",
                desktop_src=templates / "dmclineemulator.desktop",
            )
            control = (staging / "DEBIAN" / "control").read_text(
                encoding="utf-8",
            )
            self.assertIn(f"Version: {debian_version}\n", control)
            self.assertTrue(
                (staging / "opt" / "dmclineemulator" / "dmcLineEmulator")
                .is_file(),
            )
            self.assertTrue(
                (
                    staging
                    / "opt"
                    / "dmclineemulator"
                    / "_internal"
                    / "payload.txt"
                ).is_file(),
            )
            desktop = (
                staging
                / "usr"
                / "share"
                / "applications"
                / "dmclineemulator.desktop"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "Exec=/opt/dmclineemulator/dmcLineEmulator",
                desktop,
            )
            self.assertIn("Icon=dmclineemulator", desktop)
            self.assertIn("Categories=Utility;", desktop)
            self.assertIn("Terminal=false", desktop)
            self.assertTrue(
                (staging / "usr" / "share" / "pixmaps" / PIXMAP_NAME).is_file(),
            )

    def test_package_frozen_onedir_without_dpkg(self) -> None:
        icon = Path(__file__).resolve().parents[2] / "media" / "logo.png"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = root / "install"
            self._make_onedir(install)
            staging = package_frozen_onedir(
                install_dir=install,
                icon_src=icon,
                project_version="1.0.0.1.b0006",
                output_dir=root / "deb",
                run_dpkg=False,
            )
            self.assertEqual(
                staging.name,
                f"{PACKAGE_NAME}_1.0.0.1~b0006-1",
            )
            self.assertTrue((staging / "DEBIAN" / "control").is_file())


class TestDpkgDebGuard(unittest.TestCase):
    """``dpkg-deb`` must not run on Windows."""

    def test_unavailable_on_windows(self) -> None:
        with patch("build_deb.platform.system", return_value="Windows"):
            self.assertFalse(dpkg_deb_is_available())

    def test_run_dpkg_deb_exits_on_windows(self) -> None:
        stderr = io.StringIO()
        with patch("build_deb.platform.system", return_value="Windows"):
            with patch("sys.stderr", stderr):
                with self.assertRaises(SystemExit) as raised:
                    run_dpkg_deb(Path("."), Path("out.deb"))
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("dpkg-deb", stderr.getvalue())

    def test_run_dpkg_deb_passes_root_owner_group(self) -> None:
        staging = Path("staging")
        output = Path("out.deb")
        with patch("build_deb.platform.system", return_value="Linux"):
            with patch("build_deb.shutil.which", return_value="/usr/bin/dpkg-deb"):
                with patch("build_deb.subprocess.run") as run_mock:
                    with patch.object(Path, "mkdir"):
                        with patch.object(Path, "exists", return_value=False):
                            run_dpkg_deb(staging, output)
        run_mock.assert_called_once()
        argv = run_mock.call_args.args[0]
        self.assertEqual(
            argv,
            [
                "dpkg-deb",
                "--root-owner-group",
                "--build",
                str(staging),
                str(output),
            ],
        )


class TestBuildProjectDebFlag(unittest.TestCase):
    """``--linux`` freeze-only; ``--deb`` freeze then pack (+ install copy)."""

    def test_parse_deb_distinct_from_linux(self) -> None:
        linux_only = parse_cli_args(["--linux"])
        self.assertTrue(linux_only.linux)
        self.assertFalse(linux_only.deb)
        deb = parse_cli_args(["--deb"])
        self.assertTrue(deb.linux)
        self.assertTrue(deb.deb)

    def test_main_linux_does_not_package(self) -> None:
        with patch("build_project.platform.system", return_value="Linux"):
            with patch("build_project.generate_ui_files"):
                with patch("build_project.build_modules"):
                    with patch("build_project.cleanup_previous_installation_files"):
                        with patch("build_project.cleanup_build_dir"):
                            with patch(
                                "build_deb.smoke_check_linux_onedir",
                            ) as smoke:
                                with patch(
                                    "build_deb.package_frozen_onedir",
                                ) as pack:
                                    with patch(
                                        "build_deb.copy_deb_to_install_dir",
                                    ) as copy_install:
                                        main(["--linux"])
        smoke.assert_called_once()
        pack.assert_not_called()
        copy_install.assert_not_called()

    def test_main_deb_packages_after_freeze_on_linux(self) -> None:
        order: list[str] = []
        deb_artifact = Path("/tmp/dmclineemulator_1.0.0.1~b0007-1_amd64.deb")

        def _smoke(*_args: object, **_kwargs: object) -> None:
            order.append("smoke")

        def _pack(*_args: object, **_kwargs: object) -> Path:
            order.append("pack")
            return deb_artifact

        def _copy(path: Path, **_kwargs: object) -> Path:
            order.append("copy")
            self.assertEqual(path, deb_artifact)
            return Path("/tmp/install/dmcLineEmulator") / path.name

        with patch("build_project.platform.system", return_value="Linux"):
            with patch("build_project.generate_ui_files") as gen_ui:
                with patch("build_project.build_modules") as freeze:
                    with patch("build_project.cleanup_previous_installation_files"):
                        with patch("build_project.cleanup_build_dir"):
                            with patch(
                                "build_deb.smoke_check_linux_onedir",
                                side_effect=_smoke,
                            ):
                                with patch(
                                    "build_deb.package_frozen_onedir",
                                    side_effect=_pack,
                                ) as pack:
                                    with patch(
                                        "build_deb.copy_deb_to_install_dir",
                                        side_effect=_copy,
                                    ) as copy_install:
                                        main(["--deb"])
        gen_ui.assert_called_once()
        freeze.assert_called_once()
        pack.assert_called_once()
        copy_install.assert_called_once()
        self.assertEqual(order, ["smoke", "pack", "copy"])

    def test_main_deb_on_windows_uses_wsl_not_local_freeze(self) -> None:
        with patch("build_project.platform.system", return_value="Windows"):
            with patch("build_project.generate_ui_files") as gen_ui:
                with patch("build_project.build_modules") as freeze:
                    with patch(
                        "build_deb.package_frozen_onedir",
                    ) as pack:
                        with patch("build_deb.build_deb_via_wsl") as wsl_build:
                            main(["--deb"])
        wsl_build.assert_called_once_with()
        gen_ui.assert_not_called()
        freeze.assert_not_called()
        pack.assert_not_called()


class TestCopyDebToInstallDir(unittest.TestCase):
    """``.deb`` is placed next to the onedir under install."""

    def test_copy_creates_parent_and_copies_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            deb = root / "dmclineemulator_1.0.0.1~b0007-1_amd64.deb"
            deb.write_bytes(b"deb-bytes")
            install = root / "install"
            dest = copy_deb_to_install_dir(deb, install_dir=install)
            self.assertEqual(
                dest,
                install / "dmcLineEmulator" / deb.name,
            )
            self.assertTrue(dest.is_file())
            self.assertEqual(dest.read_bytes(), b"deb-bytes")


class TestWslDebOrchestration(unittest.TestCase):
    """Windows ``--deb`` path through default WSL (mocked subprocess)."""

    def test_wsl_argv_never_includes_distro_flag(self) -> None:
        argv = wsl_argv("wsl.exe", "bash", "-lc", "true")
        self.assertEqual(argv[:2], ["wsl.exe", "--"])
        self.assertNotIn("-d", argv[1:2])

    def test_find_remote_deb_leaves_glob_unquoted(self) -> None:
        """bash must expand ``*``; quoting the whole pattern breaks ls."""
        remote_dir = "/tmp/dmc-deb.XYZ"
        expected_deb = (
            f"{remote_dir}/build/deb/"
            f"{PACKAGE_NAME}_1.0.0.1~b0007-1_amd64.deb"
        )
        captured_cmds: list[str] = []

        def _captured(
            wsl: str,
            *remote_args: str,
            check: bool = False,
        ) -> subprocess.CompletedProcess[str]:
            del check
            self.assertEqual(wsl, "wsl.exe")
            self.assertEqual(remote_args[:2], ("bash", "-lc"))
            cmd = remote_args[2]
            captured_cmds.append(cmd)
            self.assertIn(f"{PACKAGE_NAME}_*_amd64.deb", cmd)
            self.assertNotIn(f"'{PACKAGE_NAME}_*_amd64.deb'", cmd)
            self.assertNotIn(f'"{PACKAGE_NAME}_*_amd64.deb"', cmd)
            # Glob star must appear outside single-quoted segments.
            self.assertRegex(cmd, rf"{PACKAGE_NAME}_[^'\"]*\*[^'\"]*_amd64\.deb")
            return subprocess.CompletedProcess(
                args=[wsl, "--", *remote_args],
                returncode=0,
                stdout=f"{expected_deb}\n",
                stderr="",
            )

        with patch("build_deb.run_wsl_captured", side_effect=_captured):
            found = find_remote_deb("wsl.exe", remote_dir)
        self.assertEqual(found, expected_deb)
        self.assertEqual(len(captured_cmds), 1)

    def test_build_deb_via_wsl_missing_wsl_exits(self) -> None:
        stderr = io.StringIO()
        with patch("build_deb.find_wsl_executable", return_value=None):
            with patch("sys.stderr", stderr):
                with self.assertRaises(SystemExit) as raised:
                    build_deb_via_wsl()
        self.assertEqual(raised.exception.code, 1)
        self.assertIn(DEBIAN_PACKAGING_DOCS, stderr.getvalue())

    def test_build_deb_via_wsl_preflight_failure_exits(self) -> None:
        stderr = io.StringIO()
        with patch("build_deb.find_wsl_executable", return_value="wsl.exe"):
            with patch(
                "build_deb.run_wsl_captured",
                return_value=subprocess.CompletedProcess(
                    args=[],
                    returncode=1,
                    stdout="",
                    stderr="missing",
                ),
            ):
                with patch("sys.stderr", stderr):
                    with self.assertRaises(SystemExit) as raised:
                        build_deb_via_wsl()
        self.assertEqual(raised.exception.code, 1)
        message = stderr.getvalue()
        self.assertIn(DEBIAN_PACKAGING_DOCS, message)
        self.assertIn("python3", message)

    def test_build_deb_via_wsl_success_copies_and_cleans(self) -> None:
        remote_tmp = "/tmp/dmc-deb.ABC"
        remote_deb = (
            f"{remote_tmp}/build/deb/"
            "dmclineemulator_1.0.0.1~b0007-1_amd64.deb"
        )
        captured_argv: list[list[str]] = []
        cleanup_calls: list[str] = []

        def _assert_no_wsl_distro_flag(argv: list[str]) -> None:
            """``wsl`` must use default distro (``--``, never ``-d``)."""
            self.assertGreaterEqual(len(argv), 2)
            self.assertEqual(argv[0], "wsl.exe")
            self.assertEqual(argv[1], "--")

        def _captured(
            wsl: str,
            *remote_args: str,
            check: bool = False,
        ) -> subprocess.CompletedProcess[str]:
            del check
            argv = [wsl, "--", *remote_args]
            captured_argv.append(argv)
            _assert_no_wsl_distro_flag(argv)
            joined = " ".join(remote_args)
            if remote_args[:1] == ("mktemp",):
                return subprocess.CompletedProcess(
                    argv, 0, stdout=f"{remote_tmp}\n", stderr="",
                )
            if "wslpath" in remote_args:
                return subprocess.CompletedProcess(
                    argv, 0, stdout="/mnt/c/proj\n", stderr="",
                )
            if "command -v python3" in joined:
                return subprocess.CompletedProcess(
                    argv, 0, stdout="/usr/bin/python3\n", stderr="",
                )
            if "tar -C" in joined:
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
            if "ls -1" in joined:
                return subprocess.CompletedProcess(
                    argv, 0, stdout=f"{remote_deb}\n", stderr="",
                )
            if "cp " in joined and remote_deb in joined:
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
            if "rm -rf" in joined:
                cleanup_calls.append(joined)
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            install = Path(tmp) / "install"
            dest_dir = install / "dmcLineEmulator"

            def _copy_side_effect(
                wsl: str,
                remote: str,
                *,
                install_dir: Path | None = None,
            ) -> Path:
                del wsl, remote
                parent = install if install_dir is None else install_dir
                out_dir = parent / "dmcLineEmulator"
                out_dir.mkdir(parents=True, exist_ok=True)
                out = out_dir / Path(remote_deb).name
                out.write_bytes(b"fake-deb")
                return out

            with patch("build_deb.find_wsl_executable", return_value="wsl.exe"):
                with patch(
                    "build_deb.run_wsl_captured",
                    side_effect=_captured,
                ):
                    with patch(
                        "build_deb.run_wsl_bash_streaming",
                        return_value=0,
                    ) as stream:
                        with patch(
                            "build_deb.copy_remote_deb_to_install",
                            side_effect=_copy_side_effect,
                        ):
                            with patch(
                                "build_deb.cleanup_wsl_temp",
                                side_effect=lambda _w, path: cleanup_calls.append(
                                    path,
                                ),
                            ):
                                dest = build_deb_via_wsl(install_dir=install)
            stream.assert_called_once()
            self.assertTrue(dest.is_file())
            self.assertEqual(dest.parent, dest_dir)
            self.assertIn(remote_tmp, cleanup_calls)
            for argv in captured_argv:
                _assert_no_wsl_distro_flag(argv)

    def test_build_deb_via_wsl_cleans_temp_on_remote_failure(self) -> None:
        remote_tmp = "/tmp/dmc-deb.FAIL"
        cleanup_paths: list[str] = []

        def _captured(
            wsl: str,
            *remote_args: str,
            check: bool = False,
        ) -> subprocess.CompletedProcess[str]:
            del check
            argv = [wsl, "--", *remote_args]
            self.assertEqual(argv[:2], ["wsl.exe", "--"])
            joined = " ".join(remote_args)
            if remote_args[:1] == ("mktemp",):
                return subprocess.CompletedProcess(
                    argv, 0, stdout=f"{remote_tmp}\n", stderr="",
                )
            if "wslpath" in remote_args:
                return subprocess.CompletedProcess(
                    argv, 0, stdout="/mnt/c/proj\n", stderr="",
                )
            if "command -v python3" in joined:
                return subprocess.CompletedProcess(
                    argv, 0, stdout="/usr/bin/python3\n", stderr="",
                )
            if "tar -C" in joined:
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

        with patch("build_deb.find_wsl_executable", return_value="wsl.exe"):
            with patch("build_deb.run_wsl_captured", side_effect=_captured):
                with patch(
                    "build_deb.run_wsl_bash_streaming",
                    return_value=42,
                ):
                    with patch(
                        "build_deb.cleanup_wsl_temp",
                        side_effect=lambda _w, path: cleanup_paths.append(path),
                    ):
                        with self.assertRaises(SystemExit) as raised:
                            build_deb_via_wsl()
        self.assertEqual(raised.exception.code, 42)
        self.assertEqual(cleanup_paths, [remote_tmp])


class TestBuildDebEntry(unittest.TestCase):
    """``build_deb.py`` requests ``--deb`` (freeze + pack)."""

    def test_run_forwards_deb_flag(self) -> None:
        from build_deb import run

        with patch("build_deb.main") as mocked:
            run([])
        mocked.assert_called_once_with(["--deb"])


if __name__ == "__main__":
    unittest.main()
