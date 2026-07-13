"""Unit tests for libs.serial_port (pyserial wrapper, mocked serial.Serial)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import serial

from libs.serial_port import (
    SerialPortConfig,
    SerialPortError,
    list_available_ports,
    open_serial_port,
    write_barcode,
)


class TestListAvailablePorts(unittest.TestCase):
    """Tests for list_available_ports."""

    @patch("libs.serial_port.list_ports.comports")
    def test_returns_device_names(self, mock_comports: MagicMock) -> None:
        """list_available_ports maps comports() entries to device strings."""
        mock_comports.return_value = [
            MagicMock(device="COM3"),
            MagicMock(device="COM7"),
        ]
        self.assertEqual(list_available_ports(), ["COM3", "COM7"])

    @patch("libs.serial_port.list_ports.comports")
    def test_empty_when_no_ports(self, mock_comports: MagicMock) -> None:
        """Empty OS port list yields an empty result."""
        mock_comports.return_value = []
        self.assertEqual(list_available_ports(), [])


class TestOpenSerialPort(unittest.TestCase):
    """Tests for open_serial_port with mocked serial.Serial."""

    @patch("libs.serial_port.serial.Serial")
    def test_opens_with_default_config(self, mock_serial_cls: MagicMock) -> None:
        """Default SerialPortConfig passes expected kwargs to serial.Serial."""
        mock_port = MagicMock()
        mock_serial_cls.return_value = mock_port
        config = SerialPortConfig(port_name="COM5")

        result = open_serial_port(config)

        self.assertIs(result, mock_port)
        mock_serial_cls.assert_called_once_with(
            port="COM5",
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
        )

    @patch("libs.serial_port.serial.Serial")
    def test_opens_with_custom_line_settings(self, mock_serial_cls: MagicMock) -> None:
        """Custom bytesize, parity and stopbits are mapped to pyserial constants."""
        mock_serial_cls.return_value = MagicMock()
        config = SerialPortConfig(
            port_name="COM1",
            baud_rate=115200,
            bytesize=7,
            parity="E",
            stopbits=2,
        )

        open_serial_port(config)

        mock_serial_cls.assert_called_once_with(
            port="COM1",
            baudrate=115200,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_TWO,
            timeout=0.1,
        )

    def test_invalid_bytesize_raises_serial_port_error(self) -> None:
        """Unknown bytesize raises SerialPortError before opening the port."""
        config = SerialPortConfig(port_name="COM1", bytesize=9)
        with self.assertRaises(SerialPortError):
            open_serial_port(config)

    def test_invalid_parity_raises_serial_port_error(self) -> None:
        """Unknown parity letter raises SerialPortError."""
        config = SerialPortConfig(port_name="COM1", parity="X")
        with self.assertRaises(SerialPortError):
            open_serial_port(config)

    @patch("libs.serial_port.serial.Serial", side_effect=serial.SerialException("busy"))
    def test_serial_exception_wrapped(self, _mock_serial_cls: MagicMock) -> None:
        """pyserial SerialException is wrapped in SerialPortError."""
        config = SerialPortConfig(port_name="COM9")
        with self.assertRaises(SerialPortError) as ctx:
            open_serial_port(config)
        self.assertIn("COM9", str(ctx.exception))


class TestWriteBarcode(unittest.TestCase):
    """Tests for write_barcode."""

    def test_writes_utf8_payload_with_suffix(self) -> None:
        """Barcode and suffix are encoded as UTF-8 and flushed."""
        mock_port = MagicMock()
        mock_port.is_open = True
        mock_port.port = "COM3"

        write_barcode(mock_port, "1234567890", suffix="\r\n")

        mock_port.write.assert_called_once_with(b"1234567890\r\n")
        mock_port.flush.assert_called_once_with()

    def test_custom_suffix(self) -> None:
        """Custom suffix is appended to the barcode text."""
        mock_port = MagicMock()
        mock_port.is_open = True
        mock_port.port = "COM3"

        write_barcode(mock_port, "ABC", suffix="\n")

        mock_port.write.assert_called_once_with(b"ABC\n")

    def test_closed_port_raises(self) -> None:
        """Writing to a closed port raises SerialPortError."""
        mock_port = MagicMock()
        mock_port.is_open = False

        with self.assertRaises(SerialPortError) as ctx:
            write_barcode(mock_port, "CODE")
        self.assertIn("закрыт", str(ctx.exception).lower())

    def test_serial_exception_on_write_wrapped(self) -> None:
        """Write failures are wrapped in SerialPortError."""
        mock_port = MagicMock()
        mock_port.is_open = True
        mock_port.port = "COM3"
        mock_port.write.side_effect = serial.SerialException("write failed")

        with self.assertRaises(SerialPortError) as ctx:
            write_barcode(mock_port, "CODE")
        self.assertIn("COM3", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
