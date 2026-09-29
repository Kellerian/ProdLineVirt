"""Unit tests for Linux onedir CLI flags in ``build_project``."""

from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from build_project import (
    decode_subprocess_output,
    main,
    parse_cli_args,
    require_linux,
    stdout_decode_encodings,
)


class TestStdoutDecoding(unittest.TestCase):
    """Platform-specific decode order for subprocess output."""

    def test_linux_prefers_utf8(self) -> None:
        with patch("build_project.platform.system", return_value="Linux"):
            self.assertEqual(
                stdout_decode_encodings(),
                ("utf-8", "cp866", "cp1251"),
            )
            self.assertEqual(
                decode_subprocess_output("строка".encode("utf-8")),
                "строка",
            )

    def test_windows_keeps_oem_order(self) -> None:
        with patch("build_project.platform.system", return_value="Windows"):
            self.assertEqual(
                stdout_decode_encodings(),
                ("cp866", "cp1251", "utf-8"),
            )
            raw = "тест".encode("cp866")
            self.assertEqual(decode_subprocess_output(raw), "тест")


class TestLinuxCliGuard(unittest.TestCase):
    """``--linux`` must refuse on Windows; ``--deb`` uses WSL there."""

    def test_parse_linux_and_deb_flags(self) -> None:
        self.assertFalse(parse_cli_args([]).linux)
        self.assertTrue(parse_cli_args(["--linux"]).linux)
        self.assertTrue(parse_cli_args(["--deb"]).linux)

    def test_require_linux_exits_on_windows(self) -> None:
        with patch("build_project.platform.system", return_value="Windows"):
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                with self.assertRaises(SystemExit) as raised:
                    require_linux()
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("only supported on Linux", stderr.getvalue())
        self.assertIn("Windows", stderr.getvalue())

    def test_require_linux_passes_on_linux(self) -> None:
        with patch("build_project.platform.system", return_value="Linux"):
            require_linux()

    def test_main_linux_flag_does_not_start_freeze_on_windows(self) -> None:
        with patch("build_project.platform.system", return_value="Windows"):
            with patch("build_project.generate_ui_files") as gen_ui:
                with patch("build_project.build_modules") as freeze:
                    with self.assertRaises(SystemExit) as raised:
                        main(["--linux"])
        self.assertEqual(raised.exception.code, 1)
        gen_ui.assert_not_called()
        freeze.assert_not_called()

    def test_main_deb_on_windows_delegates_to_wsl(self) -> None:
        with patch("build_project.platform.system", return_value="Windows"):
            with patch("build_deb.build_deb_via_wsl") as wsl_build:
                with patch("build_project.generate_ui_files") as gen_ui:
                    with patch("build_project.build_modules") as freeze:
                        main(["--deb"])
        wsl_build.assert_called_once_with()
        gen_ui.assert_not_called()
        freeze.assert_not_called()

    def test_main_without_flags_keeps_existing_pipeline(self) -> None:
        calls: list[str] = []

        def _record(name: str):
            def _inner(*_args: object, **_kwargs: object) -> None:
                calls.append(name)

            return _inner

        with patch(
            "build_project.cleanup_previous_installation_files",
            _record("cleanup_prev"),
        ):
            with patch("build_project.generate_ui_files", _record("ui")):
                with patch("build_project.build_modules", _record("build")):
                    with patch(
                        "build_project.cleanup_build_dir",
                        _record("cleanup"),
                    ):
                        main([])
                        main()
        self.assertEqual(
            calls,
            [
                "cleanup_prev",
                "ui",
                "build",
                "cleanup",
                "cleanup_prev",
                "ui",
                "build",
                "cleanup",
            ],
        )


class TestBuildDebEntry(unittest.TestCase):
    """``build_deb.py`` requests ``--deb`` (freeze + pack)."""

    def test_run_forwards_deb_flag(self) -> None:
        from build_deb import run

        with patch("build_deb.main") as mocked:
            run([])
        mocked.assert_called_once_with(["--deb"])


if __name__ == "__main__":
    unittest.main()
