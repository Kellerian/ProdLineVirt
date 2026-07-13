"""Unit tests for ScannerWidget COM-port refresh button."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.barcode_scanner.scanner_widget import ScannerWidget


def _ensure_qapplication() -> QApplication:
    """Return the singleton QApplication required for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _make_scanner(
    name: str = "SCAN_1",
    ports: list[str] | None = None,
    port_name: str = "",
) -> ScannerWidget:
    """Create ScannerWidget with COM list and icons mocked out.

    Args:
        name: Display name for the scanner widget.
        ports: Ports returned by ``list_available_ports`` during construction.
        port_name: Optional preselected COM port.

    Returns:
        Configured ``ScannerWidget`` instance.
    """
    with (
        patch(
            "core.barcode_scanner.scanner_widget.list_available_ports",
            return_value=ports if ports is not None else [],
        ),
        patch("core.barcode_scanner.scanner_widget.qta.icon", return_value=QIcon()),
    ):
        return ScannerWidget(name=name, port_name=port_name)


def _combo_port_texts(widget: ScannerWidget) -> list[str]:
    """Return all item texts from the COM combo box."""
    return [widget.cbxComPort.itemText(i) for i in range(widget.cbxComPort.count())]


class TestScannerComRefresh(unittest.TestCase):
    """tbRefreshPorts reloads COM list and preserves selection."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create QApplication once for widget construction."""
        _ensure_qapplication()

    def test_refresh_updates_combo_and_keeps_selection(self) -> None:
        """Clicking refresh reloads ports and keeps the current selection."""
        widget = _make_scanner(ports=["COM1", "COM3"], port_name="COM3")
        self.assertEqual(widget._get_port_name(), "COM3")

        with patch(
            "core.barcode_scanner.scanner_widget.list_available_ports",
            return_value=["COM3", "COM5"],
        ) as mock_ports:
            widget.tbRefreshPorts.click()

        mock_ports.assert_called_once_with()
        self.assertEqual(_combo_port_texts(widget), ["Выберите порт", "COM3", "COM5"])
        self.assertEqual(widget._get_port_name(), "COM3")

    def test_refresh_without_selection_keeps_placeholder(self) -> None:
        """Refresh with no port selected leaves the placeholder selected."""
        widget = _make_scanner(ports=["COM1"])
        self.assertEqual(widget._get_port_name(), "")

        with patch(
            "core.barcode_scanner.scanner_widget.list_available_ports",
            return_value=["COM2", "COM4"],
        ):
            widget.tbRefreshPorts.click()

        self.assertEqual(_combo_port_texts(widget), ["Выберите порт", "COM2", "COM4"])
        self.assertEqual(widget.cbxComPort.currentIndex(), 0)
        self.assertEqual(widget._get_port_name(), "")

    def test_refresh_disabled_while_running(self) -> None:
        """tbRefreshPorts is disabled together with the COM combo when running."""
        widget = _make_scanner(ports=["COM1"], port_name="COM1")
        self.assertTrue(widget.tbRefreshPorts.isEnabled())

        with (
            patch.object(widget, "_verify_port_available", return_value=True),
            patch.object(widget._scanner, "start"),
            patch.object(widget._scheduler, "start"),
            patch.object(widget._scanner, "stop"),
            patch.object(widget._scheduler, "stop"),
        ):
            widget.run(True)

            self.assertFalse(widget.cbxComPort.isEnabled())
            self.assertFalse(widget.tbRefreshPorts.isEnabled())

            widget.run(False)

        self.assertTrue(widget.cbxComPort.isEnabled())
        self.assertTrue(widget.tbRefreshPorts.isEnabled())


if __name__ == "__main__":
    unittest.main(verbosity=2)
