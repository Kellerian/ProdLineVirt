"""Unit tests for canvas FlowLayout drag-reorder area."""

from __future__ import annotations

import sys
import unittest
from unittest import mock

from PySide6.QtCore import QPoint, Qt, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QWidget

from core.main_ui.canvas_area import CanvasDeviceArea
from core.main_ui.device_card import (
    DEVICE_DRAG_MIME_TYPE,
    DeviceDragPayload,
    DeviceZone,
    encode_device_drag_payload,
)
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget


def _ensure_qapplication() -> QApplication:
    """Return singleton ``QApplication`` for Qt widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class _StubDevice(QWidget):
    """Minimal canvas device exposing ``device_id``."""

    def __init__(self, device_id: str, width: int = 120, height: int = 80) -> None:
        super().__init__()
        self.device_id = device_id
        self._width = width
        self._height = height
        self.resize(width, height)

    def sizeHint(self) -> QSize:
        """Return fixed size so ``FlowLayout`` assigns non-zero geometry."""
        return QSize(self._width, self._height)


class TestCanvasDeviceArea(unittest.TestCase):
    """Canvas reorder API and zone guards."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def setUp(self) -> None:
        self.container = QWidget()
        self.container.resize(640, 480)
        self.area = CanvasDeviceArea(self.container)

    def tearDown(self) -> None:
        self.container.close()

    def test_add_widget_tracks_order(self) -> None:
        first = _StubDevice("dev-a")
        second = _StubDevice("dev-b")
        self.area.add_widget(first)
        self.area.add_widget(second)
        self.assertEqual(self.area.get_order(), ["dev-a", "dev-b"])

    def test_set_order_reorders_widgets(self) -> None:
        first = _StubDevice("dev-a")
        second = _StubDevice("dev-b")
        third = _StubDevice("dev-c")
        for widget in (first, second, third):
            self.area.add_widget(widget)

        self.area.set_order(["dev-c", "dev-a"])
        self.assertEqual(self.area.get_order(), ["dev-c", "dev-a", "dev-b"])

    def test_remove_widget_updates_order(self) -> None:
        first = _StubDevice("dev-a")
        second = _StubDevice("dev-b")
        self.area.add_widget(first)
        self.area.add_widget(second)
        self.area.remove_widget(first)
        self.assertEqual(self.area.get_order(), ["dev-b"])

    def test_rejects_sidebar_zone_drop(self) -> None:
        from PySide6.QtCore import QMimeData

        widget = _StubDevice("dev-a")
        self.area.add_widget(widget)
        widget.show()
        self.container.show()
        QApplication.processEvents()

        mime = QMimeData()
        payload = DeviceDragPayload(device_id="dev-a", zone=DeviceZone.SIDEBAR)
        mime.setData(DEVICE_DRAG_MIME_TYPE, encode_device_drag_payload(payload))

        enter = QDragEnterEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        handled = self.area.eventFilter(self.container, enter)
        self.assertFalse(handled)
        self.assertFalse(enter.isAccepted())

    def test_reorder_by_device_id_moves_widget(self) -> None:
        first = _StubDevice("dev-a")
        second = _StubDevice("dev-b")
        self.area.add_widget(first)
        self.area.add_widget(second)
        self.area._reorder_by_device_id("dev-b", 0)
        self.assertEqual(self.area.get_order(), ["dev-b", "dev-a"])

    def test_reorder_by_device_id_moves_downward(self) -> None:
        """Insert-before index 2 places dev-a between dev-b and dev-c."""
        first = _StubDevice("dev-a")
        second = _StubDevice("dev-b")
        third = _StubDevice("dev-c")
        for widget in (first, second, third):
            self.area.add_widget(widget)
        self.area._reorder_by_device_id("dev-a", 2)
        self.assertEqual(self.area.get_order(), ["dev-b", "dev-a", "dev-c"])

    def test_reorder_middle_downward_uses_insert_index_at(self) -> None:
        """Geometry-derived insert index + downward move yields insert-before slot."""
        widgets = [_StubDevice(f"dev-{label}", width=200, height=100) for label in ("a", "b", "c")]
        for widget in widgets:
            self.area.add_widget(widget)
        self.container.show()
        for widget in widgets:
            widget.show()
        QApplication.processEvents()
        self.area.flow_layout.setGeometry(self.container.rect())
        QApplication.processEvents()

        third = widgets[2]
        third_rect = third.geometry()
        between = QPoint(third_rect.left() + 10, third_rect.center().y())
        insert_index = self.area.flow_layout.insert_index_at(between)
        self.assertEqual(insert_index, 2)
        self.area._reorder_by_device_id("dev-a", insert_index)
        self.assertEqual(self.area.get_order(), ["dev-b", "dev-a", "dev-c"])

    def test_reorder_by_device_id_moves_to_end(self) -> None:
        """Drop-to-end uses insert_index == len(widgets); move must append."""
        first = _StubDevice("dev-a")
        second = _StubDevice("dev-b")
        third = _StubDevice("dev-c")
        for widget in (first, second, third):
            self.area.add_widget(widget)
        self.area._reorder_by_device_id("dev-a", 3)
        self.assertEqual(self.area.get_order(), ["dev-b", "dev-c", "dev-a"])

    def test_insert_index_at_returns_len_for_drop_past_last(self) -> None:
        """``insert_index_at`` past the last card returns ``len(widgets)``."""
        widgets = [_StubDevice(f"dev-{index}", width=200, height=100) for index in range(3)]
        for widget in widgets:
            self.area.add_widget(widget)
        self.container.show()
        for widget in widgets:
            widget.show()
        QApplication.processEvents()
        self.area.flow_layout.setGeometry(self.container.rect())
        QApplication.processEvents()

        last = widgets[-1]
        past_last = QPoint(last.geometry().right() + 50, last.geometry().center().y())
        self.assertEqual(self.area.flow_layout.insert_index_at(past_last), 3)

    def test_move_widget_allows_append_index(self) -> None:
        """``move_widget`` accepts ``to_index == count`` for drop-to-end."""
        first = _StubDevice("dev-a")
        second = _StubDevice("dev-b")
        third = _StubDevice("dev-c")
        for widget in (first, second, third):
            self.area.add_widget(widget)
        layout = self.area.flow_layout
        self.assertTrue(layout.move_widget(0, layout.count()))
        self.assertEqual(self.area.get_order(), ["dev-b", "dev-c", "dev-a"])

    def test_text_mime_drop_is_ignored(self) -> None:
        from PySide6.QtCore import QMimeData

        first = _StubDevice("dev-a")
        second = _StubDevice("dev-b")
        self.area.add_widget(first)
        self.area.add_widget(second)

        mime = QMimeData()
        mime.setText("code-item")

        drop = QDropEvent(
            QPoint(5, 5),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        handled = self.area.eventFilter(self.container, drop)
        self.assertFalse(handled)
        self.assertFalse(drop.isAccepted())
        self.assertEqual(self.area.get_order(), ["dev-a", "dev-b"])

    def test_drop_on_descendant_reorders(self) -> None:
        from PySide6.QtCore import QMimeData

        first = _StubDevice("dev-a", width=200, height=100)
        second = _StubDevice("dev-b", width=200, height=100)
        self.area.add_widget(first)
        self.area.add_widget(second)
        code_list = QWidget(first)
        code_list.resize(180, 60)
        code_list.show()
        first.show()
        second.show()
        self.container.show()
        QApplication.processEvents()

        mime = QMimeData()
        payload = DeviceDragPayload(device_id="dev-b", zone=DeviceZone.CANVAS)
        mime.setData(DEVICE_DRAG_MIME_TYPE, encode_device_drag_payload(payload))

        drop = QDropEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        with mock.patch.object(
            self.area, "_insert_index_for_position", return_value=0
        ):
            handled = self.area.eventFilter(code_list, drop)
        self.assertTrue(handled)
        self.assertTrue(drop.isAccepted())
        self.assertEqual(self.area.get_order(), ["dev-b", "dev-a"])

    def test_rejects_sidebar_zone_drop_on_canvas(self) -> None:
        from PySide6.QtCore import QMimeData

        widget = _StubDevice("dev-a")
        self.area.add_widget(widget)
        widget.show()
        self.container.show()
        QApplication.processEvents()

        mime = QMimeData()
        payload = DeviceDragPayload(device_id="dev-a", zone=DeviceZone.SIDEBAR)
        mime.setData(DEVICE_DRAG_MIME_TYPE, encode_device_drag_payload(payload))

        drop = QDropEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        handled = self.area.eventFilter(self.container, drop)
        self.assertFalse(handled)
        self.assertFalse(drop.isAccepted())
        self.assertEqual(self.area.get_order(), ["dev-a"])

    def test_accepts_canvas_zone_drop_and_reorders(self) -> None:
        from PySide6.QtCore import QMimeData

        first = _StubDevice("dev-a", width=200, height=100)
        second = _StubDevice("dev-b", width=200, height=100)
        self.area.add_widget(first)
        self.area.add_widget(second)

        mime = QMimeData()
        payload = DeviceDragPayload(device_id="dev-b", zone=DeviceZone.CANVAS)
        mime.setData(DEVICE_DRAG_MIME_TYPE, encode_device_drag_payload(payload))

        drop = QDropEvent(
            QPoint(5, 5),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        with mock.patch.object(
            self.area, "_insert_index_for_position", return_value=0
        ):
            handled = self.area.eventFilter(self.container, drop)
        self.assertTrue(handled)
        self.assertTrue(drop.isAccepted())
        self.assertEqual(self.area.get_order(), ["dev-b", "dev-a"])

    def test_wrap_layout_survives_resize(self) -> None:
        widgets = [_StubDevice(f"dev-{index}", width=180, height=90) for index in range(4)]
        for widget in widgets:
            self.area.add_widget(widget)
        self.container.show()
        for widget in widgets:
            widget.show()
        QApplication.processEvents()

        self.container.resize(320, 480)
        QApplication.processEvents()
        self.area.flow_layout.setGeometry(self.container.rect())
        QApplication.processEvents()

        self.assertEqual(len(self.area.get_order()), 4)
        self.assertEqual(self.area.flow_layout.count(), 4)


class TestMainLineFieldCanvasIntegration(unittest.TestCase):
    """Minimal ``MainLineField`` hook for canvas area."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_add_device_uses_canvas_area(self) -> None:
        from core.main_ui.line_emul import MainLineField

        window = MainLineField()
        printer = PrinterWidget(name="PRN_CANVAS", port=9100, device_id="printer-canvas")
        camera = CameraWidget(name="CAM_CANVAS", port=23, device_id="camera-canvas")

        window._add_device(printer)
        window._add_device(camera)
        self.assertEqual(window.get_canvas_device_order(), ["printer-canvas", "camera-canvas"])

        window.set_canvas_device_order(["camera-canvas", "printer-canvas"])
        self.assertEqual(window.get_canvas_device_order(), ["camera-canvas", "printer-canvas"])
        window.close()


if __name__ == "__main__":
    unittest.main()
