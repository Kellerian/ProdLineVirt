"""Unit tests for scanner integration in transporter and generator combos."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from PySide6.QtGui import QIcon, QStandardItemModel
from PySide6.QtWidgets import QApplication

from core.barcode_scanner.scanner_widget import ScannerWidget
from core.generator.generator_widget import GeneratorWidget
from core.printing.printer_widget import PrinterWidget
from core.transporting.transporter_widget import TransporterWidget


def _ensure_qapplication() -> QApplication:
    """Return the singleton QApplication required for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _make_scanner(name: str = "SCAN_1") -> ScannerWidget:
    """Create ScannerWidget with COM list and icons mocked out."""
    with (
        patch(
            "core.barcode_scanner.scanner_widget.list_available_ports",
            return_value=[],
        ),
        patch("core.barcode_scanner.scanner_widget.qta.icon", return_value=QIcon()),
    ):
        return ScannerWidget(name=name)


def _make_printer(name: str = "PRN_1") -> PrinterWidget:
    """Create PrinterWidget for combo wiring tests."""
    return PrinterWidget(name=name, port=9100)


class TestTransporterScannerIntegration(unittest.TestCase):
    """ScannerWidget presence and model wiring in TransporterWidget."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def test_scanner_in_from_and_to_combos(self) -> None:
        """Scanner appears as source (from) and destination (to) in combos."""
        transport = TransporterWidget()
        scanner = _make_scanner("SCAN_SRC")
        printer = _make_printer()
        transport._device_data = {id(scanner): scanner, id(printer): printer}

        from_model, to_model = transport.get_data_models()

        from_names = [from_model.item(row, 0).text() for row in range(from_model.rowCount())]
        to_names = [to_model.item(row, 0).text() for row in range(to_model.rowCount())]

        self.assertEqual(from_names, ["SCAN_SRC", "PRN_1"])
        self.assertEqual(to_names, ["SCAN_SRC"])

    def test_set_from_scanner_uses_model_out(self) -> None:
        """Transporter source model is scanner.model_out."""
        transport = TransporterWidget()
        scanner = _make_scanner()
        transport._device_data = {id(scanner): scanner}
        from_model, _ = transport.get_data_models()
        transport.cbxFrom.setModel(from_model)
        transport.cbxFrom.setModelColumn(0)
        transport.cbxFrom.setCurrentIndex(0)

        transport.set_from_model(0)

        self.assertIs(transport.model_in, scanner.model_out)

    def test_set_to_scanner_uses_model_in(self) -> None:
        """Transporter destination model is scanner.model_in."""
        transport = TransporterWidget()
        scanner = _make_scanner()
        transport._device_data = {id(scanner): scanner}
        _, to_model = transport.get_data_models()
        transport.cbxTo.setModel(to_model)
        transport.cbxTo.setModelColumn(0)
        transport.cbxTo.setCurrentIndex(0)

        transport.set_to_model(0)

        self.assertIs(transport.model_out, scanner.model_in)


class TestGeneratorScannerIntegration(unittest.TestCase):
    """ScannerWidget as generator output target."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def test_scanner_in_generator_to_combo(self) -> None:
        """Scanner is listed as generator output target; printer is not."""
        generator = GeneratorWidget()
        scanner = _make_scanner("SCAN_DST")
        printer = _make_printer()
        generator._device_data = {id(scanner): scanner, id(printer): printer}

        to_model = generator.get_data_models()
        to_names = [to_model.item(row, 0).text() for row in range(to_model.rowCount())]

        self.assertEqual(to_names, ["SCAN_DST"])

    def test_set_to_scanner_uses_model_in(self) -> None:
        """Generator output model is scanner.model_in."""
        generator = GeneratorWidget()
        scanner = _make_scanner()
        generator._device_data = {id(scanner): scanner}
        to_model = generator.get_data_models()
        generator.cbxTo.setModel(to_model)
        generator.cbxTo.setModelColumn(0)
        generator.cbxTo.setCurrentIndex(0)

        generator.set_to_model(0)

        self.assertIs(generator.model_out, scanner.model_in)


if __name__ == "__main__":
    unittest.main(verbosity=2)
