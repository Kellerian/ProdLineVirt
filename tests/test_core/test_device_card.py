"""Unit tests for device card drag mime and zone guards."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QPoint, QPointF, Qt, QEvent
from PySide6.QtGui import QDrag, QDragEnterEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLineEdit, QToolButton, QWidget

from core.main_ui.device_card import (
    DEVICE_DRAG_MIME_TYPE,
    DeviceCardHeader,
    DeviceCardMixin,
    DeviceDragPayload,
    DeviceGripHandle,
    DeviceZone,
    accept_device_drag_enter,
    accept_device_drop,
    can_accept_device_drop,
    decode_device_drag_payload,
    device_drag_payload_from_mime,
    encode_device_drag_payload,
    is_same_zone_drop,
)
from core.barcode_scanner.scanner_widget import ScannerWidget
from core.generator.generator_widget import GeneratorWidget
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from core.transporting.transporter_widget import TransporterWidget


def _ensure_qapplication() -> QApplication:
    """Return singleton ``QApplication`` for Qt widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _make_scanner(name: str = "SCAN_1") -> ScannerWidget:
    """Create ``ScannerWidget`` with COM list and icons mocked out."""
    from PySide6.QtGui import QIcon

    with (
        patch(
            "core.barcode_scanner.scanner_widget.list_available_ports",
            return_value=[],
        ),
        patch("core.barcode_scanner.scanner_widget.qta.icon", return_value=QIcon()),
    ):
        return ScannerWidget(name=name)


class TestDeviceDragPayload(unittest.TestCase):
    """Encode/decode and zone guard helpers."""

    def test_roundtrip_payload(self) -> None:
        payload = DeviceDragPayload(device_id="id-printer-1", zone=DeviceZone.CANVAS)
        encoded = encode_device_drag_payload(payload)
        decoded = decode_device_drag_payload(encoded)
        self.assertEqual(decoded, payload)

    def test_decode_rejects_invalid_json(self) -> None:
        self.assertIsNone(decode_device_drag_payload(b"not-json"))

    def test_decode_rejects_unknown_zone(self) -> None:
        raw = b'{"device_id":"x","zone":"invalid"}'
        self.assertIsNone(decode_device_drag_payload(raw))

    def test_same_zone_drop_allowed(self) -> None:
        self.assertTrue(is_same_zone_drop(DeviceZone.CANVAS, DeviceZone.CANVAS))
        self.assertFalse(is_same_zone_drop(DeviceZone.SIDEBAR, DeviceZone.CANVAS))

    def test_can_accept_device_drop_rejects_cross_zone(self) -> None:
        from PySide6.QtCore import QMimeData

        mime = QMimeData()
        payload = DeviceDragPayload(device_id="dev-1", zone=DeviceZone.SIDEBAR)
        mime.setData(DEVICE_DRAG_MIME_TYPE, encode_device_drag_payload(payload))
        self.assertFalse(can_accept_device_drop(mime, DeviceZone.CANVAS))
        self.assertTrue(can_accept_device_drop(mime, DeviceZone.SIDEBAR))


class _StubDropTarget(QWidget):
    """Minimal drop target exercising zone guard helpers."""

    def __init__(self, zone: DeviceZone) -> None:
        super().__init__()
        self._zone = zone
        self.accepted_payload: DeviceDragPayload | None = None
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        accept_device_drag_enter(event, self._zone)

    def dropEvent(self, event: QDropEvent) -> None:
        self.accepted_payload = accept_device_drop(event, self._zone)


class TestDeviceCardWidgets(unittest.TestCase):
    """Widget-level device card chrome."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_grip_drag_starts_with_device_mime(self) -> None:
        """Grip mouse drag emits mime with ``device_id`` and ``zone``."""
        grip = DeviceGripHandle("grip-drag-id", DeviceZone.SIDEBAR)
        grip.resize(28, 28)
        captured_mime: list[object] = []

        def fake_exec(
            drag_self: QDrag,
            *_args: object,
            **_kwargs: object,
        ) -> Qt.DropAction:
            captured_mime.append(drag_self.mimeData())
            return Qt.DropAction.IgnoreAction

        with patch.object(QDrag, "exec", fake_exec):
            press_pos = QPointF(10, 10)
            press = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                press_pos,
                press_pos,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            grip.mousePressEvent(press)
            drag_distance = QApplication.startDragDistance() + 1
            move_pos = QPointF(10 + drag_distance, 10)
            move = QMouseEvent(
                QEvent.Type.MouseMove,
                move_pos,
                move_pos,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            grip.mouseMoveEvent(move)

        self.assertEqual(len(captured_mime), 1)
        decoded = device_drag_payload_from_mime(captured_mime[0])
        self.assertEqual(
            decoded,
            DeviceDragPayload(device_id="grip-drag-id", zone=DeviceZone.SIDEBAR),
        )
        grip.close()

    def test_grip_does_not_drag_below_move_threshold(self) -> None:
        """Grip ignores pointer movement below ``QApplication.startDragDistance()``."""
        grip = DeviceGripHandle("grip-threshold", DeviceZone.CANVAS)
        grip.resize(28, 28)
        origin = QPointF(10.0, 10.0)
        with patch.object(grip, "_start_drag") as mock_start_drag:
            press = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                origin,
                origin,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            grip.mousePressEvent(press)
            move = QMouseEvent(
                QEvent.Type.MouseMove,
                QPointF(origin.x() + 1.0, origin.y() + 1.0),
                QPointF(origin.x() + 1.0, origin.y() + 1.0),
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            grip.mouseMoveEvent(move)
            mock_start_drag.assert_not_called()
        grip.close()

    def test_non_grip_title_widget_does_not_start_device_drag(self) -> None:
        """Mouse drag on title slot must not invoke grip ``QDrag``."""
        header = DeviceCardHeader("dev-1", DeviceZone.CANVAS)
        title = QLineEdit(header)
        header.add_title_widget(title)
        header.show()
        title.show()
        QApplication.processEvents()
        origin = QPointF(2.0, 2.0)
        threshold = QApplication.startDragDistance()
        with patch.object(header.grip, "_start_drag") as mock_start_drag:
            press = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                origin,
                origin,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            title.mousePressEvent(press)
            move = QMouseEvent(
                QEvent.Type.MouseMove,
                QPointF(origin.x() + float(threshold + 5), origin.y()),
                QPointF(origin.x() + float(threshold + 5), origin.y()),
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            title.mouseMoveEvent(move)
            mock_start_drag.assert_not_called()
        header.close()

    def test_grip_start_drag_builds_expected_mime(self) -> None:
        """``DeviceGripHandle._start_drag`` sets device mime payload."""
        grip = DeviceGripHandle("direct-drag-id", DeviceZone.CANVAS)
        captured_mime: list[object] = []

        def fake_exec(
            drag_self: QDrag,
            *_args: object,
            **_kwargs: object,
        ) -> Qt.DropAction:
            captured_mime.append(drag_self.mimeData())
            return Qt.DropAction.IgnoreAction

        with patch.object(QDrag, "exec", fake_exec):
            grip._start_drag()

        self.assertEqual(len(captured_mime), 1)
        decoded = device_drag_payload_from_mime(captured_mime[0])
        self.assertEqual(
            decoded,
            DeviceDragPayload(device_id="direct-drag-id", zone=DeviceZone.CANVAS),
        )
        grip.close()

    def test_header_exposes_title_slot_and_delete_signal(self) -> None:
        received: list[bool] = []
        header = DeviceCardHeader("dev-1", DeviceZone.CANVAS)
        header.delete_clicked.connect(lambda: received.append(True))
        title = QLineEdit(header)
        header.add_title_widget(title)
        header.delete_button.click()
        self.assertEqual(received, [True])
        header.close()

    def test_mixin_mount_moves_row_widgets_and_sets_device_type(self) -> None:
        class Card(QWidget, DeviceCardMixin):
            tbDelete: QToolButton

        card = Card()
        card.setObjectName("Form")
        row = QHBoxLayout(card)
        name = QLineEdit(card)
        name.setObjectName("leName")
        run_btn = QToolButton(card)
        delete_btn = QToolButton(card)
        delete_btn.setObjectName("tbDelete")
        card.tbDelete = delete_btn
        row.addWidget(name, 4)
        row.addWidget(run_btn, 1)
        row.addWidget(delete_btn, 0)
        header = card.mount_device_card_header(
            device_id="printer-mount",
            device_type="printer",
            zone=DeviceZone.CANVAS,
            row_layout=row,
            delete_button=delete_btn,
        )
        self.assertIs(card._device_card_header, header)
        self.assertEqual(card.property("deviceType"), "printer")
        self.assertEqual(row.count(), 1)
        self.assertIs(row.itemAt(0).widget(), header)
        self.assertEqual(header.title_layout.count(), 2)
        self.assertIs(card.tbDelete, header.delete_button)
        card.close()

    def test_stub_drop_target_accepts_same_zone(self) -> None:
        from PySide6.QtCore import QMimeData

        target = _StubDropTarget(DeviceZone.CANVAS)
        mime = QMimeData()
        payload = DeviceDragPayload(device_id="dev-1", zone=DeviceZone.CANVAS)
        mime.setData(DEVICE_DRAG_MIME_TYPE, encode_device_drag_payload(payload))

        enter = QDragEnterEvent(
            QPoint(0, 0),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        target.dragEnterEvent(enter)
        self.assertTrue(enter.isAccepted())

        drop = QDropEvent(
            QPoint(0, 0),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        target.dropEvent(drop)
        self.assertTrue(drop.isAccepted())
        self.assertEqual(target.accepted_payload, payload)
        target.close()

    def test_stub_drop_target_rejects_cross_zone(self) -> None:
        from PySide6.QtCore import QMimeData

        target = _StubDropTarget(DeviceZone.CANVAS)
        mime = QMimeData()
        payload = DeviceDragPayload(device_id="dev-1", zone=DeviceZone.SIDEBAR)
        mime.setData(DEVICE_DRAG_MIME_TYPE, encode_device_drag_payload(payload))

        enter = QDragEnterEvent(
            QPoint(0, 0),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        target.dragEnterEvent(enter)
        self.assertFalse(enter.isAccepted())

        drop = QDropEvent(
            QPoint(0, 0),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        target.dropEvent(drop)
        self.assertFalse(drop.isAccepted())
        self.assertIsNone(target.accepted_payload)
        target.close()


class TestPrinterWidgetDeviceCardIntegration(unittest.TestCase):
    """``PrinterWidget`` integration with shared device card chrome."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_printer_mounts_header_with_canvas_zone_and_delete(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        device_id = "printer-card-test"
        printer = PrinterWidget(name="PRN_CARD", port=9100, device_id=device_id)

        self.assertIsNotNone(printer._device_header)
        self.assertEqual(printer.property("deviceType"), "printer")
        self.assertEqual(printer._device_header.grip.zone, DeviceZone.CANVAS)
        self.assertEqual(printer._device_header.grip.device_id, device_id)
        self.assertIs(printer.tbDelete, printer._device_header.delete_button)

        handler = MagicMock()
        printer.delete_requested.connect(handler)
        with patch(
            "core.printing.printer_widget.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            printer.tbDelete.click()

        handler.assert_called_once()
        printer.close()

    def test_printer_advanced_collapsed_by_default_and_toggle(self) -> None:
        """Advanced panel starts collapsed; toggle and set_advanced_expanded work."""
        printer = PrinterWidget(name="PRN_ADV", port=9100)
        printer.show()

        self.assertFalse(printer.is_advanced_expanded())
        self.assertTrue(printer.wAdvanced.isHidden())

        printer.set_advanced_expanded(True)
        self.assertTrue(printer.is_advanced_expanded())
        self.assertFalse(printer.wAdvanced.isHidden())
        self.assertTrue(printer.tbAdvanced.isChecked())

        printer.tbAdvanced.click()
        self.assertFalse(printer.is_advanced_expanded())
        self.assertTrue(printer.wAdvanced.isHidden())

        options = printer.options()
        self.assertFalse(options.advanced_expanded)
        printer.set_advanced_expanded(True)
        self.assertTrue(printer.options().advanced_expanded)
        printer.close()

    def test_printer_queue_visible_when_advanced_collapsed(self) -> None:
        """Code queue remains visible when advanced section is collapsed."""
        printer = PrinterWidget(name="PRN_Q", port=9100)
        printer.show()
        self.assertFalse(printer.lstData.isHidden())
        self.assertTrue(printer.wAdvanced.isHidden())
        printer.close()


class TestDeviceWidgetAdvancedPanel(unittest.TestCase):
    """Collapsible advanced panel on camera, scanner, transporter, generator."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def _widget_cases(self) -> list[tuple[str, object]]:
        """Return ``(label, widget)`` pairs for advanced-panel assertions."""
        return [
            ("camera", CameraWidget(name="CAM_ADV", port=10001)),
            ("scanner", _make_scanner("SCAN_ADV")),
            ("transporter", TransporterWidget()),
            ("generator", GeneratorWidget()),
        ]

    def test_advanced_collapsed_by_default_and_toggle(self) -> None:
        """Advanced panel starts collapsed; toggle and set_advanced_expanded work."""
        for label, widget in self._widget_cases():
            with self.subTest(widget=label):
                widget.show()

                self.assertFalse(widget.is_advanced_expanded())
                self.assertTrue(widget.wAdvanced.isHidden())

                widget.set_advanced_expanded(True)
                self.assertTrue(widget.is_advanced_expanded())
                self.assertFalse(widget.wAdvanced.isHidden())
                self.assertTrue(widget.tbAdvanced.isChecked())

                widget.tbAdvanced.click()
                self.assertFalse(widget.is_advanced_expanded())
                self.assertTrue(widget.wAdvanced.isHidden())

                options = widget.options()
                self.assertFalse(options.advanced_expanded)
                widget.set_advanced_expanded(True)
                self.assertTrue(widget.options().advanced_expanded)
                widget.close()

    def test_scanner_device_id_matches_header_after_init(self) -> None:
        """New scanner must use one generated id for mount and options()."""
        scanner = _make_scanner("SCAN_ID")
        self.assertEqual(scanner._device_header.grip.device_id, scanner.device_id)
        self.assertEqual(scanner.options().device_id, scanner.device_id)
        scanner.close()


if __name__ == "__main__":
    unittest.main()
