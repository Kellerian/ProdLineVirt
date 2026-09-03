"""Persistent user settings for Line Emulator (theme preference).

Settings are stored as JSON at ``line_emulator_user.json``:

- On Windows when ``%APPDATA%`` is set:
  ``%APPDATA%/DataMatrixControl/line_emulator_user.json``
- Otherwise (non-Windows or unset ``APPDATA``):
  ``client_info.WORKDIR/line_emulator_user.json``

The module has no Qt dependency so load/save logic can be unit-tested in isolation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

import client_info

ThemePreference = Literal["system", "light", "dark"]

_USER_SETTINGS_FILENAME = "line_emulator_user.json"
_APPDATA_SUBDIR = "DataMatrixControl"


class UserSettings(BaseModel):
    """Global Line Emulator preferences (not stored in project JSON)."""

    model_config = ConfigDict(strict=True)

    theme_preference: ThemePreference = Field(default="system")


def get_user_settings_path() -> Path:
    """Return the filesystem path to the user settings JSON file.

    On Windows the file is stored under ``%APPDATA%/DataMatrixControl/``.
    On other platforms the file is stored next to ``client_info.WORKDIR``.

    Returns:
        Absolute path to ``line_emulator_user.json``.
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / _APPDATA_SUBDIR / _USER_SETTINGS_FILENAME
    return client_info.WORKDIR / _USER_SETTINGS_FILENAME


def load_user_settings(path: Path | None = None) -> UserSettings:
    """Load user settings from JSON.

    If the file does not exist, returns a new ``UserSettings`` instance with defaults.

    Args:
        path: Optional override for the settings file location (for tests).

    Returns:
        Parsed user settings.

    Raises:
        pydantic.ValidationError: If the file exists but does not match the schema.
        OSError: If the file cannot be read.
    """
    settings_path = path if path is not None else get_user_settings_path()
    if not settings_path.is_file():
        return UserSettings()
    return UserSettings.model_validate_json(settings_path.read_text(encoding="utf-8"))


def save_user_settings(
    settings: UserSettings,
    path: Path | None = None,
) -> None:
    """Serialize user settings to JSON.

    Creates parent directories when needed.

    Args:
        settings: Settings instance to persist.
        path: Optional override for the settings file location (for tests).

    Raises:
        OSError: If the file cannot be written.
    """
    settings_path = path if path is not None else get_user_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        settings.model_dump_json(indent=4),
        encoding="utf-8",
    )
