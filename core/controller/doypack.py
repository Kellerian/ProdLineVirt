"""Doypack queue emulation loop over Modbus holding registers."""

from __future__ import annotations

import asyncio
import logging
from types import TracebackType
from typing import Optional

from core.controller.dmc_modbus.base import DmcModbusBase
from libs.loggers import CONTROLLER_LOGGER

# План #1: ядро контроллера логирует через stdlib `logging` и имя `CTL`, не через DMC-обёртки.
logger = logging.getLogger(CONTROLLER_LOGGER)


class DoypackEmulation:
    """Emulates Doypack line controller behavior via async Modbus reads/writes."""

    def __init__(
        self,
        ip: str,
        queue_size: int,
        *,
        duplex: bool = False,
        xinje: bool = False,
    ) -> None:
        """Compute register map limits and store connection target.

        Parameters
        ----------
        ip
            ``"host:port"`` string for the Modbus TCP client (loopback for the card).
        queue_size
            Number of queue slots; used with ``step`` to compute ``q_end``.
        duplex
            If True, register stride ``step`` is 2; otherwise 1.
        xinje
            If True, use Xinje register addresses; otherwise Delta.

        Raises
        ------
        ValueError
            If ``queue_size`` is not a bare ``int`` or is outside ``1..1000``
            (same domain as :attr:`core.controller.data.ControllerConfig.queue_size`).
        """
        if (
            not isinstance(queue_size, int)
            or isinstance(queue_size, bool)
            or not (1 <= queue_size <= 1000)
        ):
            raise ValueError(
                "queue_size должен быть целым числом (int) в диапазоне от 1 до 1000 "
                "включительно (как у ControllerConfig.queue_size)."
            )

        self.ip = ip
        self._controller: Optional[DmcModbusBase] = None
        self.running = False
        self._duplex = duplex
        self._xinje = xinje
        self._step = 2 if duplex else 1
        self._task: Optional[asyncio.Task[None]] = None
        self._queue_lock = asyncio.Lock()

        if xinje:
            self.q_start = 20
            self.can_start_work = 11
        else:
            self.q_start = 4146
            self.can_start_work = 2567

        self.q_end = self.q_start + (queue_size + 1) * self._step

    async def __aenter__(self) -> DoypackEmulation:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()

    async def stop(self) -> None:
        """Stop the background task and disconnect the Modbus client.

        Idempotent: always completes teardown (disconnect, clear task reference).

        If the background poll task ended with an error before cancellation, or
        finishes with an unexpected error while ``await task`` runs after
        ``cancel()`` (rare), that exception is logged to the ``CTL`` logger with
        ``exc_info`` only; it is **not** re-raised, so the UI/runtime always gets
        a normal coroutine return from ``stop()``. Inspect logs for Modbus or
        loop diagnostics — do not rely on an exception from this method for that.
        """
        self.running = False
        task = self._task
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.error(
                    "Doypack emulation background task ended with error addr=%s",
                    self.ip,
                    exc_info=True,
                )
            self._task = None

        if self._controller:
            await self._controller.disconnect()
            self._controller = None
        logger.info(
            "Doypack emulation stopped addr=%s duplex=%s xinje=%s",
            self.ip,
            self._duplex,
            self._xinje,
        )

    async def start(self) -> None:
        """Connect and start the background emulation loop.

        Raises
        ------
        RuntimeError
            If the emulation is already running, the background task is still
            active, or the Modbus TCP client cannot connect (e.g. server down).
        """
        if self.running or (self._task is not None and not self._task.done()):
            raise RuntimeError(
                "Эмуляция Doypack уже запущена или фоновый цикл ещё активен; "
                "повторный вызов start() недопустим. Сначала вызовите stop()."
            )

        if self._task is not None and self._task.done():
            self._task = None

        self._controller = DmcModbusBase(self.ip)
        connected = await self._controller.connect()
        if not connected:
            logger.error(
                "Doypack emulation Modbus connect failed addr=%s duplex=%s xinje=%s",
                self.ip,
                self._duplex,
                self._xinje,
            )
            await self._controller.disconnect()
            self._controller = None
            raise RuntimeError(
                f"Не удалось подключиться к Modbus по адресу {self.ip}"
            )

        self.running = True
        self._task = asyncio.create_task(self._run())
        logger.info(
            "Doypack emulation started addr=%s duplex=%s xinje=%s q_start=%s q_end=%s",
            self.ip,
            self._duplex,
            self._xinje,
            self.q_start,
            self.q_end,
        )

    async def _step_queue_iteration(self, address: int) -> None:
        """One queue slot: coil reset, read holding, write status code, short delay."""
        assert self._controller is not None
        async with self._queue_lock:
            await self._controller.write(self.can_start_work, False, coil=True)
            value = await self._controller.read(address, 1, coil=False)

            if value == 1:
                await self._controller.write(address, 3, coil=False)
            elif value == 0:
                await self._controller.write(address, 4, coil=False)

            await asyncio.sleep(0.1)

    async def _run(self) -> None:
        """Poll holding registers between ``q_start`` and ``q_end``."""
        assert self._controller is not None
        address = self.q_start
        while self.running:
            if address >= self.q_end:
                address = self.q_start
            try:
                await self._step_queue_iteration(address)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.error(
                    "Doypack emulation iteration failed addr=%s",
                    address,
                    exc_info=True,
                )
                if not self.running:
                    break
                await asyncio.sleep(0.5)
                continue
            address += self._step

    async def process_single_cycle(self) -> None:
        """Run one full sweep over the queue range.

        Intended for unit tests with a mocked client: call after ``start()`` has
        connected the client but **without** the background ``_task`` running
        (``_task`` must be cleared/cancelled first), or set ``running`` and
        inject a fake controller as tests do. Not for use alongside an active
        background poll task (see guard below).
        """
        if not self._controller or not self.running:
            raise RuntimeError("Эмуляция не запущена")
        if self._task is not None and not self._task.done():
            raise RuntimeError(
                "process_single_cycle недоступен пока работает фоновый цикл Doypack"
            )

        for address in range(self.q_start, self.q_end, self._step):
            await self._step_queue_iteration(address)

    async def get_status(self, address: int) -> int:
        """Read a single holding register at ``address``."""
        if not self._controller:
            raise RuntimeError("Контроллер не подключен")
        async with self._queue_lock:
            return await self._controller.read(address, 1, coil=False)

    async def set_status(self, address: int, value: int) -> None:
        """Write a holding register at ``address``."""
        if not self._controller:
            raise RuntimeError("Контроллер не подключен")
        async with self._queue_lock:
            await self._controller.write(address, value, coil=False)
