"""Design system and Qt theme for Line Emulator.

Centralizes palette tokens, QSS loading, and platform-specific Qt style
workarounds (``windowsvista`` on Windows for light-theme combo/menu popups).

``main.py`` loads ``UserSettings.theme_preference`` and calls ``apply_theme``
before ``MainLineField``. Menu actions persist preference via ``line_emul.py``.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from libs.media import get_path_to_media

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication, QStyleHints

ResolvedTheme = Literal["light", "dark"]
DeviceType = Literal["printer", "camera", "scanner", "transporter", "generator"]

_DEVICE_TYPES: Final[tuple[DeviceType, ...]] = (
    "printer",
    "camera",
    "scanner",
    "transporter",
    "generator",
)

_WINDOWS_LIGHT_STYLE: Final = "windowsvista"
_WINDOWS_DARK_STYLE_CANDIDATES: Final[tuple[str, ...]] = (
    "windows11",
    "Windows",
    "Fusion",
)


class ThemeMode(str, Enum):
    """User-facing theme preference stored in user settings."""

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class DesignTokens:
    """Palette and typography tokens mirrored in ``media/themes/*.qss``.

    Attributes:
        accent: Highlight / selection accent (gold).
        border: Primary border and menu text on light surfaces.
        button_bg: Default filled control background.
        button_pressed_bg: Pressed / checked control background.
        combo_popup_bg: QComboBox dropdown list background.
        menu_bar_bg: QMenuBar background.
        menu_bg: QMenu dropdown background.
        text_primary: Primary readable text on light surfaces.
        text_on_button: Button label on filled controls.
        text_on_dark: Primary readable text on dark surfaces.
        device_printer: Device card background — printer.
        device_camera: Device card background — camera.
        device_scanner: Device card background — scanner.
        device_transporter: Device card background — transporter.
        device_generator: Device card background — generator.
        font_ui: Sans-serif stack for labels, buttons, combo.
        font_mono: Monospace stack for code queues and tech fields.
    """

    accent: str
    border: str
    button_bg: str
    button_pressed_bg: str
    combo_popup_bg: str
    menu_bar_bg: str
    menu_bg: str
    text_primary: str
    text_on_button: str
    text_on_dark: str
    device_printer: str
    device_camera: str
    device_scanner: str
    device_transporter: str
    device_generator: str
    font_ui: str
    font_mono: str

    def device_background(self, device_type: DeviceType) -> str:
        """Return the card background color for a device type."""
        return getattr(self, _DEVICE_BACKGROUND_ATTR[device_type])

    @property
    def device_backgrounds(self) -> dict[DeviceType, str]:
        """Map device type names to card background colors."""
        return {device_type: self.device_background(device_type) for device_type in _DEVICE_TYPES}


_DEVICE_BACKGROUND_ATTR: Final[dict[DeviceType, str]] = {
    "printer": "device_printer",
    "camera": "device_camera",
    "scanner": "device_scanner",
    "transporter": "device_transporter",
    "generator": "device_generator",
}


LIGHT: Final[DesignTokens] = DesignTokens(
    accent="#f0b321",
    border="#17365D",
    button_bg="#226091",
    button_pressed_bg="#19466a",
    combo_popup_bg="#19466a",
    menu_bar_bg="#ffffff",
    menu_bg="#f5f5f5",
    text_primary="#17365D",
    text_on_button="#FFFFFF",
    text_on_dark="#FFFFFF",
    device_printer="#fff3e0",
    device_camera="#e8f5e9",
    device_scanner="#f3e5f5",
    device_transporter="#e3f2fd",
    device_generator="#fff9c4",
    font_ui='"Segoe UI", "SF Pro Text", "Helvetica Neue", sans-serif',
    font_mono='"Cascadia Mono", "Consolas", "DejaVu Sans Mono", monospace',
)

DARK: Final[DesignTokens] = DesignTokens(
    accent="#f0b321",
    border="#5a8ab0",
    button_bg="#1e4d73",
    button_pressed_bg="#163a57",
    combo_popup_bg="#163a57",
    menu_bar_bg="#2d2d2d",
    menu_bg="#3c3c3c",
    text_primary="#e0e0e0",
    text_on_button="#e8e8e8",
    text_on_dark="#e0e0e0",
    device_printer="#3d3528",
    device_camera="#2a3d2c",
    device_scanner="#352a3d",
    device_transporter="#283545",
    device_generator="#3d3a28",
    font_ui='"Segoe UI", "SF Pro Text", "Helvetica Neue", sans-serif',
    font_mono='"Cascadia Mono", "Consolas", "DejaVu Sans Mono", monospace',
)

_TOKENS_BY_MODE: Final[dict[ResolvedTheme, DesignTokens]] = {
    "light": LIGHT,
    "dark": DARK,
}


def get_tokens(mode: ResolvedTheme) -> DesignTokens:
    """Return design tokens for a resolved theme mode."""
    return _TOKENS_BY_MODE[mode]


def _theme_stylesheet_path(mode: ResolvedTheme) -> Path:
    """Resolve the on-disk path to a theme QSS file."""
    return Path(get_path_to_media(f"themes/theme_{mode}.qss"))


def load_stylesheet(mode: ResolvedTheme) -> str:
    """Load the QSS stylesheet for ``light`` or ``dark``.

    Args:
        mode: Resolved theme — not ``ThemeMode.SYSTEM`` (resolve first).

    Returns:
        Full QSS text from ``media/themes/theme_<mode>.qss``.

    Raises:
        FileNotFoundError: Stylesheet file is missing from ``media/themes/``.
        ValueError: ``mode`` is not ``light`` or ``dark``.
    """
    if mode not in _TOKENS_BY_MODE:
        raise ValueError(f"mode must be 'light' or 'dark', got {mode!r}")
    path = _theme_stylesheet_path(mode)
    if not path.is_file():
        raise FileNotFoundError(f"Theme stylesheet not found: {path}")
    return path.read_text(encoding="utf-8")


def resolve_effective_mode(
    preference: ThemeMode,
    app: QApplication | None = None,
) -> ResolvedTheme:
    """Resolve user preference to ``light`` or ``dark``.

    ``ThemeMode.SYSTEM`` prefers ``QStyleHints.colorScheme()`` when a
    ``QApplication`` is available (PySide6 6.7+), otherwise Windows registry
    ``AppsUseLightTheme``, with fallback ``"light"``.

    Args:
        preference: Stored or selected theme preference.
        app: Optional running application for Qt system theme detection.

    Returns:
        ``"light"`` or ``"dark"``.
    """
    if preference == ThemeMode.LIGHT:
        return "light"
    if preference == ThemeMode.DARK:
        return "dark"
    if app is not None:
        qt_mode = _detect_system_theme_via_qt(app)
        if qt_mode is not None:
            return qt_mode
    return _detect_system_theme()


def _detect_system_theme() -> ResolvedTheme:
    """Best-effort OS theme detection without requiring a QApplication."""
    if platform.system() == "Windows":
        return _detect_windows_theme()
    return "light"


def _detect_windows_theme() -> ResolvedTheme:
    """Read Windows ``AppsUseLightTheme`` registry value."""
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value else "dark"
    except OSError:
        return "light"


def _detect_system_theme_via_qt(app: QApplication) -> ResolvedTheme | None:
    """Resolve OS theme via ``QStyleHints.colorScheme()`` when supported.

    Args:
        app: Running ``QApplication`` instance.

    Returns:
        ``"light"`` or ``"dark"`` when Qt reports a scheme, otherwise ``None``.
    """
    from PySide6.QtCore import Qt

    hints: QStyleHints = app.styleHints()
    color_scheme = hints.colorScheme()
    if color_scheme == Qt.ColorScheme.Dark:
        return "dark"
    if color_scheme == Qt.ColorScheme.Light:
        return "light"
    return None


def apply_qt_style(app: QApplication, effective_mode: ResolvedTheme) -> None:
    """Apply platform Qt style before QSS.

    On Windows, light theme uses ``windowsvista`` to fix Qt 6.7 popup rendering
    with ``QT_QPA_PLATFORM=windows:darkmode=0`` (see ``main.py``). Dark theme
    uses ``windows11`` / ``Windows`` / ``Fusion`` so popups stay readable after
    leaving the light ``windowsvista`` workaround.

    Args:
        app: Running ``QApplication`` instance.
        effective_mode: Resolved ``light`` or ``dark`` mode.
    """
    if platform.system() != "Windows":
        return

    from PySide6.QtWidgets import QStyleFactory

    if effective_mode == "light":
        app.setStyle(_WINDOWS_LIGHT_STYLE)
        return

    available_styles = QStyleFactory.keys()
    for style_name in _WINDOWS_DARK_STYLE_CANDIDATES:
        if style_name in available_styles:
            app.setStyle(style_name)
            return


def apply_theme(app: QApplication, preference: ThemeMode = ThemeMode.LIGHT) -> ResolvedTheme:
    """Apply resolved theme: Qt style workaround + global QSS.

    Args:
        app: Running ``QApplication`` instance.
        preference: User theme preference (``system`` / ``light`` / ``dark``).

    Returns:
        Resolved ``light`` or ``dark`` mode applied to the application.
    """
    effective_mode = resolve_effective_mode(preference, app=app)
    apply_qt_style(app, effective_mode)
    app.setStyleSheet(load_stylesheet(effective_mode))
    return effective_mode


def apply_light_theme(app: QApplication) -> None:
    """Apply light theme: Qt style workaround + global ``theme_light.qss``.

    Convenience wrapper equivalent to ``apply_theme(app, ThemeMode.LIGHT)``.

    Args:
        app: ``QApplication`` instance created before the main window.
    """
    apply_theme(app, ThemeMode.LIGHT)
