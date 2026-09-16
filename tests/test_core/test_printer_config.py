"""Unit tests for printer configuration models and PrinterWidget options."""

from __future__ import annotations

import json
import sys
import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from core.main_ui.data import ConfigFile
from core.printing.data import PrinterConfig, PrinterLanguage
from core.printing.printer_widget import PrinterWidget


def _ensure_qapplication() -> QApplication:
    """Return the singleton QApplication required for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestPrinterConfig(unittest.TestCase):
    """Tests for PrinterConfig JSON and backward compatibility."""

    def test_legacy_json_without_language_defaults_to_legacy(self) -> None:
        """Printer JSON without language field loads with legacy default."""
        config = PrinterConfig.model_validate({"name": "PRN_1", "port": 9100})
        self.assertEqual(config.language, PrinterLanguage.legacy)

        legacy = json.dumps({"printers": [{"name": "PRN_1", "port": 9100}]})
        file_config = ConfigFile.model_validate_json(legacy)
        self.assertEqual(file_config.printers[0].language, PrinterLanguage.legacy)

    def test_language_string_round_trip(self) -> None:
        """language survives model_dump_json → model_validate_json as enum value."""
        original = PrinterConfig(name="PRN_1", port=9100, language=PrinterLanguage.tspl2)
        restored = PrinterConfig.model_validate_json(original.model_dump_json())
        self.assertEqual(restored.language, PrinterLanguage.tspl2)

        payload = json.dumps(
            {"name": "PRN_1", "port": 9100, "language": "ezpl"},
        )
        from_json = PrinterConfig.model_validate_json(payload)
        self.assertEqual(from_json.language, PrinterLanguage.ezpl)

    def test_all_languages_round_trip_in_config_file(self) -> None:
        """Each PrinterLanguage value persists in ConfigFile printers section."""
        for language in PrinterLanguage:
            original = ConfigFile(
                printers=[
                    PrinterConfig(
                        name="PRN_1",
                        port=9100,
                        buffer=2,
                        language=language,
                    ),
                ],
            )
            restored = ConfigFile.model_validate_json(original.model_dump_json())
            self.assertEqual(restored.printers[0].language, language)
            dumped = json.loads(original.model_dump_json())["printers"][0]
            self.assertEqual(dumped["language"], language.value)

    def test_invalid_language_type_raises_validation_error(self) -> None:
        """Non-string language in JSON raises ValidationError, not TypeError."""
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            PrinterConfig.model_validate({"name": "PRN_1", "port": 9100, "language": 123})


class TestPrinterWidgetOptions(unittest.TestCase):
    """PrinterWidget.options() and language combo behaviour."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def test_options_default_language_is_legacy(self) -> None:
        """Widget without explicit language reports legacy in options()."""
        widget = PrinterWidget(name="PRN_1", port=9100)
        options = widget.options()
        self.assertEqual(options.language, PrinterLanguage.legacy)
        self.assertEqual(options.name, "PRN_1")
        self.assertEqual(options.port, 9100)

    def test_constructor_initializes_language_combo(self) -> None:
        """Ctor language kwarg is reflected in combo and options()."""
        widget = PrinterWidget(
            name="PRN_1",
            port=9100,
            language=PrinterLanguage.zpl,
        )
        self.assertEqual(widget.options().language, PrinterLanguage.zpl)

    def test_options_follows_combo_selection(self) -> None:
        """Changing cbLanguage updates language in options()."""
        widget = PrinterWidget(name="PRN_1", port=9100)
        widget.cbLanguage.setCurrentIndex(4)
        self.assertEqual(widget.options().language, PrinterLanguage.sppl)

    def test_run_passes_selected_language_to_proxy(self) -> None:
        """Starting the widget forwards combo language to PrinterProxy.start."""
        widget = PrinterWidget(name="PRN_1", port=9100)
        widget.cbLanguage.setCurrentIndex(1)
        widget._printer.start = MagicMock()
        widget._printer.set_buffer_size = MagicMock()

        widget.tbRun.setChecked(True)

        widget._printer.start.assert_called_once_with(
            "PRN_1",
            9100,
            1,
            PrinterLanguage.tspl2,
        )

    def test_language_combo_disabled_while_running(self) -> None:
        """cbLanguage is locked together with name/port when emulator runs."""
        widget = PrinterWidget(name="PRN_1", port=9100)
        widget._printer.start = MagicMock()
        widget._printer.set_buffer_size = MagicMock()
        widget._printer.stop = MagicMock()

        widget.tbRun.setChecked(True)
        self.assertFalse(widget.cbLanguage.isEnabled())
        self.assertFalse(widget.leName.isEnabled())

        widget.tbRun.setChecked(False)
        self.assertTrue(widget.cbLanguage.isEnabled())
        widget._printer.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
