"""Tests for :class:`core.controller.runtime.ControllerRuntime`."""

from __future__ import annotations

import socket
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from pymodbus.client import AsyncModbusTcpClient

from core.controller.dmc_modbus.base import DmcModbusBase
from core.controller.runtime import (
    ControllerRuntime,
    _can_bind_port,
    _wait_bind_free,
)


def _unused_port() -> int:
    """Return a free TCP port (>1024) on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        _host, port = sock.getsockname()
    assert port > 1024
    return int(port)


class TestControllerRuntimeIntegration(unittest.TestCase):
    """Lifecycle, ports, and independence of two runtimes."""

    def test_start_tcp_connect_stop_bind_free(self) -> None:
        """Listener accepts TCP; after stop, port binds without SO_REUSEADDR."""
        port = _unused_port()
        rt = ControllerRuntime()
        try:
            rt.start(port=port, queue_size=10, duplex=False, xinje=False)
            with socket.create_connection(("127.0.0.1", port), timeout=2.0):
                pass
        finally:
            rt.stop()
        _wait_bind_free(port, timeout_s=2.0)
        self.assertTrue(_can_bind_port(port))

    def test_two_runtimes_independent(self) -> None:
        """Stopping one runtime does not stop the other (TCP still connects)."""
        p1 = _unused_port()
        p2 = _unused_port()
        while p2 == p1:
            p2 = _unused_port()
        rt1 = ControllerRuntime()
        rt2 = ControllerRuntime()
        try:
            rt1.start(port=p1, queue_size=5, duplex=False, xinje=False)
            rt2.start(port=p2, queue_size=5, duplex=True, xinje=True)
            with socket.create_connection(("127.0.0.1", p1), timeout=2.0):
                pass
            with socket.create_connection(("127.0.0.1", p2), timeout=2.0):
                pass
            rt1.stop()
            _wait_bind_free(p1, timeout_s=2.0)
            with socket.create_connection(("127.0.0.1", p2), timeout=2.0):
                pass
        finally:
            rt2.stop()
            rt1.stop()
        _wait_bind_free(p1, timeout_s=2.0)
        _wait_bind_free(p2, timeout_s=2.0)

    def test_start_fails_when_port_in_use(self) -> None:
        """Foreign listen on port → start raises; worker ends; port free after holder close."""
        port = _unused_port()
        holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rt = ControllerRuntime()
        try:
            holder.bind(("0.0.0.0", port))
            holder.listen()
            with self.assertRaises(RuntimeError):
                rt.start(port=port, queue_size=10, duplex=False, xinje=False)
        finally:
            holder.close()
        self.assertIsNone(rt._thread)
        _wait_bind_free(port, timeout_s=2.0)
        self.assertTrue(_can_bind_port(port))

    def test_invalid_queue_size(self) -> None:
        """``queue_size`` outside 1..1000 raises :exc:`ValueError` before any thread."""
        port = _unused_port()
        rt = ControllerRuntime()
        with self.assertRaises(ValueError):
            rt.start(port=port, queue_size=0, duplex=False, xinje=False)
        self.assertIsNone(rt._thread)

    def test_start_twice_raises(self) -> None:
        """Second :meth:`start` while running raises :exc:`RuntimeError`."""
        port = _unused_port()
        rt = ControllerRuntime()
        try:
            rt.start(port=port, queue_size=10, duplex=False, xinje=False)
            with self.assertRaises(RuntimeError) as ctx:
                rt.start(port=port, queue_size=10, duplex=False, xinje=False)
            self.assertEqual(str(ctx.exception), "Controller runtime already running")
        finally:
            rt.stop()
        _wait_bind_free(port, timeout_s=2.0)

    def test_doypack_connect_fails_rollback_frees_port(self) -> None:
        """If Modbus is up but Doypack cannot connect, start fails and port is released."""
        port = _unused_port()
        rt = ControllerRuntime()
        with patch.object(
            DmcModbusBase,
            "connect",
            new_callable=AsyncMock,
            return_value=False,
        ):
            with self.assertRaises(RuntimeError):
                rt.start(port=port, queue_size=10, duplex=False, xinje=False)
        self.assertIsNone(rt._thread)
        _wait_bind_free(port, timeout_s=2.0)
        self.assertTrue(_can_bind_port(port))


class TestControllerRuntimeStopOrder(unittest.TestCase):
    """Order of teardown: Doypack before Modbus."""

    def test_runtime_module_has_no_qasync_import(self) -> None:
        """Regression: ``core.controller.runtime`` must not reference ``qasync``."""
        text = (
            Path(__file__).resolve().parent.parent.parent
            / "core"
            / "controller"
            / "runtime.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("qasync", text)

    def test_stop_calls_doypack_then_modbus(self) -> None:
        """``stop`` schedules ``await doypack.stop()`` before ``await modbus.stop()``."""
        stop_order: list[str] = []

        modbus_inst = MagicMock()
        doypack_inst = MagicMock()

        async def track_doypack_stop() -> None:
            stop_order.append("doypack")

        async def track_modbus_stop() -> None:
            stop_order.append("modbus")

        doypack_inst.stop = AsyncMock(side_effect=track_doypack_stop)
        modbus_inst.stop = AsyncMock(side_effect=track_modbus_stop)
        modbus_inst.start = AsyncMock()
        doypack_inst.start = AsyncMock()

        def make_modbus(*_args: object, **_kwargs: object) -> MagicMock:
            return modbus_inst

        def make_doypack(*_args: object, **_kwargs: object) -> MagicMock:
            return doypack_inst

        port = _unused_port()
        rt = ControllerRuntime()
        with patch(
            "core.controller.runtime.ModbusEmulator", side_effect=make_modbus
        ), patch(
            "core.controller.runtime.DoypackEmulation",
            side_effect=make_doypack,
        ):
            rt.start(port=port, queue_size=10, duplex=False, xinje=False)
            rt.stop()

        self.assertEqual(stop_order, ["doypack", "modbus"])


class TestControllerRuntimeReadHoldingRegisters(unittest.IsolatedAsyncioTestCase):
    """``read_holding_registers``: worker loop, validation, lifecycle."""

    async def test_external_client_write_then_read_holding(self) -> None:
        """External client sets registers; runtime returns values and None for invalid."""
        port = _unused_port()
        rt = ControllerRuntime()
        try:
            rt.start(port=port, queue_size=10, duplex=False, xinje=False)
            client = AsyncModbusTcpClient("127.0.0.1", port=port, timeout=1.0, retries=0)
            self.assertTrue(await client.connect())
            try:
                w1 = await client.write_register(4146, 4, device_id=0)
                self.assertFalse(w1.isError(), w1)
                w2 = await client.write_register(4150, 0, device_id=0)
                self.assertFalse(w2.isError(), w2)
            finally:
                client.close()

            values = rt.read_holding_registers([4146, 4150, 10001, -1])
            self.assertEqual(values, [4, 0, None, None])
        finally:
            rt.stop()

    def test_read_holding_empty_list(self) -> None:
        """Empty address list returns ``[]`` without touching the worker."""
        port = _unused_port()
        rt = ControllerRuntime()
        try:
            rt.start(port=port, queue_size=10, duplex=False, xinje=False)
            self.assertEqual(rt.read_holding_registers([]), [])
        finally:
            rt.stop()

    def test_read_holding_after_stop_all_none(self) -> None:
        """After ``stop``, non-empty read returns all ``None``."""
        port = _unused_port()
        rt = ControllerRuntime()
        rt.start(port=port, queue_size=10, duplex=False, xinje=False)
        rt.stop()
        self.assertEqual(rt.read_holding_registers([0, 1]), [None, None])

    def test_read_holding_before_start_all_none(self) -> None:
        """Before ``start``, every address maps to ``None``."""
        rt = ControllerRuntime()
        self.assertEqual(rt.read_holding_registers([0]), [None])

    def test_runtime_module_has_no_qt_or_async_client_imports(self) -> None:
        """``runtime.py`` must not pull in Qt, qasync, or ``AsyncModbusTcpClient``."""
        text = (
            Path(__file__).resolve().parent.parent.parent
            / "core"
            / "controller"
            / "runtime.py"
        ).read_text(encoding="utf-8")
        lowered = text.lower()
        self.assertNotIn("pyside", lowered)
        self.assertNotIn("qasync", text)
        self.assertNotIn("AsyncModbusTcpClient", text)


if __name__ == "__main__":
    unittest.main()
