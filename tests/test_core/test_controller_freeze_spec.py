"""PyInstaller spec: pymodbus hiddenimports via collect_submodules."""

from __future__ import annotations

import unittest
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


class TestMainSpecPymodbusImports(unittest.TestCase):
    """Regression: frozen bundle must include pymodbus subpackages."""

    def test_main_spec_lists_collect_submodules_pymodbus(self) -> None:
        """main.spec uses collect_submodules; venv lists key pymodbus subpackages."""
        repo_root = Path(__file__).resolve().parents[2]
        spec_text = (repo_root / "build" / "spec" / "main.spec").read_text(
            encoding="utf-8"
        )
        self.assertIn("collect_submodules", spec_text)
        self.assertIn('collect_submodules("pymodbus")', spec_text)
        hidden = collect_submodules("pymodbus")
        for needle in (
            "pymodbus.server",
            "pymodbus.client",
            "pymodbus.datastore",
            "pymodbus.framer",
        ):
            self.assertIn(needle, hidden)


if __name__ == "__main__":
    unittest.main()
