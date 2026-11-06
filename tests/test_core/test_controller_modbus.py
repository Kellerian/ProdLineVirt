"""Integration tests for ModbusEmulator TCP server lifecycle and datastore bounds."""

from __future__ import annotations

import asyncio
import logging
import socket
import unittest
from unittest.mock import AsyncMock, MagicMock

from pymodbus.client import AsyncModbusTcpClient

from core.controller.dmc_modbus.exceptions import LineControllerException
from core.controller.dmc_modbus.helpers import get_modbus
from core.controller.modbus_server import ModbusEmulator


def _unused_port() -> int:
    """Return a free TCP port (>1024) on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        _host, port = sock.getsockname()
    assert port > 1024
    return int(port)


def _can_bind_port(port: int) -> bool:
    """True if ``("", port)`` accepts bind without SO_REUSEADDR."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", port))
    except OSError:
        return False
    return True


async def _wait_bind_free(port: int, timeout_s: float = 2.0) -> None:
    """Wait until the port is free (TIME_WAIT on Windows)."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    while loop.time() < deadline:
        if _can_bind_port(port):
            return
        await asyncio.sleep(0.05)
    if not _can_bind_port(port):
        raise AssertionError(f"port {port} still in use after {timeout_s}s")


class TestModbusEmulatorTcp(unittest.IsolatedAsyncioTestCase):
    """Start/stop server, external client read, bind checks, two ports."""

    async def test_start_read_stop_bind_repeat(self) -> None:
        """Holding read after start; bind after stop; second start OK."""
        port = _unused_port()
        emulator = ModbusEmulator(host="0.0.0.0", port=port, slave_id=1)
        await emulator.start(initial_values={"holding_registers": {0: 42}})

        client = AsyncModbusTcpClient("127.0.0.1", port=port, timeout=1.0, retries=0)
        self.assertTrue(await client.connect())
        try:
            rr = await client.read_holding_registers(0, count=1, device_id=0)
            if rr.isError():
                self.fail(f"read holding failed: {rr}")
            self.assertEqual(rr.registers[0], 42)
        finally:
            client.close()

        await emulator.stop()
        await _wait_bind_free(port)

        await emulator.start(initial_values={"holding_registers": {0: 42}})
        client2 = AsyncModbusTcpClient("127.0.0.1", port=port, timeout=1.0, retries=0)
        self.assertTrue(await client2.connect())
        try:
            rr2 = await client2.read_holding_registers(0, count=1, device_id=0)
            if rr2.isError():
                self.fail(f"read holding failed after second start: {rr2}")
            self.assertEqual(rr2.registers[0], 42)
        finally:
            client2.close()

        await emulator.stop()
        await _wait_bind_free(port)

    async def test_two_emulators_independent(self) -> None:
        """Two servers on different ports; stopping one leaves the other listening."""
        p1 = _unused_port()
        p2 = _unused_port()
        while p2 == p1:
            p2 = _unused_port()

        emu1 = ModbusEmulator(host="0.0.0.0", port=p1)
        emu2 = ModbusEmulator(host="0.0.0.0", port=p2)
        await emu1.start()
        await emu2.start()

        c1 = AsyncModbusTcpClient("127.0.0.1", port=p1, timeout=1.0, retries=0)
        c2 = AsyncModbusTcpClient("127.0.0.1", port=p2, timeout=1.0, retries=0)
        self.assertTrue(await c1.connect())
        self.assertTrue(await c2.connect())
        try:
            await emu1.stop()
            await _wait_bind_free(p1)
        finally:
            c1.close()

        try:
            rr = await c2.read_holding_registers(0, count=1, device_id=0)
            if rr.isError():
                self.fail(f"second server should still respond: {rr}")
        finally:
            c2.close()

        await emu2.stop()
        await _wait_bind_free(p2)

    async def test_out_of_range_coil_and_holding_rejected(self) -> None:
        """Address 5000 coil and 10000 holding are valid; 5001 and 10001 are not."""
        port = _unused_port()
        emulator = ModbusEmulator(host="0.0.0.0", port=port)
        await emulator.start()

        client = AsyncModbusTcpClient("127.0.0.1", port=port, timeout=1.0, retries=0)
        self.assertTrue(await client.connect())
        try:
            ok_coil = await client.write_coil(5000, True, device_id=0)
            self.assertFalse(ok_coil.isError(), ok_coil)

            bad_coil = await client.write_coil(5001, True, device_id=0)
            self.assertTrue(bad_coil.isError())

            ok_hr = await client.write_register(10000, 7, device_id=0)
            self.assertFalse(ok_hr.isError(), ok_hr)

            bad_hr = await client.write_register(10001, 7, device_id=0)
            self.assertTrue(bad_hr.isError())
        finally:
            client.close()

        await emulator.stop()
        await _wait_bind_free(port)


class TestGetModbusPortValidation(unittest.TestCase):
    """Unit tests for ``get_modbus`` TCP port bounds."""

    def test_rejects_port_zero(self) -> None:
        with self.assertRaises(LineControllerException) as ctx:
            get_modbus("127.0.0.1:0")
        self.assertIn("Порт должен быть", str(ctx.exception))

    def test_rejects_port_65536(self) -> None:
        with self.assertRaises(LineControllerException) as ctx:
            get_modbus("127.0.0.1:65536")
        self.assertIn("Порт должен быть", str(ctx.exception))

    def test_rejects_negative_port(self) -> None:
        with self.assertRaises(LineControllerException) as ctx:
            get_modbus("127.0.0.1:-1")
        self.assertIn("Порт должен быть", str(ctx.exception))

    def test_rejects_empty_host(self) -> None:
        """``:port`` parses to empty host (unlike ``[::]:port`` which is IPv6 ``::``)."""
        with self.assertRaises(LineControllerException) as ctx:
            get_modbus(":5020")
        self.assertIn("Хост не может быть пустым", str(ctx.exception))


class TestModbusDatastoreInitialValues(unittest.TestCase):
    """Out-of-range initial coil/holding addresses are skipped with a warning."""

    def test_setup_datastore_logs_out_of_range_once_per_bad_entry(self) -> None:
        logs = logging.getLogger("CTL")
        prior = logs.level
        try:
            logs.setLevel(logging.WARNING)
            with self.assertLogs("CTL", level=logging.WARNING) as captured:
                emulator = ModbusEmulator()
                emulator.setup_datastore(
                    {
                        "coils": {5001: True, 4999: True},
                        "holding_registers": {10001: 1, 9999: 7},
                    }
                )
        finally:
            logs.setLevel(prior)

        coil_warnings = [
            r
            for r in captured.output
            if "начального значения coil" in r and "5001" in r
        ]
        holding_warnings = [
            r
            for r in captured.output
            if "начального значения holding" in r and "10001" in r
        ]
        self.assertEqual(len(coil_warnings), 1)
        self.assertEqual(len(holding_warnings), 1)

        self.assertTrue(emulator.context is not None)
        self.assertTrue(emulator.get_coil(4999))
        self.assertEqual(emulator.get_holding_register(9999), 7)


class TestModbusEmulatorStopShutdownFailure(unittest.IsolatedAsyncioTestCase):
    """``stop`` drains state even when ``shutdown`` raises."""

    async def test_stop_cleans_up_when_shutdown_raises(self) -> None:
        """After failed shutdown, resources are cleared and chain is preserved."""
        emulator = ModbusEmulator(host="127.0.0.1", port=_unused_port())
        mock_server = MagicMock()
        mock_server.shutdown = AsyncMock(side_effect=RuntimeError("boom"))

        async def _done() -> None:
            return

        serve_task = asyncio.create_task(_done())
        await asyncio.sleep(0)

        emulator._server = mock_server
        emulator._serve_task = serve_task

        with self.assertRaises(RuntimeError) as ctx:
            await emulator.stop()

        self.assertIn("shutdown failed", str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)
        self.assertEqual(str(ctx.exception.__cause__), "boom")
        self.assertIsNone(emulator._server)
        self.assertIsNone(emulator._serve_task)
        self.assertIsNone(emulator.context)


if __name__ == "__main__":
    unittest.main()
