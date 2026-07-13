"""Unit tests for ScannerEmul core (no QApplication)."""

from __future__ import annotations

import time
import unittest
from unittest.mock import MagicMock, patch

from core.barcode_scanner.scanner_core import ScannerEmul
from libs.serial_port import SerialPortConfig, SerialPortError


def _default_config() -> SerialPortConfig:
    """Return a minimal COM config for tests."""
    return SerialPortConfig(port_name="COM_TEST")


def _wait_until(
    predicate,
    timeout_sec: float = 2.0,
    poll_sec: float = 0.01,
) -> bool:
    """Poll *predicate* until it returns truthy or timeout expires."""
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(poll_sec)
    return False


class TestScannerEmul(unittest.TestCase):
    """ScannerEmul queue processing with mocked COM layer."""

    def tearDown(self) -> None:
        """Ensure emulator thread is stopped after each test."""
        if hasattr(self, "_emul") and self._emul is not None:
            self._emul.stop()

    @patch("core.barcode_scanner.scanner_core.write_barcode")
    @patch("core.barcode_scanner.scanner_core.open_serial_port")
    def test_send_writes_codes_with_config_suffix(
        self,
        mock_open: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """Queued codes are written via write_barcode with config suffix."""
        mock_port = MagicMock()
        mock_port.is_open = True
        mock_open.return_value = mock_port
        config = SerialPortConfig(port_name="COM3", suffix="\r\n")
        self._emul = ScannerEmul("SCAN_1", config)
        self._emul.start()
        self._emul.send(["CODE-A", "CODE-B"])

        self.assertTrue(
            _wait_until(lambda: len(mock_write.call_args_list) >= 2),
            "expected both codes to be written",
        )
        self._emul.stop()

        mock_open.assert_called_once_with(config)
        mock_write.assert_any_call(mock_port, "CODE-A", "\r\n")
        mock_write.assert_any_call(mock_port, "CODE-B", "\r\n")

    @patch("core.barcode_scanner.scanner_core.write_barcode")
    @patch("core.barcode_scanner.scanner_core.open_serial_port")
    def test_get_sent_data_drains_buffer(
        self,
        mock_open: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """get_sent_data returns sent codes once and clears the internal buffer."""
        mock_open.return_value = MagicMock(is_open=True)
        self._emul = ScannerEmul("SCAN_1", _default_config())
        self._emul.start()
        self._emul.send(["X1"])

        self.assertTrue(_wait_until(lambda: self._emul.get_sent_data()))
        self.assertEqual(self._emul.get_sent_data(), [])
        self._emul.stop()

    @patch("core.barcode_scanner.scanner_core.open_serial_port")
    def test_pop_open_error_on_failed_open(self, mock_open: MagicMock) -> None:
        """Failed COM open stores an error retrievable via pop_open_error."""
        mock_open.side_effect = SerialPortError("port busy")
        self._emul = ScannerEmul("SCAN_1", _default_config())
        self._emul.start()

        self.assertTrue(_wait_until(lambda: self._emul.pop_open_error() is not None))
        self.assertIsNone(self._emul.pop_open_error())
        self._emul.stop()

    @patch("core.barcode_scanner.scanner_core.write_barcode")
    @patch("core.barcode_scanner.scanner_core.open_serial_port")
    def test_stop_closes_serial_port(
        self,
        mock_open: MagicMock,
        _mock_write: MagicMock,
    ) -> None:
        """stop() closes the underlying serial port."""
        mock_port = MagicMock()
        mock_port.is_open = True
        mock_open.return_value = mock_port
        self._emul = ScannerEmul("SCAN_1", _default_config())
        self._emul.start()
        self._emul.stop()

        mock_port.close.assert_called_once()

    @patch("core.barcode_scanner.scanner_core.write_barcode")
    @patch("core.barcode_scanner.scanner_core.open_serial_port")
    def test_clear_queues_empties_pending_and_sent(
        self,
        mock_open: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """clear_queues removes pending and already-sent codes."""
        mock_open.return_value = MagicMock(is_open=True)
        self._emul = ScannerEmul("SCAN_1", _default_config())
        self._emul.start()
        self._emul.send(["PENDING"])
        self._emul.clear_queues()
        self._emul.send(["AFTER_CLEAR"])

        self.assertTrue(
            _wait_until(lambda: mock_write.call_count >= 1),
            "expected only post-clear code to be written",
        )
        sent = self._emul.get_sent_data()
        self.assertEqual(sent, ["AFTER_CLEAR"])
        self._emul.stop()

    @patch("core.barcode_scanner.scanner_core.write_barcode")
    @patch("core.barcode_scanner.scanner_core.open_serial_port")
    def test_write_error_does_not_add_to_sent(
        self,
        mock_open: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """SerialPortError on write is logged and code is not marked as sent."""
        mock_open.return_value = MagicMock(is_open=True)
        mock_write.side_effect = SerialPortError("write failed")
        self._emul = ScannerEmul("SCAN_1", _default_config())
        self._emul.start()
        self._emul.send(["FAIL_CODE"])

        self.assertTrue(_wait_until(lambda: mock_write.called))
        time.sleep(0.05)
        self.assertEqual(self._emul.get_sent_data(), [])
        self._emul.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
