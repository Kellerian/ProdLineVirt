"""Unit tests for MainLineField widget remove API and clear_ui generators."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from core.barcode_scanner.scanner_widget import ScannerWidget
from core.generator.generator_widget import GeneratorWidget
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


def _make_scanner(name: str = "SCAN_1") -> ScannerWidget:
    """Create ScannerWidget with COM list and icons mocked out.

    Args:
        name: Display name for the scanner widget.

    Returns:
        Configured ``ScannerWidget`` instance.
    """
    with (
        patch(
            "core.barcode_scanner.scanner_widget.list_available_ports",
            return_value=[],
        ),
        patch("core.barcode_scanner.scanner_widget.qta.icon", return_value=QIcon()),
    ):
        return ScannerWidget(name=name)


def _set_run_checked(widget: object, checked: bool) -> None:
    """Set tbRun state without triggering emulator start/stop.

    Args:
        widget: Widget that exposes ``tbRun``.
        checked: Desired checked state.
    """
    tb_run = getattr(widget, "tbRun")
    tb_run.blockSignals(True)
    tb_run.setChecked(checked)
    tb_run.blockSignals(False)


def _layout_contains(layout: object, widget: object) -> bool:
    """Return whether ``widget`` is still present in a layout.

    Args:
        layout: Qt layout with ``count`` / ``itemAt``.
        widget: Widget to look for.

    Returns:
        True if the widget is still a layout child.
    """
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item is not None and item.widget() is widget:
            return True
    return False


class TestMainLineFieldRemoveApi(unittest.TestCase):
    """Remove API: devices, transporters, generators, and stale _device_data."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def setUp(self) -> None:
        """Create a main window and linked device/transport/generator widgets."""
        self.window = MainLineField()
        self.printer = PrinterWidget(name="PRN_1", port=9100)
        self.camera = CameraWidget(name="CAM_1", port=23)
        self.scanner = _make_scanner("SCAN_1")
        self.transporter = TransporterWidget()
        self.generator = GeneratorWidget()

        self.window._add_device(self.printer)
        self.window._add_device(self.camera)
        self.window._add_device(self.scanner)
        self.window._add_transport(self.transporter)
        self.window._add_generator(self.generator)
        self.transporter.setup_models(self.window._device_widgets)
        self.generator.setup_models(self.window._device_widgets)

    def tearDown(self) -> None:
        """Close the main window to release Qt resources."""
        self.window.close()

    def test_remove_stopped_printer_from_registry_and_layout(self) -> None:
        """Stopped printer is removed from ``_device_widgets`` and devices layout."""
        printer_id = id(self.printer)
        with patch.object(self.printer, "run") as mock_run:
            self.window._remove_device(self.printer)

        self.assertNotIn(printer_id, self.window._device_widgets)
        self.assertFalse(
            _layout_contains(self.window._devices_layout, self.printer)
        )
        mock_run.assert_called_with(False)

    def test_remove_stopped_camera_from_registry_and_layout(self) -> None:
        """Stopped camera is removed from ``_device_widgets`` and devices layout."""
        camera_id = id(self.camera)
        with patch.object(self.camera, "run") as mock_run:
            self.window._remove_device(self.camera)

        self.assertNotIn(camera_id, self.window._device_widgets)
        self.assertFalse(
            _layout_contains(self.window._devices_layout, self.camera)
        )
        mock_run.assert_called_with(False)

    def test_remove_stopped_scanner_from_registry_and_layout(self) -> None:
        """Stopped scanner is removed from ``_device_widgets`` and devices layout."""
        scanner_id = id(self.scanner)
        with (
            patch.object(self.scanner, "run") as mock_run,
            patch.object(self.window, "_sync_scanner_name_generator") as mock_sync,
        ):
            self.window._remove_device(self.scanner)

        self.assertNotIn(scanner_id, self.window._device_widgets)
        self.assertFalse(
            _layout_contains(self.window._devices_layout, self.scanner)
        )
        mock_run.assert_called_with(False)
        mock_sync.assert_called_once_with()

    def test_remove_transporter_from_registry(self) -> None:
        """Transporter is removed from ``_transporter_widgets``."""
        transport_id = id(self.transporter)
        with patch.object(self.transporter, "run") as mock_run:
            self.window._remove_transporter(self.transporter)

        self.assertNotIn(transport_id, self.window._transporter_widgets)
        mock_run.assert_called_with(False)

    def test_remove_generator_from_registry(self) -> None:
        """Generator is removed from ``_generator_widgets``."""
        generator_id = id(self.generator)
        with patch.object(self.generator, "run") as mock_run:
            self.window._remove_generator(self.generator)

        self.assertNotIn(generator_id, self.window._generator_widgets)
        mock_run.assert_called_with(False)

    def test_remove_device_clears_stale_keys_in_device_data(self) -> None:
        """After device removal, transporter/generator ``_device_data`` has no stale id."""
        printer_id = id(self.printer)
        self.assertIn(printer_id, self.transporter._device_data)
        self.assertIn(printer_id, self.generator._device_data)

        with patch.object(self.printer, "run"):
            self.window._remove_device(self.printer)

        self.assertNotIn(printer_id, self.transporter._device_data)
        self.assertNotIn(printer_id, self.generator._device_data)
        self.assertIn(id(self.camera), self.transporter._device_data)
        self.assertIn(id(self.scanner), self.transporter._device_data)

    def test_remove_device_clears_stale_keys_while_transporter_running(self) -> None:
        """Running transporter still drops removed device ids from ``_device_data``."""
        printer_id = id(self.printer)
        _set_run_checked(self.transporter, True)

        with patch.object(self.printer, "run"):
            self.window._remove_device(self.printer)

        self.assertNotIn(printer_id, self.transporter._device_data)
        self.assertTrue(self.transporter.tbRun.isChecked())

    def test_on_widget_delete_requested_routes_device(self) -> None:
        """``delete_requested`` from a device widget routes to ``_remove_device``."""
        with patch.object(self.window, "_remove_device") as mock_remove:
            self.printer.delete_requested.emit()
            QApplication.processEvents()

        mock_remove.assert_called_once_with(self.printer)

    def test_on_widget_delete_requested_routes_transporter(self) -> None:
        """``delete_requested`` from a transporter routes to ``_remove_transporter``."""
        with patch.object(self.window, "_remove_transporter") as mock_remove:
            self.transporter.delete_requested.emit()
            QApplication.processEvents()

        mock_remove.assert_called_once_with(self.transporter)

    def test_on_widget_delete_requested_routes_generator(self) -> None:
        """``delete_requested`` from a generator routes to ``_remove_generator``."""
        with patch.object(self.window, "_remove_generator") as mock_remove:
            self.generator.delete_requested.emit()
            QApplication.processEvents()

        mock_remove.assert_called_once_with(self.generator)


class TestWidgetDeleteClickedGuards(unittest.TestCase):
    """``_on_delete_clicked`` refuses running widgets and confirms when stopped."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def test_running_printer_shows_warning_and_does_not_emit(self) -> None:
        """Running printer shows warning and does not emit ``delete_requested``."""
        printer = PrinterWidget(name="PRN_RUN", port=9100)
        _set_run_checked(printer, True)
        handler = MagicMock()
        printer.delete_requested.connect(handler)

        with (
            patch(
                "core.printing.printer_widget.QMessageBox.warning"
            ) as mock_warning,
            patch(
                "core.printing.printer_widget.QMessageBox.question"
            ) as mock_question,
        ):
            printer._on_delete_clicked()

        mock_warning.assert_called_once()
        mock_question.assert_not_called()
        handler.assert_not_called()

    def test_stopped_printer_yes_emits_delete_requested(self) -> None:
        """Stopped printer with Yes confirmation emits ``delete_requested``."""
        printer = PrinterWidget(name="PRN_OK", port=9100)
        _set_run_checked(printer, False)
        handler = MagicMock()
        printer.delete_requested.connect(handler)

        with (
            patch(
                "core.printing.printer_widget.QMessageBox.warning"
            ) as mock_warning,
            patch(
                "core.printing.printer_widget.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ) as mock_question,
        ):
            printer._on_delete_clicked()

        mock_warning.assert_not_called()
        mock_question.assert_called_once()
        handler.assert_called_once()

    def test_stopped_printer_no_does_not_emit(self) -> None:
        """Stopped printer with No confirmation does not emit ``delete_requested``."""
        printer = PrinterWidget(name="PRN_NO", port=9100)
        handler = MagicMock()
        printer.delete_requested.connect(handler)

        with patch(
            "core.printing.printer_widget.QMessageBox.question",
            return_value=QMessageBox.StandardButton.No,
        ):
            printer._on_delete_clicked()

        handler.assert_not_called()

    def test_running_transporter_shows_warning_and_does_not_emit(self) -> None:
        """Running transporter shows warning and does not emit ``delete_requested``."""
        transporter = TransporterWidget()
        _set_run_checked(transporter, True)
        handler = MagicMock()
        transporter.delete_requested.connect(handler)

        with (
            patch(
                "core.transporting.transporter_widget.QMessageBox.warning"
            ) as mock_warning,
            patch(
                "core.transporting.transporter_widget.QMessageBox.question"
            ) as mock_question,
        ):
            transporter._on_delete_clicked()

        mock_warning.assert_called_once()
        mock_question.assert_not_called()
        handler.assert_not_called()

    def test_running_scanner_shows_warning_and_does_not_emit(self) -> None:
        """Running scanner shows warning and does not emit ``delete_requested``."""
        scanner = _make_scanner("SCAN_RUN")
        _set_run_checked(scanner, True)
        handler = MagicMock()
        scanner.delete_requested.connect(handler)

        with (
            patch(
                "core.barcode_scanner.scanner_widget.QMessageBox.warning"
            ) as mock_warning,
            patch(
                "core.barcode_scanner.scanner_widget.QMessageBox.question"
            ) as mock_question,
        ):
            scanner._on_delete_clicked()

        mock_warning.assert_called_once()
        mock_question.assert_not_called()
        handler.assert_not_called()


class TestClearUiClearsGenerators(unittest.TestCase):
    """Regression: ``clear_ui`` must stop and drop generator widgets."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def setUp(self) -> None:
        """Create a main window with one widget of each registry type."""
        self.window = MainLineField()
        self.printer = PrinterWidget(name="PRN_CLR", port=9100)
        self.transporter = TransporterWidget()
        self.generator = GeneratorWidget()
        self.window._add_device(self.printer)
        self.window._add_transport(self.transporter)
        self.window._add_generator(self.generator)

    def tearDown(self) -> None:
        """Close the main window to release Qt resources."""
        self.window.close()

    def test_clear_ui_clears_generator_widgets(self) -> None:
        """``clear_ui`` empties devices, transporters, and generators."""
        with (
            patch.object(self.printer, "run") as mock_printer_run,
            patch.object(self.transporter, "run") as mock_transport_run,
            patch.object(self.generator, "run") as mock_generator_run,
        ):
            self.window.clear_ui()

        self.assertEqual(self.window._device_widgets, {})
        self.assertEqual(self.window._transporter_widgets, {})
        self.assertEqual(self.window._generator_widgets, {})
        mock_printer_run.assert_called_with(False)
        mock_transport_run.assert_called_with(False)
        mock_generator_run.assert_called_with(False)


if __name__ == "__main__":
    unittest.main()
