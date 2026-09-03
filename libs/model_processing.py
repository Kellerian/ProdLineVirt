import time

from PySide6.QtCore import QModelIndex, QMimeData, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel

ARRIVAL_TIME_ROLE = Qt.UserRole + 1

_INTERNAL_DROP_MIME_TYPES: tuple[str, ...] = (
    "application/x-qstandarditemmodeldatalist",
    "application/x-qabstractitemmodeldatalist",
)


def _is_internal_drop_mime(data: QMimeData) -> bool:
    """Return whether *data* carries Qt item-model drag payload.

    Args:
        data: Mime payload from a QListView / QAbstractItemView drag.

    Returns:
        ``True`` when the payload is standard internal QListView DnD format.
    """
    return any(data.hasFormat(fmt) for fmt in _INTERNAL_DROP_MIME_TYPES)


class CustomItemModel(QStandardItemModel):
    """Item model with drag-and-drop enabled on valid rows."""

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Return item flags with drop enabled for valid indices."""
        flags = super().flags(index)
        if index.isValid():
            flags |= Qt.ItemFlag.ItemIsDropEnabled
        return flags

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        """Handle internal QListView drag and external text drops.

        Internal drag-and-drop (QListView → QListView) is delegated to
        ``super().dropMimeData``; ``rowsInserted`` handlers in camera and
        scanner widgets then call :func:`stamp_item`.

        External text drops mirror ``QStandardItemModel`` text-drop behaviour
        but use :func:`create_code_item` so every dropped code gets
        ``arrival_time``.

        Args:
            data: Mime payload from the drag source.
            action: Requested drop action.
            row: Target row, or ``-1`` to append.
            column: Target column index.
            parent: Parent index for the drop target.

        Returns:
            ``True`` when the drop was accepted, else ``False``.
        """
        if _is_internal_drop_mime(data):
            return super().dropMimeData(data, action, row, column, parent)

        if not data.hasText():
            return False

        if row == -1:
            row = parent.row() if parent.isValid() else self.rowCount(parent)

        inserted = 0
        for line in data.text().split("\n"):
            if not line:
                continue
            self.insertRow(row + inserted, parent)
            self.setItem(row + inserted, column, create_code_item(line))
            inserted += 1
        return inserted > 0


def create_code_item(text: str) -> QStandardItem:
    """Create a queue item for a code with an arrival timestamp.

    Args:
        text: Display text of the code.

    Returns:
        A new ``QStandardItem`` stamped with the current monotonic time.
    """
    item = QStandardItem(text)
    stamp_item(item)
    return item


def stamp_item(item: QStandardItem) -> None:
    """Set the arrival timestamp on an item to the current monotonic time.

    Args:
        item: Queue item to stamp.
    """
    item.setData(time.monotonic(), ARRIVAL_TIME_ROLE)


def _get_arrival_time(item: QStandardItem) -> float | None:
    """Return the stored monotonic arrival time, or ``None`` if missing or invalid."""
    value = item.data(ARRIVAL_TIME_ROLE)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ensure_item_stamped(item: QStandardItem) -> None:
    """Ensure a legacy item has an arrival timestamp; stamp now if missing.

    Intended for backward compatibility with queue items created before
    per-code timing. When a code enters a new node queue, call
    :func:`stamp_item` explicitly so each leg gets a fresh timestamp —
    do not use this helper at node boundaries.

    Args:
        item: Queue item that may lack an arrival timestamp.
    """
    if _get_arrival_time(item) is None:
        stamp_item(item)


def is_item_ready(item: QStandardItem, interval_ms: float | int) -> bool:
    """Return whether enough time has passed since the item's arrival.

    Legacy items without a timestamp are stamped on first check via
    :func:`ensure_item_stamped` and treated as not ready until
    ``interval_ms`` elapses from that moment. At node boundaries use
    :func:`stamp_item`, not :func:`ensure_item_stamped`.

    Args:
        item: Queue item to evaluate.
        interval_ms: Required waiting time in milliseconds.

    Returns:
        ``True`` when ``interval_ms`` or more has elapsed since arrival.
    """
    ensure_item_stamped(item)
    arrival = _get_arrival_time(item)
    if arrival is None:
        return False
    elapsed_ms = (time.monotonic() - arrival) * 1000.0
    return elapsed_ms >= float(interval_ms)


def count_ready_prefix(model: QStandardItemModel, interval_ms: float | int) -> int:
    """Count consecutive ready items from row 0 (FIFO prefix).

    Scanning stops at the first row that is not ready, preserving queue order.

    Args:
        model: Source queue model (column 0).
        interval_ms: Required waiting time in milliseconds per item.

    Returns:
        Number of leading rows whose items are ready for transfer.
    """
    count = 0
    for row in range(model.rowCount()):
        item = model.item(row, 0)
        if item is None:
            break
        if not is_item_ready(item, interval_ms):
            break
        count += 1
    return count


def update_model_data(model: QStandardItemModel, data: list[str]) -> None:
    """Replace model contents with stamped code items from ``data``.

    Args:
        model: Target queue model (column 0).
        data: Code strings to load.
    """
    model.blockSignals(True)
    model.clear()
    model.blockSignals(False)
    for row in data:
        model.appendRow(create_code_item(row))
