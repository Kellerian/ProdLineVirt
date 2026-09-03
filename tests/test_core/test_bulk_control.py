"""Unit tests for bulk widget start/stop/clear orchestration."""

from __future__ import annotations

import sys
import unittest
from collections import deque
from unittest.mock import MagicMock, patch

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.barcode_scanner.scanner_widget import ScannerWidget
from core.generator.generator_widget import GeneratorWidget
from core.main_ui.line_emul import MainLineField
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from core.transporting.transporter_widget import TransporterWidget
from libs.model_processing import create_code_item


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


class TestDeviceClearData(unittest.TestCase):
    """Public clear_data() on printer and camera widgets."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def test_printer_clear_data_clears_ui_and_core_buffer(self) -> None:
        """Printer clear_data resets list model and proxy buffer."""
        printer = PrinterWidget(name="PRN_1", port=9100)
        printer._data_list = ["code1", "code2"]
        printer.model_out.appendRow(create_code_item("code1"))
        printer._printer.clear_buffer = MagicMock()

        printer.clear_data()

        self.assertEqual(printer._data_list, [])
        self.assertEqual(printer.model_out.rowCount(), 0)
        printer._printer.clear_buffer.assert_called_once()

    def test_camera_clear_data_clears_models_and_proxy_queues(self) -> None:
        """Camera clear_data resets models and core queues via proxy."""
        camera = CameraWidget(name="CAM_1", port=23)
        camera.model_in.appendRow(create_code_item("in"))
        camera.model_out.appendRow(create_code_item("out"))
        camera._camera.clear_queues = MagicMock()

        camera.clear_data()

        self.assertEqual(camera.model_in.rowCount(), 0)
        self.assertEqual(camera.model_out.rowCount(), 0)
        camera._camera.clear_queues.assert_called_once()


def _set_run_checked(widget, checked: bool) -> None:
    """Set tbRun state without triggering emulator start/stop."""
    widget.tbRun.blockSignals(True)
    widget.tbRun.setChecked(checked)
    widget.tbRun.blockSignals(False)


class TestMainLineFieldBulkControl(unittest.TestCase):
    """Bulk start/stop/clear orchestration in MainLineField."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def setUp(self) -> None:
        """Create a main window with mocked device widgets."""
        self.window = MainLineField()
        self.printer = PrinterWidget(name="PRN_1", port=9100)
        self.camera = CameraWidget(name="CAM_1", port=23)
        self.scanner = _make_scanner("SCAN_1")
        self.transporter = TransporterWidget()
        self.generator = GeneratorWidget()

        self.window._device_widgets = {
            self.printer.device_id: self.printer,
            self.camera.device_id: self.camera,
            self.scanner.device_id: self.scanner,
        }
        self.window._transporter_widgets = {
            self.transporter.device_id: self.transporter
        }
        self.window._generator_widgets = {
            self.generator.device_id: self.generator
        }

    def test_bulk_start_all_order(self) -> None:
        """Start all: devices before transporters before generators."""
        call_order: list[str] = []

        def track_start(widgets: list) -> None:
            for widget in widgets:
                if widget is self.printer:
                    call_order.append("printer")
                elif widget is self.camera:
                    call_order.append("camera")
                elif widget is self.scanner:
                    call_order.append("scanner")
                elif widget is self.transporter:
                    call_order.append("transporter")
                elif widget is self.generator:
                    call_order.append("generator")

        original_start = MainLineField._start_widgets

        def patched_start(*args) -> None:
            widgets = args[-1]
            track_start(list(widgets))
            original_start(widgets)

        with patch.object(MainLineField, "_start_widgets", patched_start):
            self.window._bulk_start_all()

        self.assertEqual(
            call_order,
            ["printer", "camera", "scanner", "transporter", "generator"],
        )

    def test_bulk_stop_all_reverse_order(self) -> None:
        """Stop all: generators before transporters before devices."""
        call_order: list[str] = []

        def track_stop(widgets: list) -> None:
            for widget in widgets:
                if widget is self.generator:
                    call_order.append("generator")
                elif widget is self.transporter:
                    call_order.append("transporter")
                elif widget is self.printer:
                    call_order.append("printer")
                elif widget is self.camera:
                    call_order.append("camera")
                elif widget is self.scanner:
                    call_order.append("scanner")

        original_stop = MainLineField._stop_widgets

        def patched_stop(*args) -> None:
            widgets = args[-1]
            track_stop(list(widgets))
            original_stop(widgets)

        with patch.object(MainLineField, "_stop_widgets", patched_stop):
            self.window._bulk_stop_all()

        self.assertEqual(
            call_order,
            ["generator", "transporter", "scanner", "camera", "printer"],
        )

    def test_start_widgets_skips_already_running(self) -> None:
        """Bulk start only toggles widgets that are stopped."""
        with patch.object(PrinterWidget, "run"):
            with patch.object(CameraWidget, "run"):
                _set_run_checked(self.printer, True)
                _set_run_checked(self.camera, False)

                MainLineField._start_widgets([self.printer, self.camera])

                self.assertTrue(self.printer.tbRun.isChecked())
                self.assertTrue(self.camera.tbRun.isChecked())

    def test_stop_widgets_skips_already_stopped(self) -> None:
        """Bulk stop only toggles widgets that are running."""
        with patch.object(PrinterWidget, "run"):
            with patch.object(CameraWidget, "run"):
                _set_run_checked(self.printer, False)
                _set_run_checked(self.camera, True)

                MainLineField._stop_widgets([self.printer, self.camera])

                self.assertFalse(self.printer.tbRun.isChecked())
                self.assertFalse(self.camera.tbRun.isChecked())

    def test_bulk_clear_all_calls_clear_data_on_devices(self) -> None:
        """Bulk clear invokes clear_data on printers, cameras, scanners."""
        for widget in (self.printer, self.camera, self.scanner):
            widget.clear_data = MagicMock()

        self.window._bulk_clear_all()

        self.printer.clear_data.assert_called_once()
        self.camera.clear_data.assert_called_once()
        self.scanner.clear_data.assert_called_once()

    def test_bulk_clear_does_not_stop_widgets(self) -> None:
        """Clear data leaves Run toggles unchanged."""
        _set_run_checked(self.printer, True)
        _set_run_checked(self.camera, True)
        _set_run_checked(self.scanner, True)

        with patch.object(PrinterWidget, "clear_data", return_value=None):
            with patch.object(CameraWidget, "clear_data", return_value=None):
                with patch.object(ScannerWidget, "clear_data", return_value=None):
                    self.window._bulk_clear_all()

        self.assertTrue(self.printer.tbRun.isChecked())
        self.assertTrue(self.camera.tbRun.isChecked())
        self.assertTrue(self.scanner.tbRun.isChecked())


class TestPrinterProxyClearBuffer(unittest.TestCase):
    """PrinterProxy.clear_buffer delegates to PrinterEmul."""

    def test_clear_buffer_when_printer_running(self) -> None:
        """clear_buffer clears the core deque when emulator is active."""
        from core.printing.printer_proxy import PrinterProxy

        proxy = PrinterProxy()
        proxy._printer = MagicMock()
        proxy._printer._print_buffer = deque(["a", "b"])

        proxy.clear_buffer()

        proxy._printer.clear_buffer.assert_called_once()
