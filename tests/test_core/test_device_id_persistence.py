"""Unit tests for stable device_id persistence via widgets and ConfigFile."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.barcode_scanner.scanner_widget import ScannerWidget
from core.generator.generator_widget import GeneratorWidget
from core.main_ui.data import ConfigFile
from core.main_ui.line_emul import MainLineField
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from core.transporting.transporter_widget import TransporterWidget


def _ensure_qapplication() -> QApplication:
    """Return the singleton QApplication required for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _make_scanner(name: str = "SCAN_1", device_id: str | None = None) -> ScannerWidget:
    """Create ScannerWidget with COM list and icons mocked out."""
    with (
        patch(
            "core.barcode_scanner.scanner_widget.list_available_ports",
            return_value=[],
        ),
        patch("core.barcode_scanner.scanner_widget.qta.icon", return_value=QIcon()),
    ):
        return ScannerWidget(name=name, device_id=device_id)


class TestDeviceIdPersistence(unittest.TestCase):
    """Widget options() round-trip through ConfigFile JSON and process_config."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def setUp(self) -> None:
        """Build a main window with fixed device ids and linked sidebar widgets."""
        self.window = MainLineField()
        self.printer = PrinterWidget(
            name="PRN_1", port=9100, device_id="id-printer-fixed"
        )
        self.camera = CameraWidget(
            name="CAM_1", port=10001, device_id="id-camera-fixed"
        )
        self.scanner = _make_scanner("SCAN_1", device_id="id-scanner-fixed")
        self.transporter = TransporterWidget(device_id="id-transporter-fixed")
        self.generator = GeneratorWidget(device_id="id-generator-fixed")

        self.window._add_device(self.printer)
        self.window._add_device(self.camera)
        self.window._add_device(self.scanner)
        self.window._add_transport(self.transporter)
        self.window._add_generator(self.generator)
        self.transporter.setup_models(self.window._device_widgets)
        self.generator.setup_models(self.window._device_widgets)
        self.transporter.set_source_ids(
            self.scanner.device_id, self.camera.device_id
        )
        self.generator.set_to_ids(self.camera.device_id)

    def tearDown(self) -> None:
        """Close the main window to release Qt resources."""
        self.window.close()

    def test_options_roundtrip_preserves_device_ids_and_links(self) -> None:
        """Save/load cycle keeps stable ids and transporter source/target refs."""
        config = ConfigFile(
            printers=[
                dev.options()
                for dev in self.window._device_widgets.values()
                if isinstance(dev, PrinterWidget)
            ],
            cameras=[
                dev.options()
                for dev in self.window._device_widgets.values()
                if isinstance(dev, CameraWidget)
            ],
            scanners=[
                dev.options()
                for dev in self.window._device_widgets.values()
                if isinstance(dev, ScannerWidget)
            ],
            transporters=[dev.options() for dev in self.window._transporter_widgets.values()],
            generators=[dev.options() for dev in self.window._generator_widgets.values()],
        )
        restored = ConfigFile.model_validate_json(config.model_dump_json())

        self.assertEqual(restored.transporters[0].device_id, "id-transporter-fixed")
        self.assertEqual(restored.transporters[0].take_from, "id-scanner-fixed")
        self.assertEqual(restored.transporters[0].give_to, "id-camera-fixed")
        self.assertEqual(restored.generators[0].device_id, "id-generator-fixed")
        self.assertEqual(restored.generators[0].give_to, "id-camera-fixed")

        reload_window = MainLineField()
        try:
            reload_window.process_config(restored)
            self.assertEqual(
                list(reload_window._transporter_widgets.keys()),
                ["id-transporter-fixed"],
            )
            self.assertEqual(
                list(reload_window._generator_widgets.keys()),
                ["id-generator-fixed"],
            )
            reloaded_transport = reload_window._transporter_widgets[
                "id-transporter-fixed"
            ]
            reloaded_generator = reload_window._generator_widgets[
                "id-generator-fixed"
            ]
            self.assertEqual(
                reloaded_transport.options().take_from, "id-scanner-fixed"
            )
            self.assertEqual(
                reloaded_transport.options().give_to, "id-camera-fixed"
            )
            self.assertEqual(
                reloaded_generator.options().give_to, "id-camera-fixed"
            )
        finally:
            reload_window.close()

    def test_options_without_combo_selection_uses_empty_refs(self) -> None:
        """options() does not crash when source/target combo has no valid widget."""
        transporter = TransporterWidget(device_id="id-transporter-empty")
        generator = GeneratorWidget(device_id="id-generator-empty")

        transport_cfg = transporter.options()
        generator_cfg = generator.options()

        self.assertEqual(transport_cfg.take_from, "")
        self.assertEqual(transport_cfg.give_to, "")
        self.assertEqual(generator_cfg.give_to, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
