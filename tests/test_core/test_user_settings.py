"""Unit tests for Line Emulator user settings persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from core.main_ui.user_settings import (
    UserSettings,
    get_user_settings_path,
    load_user_settings,
    save_user_settings,
)


class TestUserSettingsDefaults(unittest.TestCase):
    """Default values when no settings file exists."""

    def test_load_returns_system_theme_when_file_missing(self) -> None:
        """Missing file yields default ``theme_preference='system'``."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "line_emulator_user.json"
            settings = load_user_settings(settings_path)

        self.assertEqual(settings.theme_preference, "system")

    def test_user_settings_model_default(self) -> None:
        """Fresh ``UserSettings`` instance uses system theme."""
        settings = UserSettings()
        self.assertEqual(settings.theme_preference, "system")


class TestUserSettingsThemeRoundtrip(unittest.TestCase):
    """Save/load roundtrip for theme preference values."""

    def test_roundtrip_system_light_dark(self) -> None:
        """Each supported theme preference survives save and reload."""
        preferences = ("system", "light", "dark")
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "line_emulator_user.json"
            for preference in preferences:
                with self.subTest(theme_preference=preference):
                    save_user_settings(
                        UserSettings(theme_preference=preference),
                        settings_path,
                    )
                    loaded = load_user_settings(settings_path)
                    self.assertEqual(loaded.theme_preference, preference)

    def test_saved_json_contains_theme_preference(self) -> None:
        """Persisted JSON includes the selected theme field."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "line_emulator_user.json"
            save_user_settings(UserSettings(theme_preference="dark"), settings_path)
            payload = json.loads(settings_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["theme_preference"], "dark")

    def test_save_creates_parent_directories(self) -> None:
        """``save_user_settings`` creates nested parent folders when needed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "nested" / "line_emulator_user.json"
            save_user_settings(UserSettings(theme_preference="light"), settings_path)

            self.assertTrue(settings_path.is_file())
            self.assertEqual(
                load_user_settings(settings_path).theme_preference,
                "light",
            )

    def test_invalid_theme_rejected_on_load(self) -> None:
        """Corrupt theme value raises validation error on load."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "line_emulator_user.json"
            settings_path.write_text(
                json.dumps({"theme_preference": "neon"}),
                encoding="utf-8",
            )

            with self.assertRaises(ValidationError):
                load_user_settings(settings_path)


class TestGetUserSettingsPath(unittest.TestCase):
    """Filesystem path resolution for user settings."""

    @patch.dict("os.environ", {"APPDATA": r"C:\Users\Test\AppData\Roaming"}, clear=False)
    @patch("core.main_ui.user_settings.sys.platform", "win32")
    def test_windows_uses_appdata_subdirectory(self) -> None:
        """On Windows with APPDATA, settings live under DataMatrixControl."""
        path = get_user_settings_path()
        self.assertEqual(
            path,
            Path(r"C:\Users\Test\AppData\Roaming")
            / "DataMatrixControl"
            / "line_emulator_user.json",
        )

    @patch("core.main_ui.user_settings.sys.platform", "linux")
    def test_non_windows_uses_workdir(self) -> None:
        """On non-Windows platforms settings are stored next to WORKDIR."""
        with patch("core.main_ui.user_settings.client_info.WORKDIR", Path("/opt/dmc")):
            path = get_user_settings_path()

        self.assertEqual(path, Path("/opt/dmc") / "line_emulator_user.json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
