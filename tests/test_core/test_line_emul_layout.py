"""Unit tests for MainLineField layout persistence, reset, and visual order."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt
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


def _build_populated_window() -> tuple[MainLineField, dict[str, object]]:
    """Create a main window with one widget of each type and fixed ids."""
    window = MainLineField()
    widgets = {
        "printer": PrinterWidget(
            name="PRN_9100", port=9100, device_id="id-printer-layout"
        ),
        "camera": CameraWidget(
            name="CAM_23", port=23, device_id="id-camera-layout"
        ),
        "scanner": _make_scanner("SCAN_1", device_id="id-scanner-layout"),
        "transporter": TransporterWidget(device_id="id-transporter-layout"),
        "generator": GeneratorWidget(device_id="id-generator-layout"),
    }
    window._add_device(widgets["printer"])  # type: ignore[arg-type]
    window._add_device(widgets["camera"])  # type: ignore[arg-type]
    window._add_device(widgets["scanner"])  # type: ignore[arg-type]
    window._add_transport(widgets["transporter"])  # type: ignore[arg-type]
    window._add_generator(widgets["generator"])  # type: ignore[arg-type]
    widgets["transporter"].setup_models(window._device_widgets)  # type: ignore[attr-defined]
    widgets["generator"].setup_models(window._device_widgets)  # type: ignore[attr-defined]
    widgets["transporter"].set_source_ids(  # type: ignore[attr-defined]
        widgets["printer"].device_id,  # type: ignore[attr-defined]
        widgets["camera"].device_id,  # type: ignore[attr-defined]
    )
    widgets["generator"].set_to_ids(widgets["camera"].device_id)  # type: ignore[attr-defined]
    return window, widgets


class TestMainLineFieldLayoutPersistence(unittest.TestCase):
    """Save/load roundtrip for sidebar/canvas order and dock_state."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_save_load_roundtrip_preserves_layout_fields(self) -> None:
        """File save/load restores order arrays, dock_state, and advanced panels."""
        window, widgets = _build_populated_window()
        try:
            widgets["printer"].set_advanced_expanded(True)  # type: ignore[attr-defined]
            widgets["transporter"].set_advanced_expanded(True)  # type: ignore[attr-defined]
            window.set_sidebar_device_order(
                ["id-generator-layout", "id-transporter-layout"]
            )
            window.set_canvas_device_order(
                ["id-scanner-layout", "id-printer-layout", "id-camera-layout"]
            )
            window.removeDockWidget(window.dockSidebar)
            window.addDockWidget(
                Qt.DockWidgetArea.RightDockWidgetArea, window.dockSidebar
            )
            expected_dock_state = window._encode_dock_state()

            with tempfile.TemporaryDirectory() as tmp_dir:
                file_path = Path(tmp_dir) / "layout_test.json"
                window.save_configuration_to_file(file_path)
                saved = json.loads(file_path.read_text(encoding="utf-8"))

            self.assertEqual(
                saved["sidebar_order"],
                ["id-generator-layout", "id-transporter-layout"],
            )
            self.assertEqual(
                saved["canvas_order"],
                ["id-scanner-layout", "id-printer-layout", "id-camera-layout"],
            )
            self.assertEqual(saved["dock_state"], expected_dock_state)

            reload_window = MainLineField()
            try:
                reload_window.process_config(ConfigFile.model_validate(saved))
                self.assertEqual(
                    reload_window.get_sidebar_device_order(),
                    ["id-generator-layout", "id-transporter-layout"],
                )
                self.assertEqual(
                    reload_window.get_canvas_device_order(),
                    ["id-scanner-layout", "id-printer-layout", "id-camera-layout"],
                )
                self.assertEqual(
                    reload_window.dockWidgetArea(reload_window.dockSidebar),
                    Qt.DockWidgetArea.RightDockWidgetArea,
                )
                reloaded_printer = reload_window._device_widgets["id-printer-layout"]
                reloaded_transporter = reload_window._transporter_widgets[
                    "id-transporter-layout"
                ]
                self.assertTrue(reloaded_printer.is_advanced_expanded())
                self.assertTrue(reloaded_transporter.is_advanced_expanded())
            finally:
                reload_window.close()
        finally:
            window.close()

    def test_process_config_restores_saved_visual_order(self) -> None:
        """``process_config`` applies sidebar and canvas order from config."""
        window, _widgets = _build_populated_window()
        try:
            config = ConfigFile.model_validate(
                {
                    "printers": [
                        {
                            "device_id": "id-printer-layout",
                            "name": "PRN_9100",
                            "port": 9100,
                        }
                    ],
                    "cameras": [
                        {
                            "device_id": "id-camera-layout",
                            "name": "CAM_23",
                            "port": 23,
                            "config": {"packet_size": 1, "interval": 250},
                        }
                    ],
                    "scanners": [
                        {
                            "device_id": "id-scanner-layout",
                            "name": "SCAN_1",
                            "port_name": "COM1",
                            "config": {
                                "baud_rate": 9600,
                                "bytesize": 8,
                                "parity": "N",
                                "stopbits": 1,
                                "suffix": "\r\n",
                            },
                        }
                    ],
                    "transporters": [
                        {
                            "device_id": "id-transporter-layout",
                            "take_from": "id-scanner-layout",
                            "give_to": "id-camera-layout",
                            "interval": 100,
                        }
                    ],
                    "generators": [
                        {
                            "device_id": "id-generator-layout",
                            "generator_type": "KM_01_14_21_13_93_4",
                            "gtin": "07665585002196",
                            "give_to": "id-camera-layout",
                            "interval": 500,
                        }
                    ],
                    "sidebar_order": [
                        "id-generator-layout",
                        "id-transporter-layout",
                    ],
                    "canvas_order": [
                        "id-scanner-layout",
                        "id-camera-layout",
                        "id-printer-layout",
                    ],
                }
            )
            window.clear_ui()
            window.process_config(config)

            self.assertEqual(
                window.get_sidebar_device_order(),
                ["id-generator-layout", "id-transporter-layout"],
            )
            self.assertEqual(
                window.get_canvas_device_order(),
                [
                    "id-scanner-layout",
                    "id-camera-layout",
                    "id-printer-layout",
                ],
            )
        finally:
            window.close()

    def test_process_config_applies_legacy_migration_defaults(self) -> None:
        """Legacy JSON without layout fields opens with migration defaults."""
        legacy_payload = {
            "printers": [
                {
                    "name": "PRN_9100",
                    "port": 9100,
                    "buffer": 1,
                }
            ],
            "cameras": [],
            "scanners": [],
            "transporters": [
                {
                    "take_from": "PRN_9100",
                    "give_to": "PRN_9100",
                    "interval": 250,
                }
            ],
            "generators": [],
        }
        config = ConfigFile.model_validate_json(json.dumps(legacy_payload))
        self.assertEqual(len(config.sidebar_order), 1)
        self.assertEqual(len(config.canvas_order), 1)
        self.assertIsNone(config.dock_state)

        window = MainLineField()
        try:
            window.process_config(config)
            self.assertEqual(len(window.get_sidebar_device_order()), 1)
            self.assertEqual(len(window.get_canvas_device_order()), 1)
            self.assertEqual(
                window.dockWidgetArea(window.dockSidebar),
                Qt.DockWidgetArea.LeftDockWidgetArea,
            )
        finally:
            window.close()


class TestMainLineFieldResetLayout(unittest.TestCase):
    """View → Reset layout restores defaults without crashing."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_reset_layout_restores_default_dock_and_order(self) -> None:
        """``_apply_default_layout`` resets dock left and default device order."""
        window, _widgets = _build_populated_window()
        try:
            window.set_sidebar_device_order(
                ["id-generator-layout", "id-transporter-layout"]
            )
            window.set_canvas_device_order(
                ["id-scanner-layout", "id-camera-layout", "id-printer-layout"]
            )
            window.removeDockWidget(window.dockSidebar)
            window.addDockWidget(
                Qt.DockWidgetArea.RightDockWidgetArea, window.dockSidebar
            )

            window._apply_default_layout()

            self.assertEqual(
                window.dockWidgetArea(window.dockSidebar),
                Qt.DockWidgetArea.LeftDockWidgetArea,
            )
            self.assertEqual(
                window.get_sidebar_device_order(),
                ["id-transporter-layout", "id-generator-layout"],
            )
            self.assertEqual(
                window.get_canvas_device_order(),
                [
                    "id-printer-layout",
                    "id-camera-layout",
                    "id-scanner-layout",
                ],
            )
        finally:
            window.close()

    def test_ac_reset_layout_slot_does_not_crash(self) -> None:
        """Menu reset action runs without raising."""
        window, _widgets = _build_populated_window()
        try:
            window._on_reset_layout()
            self.assertEqual(
                window.dockWidgetArea(window.dockSidebar),
                Qt.DockWidgetArea.LeftDockWidgetArea,
            )
        finally:
            window.close()


class TestMainLineFieldVisualOrderIterators(unittest.TestCase):
    """Bulk iterators follow sidebar/canvas visual order."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_iterators_follow_visual_order(self) -> None:
        """Device and sidebar iterators respect reordered layout."""
        window, widgets = _build_populated_window()
        try:
            window.set_sidebar_device_order(
                ["id-generator-layout", "id-transporter-layout"]
            )
            window.set_canvas_device_order(
                ["id-scanner-layout", "id-camera-layout", "id-printer-layout"]
            )

            self.assertEqual(
                [w.device_id for w in window._iter_generators()],
                ["id-generator-layout"],
            )
            self.assertEqual(
                [w.device_id for w in window._iter_transporters()],
                ["id-transporter-layout"],
            )
            self.assertEqual(
                [w.device_id for w in window._iter_devices()],
                [
                    "id-scanner-layout",
                    "id-camera-layout",
                    "id-printer-layout",
                ],
            )
            self.assertEqual(
                [w.device_id for w in window._iter_printers()],
                ["id-printer-layout"],
            )
            self.assertIs(widgets["printer"], next(window._iter_printers()))
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
