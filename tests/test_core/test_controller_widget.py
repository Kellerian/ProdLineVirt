"""Unit tests for :class:`core.controller.controller_widget.ControllerWidget`."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractItemView,
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

    def test_tbl_registers_tooltip(self) -> None:
        """Generated tooltip documents D/M and bare-number grammar."""
        widget = ControllerWidget(name="CTL_UI", port=5020)
        tip = widget.tblRegisters.toolTip()
        self.assertIn("4096+N", tip)
        self.assertIn("2048+N", tip)
        self.assertIn("2048", tip)
        self.assertIn("5000", tip)


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
        self.assertEqual(opt.register_addresses, ["4146", "4150"])

    def test_options_collects_tokens(self) -> None:
        """``options()`` saves stripped tokens, skips blanks and value column."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        widget.tblRegisters.setRowCount(0)
        for _ in range(5):
            widget.btnAddRegister.click()
        texts = ["D100", "", "M100", "2801", "4146"]
        for row, addr in enumerate(texts):
            item0 = widget.tblRegisters.item(row, 0)
            assert item0 is not None
            item0.setText(addr)
            val = widget.tblRegisters.item(row, 1)
            assert val is not None
            val.setText("junk")
        opt = widget.options()
        self.assertEqual(
            opt.register_addresses,
            ["D100", "M100", "2801", "4146"],
        )

    def test_options_invalid_address_raises(self) -> None:
        """Invalid token raises ValueError with row number."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        widget.tblRegisters.setRowCount(0)
        widget.btnAddRegister.click()
        item0 = widget.tblRegisters.item(0, 0)
        assert item0 is not None
        item0.setText("abc")
        with self.assertRaises(ValueError) as ctx:
            widget.options()
        self.assertIn("Строка 1", str(ctx.exception))
        self.assertIn("недопустимый адрес переменной", str(ctx.exception))

        for bad in ("10001", "M2953", "X100"):
            widget.tblRegisters.setRowCount(0)
            widget.btnAddRegister.click()
            bad_item = widget.tblRegisters.item(0, 0)
            assert bad_item is not None
            bad_item.setText(bad)
            with self.assertRaises(ValueError) as ctx_bad:
                widget.options()
            self.assertIn("Строка 1", str(ctx_bad.exception))

    def test_options_invalid_address_second_row_raises(self) -> None:
        """Blank first row, bad token on row 2 — error cites «Строка 2»."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        widget.tblRegisters.setRowCount(0)
        for _ in range(2):
            widget.btnAddRegister.click()
        row0 = widget.tblRegisters.item(0, 0)
        row1 = widget.tblRegisters.item(1, 0)
        assert row0 is not None and row1 is not None
        row0.setText("")
        row1.setText("abc")
        with self.assertRaises(ValueError) as ctx:
            widget.options()
        self.assertIn("Строка 2", str(ctx.exception))
        self.assertIn("недопустимый адрес переменной", str(ctx.exception))

    def test_load_options_register_rows(self) -> None:
        """load_options builds rows from config; value column empty."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        cfg = ControllerConfig(
            name="CTL_R",
            port=5020,
            queue_size=10,
            mode=ControllerMode.simplex,
            controller_type=ControllerType.delta,
            register_addresses=["D100", "20"],
        )
        widget.load_options(cfg)
        self.assertEqual(widget.tblRegisters.rowCount(), 2)
        self.assertEqual(widget.tblRegisters.item(0, 0).text(), "D100")
        self.assertEqual(widget.tblRegisters.item(1, 0).text(), "20")
        self.assertEqual(widget.tblRegisters.item(0, 1).text(), "")
        self.assertEqual(widget.tblRegisters.item(1, 1).text(), "")

    def test_load_options_legacy_int_addresses(self) -> None:
        """Legacy numeric ``register_addresses`` show as decimal strings."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        cfg = ControllerConfig.model_validate(
            {
                "name": "CTL_R",
                "port": 5020,
                "register_addresses": [4146, 2801],
            }
        )
        widget.load_options(cfg)
        self.assertEqual(widget.tblRegisters.rowCount(), 2)
        self.assertEqual(widget.tblRegisters.item(0, 0).text(), "4146")
        self.assertEqual(widget.tblRegisters.item(1, 0).text(), "2801")

    def test_run_polls_registers_with_mock_runtime(self) -> None:
        """After start: timer on, read_points fills value column with colors."""
        widget = ControllerWidget(
            name="CTL_R",
            port=5020,
            register_addresses=[4146, 2801],
        )
        with patch(
            "core.controller.controller_widget.ControllerRuntime",
        ) as mock_rt_cls:
            instance = MagicMock()
            instance.read_points.return_value = [4, False]
            mock_rt_cls.return_value = instance
            widget.tbRun.setChecked(True)

        instance.read_points.assert_called()
        call_points = instance.read_points.call_args[0][0]
        self.assertEqual(call_points[0], ("holding", 4146))
        self.assertEqual(call_points[1], ("coil", 2801))
        self.assertTrue(widget._register_poll_timer.isActive())
        item0 = widget.tblRegisters.item(0, 1)
        item1 = widget.tblRegisters.item(1, 1)
        assert item0 is not None and item1 is not None
        self.assertEqual(item0.text(), "4")
        self.assertEqual(item1.text(), "False")
        self.assertEqual(item0.foreground().color(), QColor(0, 128, 0))
        self.assertEqual(item1.foreground().color(), QColor(0, 128, 0))

        instance.read_points.return_value = [0, True]
        widget._poll_register_values()
        self.assertEqual(item0.text(), "0")
        self.assertEqual(item1.text(), "True")

        widget.tbRun.setChecked(False)
        instance.stop.assert_called_once()
        self.assertFalse(widget._register_poll_timer.isActive())
        self.assertEqual(item0.text(), "")
        self.assertEqual(item1.text(), "")
        self.assertIsNone(item0.data(Qt.ItemDataRole.ForegroundRole))
        self.assertIsNone(item1.data(Qt.ItemDataRole.ForegroundRole))
        self.assertTrue(widget.btnAddRegister.isEnabled())
        self.assertTrue(widget.leName.isEnabled())

    def test_poll_none_and_bool_values(self) -> None:
        """``None`` slot is red empty cell; ``bool`` stays green."""
        widget = ControllerWidget(
            name="CTL_R",
            port=5020,
            register_addresses=[4146, 2801],
        )
        with patch(
            "core.controller.controller_widget.ControllerRuntime",
        ) as mock_rt_cls:
            instance = MagicMock()
            instance.read_points.return_value = [None, False]
            mock_rt_cls.return_value = instance
            widget.tbRun.setChecked(True)

        item0 = widget.tblRegisters.item(0, 1)
        item1 = widget.tblRegisters.item(1, 1)
        assert item0 is not None and item1 is not None
        self.assertEqual(item0.text(), "")
        self.assertEqual(item0.foreground().color(), QColor(128, 0, 0))
        self.assertEqual(item1.text(), "False")
        self.assertEqual(item1.foreground().color(), QColor(0, 128, 0))

    def test_poll_invalid_address_skips_read_points_row(self) -> None:
        """Invalid address on tick clears value without calling read for it."""
        widget = ControllerWidget(name="CTL_R", port=5020)
        widget.tblRegisters.setRowCount(0)
        widget.btnAddRegister.click()
        item0 = widget.tblRegisters.item(0, 0)
        assert item0 is not None
        item0.setText("abc")
        widget.tblRegisters.item(0, 1).setForeground(QColor(0, 128, 0))
        with patch(
            "core.controller.controller_widget.ControllerRuntime",
        ) as mock_rt_cls:
            instance = MagicMock()
            instance.read_points.return_value = []
            mock_rt_cls.return_value = instance
            widget.tbRun.setChecked(True)

        instance.read_points.assert_not_called()
        val_item = widget.tblRegisters.item(0, 1)
        assert val_item is not None
        self.assertEqual(val_item.text(), "")
        self.assertIsNone(val_item.data(Qt.ItemDataRole.ForegroundRole))

    def test_poll_read_points_failure_keeps_cells(self) -> None:
        """Exception or length mismatch leaves displayed values unchanged."""
        widget = ControllerWidget(
            name="CTL_R",
            port=5020,
            register_addresses=[4146],
        )
        widget.tblRegisters.item(0, 1).setText("keep")
        with patch(
            "core.controller.controller_widget.ControllerRuntime",
        ) as mock_rt_cls:
            instance = MagicMock()
            mock_rt_cls.return_value = instance
            instance.read_points.side_effect = RuntimeError("fail")
            widget.tbRun.setChecked(True)

        self.assertEqual(widget.tblRegisters.item(0, 1).text(), "keep")

        instance.read_points.side_effect = None
        instance.read_points.return_value = []
        widget._poll_register_values()
        self.assertEqual(widget.tblRegisters.item(0, 1).text(), "keep")

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


class TestControllerWidgetValueEdit(unittest.TestCase):
    """Editable value column while runtime is running."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def _start_mock_runtime(
        self,
        widget: ControllerWidget,
        *,
        read_points_return: list | None = None,
    ) -> MagicMock:
        """Start widget with mocked ``ControllerRuntime`` and optional poll data."""
        patcher = patch("core.controller.controller_widget.ControllerRuntime")
        self.addCleanup(patcher.stop)
        mock_rt_cls = patcher.start()
        instance = MagicMock()
        if read_points_return is not None:
            instance.read_points.return_value = read_points_return
        mock_rt_cls.return_value = instance
        widget.tbRun.setChecked(True)
        return instance

    def test_stopped_value_edit_ignored(self) -> None:
        """Stopped card: junk in value column is kept; no write_point."""
        widget = ControllerWidget(name="CTL_V", port=5020)
        widget.btnAddRegister.click()
        val = widget.tblRegisters.item(0, 1)
        addr = widget.tblRegisters.item(0, 0)
        assert val is not None and addr is not None
        addr.setText("100")
        for text in ("999", "junk", "keep"):
            val.setText(text)
            self.assertEqual(val.text(), text)
        self.assertFalse(val.flags() & Qt.ItemFlag.ItemIsEditable)
        opt = widget.options()
        self.assertEqual(opt.register_addresses, ["100"])

    def test_run_toggles_value_editable_flags(self) -> None:
        """Start enables value edit; stop clears column and flags."""
        widget = ControllerWidget(
            name="CTL_V",
            port=5020,
            register_addresses=["100"],
        )
        instance = self._start_mock_runtime(widget, read_points_return=[0])
        val = widget.tblRegisters.item(0, 1)
        addr = widget.tblRegisters.item(0, 0)
        assert val is not None and addr is not None
        self.assertTrue(val.flags() & Qt.ItemFlag.ItemIsEditable)
        self.assertTrue(addr.flags() & Qt.ItemFlag.ItemIsEditable)
        triggers = widget.tblRegisters.editTriggers()
        self.assertTrue(triggers & QAbstractItemView.EditTrigger.AnyKeyPressed)

        widget.tbRun.setChecked(False)
        instance.stop.assert_called_once()
        self.assertFalse(val.flags() & Qt.ItemFlag.ItemIsEditable)
        self.assertEqual(val.text(), "")
        self.assertIsNone(val.data(Qt.ItemDataRole.ForegroundRole))

    def test_start_failure_value_not_editable(self) -> None:
        """Failed start: value column stays read-only, timer off."""
        widget = ControllerWidget(name="CTL_V", port=5020, register_addresses=["10"])
        with (
            patch("core.controller.controller_widget.ControllerRuntime") as mock_rt_cls,
            patch("core.controller.controller_widget.logger.error"),
        ):
            instance = MagicMock()
            mock_rt_cls.return_value = instance
            instance.start.side_effect = RuntimeError("bind failed")
            widget.tbRun.setChecked(True)
        val = widget.tblRegisters.item(0, 1)
        assert val is not None
        self.assertFalse(val.flags() & Qt.ItemFlag.ItemIsEditable)
        self.assertFalse(widget._register_poll_timer.isActive())

    def test_add_row_while_running_value_editable(self) -> None:
        """New row while running has editable value column."""
        widget = ControllerWidget(name="CTL_V", port=5020)
        self._start_mock_runtime(widget, read_points_return=[])
        widget.btnAddRegister.click()
        row = widget.tblRegisters.rowCount() - 1
        val = widget.tblRegisters.item(row, 1)
        assert val is not None
        self.assertTrue(val.flags() & Qt.ItemFlag.ItemIsEditable)

    def test_holding_write_on_commit(self) -> None:
        """Poll then user commit calls write_point once."""
        widget = ControllerWidget(name="CTL_V", port=5020, register_addresses=["100"])
        instance = self._start_mock_runtime(widget, read_points_return=[4])
        val = widget.tblRegisters.item(0, 1)
        assert val is not None
        self.assertEqual(val.text(), "4")
        instance.write_point.return_value = True
        val.setText("15")
        instance.write_point.assert_called_once_with("holding", 100, 15)
        self.assertEqual(val.text(), "15")
        self.assertEqual(val.foreground().color(), QColor(0, 128, 0))
        self.assertEqual(widget.options().register_addresses, ["100"])

    def test_holding_bounds_and_reject(self) -> None:
        """Valid max and rejected inputs revert to last poll without message box."""
        widget = ControllerWidget(name="CTL_V", port=5020, register_addresses=["100"])
        instance = self._start_mock_runtime(widget, read_points_return=[4])
        val = widget.tblRegisters.item(0, 1)
        assert val is not None
        instance.write_point.return_value = True

        val.setText("65535")
        instance.write_point.assert_called_with("holding", 100, 65535)
        self.assertEqual(val.text(), "65535")

        instance.write_point.reset_mock()
        bad_inputs = (
            "65536",
            "-1",
            "1.5",
            "1,5",
            "",
            "   ",
            "abc",
            "+3",
            "True",
            "False",
        )
        with patch(
            "core.controller.controller_widget.QMessageBox.warning",
        ) as mock_warn, patch(
            "core.controller.controller_widget.QMessageBox.information",
        ) as mock_info, patch(
            "core.controller.controller_widget.QMessageBox.critical",
        ) as mock_crit:
            for bad in bad_inputs:
                val.setText(bad)
                self.assertEqual(val.text(), "65535")
                self.assertEqual(val.foreground().color(), QColor(0, 128, 0))
        instance.write_point.assert_not_called()
        mock_warn.assert_not_called()
        mock_info.assert_not_called()
        mock_crit.assert_not_called()

    def test_holding_leading_zeros(self) -> None:
        """Leading zeros collapse on write."""
        widget = ControllerWidget(name="CTL_V", port=5020, register_addresses=["100"])
        instance = self._start_mock_runtime(widget, read_points_return=[0])
        val = widget.tblRegisters.item(0, 1)
        assert val is not None
        instance.write_point.return_value = True
        val.setText("0007")
        instance.write_point.assert_called_once_with("holding", 100, 7)
        self.assertEqual(val.text(), "7")

    def test_coil_write_and_reject_words(self) -> None:
        """Coil uses 0/>0; words True/False rejected."""
        widget = ControllerWidget(name="CTL_V", port=5020, register_addresses=["2801"])
        instance = self._start_mock_runtime(widget, read_points_return=[False])
        val = widget.tblRegisters.item(0, 1)
        assert val is not None
        instance.write_point.return_value = True

        val.setText("0")
        instance.write_point.assert_called_with("coil", 2801, False)
        self.assertEqual(val.text(), "False")

        instance.write_point.reset_mock()
        val.setText("2")
        instance.write_point.assert_called_with("coil", 2801, True)
        self.assertEqual(val.text(), "True")

        instance.write_point.reset_mock()
        val.setText("0007")
        instance.write_point.assert_called_with("coil", 2801, True)

        instance.write_point.reset_mock()
        val.setText("True")
        instance.write_point.assert_not_called()
        self.assertEqual(val.text(), "True")

    def test_queue_addresses_writable(self) -> None:
        """Doypack queue addresses accept writes like any holding."""
        for addr in ("4146", "20"):
            widget = ControllerWidget(name="CTL_V", port=5020, register_addresses=[addr])
            instance = self._start_mock_runtime(widget, read_points_return=[1])
            val = widget.tblRegisters.item(0, 1)
            assert val is not None
            instance.write_point.return_value = True
            val.setText("9")
            instance.write_point.assert_called_once_with(
                "holding",
                int(addr),
                9,
            )

    def test_invalid_address_no_write(self) -> None:
        """Invalid address in col0: value edit does not call write_point."""
        widget = ControllerWidget(name="CTL_V", port=5020)
        widget.btnAddRegister.click()
        addr = widget.tblRegisters.item(0, 0)
        val = widget.tblRegisters.item(0, 1)
        assert addr is not None and val is not None
        addr.setText("abc")
        instance = self._start_mock_runtime(widget, read_points_return=[])
        val.setText("1")
        instance.write_point.assert_not_called()

    def test_address_column_edit_no_write_point(self) -> None:
        """Editing variable column does not write or revert address."""
        widget = ControllerWidget(name="CTL_V", port=5020, register_addresses=["100"])
        instance = self._start_mock_runtime(widget, read_points_return=[4])
        addr = widget.tblRegisters.item(0, 0)
        assert addr is not None
        addr.setText("200")
        instance.write_point.assert_not_called()
        self.assertEqual(addr.text(), "200")

    def test_poll_does_not_call_write_point(self) -> None:
        """Polling updates display only; write_point not used."""
        widget = ControllerWidget(name="CTL_V", port=5020, register_addresses=["100"])
        instance = self._start_mock_runtime(widget, read_points_return=[4])
        instance.write_point.assert_not_called()
        instance.write_point.reset_mock()
        instance.read_points.return_value = [5]
        widget._poll_register_values()
        instance.write_point.assert_not_called()
        val = widget.tblRegisters.item(0, 1)
        assert val is not None
        self.assertEqual(val.text(), "5")

    def test_keyboard_opens_editor_not_search(self) -> None:
        """AnyKeyPressed opens editor on current row, not keyboard search jump."""
        widget = ControllerWidget(
            name="CTL_V",
            port=5020,
            register_addresses=["100", "200"],
        )
        instance = self._start_mock_runtime(widget, read_points_return=[4, 4])
        try:
            widget.show()
            widget.tblRegisters.setCurrentCell(0, 1)
            QTest.keyClick(widget.tblRegisters, Qt.Key.Key_4)
            self.assertEqual(
                widget.tblRegisters.state(),
                QAbstractItemView.State.EditingState,
            )
            self.assertEqual(widget.tblRegisters.currentRow(), 0)
            instance.write_point.assert_not_called()
            QTest.keyClick(widget.tblRegisters, Qt.Key.Key_Escape)
            instance.write_point.assert_not_called()
        finally:
            widget.close()

    def test_poll_skips_row_with_open_value_editor(self) -> None:
        """While value editor is open, poll does not change that row."""
        widget = ControllerWidget(
            name="CTL_V",
            port=5020,
            register_addresses=["100", "200"],
        )
        instance = self._start_mock_runtime(widget, read_points_return=[4, 8])
        val0 = widget.tblRegisters.item(0, 1)
        val1 = widget.tblRegisters.item(1, 1)
        assert val0 is not None and val1 is not None
        try:
            widget.show()
            QApplication.processEvents()
            widget.tblRegisters.setCurrentCell(0, 1)
            widget.tblRegisters.editItem(val0)
            QApplication.processEvents()
            self.assertEqual(
                widget.tblRegisters.state(),
                QAbstractItemView.State.EditingState,
            )
            instance.read_points.return_value = [99, None]
            widget._poll_register_values()
            self.assertEqual(val0.text(), "4")
            self.assertEqual(val0.foreground().color(), QColor(0, 128, 0))
            self.assertEqual(val1.text(), "")
            self.assertEqual(val1.foreground().color(), QColor(128, 0, 0))
        finally:
            widget.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
