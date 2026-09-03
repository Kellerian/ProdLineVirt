"""Unit tests for per-code arrival timing helpers in model_processing."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from PySide6.QtCore import QModelIndex, QMimeData, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication

from libs.model_processing import (
    ARRIVAL_TIME_ROLE,
    CustomItemModel,
    count_ready_prefix,
    create_code_item,
    is_item_ready,
    stamp_item,
    update_model_data,
)

_MONO_BASE = 1000.0


def _ensure_qapplication() -> QApplication:
    """Return the singleton QApplication required for Qt model items."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestModelProcessingTiming(unittest.TestCase):
    """Tests for stamp_item, is_item_ready, and count_ready_prefix."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for all tests in this class."""
        _ensure_qapplication()

    def setUp(self) -> None:
        """Fix monotonic clock at a known base for deterministic timing."""
        self._mono = _MONO_BASE
        self._mono_patcher = patch(
            "libs.model_processing.time.monotonic",
            side_effect=self._advance_mono,
        )
        self._mono_patcher.start()

    def tearDown(self) -> None:
        """Stop monotonic patch after each test."""
        self._mono_patcher.stop()

    def _advance_mono(self) -> float:
        """Return current mocked monotonic time."""
        return self._mono

    def _elapse_ms(self, milliseconds: float) -> None:
        """Advance mocked monotonic clock by the given milliseconds."""
        self._mono += milliseconds / 1000.0

    def test_create_code_item_stamps_arrival_time(self) -> None:
        """create_code_item stores monotonic arrival time in UserRole."""
        item = create_code_item("CODE-1")
        self.assertEqual(item.text(), "CODE-1")
        self.assertEqual(item.data(ARRIVAL_TIME_ROLE), _MONO_BASE)

    def test_is_item_ready_false_before_interval(self) -> None:
        """Item is not ready until interval_ms has elapsed."""
        item = create_code_item("CODE-1")
        self.assertFalse(is_item_ready(item, 250))
        self._elapse_ms(249)
        self.assertFalse(is_item_ready(item, 250))

    def test_is_item_ready_true_at_interval_boundary(self) -> None:
        """Item becomes ready when elapsed time reaches interval_ms (inclusive)."""
        item = create_code_item("CODE-1")
        self._elapse_ms(250)
        self.assertTrue(is_item_ready(item, 250))

    def test_is_item_ready_true_after_interval(self) -> None:
        """Item stays ready once interval_ms has passed."""
        item = create_code_item("CODE-1")
        self._elapse_ms(500)
        self.assertTrue(is_item_ready(item, 100))

    def test_is_item_ready_legacy_item_stamped_on_first_check(self) -> None:
        """Legacy item without stamp gets timestamp on first check and is not ready."""
        item = QStandardItem("LEGACY")
        self.assertIsNone(item.data(ARRIVAL_TIME_ROLE))
        self.assertFalse(is_item_ready(item, 100))
        self.assertEqual(item.data(ARRIVAL_TIME_ROLE), _MONO_BASE)

    def test_is_item_ready_legacy_becomes_ready_after_interval(self) -> None:
        """Legacy item becomes ready after interval from first-check stamp."""
        item = QStandardItem("LEGACY")
        self.assertFalse(is_item_ready(item, 100))
        self._elapse_ms(100)
        self.assertTrue(is_item_ready(item, 100))

    def test_count_ready_prefix_empty_model(self) -> None:
        """Empty model yields zero ready items."""
        model = QStandardItemModel()
        self.assertEqual(count_ready_prefix(model, 100), 0)

    def test_count_ready_prefix_all_ready(self) -> None:
        """All items counted when every leading row is ready."""
        model = QStandardItemModel()
        for code in ("A", "B", "C"):
            model.appendRow(create_code_item(code))
        self._elapse_ms(200)
        self.assertEqual(count_ready_prefix(model, 100), 3)

    def test_count_ready_prefix_stops_at_first_not_ready(self) -> None:
        """FIFO prefix stops at the first row that is not yet ready."""
        model = QStandardItemModel()
        model.appendRow(create_code_item("A"))
        self._elapse_ms(150)
        model.appendRow(create_code_item("B"))
        model.appendRow(create_code_item("C"))
        self.assertEqual(count_ready_prefix(model, 100), 1)

    def test_count_ready_prefix_zero_interval(self) -> None:
        """Zero interval treats stamped items as immediately ready."""
        model = QStandardItemModel()
        model.appendRow(create_code_item("A"))
        model.appendRow(create_code_item("B"))
        self.assertEqual(count_ready_prefix(model, 0), 2)

    def test_stamp_item_refreshes_arrival_at_node_boundary(self) -> None:
        """Re-stamping at a node boundary resets readiness for the new leg."""
        item = create_code_item("CODE-1")
        self._elapse_ms(500)
        self.assertTrue(is_item_ready(item, 100))
        stamp_item(item)
        self.assertFalse(is_item_ready(item, 100))

    def test_update_model_data_stamps_all_items(self) -> None:
        """update_model_data replaces rows with items carrying ARRIVAL_TIME_ROLE."""
        model = QStandardItemModel()
        update_model_data(model, ["A", "B", "C"])
        self.assertEqual(model.rowCount(), 3)
        for row in range(model.rowCount()):
            item = model.item(row, 0)
            assert item is not None
            self.assertEqual(item.text(), ("A", "B", "C")[row])
            self.assertEqual(item.data(ARRIVAL_TIME_ROLE), _MONO_BASE)


class TestCustomItemModelDrop(unittest.TestCase):
    """Tests for CustomItemModel dropMimeData and flags."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for all tests in this class."""
        _ensure_qapplication()

    def setUp(self) -> None:
        """Fix monotonic clock at a known base for deterministic timing."""
        self._mono = _MONO_BASE
        self._mono_patcher = patch(
            "libs.model_processing.time.monotonic",
            side_effect=self._advance_mono,
        )
        self._mono_patcher.start()

    def tearDown(self) -> None:
        """Stop monotonic patch after each test."""
        self._mono_patcher.stop()

    def _advance_mono(self) -> float:
        """Return current mocked monotonic time."""
        return self._mono

    def test_drop_mime_data_internal_format(self) -> None:
        """Internal QListView MIME from QStandardItemModel inserts a row."""
        source = QStandardItemModel()
        source.appendRow(QStandardItem("DRAG-CODE"))
        mime_data = source.mimeData([source.index(0, 0)])
        self.assertTrue(
            mime_data.hasFormat("application/x-qstandarditemmodeldatalist")
        )

        target = CustomItemModel()
        accepted = target.dropMimeData(
            mime_data,
            Qt.DropAction.CopyAction,
            -1,
            0,
            QModelIndex(),
        )

        self.assertTrue(accepted)
        self.assertEqual(target.rowCount(), 1)
        item = target.item(0, 0)
        assert item is not None
        self.assertEqual(item.text(), "DRAG-CODE")

    def test_drop_mime_data_text_external(self) -> None:
        """External text/plain drop creates stamped code items."""
        mime_data = QMimeData()
        mime_data.setText("EXT-CODE")

        target = CustomItemModel()
        accepted = target.dropMimeData(
            mime_data,
            Qt.DropAction.CopyAction,
            -1,
            0,
            QModelIndex(),
        )

        self.assertTrue(accepted)
        self.assertEqual(target.rowCount(), 1)
        item = target.item(0, 0)
        assert item is not None
        self.assertEqual(item.text(), "EXT-CODE")
        self.assertEqual(item.data(ARRIVAL_TIME_ROLE), _MONO_BASE)

    def test_custom_item_model_flags(self) -> None:
        """Valid index has Enabled, Selectable, and DropEnabled flags."""
        model = CustomItemModel()
        model.appendRow(create_code_item("FLAG-CODE"))
        index = model.index(0, 0)

        flags = model.flags(index)
        self.assertTrue(flags & Qt.ItemFlag.ItemIsEnabled)
        self.assertTrue(flags & Qt.ItemFlag.ItemIsSelectable)
        self.assertTrue(flags & Qt.ItemFlag.ItemIsDropEnabled)


if __name__ == "__main__":
    unittest.main()
