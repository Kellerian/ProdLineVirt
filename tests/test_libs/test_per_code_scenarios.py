"""Scripted verification for plan #7 per-code transfer timing scenarios."""

import time
import unittest

from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

from libs.model_processing import (  # noqa: E402
    ARRIVAL_TIME_ROLE,
    count_ready_prefix,
    create_code_item,
    is_item_ready,
    stamp_item,
    CustomItemModel,
)


class TestPerCodeScenarios(unittest.TestCase):
    """Headless checks aligned with manual scenarios in plan #7."""

    def test_camera_single_batch_waits_for_ready_prefix(self) -> None:
        """Scenario 1: codes wait interval before ready prefix allows send."""
        model = CustomItemModel()
        interval = 100
        for code in ("A", "B", "C"):
            model.appendRow(create_code_item(code))
        self.assertEqual(count_ready_prefix(model, interval), 0)
        time.sleep(interval / 1000.0 + 0.02)
        self.assertEqual(count_ready_prefix(model, interval), 3)

    def test_camera_batch_fifo_prefix(self) -> None:
        """Scenario 2: unripe head blocks batch even if tail is old."""
        model = CustomItemModel()
        interval = 80
        for code in ("1", "2", "3", "4", "5"):
            model.appendRow(create_code_item(code))
        time.sleep(interval / 1000.0 + 0.02)
        self.assertEqual(count_ready_prefix(model, interval), 5)
        model.insertRow(0, create_code_item("NEW"))
        self.assertEqual(count_ready_prefix(model, interval), 0)

    def test_transporter_fifo_head_readiness(self) -> None:
        """Scenario 3: head must become ready before transfer."""
        model = CustomItemModel()
        interval = 50
        model.appendRow(create_code_item("first"))
        model.appendRow(create_code_item("second"))
        head = model.item(0, 0)
        self.assertIsNotNone(head)
        self.assertFalse(is_item_ready(head, interval))
        time.sleep(interval / 1000.0 + 0.02)
        self.assertTrue(is_item_ready(head, interval))

    def test_dynamic_interval_recalc(self) -> None:
        """Scenario 5: interval change applies on next readiness check."""
        item = create_code_item("X")
        time.sleep(0.15)
        self.assertFalse(is_item_ready(item, 200))
        self.assertTrue(is_item_ready(item, 100))

    def test_node_boundary_fresh_stamp(self) -> None:
        """Transporter leg: create_code_item gives new arrival at receiver."""
        transferred = create_code_item("DM123")
        old = transferred.data(ARRIVAL_TIME_ROLE)
        self.assertIsNotNone(old)
        time.sleep(0.05)
        stamp_item(transferred)
        new = transferred.data(ARRIVAL_TIME_ROLE)
        self.assertIsNotNone(new)
        self.assertGreater(float(new), float(old))


if __name__ == "__main__":
    unittest.main(verbosity=2)
