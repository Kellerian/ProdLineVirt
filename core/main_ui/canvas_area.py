"""Canvas device area with FlowLayout drag-reorder for Line Emulator."""

from __future__ import annotations

from PySide6.QtCore import QChildEvent, QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QScrollArea, QWidget

from core.main_ui.device_card import (
    DeviceZone,
    accept_device_drag_enter,
    accept_device_drag_move,
    accept_device_drop,
)
from core.main_ui.flow_layout import FlowLayout


class CanvasDeviceArea(QObject):
    """FlowLayout host for canvas devices with grip-based drag reorder.

    Accepts drops only from ``DeviceZone.CANVAS`` mime payloads. Sidebar device
    drags and non-device mimes are ignored so code-queue DnD stays separate.
    """

    def __init__(self, container: QWidget, *, spacing: int = 6) -> None:
        """Attach a reorderable flow layout to ``container``.

        Args:
            container: Host widget (``scaDevices`` in ``MainLineField``).
            spacing: Horizontal and vertical spacing between cards.
        """
        super().__init__(container)
        self._container = container
        self._drop_filter_targets: set[QWidget] = set()
        self._container.setAcceptDrops(True)
        self._layout = FlowLayout(container, spacing=spacing)
        container.setLayout(self._layout)
        self._drop_indicator = QFrame(container)
        self._drop_indicator.setObjectName("canvasDropIndicator")
        self._drop_indicator.setFixedHeight(3)
        self._drop_indicator.setStyleSheet("background-color: #f0b321;")
        self._drop_indicator.hide()
        self._container.installEventFilter(self)
        self._attach_scroll_viewport(container)

    @property
    def flow_layout(self) -> FlowLayout:
        """Underlying auto-wrap layout."""
        return self._layout

    def add_widget(self, widget: QWidget) -> None:
        """Append a canvas device widget and enable drop handling on it.

        Args:
            widget: Device widget exposing ``device_id``.

        Raises:
            ValueError: When ``widget`` has no ``device_id`` attribute.
        """
        device_id = getattr(widget, "device_id", None)
        if not isinstance(device_id, str) or not device_id:
            raise ValueError("Canvas device widget must expose non-empty device_id")
        self._layout.addWidget(widget)
        self._install_drop_filters(widget)
        self.relayout()

    def relayout(self) -> None:
        """Re-run flow geometry when the container has a valid size."""
        rect = self._container.rect()
        if rect.width() > 0 and rect.height() > 0:
            self._layout.setGeometry(rect)
        self._container.updateGeometry()
        self._container.update()

    def remove_widget(self, widget: QWidget) -> None:
        """Remove ``widget`` from the flow layout.

        Args:
            widget: Device widget previously added via ``add_widget``.
        """
        self._remove_drop_filters(widget)
        self._layout.remove_widget(widget)

    def get_order(self) -> list[str]:
        """Return ``device_id`` values in current visual flow order."""
        order: list[str] = []
        for widget in self._layout.ordered_widgets():
            device_id = getattr(widget, "device_id", None)
            if isinstance(device_id, str) and device_id:
                order.append(device_id)
        return order

    def set_order(self, device_ids: list[str]) -> None:
        """Reorder widgets to match ``device_ids``.

        Unknown ids are skipped; widgets not listed keep their relative order
        and are appended after the requested sequence.

        Args:
            device_ids: Desired canvas order by stable ``device_id``.
        """
        widgets_by_id: dict[str, QWidget] = {}
        for widget in self._layout.ordered_widgets():
            device_id = getattr(widget, "device_id", None)
            if isinstance(device_id, str) and device_id:
                widgets_by_id[device_id] = widget

        ordered: list[QWidget] = []
        seen: set[str] = set()
        for device_id in device_ids:
            widget = widgets_by_id.get(device_id)
            if widget is None:
                continue
            ordered.append(widget)
            seen.add(device_id)
        for widget in self._layout.ordered_widgets():
            device_id = getattr(widget, "device_id", None)
            if isinstance(device_id, str) and device_id and device_id not in seen:
                ordered.append(widget)

        if not ordered:
            return

        self._layout.set_widget_order(ordered)
        self._refresh_layout()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Route drag events from the container and device cards to reorder logic."""
        event_type = event.type()
        if event_type == QEvent.Type.ChildAdded:
            child_event = event
            if isinstance(child_event, QChildEvent):
                child = child_event.child()
                if isinstance(child, QWidget) and child is not self._container:
                    self._install_drop_filters(child)
            return False
        if event_type not in (
            QEvent.Type.DragEnter,
            QEvent.Type.DragMove,
            QEvent.Type.DragLeave,
            QEvent.Type.Drop,
        ):
            return False
        if not isinstance(
            event,
            (QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, QDropEvent),
        ):
            return False

        if isinstance(event, QDragLeaveEvent):
            self._hide_drop_indicator()
            return False

        if isinstance(event, QDragEnterEvent):
            accept_device_drag_enter(event, DeviceZone.CANVAS)
            return event.isAccepted()

        if isinstance(event, QDragMoveEvent):
            if not accept_device_drag_move(event, DeviceZone.CANVAS):
                self._hide_drop_indicator()
                return False
            drop_pos = self._event_position_in_container(watched, event)
            insert_index = self._insert_index_for_position(drop_pos)
            self._show_drop_indicator(insert_index)
            return True

        self._hide_drop_indicator()
        payload = accept_device_drop(event, DeviceZone.CANVAS)
        if payload is None:
            return False
        drop_pos = self._event_position_in_container(watched, event)
        insert_index = self._insert_index_for_position(drop_pos)
        self._reorder_by_device_id(payload.device_id, insert_index)
        return True

    def _event_position_in_container(
        self, watched: QObject, event: QDragMoveEvent | QDropEvent
    ) -> QPoint:
        """Map a drag/drop event position into ``container`` coordinates."""
        if watched is self._container:
            return event.position().toPoint()
        if isinstance(watched, QWidget):
            global_pos = watched.mapToGlobal(event.position().toPoint())
            return self._container.mapFromGlobal(global_pos)
        return event.position().toPoint()

    def _attach_scroll_viewport(self, container: QWidget) -> None:
        """Route drops through the parent ``QScrollArea`` viewport when present."""
        parent = container.parentWidget()
        if not isinstance(parent, QScrollArea):
            return
        viewport = parent.viewport()
        if viewport is None or viewport in self._drop_filter_targets:
            return
        viewport.setAcceptDrops(True)
        viewport.installEventFilter(self)
        self._drop_filter_targets.add(viewport)

    def _insert_index_for_position(self, pos: QPoint) -> int:
        """Return layout insert index for a point in container coordinates."""
        return self._layout.insert_index_at(pos)

    def _find_widget(self, device_id: str) -> QWidget | None:
        """Return the canvas widget for ``device_id``, if present."""
        for widget in self._layout.ordered_widgets():
            if getattr(widget, "device_id", None) == device_id:
                return widget
        return None

    def _reorder_by_device_id(self, device_id: str, insert_index: int) -> None:
        """Move the widget identified by ``device_id`` to ``insert_index``.

        ``insert_index`` follows insert-before semantics (same as
        ``FlowLayout.insert_index_at`` and ``SidebarLayout._insert_index_at``).
        When the source lies before the target, decrement after pop adjustment
        (see ``SidebarLayout._move_widget_to_index``).
        """
        widget = self._find_widget(device_id)
        if widget is None:
            return
        current_index = self._layout.index_of_widget(widget)
        if current_index < 0:
            return
        if current_index < insert_index:
            insert_index -= 1
        if current_index == insert_index:
            return
        if not self._layout.move_widget(current_index, insert_index):
            return
        self._refresh_layout()

    def _install_drop_filters(self, widget: QWidget) -> None:
        """Enable device reorder drop routing on ``widget`` and descendants."""
        if widget is self._container:
            widget.setAcceptDrops(True)
            return
        if widget.objectName() == "deviceCardGrip":
            return
        if widget in self._drop_filter_targets:
            return
        self._drop_filter_targets.add(widget)
        widget.setAcceptDrops(True)
        widget.installEventFilter(self)
        for child in widget.findChildren(
            QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly
        ):
            self._install_drop_filters(child)

    def _remove_drop_filters(self, widget: QWidget) -> None:
        """Remove device reorder drop routing from ``widget`` and descendants."""
        if widget is self._container:
            return
        for child in widget.findChildren(QWidget):
            if child is widget:
                continue
            if child in self._drop_filter_targets:
                child.removeEventFilter(self)
                self._drop_filter_targets.discard(child)
        if widget in self._drop_filter_targets:
            widget.removeEventFilter(self)
            self._drop_filter_targets.discard(widget)

    def _show_drop_indicator(self, insert_index: int) -> None:
        """Position the overlay line for the target insert slot."""
        widgets = self._layout.ordered_widgets()
        if not widgets:
            self._drop_indicator.setGeometry(0, 0, max(self._container.width(), 40), 3)
        elif insert_index >= len(widgets):
            last = widgets[-1]
            y = last.geometry().bottom() + 1
            self._drop_indicator.setGeometry(0, y, self._container.width(), 3)
        else:
            target = widgets[insert_index]
            y = max(0, target.geometry().top() - 2)
            self._drop_indicator.setGeometry(0, y, self._container.width(), 3)
        self._drop_indicator.show()
        self._drop_indicator.raise_()

    def _hide_drop_indicator(self) -> None:
        """Hide the canvas drop indicator overlay."""
        self._drop_indicator.hide()

    def _refresh_layout(self) -> None:
        """Invalidate geometry so wrapped rows reflow after reorder."""
        self.relayout()
