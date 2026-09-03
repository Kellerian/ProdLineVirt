"""Unit tests for theme resolution and QSS loading (no GUI assertions)."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from libs.qt_theme import (
    DARK,
    LIGHT,
    ThemeMode,
    apply_theme,
    get_tokens,
    load_stylesheet,
    resolve_effective_mode,
)


def _ensure_qapplication() -> QApplication:
    """Return the singleton QApplication required for Qt style hints."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestResolveEffectiveMode(unittest.TestCase):
    """Tests for explicit and system theme resolution."""

    def test_light_and_dark_preferences(self) -> None:
        """Explicit preferences resolve without OS heuristics."""
        self.assertEqual(resolve_effective_mode(ThemeMode.LIGHT), "light")
        self.assertEqual(resolve_effective_mode(ThemeMode.DARK), "dark")

    @patch("libs.qt_theme._detect_system_theme", return_value="dark")
    def test_system_preference_uses_os_heuristic(self, _mock_detect) -> None:
        """System preference delegates to OS detection when Qt hints are absent."""
        self.assertEqual(resolve_effective_mode(ThemeMode.SYSTEM), "dark")

    @patch("libs.qt_theme._detect_system_theme_via_qt", return_value="dark")
    def test_system_preference_prefers_qt_hints(self, _mock_qt_detect) -> None:
        """System preference prefers QStyleHints when QApplication is provided."""
        app = _ensure_qapplication()
        self.assertEqual(
            resolve_effective_mode(ThemeMode.SYSTEM, app=app),
            "dark",
        )

    @patch("libs.qt_theme._detect_system_theme_via_qt", return_value=None)
    @patch("libs.qt_theme._detect_system_theme", return_value="light")
    def test_system_falls_back_to_os_when_qt_unavailable(
        self, _mock_os_detect, _mock_qt_detect
    ) -> None:
        """System preference uses OS heuristic when Qt color scheme is unknown."""
        app = _ensure_qapplication()
        self.assertEqual(
            resolve_effective_mode(ThemeMode.SYSTEM, app=app),
            "light",
        )


class TestDesignTokens(unittest.TestCase):
    """Tests for palette token loading without GUI assertions."""

    def test_get_tokens_returns_light_and_dark_singletons(self) -> None:
        """``get_tokens`` maps resolved modes to module-level token objects."""
        self.assertIs(get_tokens("light"), LIGHT)
        self.assertIs(get_tokens("dark"), DARK)

    def test_device_backgrounds_match_device_type_keys(self) -> None:
        """Each device type exposes a distinct card background color."""
        for mode, tokens in (("light", LIGHT), ("dark", DARK)):
            with self.subTest(mode=mode):
                backgrounds = tokens.device_backgrounds
                self.assertEqual(
                    set(backgrounds.keys()),
                    {"printer", "camera", "scanner", "transporter", "generator"},
                )
                self.assertEqual(
                    tokens.device_background("printer"),
                    backgrounds["printer"],
                )
                self.assertNotEqual(
                    backgrounds["printer"],
                    backgrounds["camera"],
                )


class TestLoadStylesheet(unittest.TestCase):
    """Smoke tests for theme QSS files on disk."""

    def test_load_light_and_dark_stylesheets(self) -> None:
        """Both theme files load and contain deviceType selectors."""
        for mode in ("light", "dark"):
            qss = load_stylesheet(mode)
            self.assertIn('QWidget#Form[deviceType="printer"]', qss)
            self.assertIn("QMenuBar", qss)
            self.assertIn("QDockWidget", qss)

    def test_invalid_mode_raises_value_error(self) -> None:
        """Unknown resolved mode is rejected before filesystem access."""
        with self.assertRaises(ValueError):
            load_stylesheet("neon")  # type: ignore[arg-type]


class TestApplyTheme(unittest.TestCase):
    """Smoke tests for global theme application with minimal QApplication."""

    def test_apply_theme_sets_stylesheet_for_light_and_dark(self) -> None:
        """``apply_theme`` loads QSS and returns the resolved mode."""
        app = _ensure_qapplication()
        for preference, expected in (
            (ThemeMode.LIGHT, "light"),
            (ThemeMode.DARK, "dark"),
        ):
            with self.subTest(preference=preference.value):
                effective = apply_theme(app, preference)
                self.assertEqual(effective, expected)
                self.assertIn(
                    'QWidget#Form[deviceType="printer"]',
                    app.styleSheet(),
                )


if __name__ == "__main__":
    unittest.main()
