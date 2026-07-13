"""Unit tests for transporter burst rate-limiting (same arrival stamp batch)."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QApplication

from core.transporting.transporter_widget import TransporterWidget
from libs.model_processing import ARRIVAL_TIME_ROLE, create_code_item

_MONO_BASE = 5000.0
_BURST_COUNT = 10
_INTERVAL_MS = 250


def _ensure_qapplication() -> QApplication:
    """Return the singleton QApplication required for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _append_burst_codes(model: QStandardItemModel, count: int) -> None:
    """Append *count* codes stamped with the same monotonic arrival time."""
    for index in range(count):
        model.appendRow(create_code_item(f"CODE-{index}"))
    first = model.item(0, 0)
    assert first is not None
    shared_stamp = first.data(ARRIVAL_TIME_ROLE)
    for row in range(1, count):
        item = model.item(row, 0)
        assert item is not None
        item.setData(shared_stamp, ARRIVAL_TIME_ROLE)


class TestTransporterBurstRateLimit(unittest.TestCase):
    """Burst from printer: N codes with one stamp → one transfer per spInterval."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def setUp(self) -> None:
        """Fix monotonic clock for deterministic readiness and rate-limit checks."""
        self._mono = _MONO_BASE
        self._patchers = [
            patch(
                "libs.model_processing.time.monotonic",
                side_effect=self._mono_now,
            ),
            patch(
                "core.transporting.transporter_widget.time.monotonic",
                side_effect=self._mono_now,
            ),
        ]
        for patcher in self._patchers:
            patcher.start()

    def tearDown(self) -> None:
        """Stop monotonic patches after each test."""
        for patcher in self._patchers:
            patcher.stop()

    def _mono_now(self) -> float:
        """Return current mocked monotonic time."""
        return self._mono

    def _elapse_ms(self, milliseconds: float) -> None:
        """Advance mocked monotonic clock by the given milliseconds."""
        self._mono += milliseconds / 1000.0

    def _make_transporter(
        self,
        source: QStandardItemModel,
        dest: QStandardItemModel,
        interval_ms: int = _INTERVAL_MS,
    ) -> TransporterWidget:
        """Wire a transporter directly to source and destination models."""
        transport = TransporterWidget()
        transport.set_interval(interval_ms)
        transport.model_in = source
        transport.model_out = dest
        return transport

    def test_burst_same_stamp_one_transfer_per_interval(self) -> None:
        """After interval, many scheduler ticks move only one code per spInterval."""
        source = QStandardItemModel()
        dest = QStandardItemModel()
        _append_burst_codes(source, _BURST_COUNT)
        transport = self._make_transporter(source, dest)

        for _ in range(_BURST_COUNT):
            transport.send_data()
        self.assertEqual(dest.rowCount(), 0)
        self.assertEqual(source.rowCount(), _BURST_COUNT)

        self._elapse_ms(_INTERVAL_MS)

        for _ in range(_BURST_COUNT):
            transport.send_data()

        self.assertEqual(
            dest.rowCount(),
            1,
            "Without inter-transfer rate limit all burst codes would drain at once",
        )
        self.assertEqual(source.rowCount(), _BURST_COUNT - 1)

    def test_burst_second_transfer_after_next_interval(self) -> None:
        """Second code transfers only after another full spInterval."""
        source = QStandardItemModel()
        dest = QStandardItemModel()
        _append_burst_codes(source, _BURST_COUNT)
        transport = self._make_transporter(source, dest)

        self._elapse_ms(_INTERVAL_MS)
        transport.send_data()
        self.assertEqual(dest.rowCount(), 1)

        for _ in range(_BURST_COUNT):
            transport.send_data()
        self.assertEqual(dest.rowCount(), 1)

        self._elapse_ms(_INTERVAL_MS)
        transport.send_data()
        self.assertEqual(dest.rowCount(), 2)
        self.assertEqual(source.rowCount(), _BURST_COUNT - 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
