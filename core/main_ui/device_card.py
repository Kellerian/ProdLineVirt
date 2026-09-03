"""Shared device card chrome for Line Emulator reorder and theming.

Provides ``DeviceCardHeader`` (grip, title slot, delete), drag mime helpers,
and ``DeviceCardMixin`` for ``deviceType`` QSS on device widgets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Final

from PySide6.QtCore import QByteArray, QPoint, Qt, Signal
from PySide6.QtGui import (
    QDrag,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from libs.qt_theme import DeviceType

if TYPE_CHECKING:
    from PySide6.QtCore import QMimeData
    from PySide6.QtWidgets import QLayout

DEVICE_DRAG_MIME_TYPE: Final = "application/x-line-emulator-device-id"


class DeviceZone(str, Enum):
    """Layout zone for drag-reorder guard (sidebar vs canvas)."""

    SIDEBAR = "sidebar"
    CANVAS = "canvas"


@dataclass(frozen=True)
class DeviceDragPayload:
    """Decoded device drag mime payload."""

    device_id: str
    zone: DeviceZone


def encode_device_drag_payload(payload: DeviceDragPayload) -> QByteArray:
    """Serialize ``device_id`` and ``zone`` for ``QMimeData``."""
    text = json.dumps(
        {"device_id": payload.device_id, "zone": payload.zone.value},
        separators=(",", ":"),
    )
    return QByteArray(text.encode("utf-8"))


def decode_device_drag_payload(data: QByteArray | bytes | bytearray) -> DeviceDragPayload | None:
    """Parse drag mime bytes; return ``None`` when malformed."""
    try:
        if isinstance(data, QByteArray):
            raw = bytes(data)
        else:
            raw = bytes(data)
        parsed = json.loads(raw.decode("utf-8"))
        device_id = parsed["device_id"]
        zone = DeviceZone(parsed["zone"])
    except (KeyError, TypeError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(device_id, str) or not device_id:
        return None
    return DeviceDragPayload(device_id=device_id, zone=zone)


def device_drag_payload_from_mime(mime: QMimeData) -> DeviceDragPayload | None:
    """Extract device drag payload from ``QMimeData``, if present."""
    if not mime.hasFormat(DEVICE_DRAG_MIME_TYPE):
        return None
    return decode_device_drag_payload(mime.data(DEVICE_DRAG_MIME_TYPE))


def is_same_zone_drop(source_zone: DeviceZone, target_zone: DeviceZone) -> bool:
    """Return whether a drop is allowed between two zones."""
    return source_zone == target_zone


def can_accept_device_drop(mime: QMimeData, target_zone: DeviceZone) -> bool:
    """Return whether ``mime`` carries a device drag allowed in ``target_zone``."""
    payload = device_drag_payload_from_mime(mime)
    if payload is None:
        return False
    return is_same_zone_drop(payload.zone, target_zone)


def accept_device_drag_enter(event: QDragEnterEvent, target_zone: DeviceZone) -> bool:
    """Accept or ignore a drag-enter event based on zone guard."""
    if can_accept_device_drop(event.mimeData(), target_zone):
        event.acceptProposedAction()
        return True
    event.ignore()
    return False


def accept_device_drag_move(event: QDragMoveEvent, target_zone: DeviceZone) -> bool:
    """Accept or ignore a drag-move event based on zone guard."""
    if can_accept_device_drop(event.mimeData(), target_zone):
        event.acceptProposedAction()
        return True
    event.ignore()
    return False


def accept_device_drop(event: QDropEvent, target_zone: DeviceZone) -> DeviceDragPayload | None:
    """Accept a drop when zones match; return payload or ``None``."""
    payload = device_drag_payload_from_mime(event.mimeData())
    if payload is None or not is_same_zone_drop(payload.zone, target_zone):
        event.ignore()
        return None
    event.acceptProposedAction()
    return payload


class DeviceGripHandle(QWidget):
    """Grip ``≡`` — the sole ``QDrag`` source for device card reorder."""

    def __init__(
        self,
        device_id: str,
        zone: DeviceZone,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize grip handle bound to ``device_id`` and ``zone``.

        Args:
            device_id: Stable device identifier from config.
            zone: Sidebar or canvas zone for cross-zone rejection.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._device_id = device_id
        self._zone = zone
        self._drag_start_pos: QPoint | None = None
        self.setObjectName("deviceCardGrip")
        self.setToolTip("Перетащите для изменения порядка")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFixedSize(28, 28)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Draw the grip glyph centered in the handle."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), "≡")

    @property
    def device_id(self) -> str:
        """Stable device identifier carried in drag mime."""
        return self._device_id

    @property
    def zone(self) -> DeviceZone:
        """Layout zone carried in drag mime."""
        return self._zone

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Record drag origin on left press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Start ``QDrag`` once the pointer moves past the platform threshold."""
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self._drag_start_pos is None:
            super().mouseMoveEvent(event)
            return
        if (
            event.position().toPoint() - self._drag_start_pos
        ).manhattanLength() < QApplication.startDragDistance():
            return
        self._start_drag()
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Clear drag origin on release."""
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def _start_drag(self) -> None:
        """Execute drag with custom device mime payload."""
        from PySide6.QtCore import QMimeData

        mime = QMimeData()
        payload = DeviceDragPayload(device_id=self._device_id, zone=self._zone)
        encoded = encode_device_drag_payload(payload)
        mime.setData(DEVICE_DRAG_MIME_TYPE, encoded)
        mime.setText(f"line-emulator-device:{payload.device_id}:{payload.zone.value}")
        drag = QDrag(self)
        drag.setMimeData(mime)
        pixmap = self.grab()
        if not pixmap.isNull():
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        drag.exec(Qt.DropAction.MoveAction)


class DeviceCardHeader(QWidget):
    """Card header row: grip, optional title widgets, delete button."""

    delete_clicked = Signal()

    def __init__(
        self,
        device_id: str,
        zone: DeviceZone,
        parent: QWidget | None = None,
    ) -> None:
        """Build header chrome for one device card.

        Args:
            device_id: Stable device identifier for drag mime.
            zone: Sidebar or canvas zone for drag guard.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("deviceCardHeader")
        self._grip = DeviceGripHandle(device_id, zone, parent=self)
        self._title_layout = QHBoxLayout()
        self._title_layout.setContentsMargins(0, 0, 0, 0)
        self._title_layout.setSpacing(1)
        self._delete = QToolButton(self)
        self._delete.setObjectName("tbDelete")
        self._delete.setMinimumSize(28, 28)
        self._delete.setMaximumSize(28, 28)
        self._delete.setText("X")
        self._delete.setToolTip("Удалить")
        self._delete.clicked.connect(self.delete_clicked.emit)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.addWidget(self._grip, 0)
        layout.addLayout(self._title_layout, 1)
        layout.addWidget(self._delete, 0)

    @property
    def grip(self) -> DeviceGripHandle:
        """Drag handle widget."""
        return self._grip

    @property
    def title_layout(self) -> QHBoxLayout:
        """Layout slot for name, run/stop, and other header controls."""
        return self._title_layout

    @property
    def delete_button(self) -> QToolButton:
        """Delete control in the header row."""
        return self._delete

    def add_title_widget(self, widget: QWidget, stretch: int = 0) -> None:
        """Append a widget to the title slot.

        Args:
            widget: Control to show between grip and delete.
            stretch: Optional horizontal stretch factor.
        """
        self._title_layout.addWidget(widget, stretch)


class DeviceCardMixin:
    """Mixin for device widgets: ``deviceType`` QSS and header mounting."""

    _device_card_header: DeviceCardHeader | None = None
    _advanced_toggle: QToolButton | None = None
    _advanced_panel: QWidget | None = None
    _advanced_expanded: bool = False

    def apply_device_type(self, device_type: DeviceType) -> None:
        """Set dynamic ``deviceType`` property for theme QSS selectors."""
        self.setProperty("deviceType", device_type)
        self.style().unpolish(self)
        self.style().polish(self)

    def mount_device_card_header(
        self,
        *,
        device_id: str,
        device_type: DeviceType,
        zone: DeviceZone,
        row_layout: QLayout,
        delete_button: QToolButton,
    ) -> DeviceCardHeader:
        """Replace a legacy .ui header row with ``DeviceCardHeader``.

        Moves existing row widgets (except ``delete_button``) into the header
        title slot, removes the legacy delete control, and applies ``deviceType``.

        Args:
            device_id: Stable device identifier.
            device_type: Token for ``QWidget#Form[deviceType=...]`` QSS.
            zone: Sidebar or canvas zone for drag mime.
            row_layout: Existing header ``QHBoxLayout`` from ``setupUi``.
            delete_button: Legacy ``tbDelete`` replaced by header delete.

        Returns:
            Mounted header instance (also stored on ``_device_card_header``).
        """
        if not isinstance(row_layout, QHBoxLayout):
            raise TypeError("row_layout must be QHBoxLayout")
        title_entries: list[tuple[QWidget, int]] = []
        for index in range(row_layout.count()):
            item = row_layout.itemAt(index)
            if item is None:
                continue
            widget = item.widget()
            if widget is None or widget is delete_button:
                continue
            title_entries.append((widget, row_layout.stretch(index)))
        for widget, _ in title_entries:
            row_layout.removeWidget(widget)
        row_layout.removeWidget(delete_button)
        delete_button.setParent(None)
        delete_button.deleteLater()
        header = DeviceCardHeader(device_id, zone, parent=self)
        for widget, stretch in title_entries:
            header.add_title_widget(widget, stretch)
        row_layout.addWidget(header, 1)
        self.apply_device_type(device_type)
        self._device_card_header = header
        if getattr(self, "tbDelete", None) is delete_button:
            self.tbDelete = header.delete_button
        return header

    def wire_advanced_panel(
        self,
        toggle_button: QToolButton,
        panel: QWidget,
        *,
        expanded: bool = False,
    ) -> None:
        """Connect «Дополнительно» toggle to a collapsible advanced panel.

        Args:
            toggle_button: Checkable ``QToolButton`` from ``setupUi``.
            panel: Container widget (``wAdvanced``) toggled visible/hidden.
            expanded: Initial expanded state (default collapsed).
        """
        self._advanced_toggle = toggle_button
        self._advanced_panel = panel
        toggle_button.setCheckable(True)
        toggle_button.setAutoRaise(True)
        toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        toggle_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        toggle_button.setMinimumHeight(24)
        toggle_button.setMaximumHeight(28)
        toggle_button.setText("Дополнительно")
        toggle_button.toggled.connect(self.set_advanced_expanded)
        self.set_advanced_expanded(expanded)

    def set_advanced_expanded(self, expanded: bool) -> None:
        """Show or hide the advanced panel and sync the toggle button."""
        self._advanced_expanded = expanded
        if self._advanced_panel is not None:
            self._advanced_panel.setVisible(expanded)
        if self._advanced_toggle is not None:
            self._advanced_toggle.blockSignals(True)
            self._advanced_toggle.setChecked(expanded)
            self._advanced_toggle.setArrowType(
                Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
            )
            self._advanced_toggle.blockSignals(False)

    def is_advanced_expanded(self) -> bool:
        """Return whether the advanced section is expanded."""
        return self._advanced_expanded
