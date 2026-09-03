"""Unit tests for reorderable sidebar layout."""

from __future__ import annotations

import sys
import unittest

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QWidget

from core.generator.generator_widget import GeneratorWidget
from core.main_ui.device_card import (
    DEVICE_DRAG_MIME_TYPE,
    DeviceDragPayload,
    DeviceZone,
    encode_device_drag_payload,
)
from core.main_ui.sidebar_layout import SidebarLayout
from core.transporting.transporter_widget import TransporterWidget


def _ensure_qapplication() -> QApplication:
    """Return singleton ``QApplication`` for Qt widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestSidebarLayoutOrderApi(unittest.TestCase):
    """SidebarLayout add/remove/order API."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def setUp(self) -> None:
        self.sidebar = SidebarLayout()
        self.transporter = TransporterWidget(device_id="id-transporter-1")
        self.generator = GeneratorWidget(device_id="id-generator-1")

    def tearDown(self) -> None:
        self.sidebar.close()

    def test_add_widget_and_get_order(self) -> None:
        """``get_order`` reflects append order."""
        self.sidebar.add_widget(self.transporter)
        self.sidebar.add_widget(self.generator)
        self.assertEqual(
            self.sidebar.get_order(),
            ["id-transporter-1", "id-generator-1"],
        )

    def test_set_order_reorders_widgets(self) -> None:
        """``set_order`` rearranges transporter and generator."""
        self.sidebar.add_widget(self.transporter)
        self.sidebar.add_widget(self.generator)
        self.sidebar.set_order(["id-generator-1", "id-transporter-1"])
        self.assertEqual(
            self.sidebar.get_order(),
            ["id-generator-1", "id-transporter-1"],
        )

    def test_remove_widget_updates_order(self) -> None:
        """``remove_widget`` drops the widget from ``get_order``."""
        self.sidebar.add_widget(self.transporter)
        self.sidebar.add_widget(self.generator)
        self.sidebar.remove_widget(self.transporter)
        self.assertEqual(self.sidebar.get_order(), ["id-generator-1"])

    def test_add_widget_requires_device_id(self) -> None:
        """Widgets without ``device_id`` are rejected."""
        plain = QWidget()
        with self.assertRaises(TypeError):
            self.sidebar.add_widget(plain)
        plain.close()


class TestSidebarLayoutDropGuard(unittest.TestCase):
    """Zone guard and reorder via simulated drops."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def setUp(self) -> None:
        self.sidebar = SidebarLayout()
        self.transporter = TransporterWidget(device_id="id-transporter-1")
        self.generator = GeneratorWidget(device_id="id-generator-1")
        self.sidebar.add_widget(self.transporter)
        self.sidebar.add_widget(self.generator)
        self.sidebar.resize(300, 400)
        self.sidebar.show()

    def tearDown(self) -> None:
        self.sidebar.close()

    def _mime_for(self, payload: DeviceDragPayload) -> object:
        from PySide6.QtCore import QMimeData

        mime = QMimeData()
        mime.setData(DEVICE_DRAG_MIME_TYPE, encode_device_drag_payload(payload))
        return mime

    def test_rejects_canvas_zone_drag_enter(self) -> None:
        """Cross-zone canvas payload is ignored on drag enter."""
        mime = self._mime_for(
            DeviceDragPayload(device_id="id-transporter-1", zone=DeviceZone.CANVAS)
        )
        event = QDragEnterEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.sidebar.dragEnterEvent(event)
        self.assertFalse(event.isAccepted())

    def test_drop_reorders_sidebar_widgets(self) -> None:
        """Same-zone drop moves transporter below generator."""
        mime = self._mime_for(
            DeviceDragPayload(device_id="id-transporter-1", zone=DeviceZone.SIDEBAR)
        )
        generator_bottom = self.generator.mapTo(
            self.sidebar, self.generator.rect().bottomLeft()
        )
        drop_y = generator_bottom.y() + 4
        drop = QDropEvent(
            QPoint(10, drop_y),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.sidebar.dropEvent(drop)
        self.assertTrue(drop.isAccepted())
        self.assertEqual(
            self.sidebar.get_order(),
            ["id-generator-1", "id-transporter-1"],
        )

    def test_drop_on_nested_child_reorders_via_event_filter(self) -> None:
        """Drop routed through a nested child widget must not crash and must reorder."""
        from PySide6.QtGui import QDragMoveEvent

        mime = self._mime_for(
            DeviceDragPayload(device_id="id-transporter-1", zone=DeviceZone.SIDEBAR)
        )
        child = self.generator.findChild(QWidget, "leName")
        if child is None:
            self.skipTest("Generator leName widget not found")
        generator_bottom = self.generator.mapTo(
            self.sidebar, self.generator.rect().bottomLeft()
        )
        drop_y = generator_bottom.y() + 4
        local_point = child.mapFrom(self.sidebar, QPoint(10, drop_y))
        move = QDragMoveEvent(
            local_point,
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.sidebar.eventFilter(child, move)
        self.assertTrue(move.isAccepted())

        drop = QDropEvent(
            local_point,
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        handled = self.sidebar.eventFilter(child, drop)
        self.assertTrue(handled)
        self.assertTrue(drop.isAccepted())
        self.assertEqual(
            self.sidebar.get_order(),
            ["id-generator-1", "id-transporter-1"],
        )


class TestMainLineFieldSidebarIntegration(unittest.TestCase):
    """Minimal ``MainLineField`` hook for sidebar layout."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_add_sidebar_devices_uses_sidebar_layout(self) -> None:
        from core.main_ui.line_emul import MainLineField

        window = MainLineField()
        transporter = TransporterWidget(device_id="transporter-sidebar")
        generator = GeneratorWidget(device_id="generator-sidebar")

        window._add_transport(transporter)
        window._add_generator(generator)
        self.assertEqual(
            window.get_sidebar_device_order(),
            ["transporter-sidebar", "generator-sidebar"],
        )

        window.set_sidebar_device_order(["generator-sidebar", "transporter-sidebar"])
        self.assertEqual(
            window.get_sidebar_device_order(),
            ["generator-sidebar", "transporter-sidebar"],
        )
        window.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
