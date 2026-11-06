"""Unit tests for Doypack emulation parameters and one polling cycle."""

from __future__ import annotations

import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path
from typing import Any, List, Tuple, Union
from unittest.mock import MagicMock

from core.controller.dmc_modbus.base import DmcModbusBase
from core.controller.doypack import DoypackEmulation


Record = Tuple[str, int, Union[bool, int], bool]


class _FakeDmcModbus:
    """In-memory stand-in for :class:`DmcModbusBase` with ordered call recording."""

    def __init__(self) -> None:
        self.calls: List[Record] = []
        self._hr: dict[int, int] = {}

    async def write(self, address: int, data: Union[bool, int], *, coil: bool) -> None:
        self.calls.append(("write", address, data, coil))
        if not coil:
            self._hr[address] = int(data)

    async def read(self, address: int, count: int, *, coil: bool) -> Any:
        self.calls.append(("read", address, count, coil))
        if coil:
            return False
        return self._hr.get(address, 0)

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass


class TestDoypackQueueSizeValidation(unittest.TestCase):
    """``queue_size`` must match ``ControllerConfig.queue_size`` domain (1..1000)."""

    def test_invalid_queue_size_raises_value_error(self) -> None:
        """``queue_size`` 0, -1, or 1001 is rejected with :exc:`ValueError`."""
        for invalid in (0, -1, 1001):
            with self.subTest(queue_size=invalid):
                with self.assertRaises(ValueError):
                    DoypackEmulation("127.0.0.1:5020", invalid)


class TestDoypackAddresses(unittest.TestCase):
    """``q_start``, ``can_start_work``, ``step``, ``q_end`` match ControllerServerEmulator."""

    def _params(
        self,
        *,
        queue_size: int,
        duplex: bool,
        xinje: bool,
    ) -> Tuple[int, int, int, int]:
        emulation = DoypackEmulation(
            "127.0.0.1:5020",
            queue_size,
            duplex=duplex,
            xinje=xinje,
        )
        step = 2 if duplex else 1
        q_end = emulation.q_start + (queue_size + 1) * step
        return emulation.q_start, emulation.can_start_work, step, q_end

    def test_xinje_simplex_queue_10(self) -> None:
        """Xinje simplex: q_end = 20 + 11 = 31."""
        qs, csw, step, qe = self._params(queue_size=10, duplex=False, xinje=True)
        self.assertEqual(qs, 20)
        self.assertEqual(csw, 11)
        self.assertEqual(step, 1)
        self.assertEqual(qe, 31)

    def test_xinje_duplex_queue_10(self) -> None:
        """Xinje duplex: q_end = 20 + 22 = 42."""
        qs, csw, step, qe = self._params(queue_size=10, duplex=True, xinje=True)
        self.assertEqual(qs, 20)
        self.assertEqual(csw, 11)
        self.assertEqual(step, 2)
        self.assertEqual(qe, 42)

    def test_delta_simplex_queue_10(self) -> None:
        """Delta simplex."""
        qs, csw, step, qe = self._params(queue_size=10, duplex=False, xinje=False)
        self.assertEqual(qs, 4146)
        self.assertEqual(csw, 2567)
        self.assertEqual(step, 1)
        self.assertEqual(qe, 4157)

    def test_delta_duplex_queue_10(self) -> None:
        """Delta duplex: q_end = 4146 + 22 = 4168."""
        qs, csw, step, qe = self._params(queue_size=10, duplex=True, xinje=False)
        self.assertEqual(qs, 4146)
        self.assertEqual(csw, 2567)
        self.assertEqual(step, 2)
        self.assertEqual(qe, 4168)


class TestDmcModbusBaseDefaults(unittest.TestCase):
    """Constructor defaults."""

    @unittest.mock.patch("core.controller.dmc_modbus.base.get_modbus", return_value=MagicMock())
    def test_default_slave_id_is_zero(self, _mock: MagicMock) -> None:
        proxy = DmcModbusBase("127.0.0.1:5020")
        self.assertEqual(proxy.id, 0)


class TestDoypackSingleCycle(unittest.IsolatedAsyncioTestCase):
    """One queue sweep with mocked Modbus client."""

    async def test_one_cycle_writes_expected_holding_values(self) -> None:
        """Holding 1→3, 0→4; coil can_start_work False before each read."""
        fake = _FakeDmcModbus()
        emulation = DoypackEmulation(
            "127.0.0.1:65020",
            queue_size=1,
            duplex=False,
            xinje=True,
        )
        emulation._controller = fake  # type: ignore[assignment]
        emulation.running = True
        fake._hr[emulation.q_start] = 1
        fake._hr[emulation.q_start + emulation._step] = 0

        await emulation.process_single_cycle()

        writes = [(a, d, c) for op, a, d, c in fake.calls if op == "write"]
        reads_hr = [a for op, a, _cnt, c in fake.calls if op == "read" and not c]

        self.assertEqual(
            reads_hr,
            [emulation.q_start, emulation.q_start + emulation._step],
        )

        expected_coil = (emulation.can_start_work, False, True)
        self.assertEqual(writes.count(expected_coil), 2)
        self.assertEqual(writes, [
            expected_coil,
            (emulation.q_start, 3, False),
            expected_coil,
            (emulation.q_start + emulation._step, 4, False),
        ])


class TestDoypackImportNoQt(unittest.TestCase):
    """``core.controller`` must not load PySide."""

    def test_import_without_pyside(self) -> None:
        """Run isolated import so earlier tests do not preload Qt."""
        repo_root = Path(__file__).resolve().parents[2]
        code = (
            "import sys;"
            "import core.controller;"
            "assert 'PySide6' not in sys.modules;"
            "assert 'PySide2' not in sys.modules"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=proc.stdout + proc.stderr,
        )


if __name__ == "__main__":
    unittest.main()
