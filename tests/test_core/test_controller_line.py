"""Integration tests: ControllerWidget on MainLineField, save/load JSON."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.controller.controller_widget import ControllerWidget
from core.controller.data import ControllerConfig, ControllerMode, ControllerType
from core.main_ui.data import ConfigFile
from core.main_ui.line_emul import MainLineField


def _ensure_qapplication() -> QApplication:
    """Return the singleton QApplication required for Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestControllerLineIntegration(unittest.TestCase):
    """Default ports, ConfigFile round-trip, legacy JSON without controllers."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapplication()

    def setUp(self) -> None:
        self.field = MainLineField()

    def tearDown(self) -> None:
        self.field.close()

    def test_default_controller_ports_increment(self) -> None:
        """Next default ports from generator are 5020, then 5021."""
        p1 = next(self.field.controller_port)
        c1 = self.field.add_controller(f"CTL_{p1}", p1)
        p2 = next(self.field.controller_port)
        c2 = self.field.add_controller(f"CTL_{p2}", p2)
        self.assertEqual(p1, 5020)
        self.assertEqual(p2, 5021)
        self.assertEqual(int(c1.lePort.text()), 5020)
        self.assertEqual(int(c2.lePort.text()), 5021)
        self.assertIn(id(c1), self.field._controller_widgets)
        self.assertIn(id(c2), self.field._controller_widgets)

    def test_options_round_trip_config_file(self) -> None:
        """options() is saved and restored by process_config."""
        ctl = self.field.add_controller(
            "MyCtl",
            5600,
            queue_size=20,
            mode=ControllerMode.duplex,
            controller_type=ControllerType.xinje,
        )
        ctl.tblRegisters.setRowCount(0)
        ctl.btnAddRegister.click()
        ctl.btnAddRegister.click()
        item0 = ctl.tblRegisters.item(0, 0)
        item1 = ctl.tblRegisters.item(1, 0)
        assert item0 is not None and item1 is not None
        item0.setText("4146")
        item1.setText("4150")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            path = Path(tmp.name)
        try:
            cfg = ConfigFile(
                controllers=[ctl.options()],
                printers=[],
                cameras=[],
                scanners=[],
                transporters=[],
                generators=[],
            )
            path.write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
            loaded = ConfigFile.model_validate_json(path.read_text(encoding="utf-8"))
            self.field.clear_ui()
            self.field.process_config(loaded)
            self.assertEqual(len(self.field._controller_widgets), 1)
            w = next(iter(self.field._controller_widgets.values()))
            assert isinstance(w, ControllerWidget)
            expected = loaded.controllers[0]
            self.assertEqual(w.options().model_dump(), expected.model_dump())
            self.assertEqual(expected.register_addresses, [4146, 4150])
            self.assertEqual(w.tblRegisters.rowCount(), 2)
            self.assertEqual(w.tblRegisters.item(0, 0).text(), "4146")
            self.assertEqual(w.tblRegisters.item(1, 0).text(), "4150")
            self.assertEqual(w.tblRegisters.item(0, 1).text(), "")
            self.assertEqual(w.tblRegisters.item(1, 1).text(), "")
        finally:
            path.unlink(missing_ok=True)

    def test_legacy_json_without_controllers_opens_empty(self) -> None:
        """Old JSON without controllers key loads with no controller cards."""
        legacy = json.dumps(
            {"printers": [], "cameras": [], "scanners": []},
            ensure_ascii=False,
        )
        cfg = ConfigFile.model_validate_json(legacy)
        self.field.process_config(cfg)
        self.assertEqual(self.field._controller_widgets, {})


if __name__ == "__main__":
    unittest.main()
