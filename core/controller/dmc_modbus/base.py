"""Thin async Modbus proxy used by Doypack emulation."""

from __future__ import annotations

import asyncio
import logging
from types import TracebackType
from typing import Any

from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu.bit_message import ReadCoilsResponse
from pymodbus.pdu.register_message import ReadHoldingRegistersResponse
from socket import IPPROTO_TCP, SOL_SOCKET, TCP_NODELAY, SO_KEEPALIVE

from core.controller.dmc_modbus.helpers import get_modbus
from libs.loggers import CONTROLLER_LOGGER

# План #1: контроллер — stdlib `logging` с именем CTL (см. подзадача #1 в плане линии).
logger = logging.getLogger(CONTROLLER_LOGGER)


class DmcModbusBase:
    """Async Modbus TCP helper with optional coil/holding read-write."""

    def __init__(self, addr: str, slave_id: int = 0) -> None:
        """Initialize proxy; call :meth:`connect` before I/O.

        Parameters
        ----------
        addr
            ``"host:port"`` string passed to :func:`get_modbus`.
        slave_id
            Modbus unit / device id for requests (default ``0``).
        """
        self.id = slave_id
        self.addr = addr
        self._modbus = get_modbus(addr)
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> DmcModbusBase:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.disconnect()

    async def connect(self) -> bool:
        """Connect to the server and tune the TCP socket when possible."""
        res = await self._modbus.connect()
        if not res:
            logger.debug("Modbus connect returned False for addr=%s", self.addr)
            return False

        if hasattr(self._modbus, "socket") and self._modbus.socket:
            try:
                self._modbus.socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
                self._modbus.socket.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
            except OSError:
                logger.debug(
                    "Modbus socket setsockopt failed addr=%s",
                    self.addr,
                    exc_info=True,
                )
        return res

    async def disconnect(self) -> None:
        """Close the underlying client."""
        async with self._lock:
            if self._modbus and self._modbus.connected:
                # pymodbus AsyncModbusTcpClient.close() — синхронный в их API (как в __aexit__);
                # сознательно не await.
                self._modbus.close()

    async def _write(self, address: int, data: bool | int, *, coil: bool) -> None:
        async with self._lock:
            if not self._modbus.connected:
                raise ModbusIOException("Нет подключения к контроллеру")

            if coil:
                result = await self._modbus.write_coil(
                    address, data, device_id=self.id
                )
            else:
                result = await self._modbus.write_register(
                    address, data, device_id=self.id
                )

            if result.isError():
                raise ModbusIOException(f"Ошибка записи в контроллер: {result}")

    async def _read(self, address: int, count: int, *, coil: bool) -> Any:
        async with self._lock:
            if not self._modbus.connected:
                raise ModbusIOException("Нет подключения к контроллеру")

            if coil:
                result = await self._modbus.read_coils(
                    address, count=count, device_id=self.id
                )
            else:
                result = await self._modbus.read_holding_registers(
                    address, count=count, device_id=self.id
                )

            if result.isError():
                raise ModbusIOException(f"Ошибка чтения из контроллера: {result}")

            if isinstance(result, ReadHoldingRegistersResponse):
                if count > 1:
                    return result.registers
                return result.registers[0]
            if isinstance(result, ReadCoilsResponse):
                if count > 1:
                    return result.bits
                return result.bits[0]
            raise ModbusIOException(f"Unexpected Modbus response type: {type(result)}")

    async def write(self, address: int, data: bool | int, *, coil: bool) -> None:
        """Write a coil or holding register."""
        await self._write(address, data, coil=coil)

    async def read(self, address: int, count: int, *, coil: bool) -> Any:
        """Read coils or holding registers."""
        return await self._read(address, count, coil=coil)
