"""Unit tests for :class:`core.controller.controller_widget.ControllerWidget`."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QSizePolicy,
)

from core.controller.controller_widget import ControllerWidget
from core.controller.data import ControllerConfig, ControllerMode, ControllerType


def _ensure_qapplication() -> QApplication:
    """Return the singleton QApplication required for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _set_run_checked(widget: ControllerWidget, checked: bool) -> None:
    """Set ``tbRun`` state without invoking ``run`` (block signals)."""
    tb_run = widget.tbRun
    tb_run.blockSignals(True)
    tb_run.setChecked(checked)
    tb_run.blockSignals(False)


class TestControllerWidgetOptions(unittest.TestCase):
    """``options()`` and combo behaviour."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_options_defaults(self) -> None:
        """Constructor defaults match ``ControllerConfig``."""
        widget = ControllerWidget(name="CTL_1", port=5020)
        opt = widget.options()
        self.assertIsInstance(opt, ControllerConfig)
        self.assertEqual(opt.name, "CTL_1")
        self.assertEqual(opt.port, 5020)
        self.assertEqual(opt.queue_size, 10)
        self.assertEqual(opt.mode, ControllerMode.simplex)
        self.assertEqual(opt.controller_type, ControllerType.delta)

    def test_constructor_sets_duplex_and_xinje_combos(self) -> None:
        """Arguments ``mode`` / ``controller_type`` select the correct combo indices."""
        widget = ControllerWidget(
            name="CTL_2",
            port=5021,
            queue_size=7,
            mode=ControllerMode.duplex,
            controller_type=ControllerType.xinje,
        )
        self.assertEqual(widget.cbMode.currentIndex(), 1)
        self.assertEqual(widget.cbType.currentIndex(), 1)
        opt = widget.options()
        self.assertEqual(opt.mode, ControllerMode.duplex)
        self.assertEqual(opt.controller_type, ControllerType.xinje)
        self.assertEqual(opt.queue_size, 7)

    def test_options_follows_combos(self) -> None:
        """Mode and type combos are reflected in ``options()``."""
        widget = ControllerWidget(name="CTL_1", port=5020)
        widget.cbMode.setCurrentIndex(1)
        widget.cbType.setCurrentIndex(1)
        widget.spQueueSize.setValue(42)
        opt = widget.options()
        self.assertEqual(opt.mode, ControllerMode.duplex)
        self.assertEqual(opt.controller_type, ControllerType.xinje)
        self.assertEqual(opt.queue_size, 42)

    def test_options_invalid_port_raises(self) -> None:
        """Non-numeric port in ``options()`` raises :exc:`ValueError`."""
        widget = ControllerWidget(name="CTL_1", port=5020)
        widget.lePort.setText("bad")
        with self.assertRaises(ValueError):
            widget.options()


class TestControllerWidgetRun(unittest.TestCase):
    """``run`` toggling with mocked :class:`ControllerRuntime`."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_run_start_calls_runtime_with_flags(self) -> None:
        """Starting forwards port, queue, duplex, xinje to ``ControllerRuntime.start``."""
        widget = ControllerWidget(
            name="CTL_1",
            port=5020,
            queue_size=20,
            mode=ControllerMode.duplex,
            controller_type=ControllerType.xinje,
        )
        with patch(
            "core.controller.controller_widget.ControllerRuntime",
        ) as mock_rt_cls:
            instance = MagicMock()
            mock_rt_cls.return_value = instance
            widget.tbRun.setChecked(True)

        instance.start.assert_called_once_with(
            5020,
            20,
            duplex=True,
            xinje=True,
        )
        self.assertIs(widget._runtime, instance)
        self.assertFalse(widget.leName.isEnabled())
        self.assertFalse(widget.lePort.isEnabled())
        self.assertFalse(widget.spQueueSize.isEnabled())
        self.assertFalse(widget.cbMode.isEnabled())
        self.assertFalse(widget.cbType.isEnabled())

    def test_run_stop_calls_runtime_stop(self) -> None:
        """Unchecking run invokes ``stop`` and re-enables fields."""
        widget = ControllerWidget(name="CTL_1", port=5020)
        with patch(
            "core.controller.controller_widget.ControllerRuntime",
        ) as mock_rt_cls:
            instance = MagicMock()
            mock_rt_cls.return_value = instance
            widget.tbRun.setChecked(True)
            widget.tbRun.setChecked(False)

        instance.stop.assert_called_once()
        self.assertIsNone(widget._runtime)
        self.assertTrue(widget.lePort.isEnabled())

    def test_run_invalid_port_unchecks(self) -> None:
        """Non-numeric port leaves run unchecked (как у принтера)."""
        widget = ControllerWidget(name="CTL_1", port=5020)
        widget.lePort.setText("not_a_port")
        widget.tbRun.setChecked(True)
        self.assertFalse(widget.tbRun.isChecked())

    def test_run_start_failure_logs_and_resets(self) -> None:
        """On ``start`` exception: log ERROR exc_info, stop, unblock, unchecked."""
        widget = ControllerWidget(name="CTL_1", port=5020)
        with (
            patch(
                "core.controller.controller_widget.ControllerRuntime",
            ) as mock_rt_cls,
            patch("core.controller.controller_widget.logger.error") as mock_error,
        ):
            instance = MagicMock()
            mock_rt_cls.return_value = instance
            instance.start.side_effect = RuntimeError("bind failed")
            widget.tbRun.setChecked(True)

        mock_error.assert_called_once()
        _, kwargs = mock_error.call_args
        self.assertTrue(kwargs.get("exc_info"))
        instance.stop.assert_called_once()
        self.assertIsNone(widget._runtime)
        self.assertFalse(widget.tbRun.isChecked())
        self.assertTrue(widget.lePort.isEnabled())


class TestControllerWidgetDelete(unittest.TestCase):
    """``_on_delete_clicked`` mirrors printer behaviour."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_running_shows_warning_and_does_not_emit(self) -> None:
        widget = ControllerWidget(name="CTL_RUN", port=5020)
        _set_run_checked(widget, True)
        handler = MagicMock()
        widget.delete_requested.connect(handler)

        with (
            patch(
                "core.controller.controller_widget.QMessageBox.warning",
            ) as mock_warning,
            patch(
                "core.controller.controller_widget.QMessageBox.question",
            ) as mock_question,
        ):
            widget._on_delete_clicked()

        mock_warning.assert_called_once()
        mock_question.assert_not_called()
        handler.assert_not_called()

    def test_stopped_yes_emits_delete_requested(self) -> None:
        widget = ControllerWidget(name="CTL_OK", port=5020)
        _set_run_checked(widget, False)
        handler = MagicMock()
        widget.delete_requested.connect(handler)

        with (
            patch(
                "core.controller.controller_widget.QMessageBox.warning",
            ) as mock_warning,
            patch(
                "core.controller.controller_widget.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ) as mock_question,
        ):
            widget._on_delete_clicked()

        mock_warning.assert_not_called()
        mock_question.assert_called_once()
        handler.assert_called_once()

    def test_stopped_no_does_not_emit(self) -> None:
        widget = ControllerWidget(name="CTL_NO", port=5020)
        handler = MagicMock()
        widget.delete_requested.connect(handler)

        with patch(
            "core.controller.controller_widget.QMessageBox.question",
            return_value=QMessageBox.StandardButton.No,
        ):
            widget._on_delete_clicked()

        handler.assert_not_called()


class TestControllerWidgetUIForm(unittest.TestCase):
    """Generated form: layout stretch, policy, new controls."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_form_size_policies_and_stretch(self) -> None:
        """Stretch 1 on table row; compact rows use Fixed vertical policy."""
        widget = ControllerWidget(name="CTL_UI", port=5020)
        self.assertTrue(hasattr(widget, "btnAddRegister"))
        self.assertTrue(hasattr(widget, "tblRegisters"))
        self.assertEqual(widget.maximumSize().width(), 260)
        self.assertEqual(widget.maximumSize().height(), 16777215)
        layout = widget.layout()
        self.assertIsNotNone(layout)
        assert layout is not None  # narrow for mypy
        self.assertEqual(layout.stretch(0), 0)
        self.assertEqual(layout.stretch(1), 0)
        self.assertEqual(layout.stretch(2), 0)
        self.assertEqual(layout.stretch(3), 0)
        self.assertEqual(layout.stretch(4), 1)
        self.assertEqual(
            widget.leName.sizePolicy().verticalPolicy(),
            QSizePolicy.Policy.Fixed,
        )
        self.assertEqual(
            widget.lePort.sizePolicy().verticalPolicy(),
            QSizePolicy.Policy.Fixed,
        )
        self.assertEqual(
            widget.labelQueue.sizePolicy().verticalPolicy(),
            QSizePolicy.Policy.Fixed,
        )
        self.assertEqual(
            widget.labelMode.sizePolicy().verticalPolicy(),
            QSizePolicy.Policy.Fixed,
        )
        self.assertEqual(
            widget.labelType.sizePolicy().verticalPolicy(),
            QSizePolicy.Policy.Fixed,
        )
        self.assertEqual(
            widget.spQueueSize.sizePolicy().verticalPolicy(),
            QSizePolicy.Policy.Fixed,
        )
        self.assertEqual(
            widget.cbMode.sizePolicy().verticalPolicy(),
            QSizePolicy.Policy.Fixed,
        )
        self.assertEqual(
            widget.cbType.sizePolicy().verticalPolicy(),
            QSizePolicy.Policy.Fixed,
        )


class TestControllerWidgetRegisters(unittest.TestCase):
    """Register table: options, load_options, polling."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def test_add_register_row_editable_flags(self) -> None:
        """Add row: col0 editable, col1 read-only."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        n0 = widget.tblRegisters.rowCount()
        widget.btnAddRegister.click()
        self.assertEqual(widget.tblRegisters.rowCount(), n0 + 1)
        row = widget.tblRegisters.rowCount() - 1
        item0 = widget.tblRegisters.item(row, 0)
        item1 = widget.tblRegisters.item(row, 1)
        assert item0 is not None and item1 is not None
        self.assertTrue(item0.flags() & Qt.ItemFlag.ItemIsEditable)
        self.assertFalse(item1.flags() & Qt.ItemFlag.ItemIsEditable)

    def test_options_skips_blank_and_collects_addresses(self) -> None:
        """Blank rows skipped; order preserved; value column ignored."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        widget.tblRegisters.setRowCount(0)
        for _ in range(3):
            widget.btnAddRegister.click()
        item00 = widget.tblRegisters.item(0, 0)
        item10 = widget.tblRegisters.item(1, 0)
        item20 = widget.tblRegisters.item(2, 0)
        item01 = widget.tblRegisters.item(0, 1)
        assert item00 is not None and item10 is not None
        assert item20 is not None and item01 is not None
        item00.setText("4146")
        item10.setText("")
        item20.setText("4150")
        item01.setText("999")
        opt = widget.options()
        self.assertEqual(opt.register_addresses, [4146, 4150])

    def test_options_invalid_address_raises(self) -> None:
        """Non-integer or out-of-range address raises ValueError with row number."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        widget.tblRegisters.setRowCount(0)
        widget.btnAddRegister.click()
        item0 = widget.tblRegisters.item(0, 0)
        assert item0 is not None
        item0.setText("abc")
        with self.assertRaises(ValueError) as ctx:
            widget.options()
        self.assertIn("Строка 1", str(ctx.exception))

        widget.tblRegisters.setRowCount(0)
        widget.btnAddRegister.click()
        item0b = widget.tblRegisters.item(0, 0)
        assert item0b is not None
        item0b.setText("10001")
        with self.assertRaises(ValueError) as ctx2:
            widget.options()
        self.assertIn("Строка 1", str(ctx2.exception))

    def test_load_options_register_rows(self) -> None:
        """load_options builds rows from config; value column empty."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        cfg = ControllerConfig(
            name="CTL_R",
            port=5020,
            queue_size=10,
            mode=ControllerMode.simplex,
            controller_type=ControllerType.delta,
            register_addresses=[20, 22],
        )
        widget.load_options(cfg)
        self.assertEqual(widget.tblRegisters.rowCount(), 2)
        self.assertEqual(widget.tblRegisters.item(0, 0).text(), "20")
        self.assertEqual(widget.tblRegisters.item(1, 0).text(), "22")
        self.assertEqual(widget.tblRegisters.item(0, 1).text(), "")
        self.assertEqual(widget.tblRegisters.item(1, 1).text(), "")

    def test_run_polls_registers_with_mock_runtime(self) -> None:
        """After start: timer on, read_holding_registers fills value column."""
        widget = ControllerWidget(
            name="CTL_R",
            port=5020,
            register_addresses=[4146, 4150],
        )
        with patch(
            "core.controller.controller_widget.ControllerRuntime",
        ) as mock_rt_cls:
            instance = MagicMock()
            instance.read_holding_registers.return_value = [4, 0]
            mock_rt_cls.return_value = instance
            widget.tbRun.setChecked(True)

        instance.read_holding_registers.assert_called()
        self.assertTrue(widget._register_poll_timer.isActive())
        self.assertEqual(widget.tblRegisters.item(0, 1).text(), "4")
        self.assertEqual(widget.tblRegisters.item(1, 1).text(), "0")

        widget.tbRun.setChecked(False)
        instance.stop.assert_called_once()
        self.assertFalse(widget._register_poll_timer.isActive())
        self.assertEqual(widget.tblRegisters.item(0, 1).text(), "")
        self.assertEqual(widget.tblRegisters.item(1, 1).text(), "")
        self.assertTrue(widget.btnAddRegister.isEnabled())
        self.assertTrue(widget.leName.isEnabled())

    def test_poll_none_values_clears_value_column(self) -> None:
        """``[None, None]`` from read_holding_registers clears the value column."""
        widget = ControllerWidget(
            name="CTL_R",
            port=5020,
            register_addresses=[4146, 4150],
        )
        widget.tblRegisters.item(0, 1).setText("99")
        widget.tblRegisters.item(1, 1).setText("88")
        with patch(
            "core.controller.controller_widget.ControllerRuntime",
        ) as mock_rt_cls:
            instance = MagicMock()
            instance.read_holding_registers.return_value = [None, None]
            mock_rt_cls.return_value = instance
            widget.tbRun.setChecked(True)

        self.assertEqual(widget.tblRegisters.item(0, 1).text(), "")
        self.assertEqual(widget.tblRegisters.item(1, 1).text(), "")

    def test_run_start_failure_timer_inactive(self) -> None:
        """On start exception: poll timer stays inactive."""
        widget = ControllerWidget(
            name="CTL_R",
            port=5020,
            register_addresses=[10],
        )
        with (
            patch(
                "core.controller.controller_widget.ControllerRuntime",
            ) as mock_rt_cls,
            patch("core.controller.controller_widget.logger.error"),
        ):
            instance = MagicMock()
            mock_rt_cls.return_value = instance
            instance.start.side_effect = RuntimeError("bind failed")
            widget.tbRun.setChecked(True)

        self.assertFalse(widget._register_poll_timer.isActive())
        self.assertFalse(widget.tbRun.isChecked())


if __name__ == "__main__":
    unittest.main(verbosity=2)
