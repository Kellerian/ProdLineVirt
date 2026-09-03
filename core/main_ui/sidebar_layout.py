"""Reorderable vertical sidebar container for Line Emulator transporters and generators."""

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import QChildEvent, QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from core.main_ui.device_card import (
    DeviceZone,
    accept_device_drag_enter,
    accept_device_drag_move,
    accept_device_drop,
)


class SidebarLayout(QWidget):
    """Vertical sidebar list with drag-reorder guarded to ``DeviceZone.SIDEBAR``."""

    _DROP_INDICATOR_HEIGHT: int = 3

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create an empty reorderable sidebar container.

        Args:
            parent: Optional parent widget (typically ``scaTransporters``).
        """
        super().__init__(parent)
        self.setObjectName("sidebarLayout")
        self.setAcceptDrops(True)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(1)
        self._widgets: dict[str, QWidget] = {}
        self._drop_filter_targets: set[QWidget] = set()
        self._drop_indicator = QFrame(self)
        self._drop_indicator.setObjectName("sidebarDropIndicator")
        self._drop_indicator.setFixedHeight(self._DROP_INDICATOR_HEIGHT)
        self._drop_indicator.setStyleSheet("background-color: #f0b321;")
        self._drop_indicator.hide()
        self._attach_scroll_viewport()

    def _attach_scroll_viewport(self) -> None:
        """Route drops through the parent ``QScrollArea`` viewport when present."""
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QScrollArea):
            parent = parent.parentWidget()
        if not isinstance(parent, QScrollArea):
            return
        viewport = parent.viewport()
        if viewport is None or viewport in self._drop_filter_targets:
            return
        viewport.setAcceptDrops(True)
        viewport.installEventFilter(self)
        self._drop_filter_targets.add(viewport)

    def add_widget(self, widget: QWidget) -> None:
        """Append a device widget to the sidebar list.

        Args:
            widget: Widget exposing ``device_id``.

        Raises:
            TypeError: When ``widget`` has no ``device_id`` attribute.
            ValueError: When ``device_id`` is already registered.
        """
        device_id = self._require_device_id(widget)
        if device_id in self._widgets:
            raise ValueError(f"Sidebar widget already registered: {device_id}")
        self._widgets[device_id] = widget
        self._install_drop_filters(widget)
        self._layout.addWidget(widget)

    def remove_widget(self, widget: QWidget) -> None:
        """Remove a widget from the sidebar layout without destroying it.

        Args:
            widget: Previously added sidebar widget.
        """
        device_id = getattr(widget, "device_id", None)
        if isinstance(device_id, str) and device_id in self._widgets:
            del self._widgets[device_id]
        self._remove_drop_filters(widget)
        self._layout.removeWidget(widget)

    def get_order(self) -> list[str]:
        """Return ``device_id`` values in current visual order."""
        return [self._require_device_id(widget) for widget in self._layout_widgets()]

    def set_order(self, device_ids: Iterable[str]) -> None:
        """Reorder sidebar widgets to match ``device_ids``.

        Unknown ids are skipped. Widgets not listed keep their relative order
        and are appended after the listed ones.

        Args:
            device_ids: Desired top-to-bottom ``device_id`` sequence.
        """
        ordered_widgets: list[QWidget] = []
        seen: set[str] = set()
        for device_id in device_ids:
            widget = self._widgets.get(device_id)
            if widget is None or device_id in seen:
                continue
            ordered_widgets.append(widget)
            seen.add(device_id)
        for device_id, widget in self._widgets.items():
            if device_id not in seen:
                ordered_widgets.append(widget)
        self._apply_widget_order(ordered_widgets)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept drags from the sidebar zone only."""
        accept_device_drag_enter(event, DeviceZone.SIDEBAR)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Track pointer position and show the drop indicator."""
        if not accept_device_drag_move(event, DeviceZone.SIDEBAR):
            self._hide_drop_indicator()
            return
        insert_index = self._insert_index_at(event.position().toPoint())
        self._show_drop_indicator(insert_index)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Hide the drop indicator when the drag leaves the sidebar."""
        self._hide_drop_indicator()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """Reorder a sidebar widget by ``device_id`` from drag mime."""
        self._handle_drop(event, event.position().toPoint())

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Route drag events from device cards to sidebar reorder logic."""
        event_type = event.type()
        if event_type == QEvent.Type.ChildAdded:
            child_event = event
            if isinstance(child_event, QChildEvent):
                child = child_event.child()
                if (
                    isinstance(child, QWidget)
                    and child is not self
                    and child is not self._drop_indicator
                ):
                    self._install_drop_filters(child)
            return False
        if event_type not in (
            QEvent.Type.DragEnter,
            QEvent.Type.DragMove,
            QEvent.Type.Drop,
        ):
            return False
        if not isinstance(
            event, (QDragEnterEvent, QDragMoveEvent, QDropEvent)
        ):
            return False

        if isinstance(event, QDragEnterEvent):
            accept_device_drag_enter(event, DeviceZone.SIDEBAR)
            return event.isAccepted()

        pos = self._event_position_in_sidebar(watched, event)

        if isinstance(event, QDragMoveEvent):
            if accept_device_drag_move(event, DeviceZone.SIDEBAR):
                insert_index = self._insert_index_at(pos)
                self._show_drop_indicator(insert_index)
                return True
            self._hide_drop_indicator()
            return False

        return self._handle_drop(event, pos)

    def _event_position_in_sidebar(
        self, watched: QObject, event: QDragMoveEvent | QDropEvent
    ) -> QPoint:
        """Map a drag/drop event position into sidebar-local coordinates."""
        if watched is self:
            return event.position().toPoint()
        if isinstance(watched, QWidget):
            global_pos = watched.mapToGlobal(event.position().toPoint())
            return self.mapFromGlobal(global_pos)
        return event.position().toPoint()

    def _handle_drop(self, event: QDropEvent, pos: QPoint) -> bool:
        """Apply a sidebar-zone drop at ``pos``; return whether it was handled."""
        payload = accept_device_drop(event, DeviceZone.SIDEBAR)
        self._hide_drop_indicator()
        if payload is None:
            return False
        widget = self._widgets.get(payload.device_id)
        if widget is None:
            return False
        target_index = self._insert_index_at(pos)
        self._move_widget_to_index(widget, target_index)
        return True

    def _require_device_id(self, widget: QWidget) -> str:
        """Return ``device_id`` from ``widget`` or raise ``TypeError``."""
        device_id = getattr(widget, "device_id", None)
        if not isinstance(device_id, str) or not device_id:
            raise TypeError("Sidebar widgets must expose a non-empty device_id")
        return device_id

    def _layout_widgets(self) -> list[QWidget]:
        """Return managed widgets currently in the layout (excluding indicator)."""
        widgets: list[QWidget] = []
        for index in range(self._layout.count()):
            item = self._layout.itemAt(index)
            if item is None:
                continue
            widget = item.widget()
            if widget is None or widget is self._drop_indicator:
                continue
            widgets.append(widget)
        return widgets

    def _apply_widget_order(self, ordered_widgets: list[QWidget]) -> None:
        """Replace layout item order without changing registry membership."""
        for widget in self._layout_widgets():
            self._layout.removeWidget(widget)
        self._hide_drop_indicator()
        for widget in ordered_widgets:
            self._layout.addWidget(widget)

    def _insert_index_at(self, pos: QPoint) -> int:
        """Map a local point to a layout insert index."""
        widgets = self._layout_widgets()
        if not widgets:
            return 0
        for index, widget in enumerate(widgets):
            top_left = widget.mapTo(self, widget.rect().topLeft())
            mid_y = top_left.y() + widget.height() // 2
            if pos.y() < mid_y:
                return index
        return len(widgets)

    def _show_drop_indicator(self, index: int) -> None:
        """Insert or move the drop indicator line at ``index``."""
        index = max(0, min(index, len(self._layout_widgets())))
        if self._drop_indicator.parent() is None:
            self._layout.insertWidget(index, self._drop_indicator)
        else:
            current_index = self._layout.indexOf(self._drop_indicator)
            if current_index != index:
                self._layout.removeWidget(self._drop_indicator)
                self._layout.insertWidget(index, self._drop_indicator)
        self._drop_indicator.show()

    def _hide_drop_indicator(self) -> None:
        """Remove the drop indicator from the layout."""
        if self._drop_indicator.parent() is not None:
            self._layout.removeWidget(self._drop_indicator)
        self._drop_indicator.hide()

    def _move_widget_to_index(self, widget: QWidget, target_index: int) -> None:
        """Move ``widget`` to ``target_index`` when the position changes."""
        widgets = self._layout_widgets()
        if widget not in widgets:
            return
        source_index = widgets.index(widget)
        if source_index < target_index:
            target_index -= 1
        if source_index == target_index:
            return
        self._layout.removeWidget(widget)
        self._layout.insertWidget(target_index, widget)

    def _install_drop_filters(self, widget: QWidget) -> None:
        """Enable sidebar drop routing on ``widget`` and its descendants."""
        if (
            widget is self
            or widget is self._drop_indicator
            or widget.objectName() == "deviceCardGrip"
            or widget in self._drop_filter_targets
        ):
            return
        self._drop_filter_targets.add(widget)
        widget.setAcceptDrops(True)
        widget.installEventFilter(self)
        for child in widget.findChildren(
            QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly
        ):
            self._install_drop_filters(child)

    def _remove_drop_filters(self, widget: QWidget) -> None:
        """Remove sidebar drop routing from ``widget`` and its descendants."""
        for child in widget.findChildren(QWidget):
            if child is widget:
                continue
            if child in self._drop_filter_targets:
                child.removeEventFilter(self)
                self._drop_filter_targets.discard(child)
        if widget in self._drop_filter_targets:
            widget.removeEventFilter(self)
            self._drop_filter_targets.discard(widget)
