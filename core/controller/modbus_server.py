"""Modbus TCP server emulator for the line controller (datastore + lifecycle)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from pymodbus import ModbusDeviceIdentification
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer

from libs.loggers import CONTROLLER_LOGGER

# План #1: ядро контроллера — stdlib logging + имя CTL; без DMC-обёрток.
logger = logging.getLogger(CONTROLLER_LOGGER)


class ModbusEmulator:
    """Async Modbus TCP server with fixed datastore layout and pymodbus 3.12 lifecycle."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5020,
        slave_id: int = 1,
    ) -> None:
        """Create emulator settings.

        ``slave_id`` is kept for logging and future routing; pymodbus is built
        with a single device context (tests use ``device_id=0`` on the client).
        """
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.context: Optional[ModbusServerContext] = None
        self._server: Optional[ModbusTcpServer] = None
        self._serve_task: Optional[asyncio.Task[None]] = None

        # pymodbus 3.x applies ``address + 1`` inside ``ModbusDeviceContext``; with
        # sequential blocks starting at 0, index ``n + 1`` backs Modbus address ``n``.
        # Capacity must allow writes at coil 5000 and holding 10000 (see acceptance tests).
        self.coils_size = 5002
        self.discrete_inputs_size = 102
        self.holding_registers_size = 10002
        self.input_registers_size = 102

    def setup_datastore(self, initial_values: Optional[Dict[str, Any]] = None) -> None:
        """Build Modbus datastore blocks and single-device server context.

        Parameters
        ----------
        initial_values
            Optional ``coils`` / ``holding_registers`` address maps.
        """
        coils_data = [False] * self.coils_size
        holding_data = [0] * self.holding_registers_size

        if initial_values:
            if "coils" in initial_values:
                for addr, value in initial_values["coils"].items():
                    idx = addr + 1
                    if 0 <= idx < self.coils_size:
                        coils_data[idx] = value
                    else:
                        logger.warning(
                            "Modbus datastore: пропуск начального значения coil, "
                            "Modbus-адрес %s вне допустимого индекса (0 ≤ адрес ≤ %s)",
                            addr,
                            self.coils_size - 2,
                        )

            if "holding_registers" in initial_values:
                for addr, value in initial_values["holding_registers"].items():
                    idx = addr + 1
                    if 0 <= idx < self.holding_registers_size:
                        holding_data[idx] = value
                    else:
                        logger.warning(
                            "Modbus datastore: пропуск начального значения holding, "
                            "Modbus-адрес %s вне допустимого индекса (0 ≤ адрес ≤ %s)",
                            addr,
                            self.holding_registers_size - 2,
                        )

        coils = ModbusSequentialDataBlock(0, coils_data)
        discrete_inputs = ModbusSequentialDataBlock(
            0, [False] * self.discrete_inputs_size
        )
        holding_registers = ModbusSequentialDataBlock(0, holding_data)
        input_registers = ModbusSequentialDataBlock(
            0, [0] * self.input_registers_size
        )

        slave_context = ModbusDeviceContext(
            di=discrete_inputs,
            co=coils,
            hr=holding_registers,
            ir=input_registers,
        )

        self.context = ModbusServerContext(devices=slave_context, single=True)

    @staticmethod
    def setup_device_info() -> ModbusDeviceIdentification:
        """Device identification block reported to Modbus clients."""
        identity = ModbusDeviceIdentification()
        identity.VendorName = "PyModbus"
        identity.ProductCode = "EMU"
        identity.VendorUrl = "https://github.com/pymodbus-dev/pymodbus/"
        identity.ProductName = "Modbus Emulator"
        identity.ModelName = "Emulator"
        identity.MajorMinorRevision = "1.0"
        return identity

    async def start(self, initial_values: Optional[Dict[str, Any]] = None) -> None:
        """Create server, listen, and wait until the socket is active.

        Raises
        ------
        RuntimeError
            If a start is attempted while the server is already running.
        """
        if self._serve_task is not None and not self._serve_task.done():
            raise RuntimeError("Modbus emulator server is already running")

        self.setup_datastore(initial_values)
        assert self.context is not None
        identity = self.setup_device_info()

        self._server = ModbusTcpServer(
            self.context,
            identity=identity,
            address=(self.host, self.port),
        )

        async def _run() -> None:
            assert self._server is not None
            await self._server.serve_forever()

        self._serve_task = asyncio.create_task(_run())

        loop = asyncio.get_running_loop()
        deadline = loop.time() + 5.0
        while self._server is not None and not self._server.is_active():
            if self._serve_task.done():
                exc = self._serve_task.exception()
                self._serve_task = None
                self._server = None
                err = RuntimeError(
                    f"Modbus TCP server failed to start on {self.host}:{self.port}"
                )
                if exc is not None:
                    logger.error(
                        "Modbus TCP server task failed host=%s port=%s",
                        self.host,
                        self.port,
                        exc_info=(type(exc), exc, exc.__traceback__),
                    )
                    raise err from exc
                logger.error("%s", err)
                raise err
            if loop.time() >= deadline:
                err = RuntimeError(
                    f"Modbus TCP server failed to listen on {self.host}:{self.port}"
                )
                # No active exception here — avoid exc_info=True (misleading stack in logs).
                logger.error("%s", err)
                try:
                    await self.stop()
                except Exception:
                    logger.error(
                        "Modbus emulator: cleanup failed after listen timeout "
                        "host=%s port=%s",
                        self.host,
                        self.port,
                        exc_info=True,
                    )
                raise err
            await asyncio.sleep(0.01)

        logger.info(
            "Modbus TCP server started host=%s port=%s slave_id=%s",
            self.host,
            self.port,
            self.slave_id,
        )

    async def _await_serve_task(
        self, serve_task: asyncio.Task[None] | None
    ) -> None:
        """Wait for ``serve_task`` to finish, with cancel-on-timeout (up to 5s)."""
        if serve_task is None:
            return
        try:
            await asyncio.wait_for(serve_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.error(
                "Modbus serve_forever task did not finish in time host=%s port=%s",
                self.host,
                self.port,
            )
            serve_task.cancel()
            try:
                await serve_task
            except asyncio.CancelledError:
                pass

    async def stop(self) -> None:
        """Shut down listener and await the serve task (no task.cancel before shutdown)."""
        server = self._server
        serve_task = self._serve_task

        if server is None and serve_task is None:
            return

        shutdown_exc: Exception | None = None
        if server is not None:
            try:
                await server.shutdown()
            except Exception as exc:
                logger.error(
                    "Modbus TCP server shutdown failed host=%s port=%s",
                    self.host,
                    self.port,
                    exc_info=True,
                )
                shutdown_exc = exc

        await self._await_serve_task(serve_task)
        self._serve_task = None
        self._server = None
        self.context = None

        if shutdown_exc is not None:
            raise RuntimeError(
                f"Modbus TCP server shutdown failed on {self.host}:{self.port}"
            ) from shutdown_exc

        logger.info(
            "Modbus TCP server stopped host=%s port=%s",
            self.host,
            self.port,
        )

    def _require_datastore(self) -> None:
        """Raise if the Modbus datastore was not built (before start/setup_datastore)."""
        if self.context is None:
            raise RuntimeError(
                "Modbus datastore is not initialized; call start() or setup_datastore() first."
            )

    def update_coil(self, address: int, value: bool) -> None:
        """Write a coil at Modbus address ``address`` (same numbering as wire protocol).

        Raises
        ------
        RuntimeError
            If ``setup_datastore()`` / ``start()`` has not run (no datastore).
        """
        self._require_datastore()
        assert self.context is not None
        self.context[0].setValues(1, address, [value])

    def update_holding_register(self, address: int, value: int) -> None:
        """Write a holding register at Modbus address ``address``.

        Raises
        ------
        RuntimeError
            If ``setup_datastore()`` / ``start()`` has not run (no datastore).
        """
        self._require_datastore()
        assert self.context is not None
        self.context[0].setValues(3, address, [value])

    def get_coil(self, address: int) -> bool:
        """Read a single coil at Modbus address ``address``.

        Raises
        ------
        RuntimeError
            If ``setup_datastore()`` / ``start()`` has not run (no datastore).
        """
        self._require_datastore()
        assert self.context is not None
        return self.context[0].getValues(1, address, count=1)[0]

    def get_holding_register(self, address: int) -> int:
        """Read a single holding register at Modbus address ``address``.

        Raises
        ------
        RuntimeError
            If ``setup_datastore()`` / ``start()`` has not run (no datastore).
        """
        self._require_datastore()
        assert self.context is not None
        return self.context[0].getValues(3, address, count=1)[0]

    def get_multiple_registers(self, address: int, count: int) -> list[int]:
        """Read ``count`` holding registers starting at ``address``.

        Raises
        ------
        RuntimeError
            If ``setup_datastore()`` / ``start()`` has not run (no datastore).
        """
        self._require_datastore()
        assert self.context is not None
        return self.context[0].getValues(3, address, count=count)
