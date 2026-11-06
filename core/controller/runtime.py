"""Background asyncio runtime for Modbus + Doypack controller emulation (no Qt)."""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import socket
import threading
import time
from collections.abc import Sequence
from typing import Optional

from core.controller.doypack import DoypackEmulation
from core.controller.modbus_server import ModbusEmulator
from libs.loggers import CONTROLLER_LOGGER

# План линии: подсистема контроллера — stdlib logging + имя CTL (как modbus_server/doypack).
logger = logging.getLogger(CONTROLLER_LOGGER)


def _can_bind_port(port: int) -> bool:
    """Return True if ``("", port)`` accepts bind without ``SO_REUSEADDR``."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("", port))
    except OSError:
        return False
    return True


def _wait_bind_free(port: int, timeout_s: float = 2.0) -> None:
    """Poll until ``port`` is free or ``timeout_s`` elapses."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if _can_bind_port(port):
            return
        time.sleep(0.05)


def _assert_listen_port_available(port: int) -> None:
    """Raise :exc:`RuntimeError` if ``port`` is not free for a new Modbus listener."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.25):
            pass
    except OSError:
        pass
    else:
        raise RuntimeError(
            f"Controller runtime cannot use TCP port {port} "
            "(already accepting connections on loopback)"
        )

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
            if exclusive is not None:
                try:
                    sock.setsockopt(socket.SOL_SOCKET, exclusive, 1)
                except OSError:
                    pass
            sock.bind(("0.0.0.0", port))
    except OSError as exc:
        raise RuntimeError(
            f"Controller runtime cannot bind TCP port {port} (address already in use or denied)"
        ) from exc


def _drain_tasks_and_close_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Cancel pending tasks, run shutdown hooks, and close ``loop`` (best-effort)."""
    try:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        logger.error(
            "Controller runtime: task drain failed",
            exc_info=True,
        )
    try:
        loop.run_until_complete(loop.shutdown_asyncgens())
    except Exception:
        logger.error(
            "Controller runtime: shutdown_asyncgens failed",
            exc_info=True,
        )
    try:
        loop.close()
    except Exception:
        logger.error(
            "Controller runtime: loop.close failed",
            exc_info=True,
        )


class ControllerRuntime:
    """Runs :class:`ModbusEmulator` and :class:`DoypackEmulation` on a dedicated thread.

    The public API is synchronous and safe to call from a UI main thread. The worker
    thread installs its own asyncio event loop; Qt is not used.
    """

    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._modbus: Optional[ModbusEmulator] = None
        self._doypack: Optional[DoypackEmulation] = None
        self._port: Optional[int] = None
        self._state_lock = threading.Lock()
        # Serializes start(); paired with _state_lock so two threads cannot both pass
        # the «already running» check before _thread is assigned.
        self._start_lock = threading.Lock()

    def start(
        self,
        port: int,
        queue_size: int,
        duplex: bool,
        xinje: bool,
    ) -> None:
        """Start listening on ``port`` and connect Doypack to ``127.0.0.1:{port}``.

        Blocks until both servers are up or raises on failure / 5s start budget.

        Raises
        ------
        RuntimeError
            If this runtime is already running, if the listen port is in use,
            or if the start phase does not become ready within 5 seconds.
        ValueError
            If ``queue_size`` is outside ``1..1000``.
        """
        if (
            not isinstance(queue_size, int)
            or isinstance(queue_size, bool)
            or not (1 <= queue_size <= 1000)
        ):
            raise ValueError(
                "queue_size must be int in 1..1000 inclusive "
                "(same domain as DoypackEmulation / ControllerConfig)."
            )

        with self._start_lock:
            with self._state_lock:
                self._join_stale_thread_unlocked()
                if self._thread is not None and self._thread.is_alive():
                    raise RuntimeError("Controller runtime already running")

            _assert_listen_port_available(port)

            ready: concurrent.futures.Future[
                tuple[ModbusEmulator, DoypackEmulation, asyncio.AbstractEventLoop]
            ] = concurrent.futures.Future()

            def _thread_target() -> None:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                modbus: Optional[ModbusEmulator] = None
                doypack: Optional[DoypackEmulation] = None

                async def _start_both() -> None:
                    nonlocal modbus, doypack
                    modbus = ModbusEmulator(host="0.0.0.0", port=port)
                    doypack = DoypackEmulation(
                        f"127.0.0.1:{port}",
                        queue_size,
                        duplex=duplex,
                        xinje=xinje,
                    )
                    assert modbus is not None and doypack is not None
                    await modbus.start()
                    await doypack.start()

                async def _rollback() -> None:
                    if doypack is not None:
                        try:
                            await doypack.stop()
                        except Exception:
                            logger.error(
                                "Controller runtime rollback: Doypack stop failed port=%s",
                                port,
                                exc_info=True,
                            )
                    if modbus is not None:
                        try:
                            await modbus.stop()
                        except Exception:
                            logger.error(
                                "Controller runtime rollback: Modbus stop failed port=%s",
                                port,
                                exc_info=True,
                            )

                try:
                    loop.run_until_complete(
                        asyncio.wait_for(_start_both(), timeout=5.0)
                    )
                except BaseException as exc:
                    try:
                        loop.run_until_complete(_rollback())
                    except BaseException:
                        logger.error(
                            "Controller runtime rollback failed port=%s",
                            port,
                            exc_info=True,
                        )
                    if not ready.done():
                        ready.set_exception(exc)
                    _drain_tasks_and_close_loop(loop)
                    return

                assert modbus is not None and doypack is not None
                ready.set_result((modbus, doypack, loop))
                try:
                    loop.run_forever()
                finally:
                    _drain_tasks_and_close_loop(loop)

            thread = threading.Thread(
                target=_thread_target,
                name=f"controller-{port}",
                daemon=False,
            )
            with self._state_lock:
                self._thread = thread
            thread.start()

            try:
                modbus_r, doypack_r, loop_r = ready.result(timeout=5.0)
            except concurrent.futures.TimeoutError as exc:
                logger.error(
                    "Controller runtime did not signal ready within 5s port=%s",
                    port,
                )
                with self._state_lock:
                    thr = self._thread
                if thr is not None:
                    thr.join(timeout=65.0)
                    if thr.is_alive():
                        logger.error(
                            "Controller runtime: worker still alive after ready timeout "
                            "join port=%s (refs kept; call stop() or abandon instance)",
                            port,
                        )
                    else:
                        with self._state_lock:
                            self._clear_refs_unlocked()
                raise RuntimeError(
                    "Controller runtime failed to become ready within 5 seconds"
                ) from exc
            except BaseException:
                with self._state_lock:
                    thr = self._thread
                if thr is not None:
                    thr.join(timeout=65.0)
                    if not thr.is_alive():
                        with self._state_lock:
                            self._clear_refs_unlocked()
                    else:
                        logger.error(
                            "Controller runtime: worker still alive after failed start "
                            "join port=%s (refs kept)",
                            port,
                        )
                raise

            with self._state_lock:
                self._modbus = modbus_r
                self._doypack = doypack_r
                self._loop = loop_r
                self._port = port

    def stop(self) -> None:
        """Stop Modbus and Doypack and join the worker thread (idempotent)."""
        with self._state_lock:
            thread = self._thread
            loop = self._loop
            doypack = self._doypack
            modbus = self._modbus
            port = self._port

        if thread is None:
            return
        if not thread.is_alive():
            with self._state_lock:
                self._clear_refs_unlocked()
            return
        if loop is None or loop.is_closed():
            thread.join(timeout=5.0)
            if thread.is_alive():
                logger.error(
                    "Controller runtime stop: no usable event loop but worker still alive "
                    "port=%s (refs kept)",
                    port,
                )
                return
            with self._state_lock:
                self._clear_refs_unlocked()
            return

        async def _shutdown() -> None:
            if doypack is not None:
                await doypack.stop()
            if modbus is not None:
                await modbus.stop()
            loop.call_soon_threadsafe(loop.stop)

        try:
            fut = asyncio.run_coroutine_threadsafe(_shutdown(), loop)
            fut.result(timeout=60.0)
        except Exception:
            logger.error(
                "Controller runtime stop: shutdown coroutine failed port=%s",
                port,
                exc_info=True,
            )
            try:
                loop.call_soon_threadsafe(loop.stop)
            except Exception:
                logger.error(
                    "Controller runtime stop: loop.stop failed port=%s",
                    port,
                    exc_info=True,
                )

        thread.join(timeout=5.0)
        if thread.is_alive():
            logger.error(
                "Controller runtime stop: thread join timed out port=%s "
                "(refs kept; worker may still hold the port)",
                port,
            )
            return

        if port is not None:
            _wait_bind_free(port, timeout_s=2.0)
            if not _can_bind_port(port):
                logger.error(
                    "Controller runtime stop: port %s still in use after 2s (bind check)",
                    port,
                )

        with self._state_lock:
            self._clear_refs_unlocked()

    def read_holding_registers(self, addresses: Sequence[int]) -> list[int | None]:
        """Read holding register values from the worker's Modbus datastore (synchronous).

        Schedules work on the runtime's asyncio loop via :func:`asyncio.run_coroutine_threadsafe`.
        Safe to call from a UI thread. Does not use Doypack ``get_status`` or a second Modbus
        client.

        Parameters
        ----------
        addresses
            Modbus holding addresses in ``0..10000`` (inclusive). Non-integers, ``bool``,
            and out-of-range values yield ``None`` for that slot without touching the datastore.

        Returns
        -------
        list[int | None]
            One entry per input address, same order. ``int`` is the register value; ``None``
            means invalid address, datastore error, stopped runtime, or read timeout (0.25 s).
            Empty ``addresses`` returns ``[]``.
        """
        if not addresses:
            return []

        addr_tuple = tuple(addresses)
        n = len(addr_tuple)

        with self._state_lock:
            loop = self._loop
            modbus = self._modbus
            thread = self._thread

        if (
            thread is None
            or not thread.is_alive()
            or loop is None
            or loop.is_closed()
            or modbus is None
        ):
            return [None] * n

        async def _read_on_loop() -> list[int | None]:
            results: list[int | None] = []
            for address in addr_tuple:
                if (
                    not isinstance(address, int)
                    or isinstance(address, bool)
                    or not (0 <= address <= 10000)
                ):
                    results.append(None)
                    continue
                try:
                    results.append(int(modbus.get_holding_register(address)))
                except Exception as exc:
                    logger.debug(
                        "Controller runtime read_holding_registers failed address=%s: %s",
                        address,
                        exc,
                    )
                    results.append(None)
            return results

        try:
            fut = asyncio.run_coroutine_threadsafe(_read_on_loop(), loop)
        except Exception as exc:
            logger.debug(
                "Controller runtime read_holding_registers schedule failed: %s",
                exc,
            )
            return [None] * n

        try:
            return fut.result(timeout=0.25)
        except concurrent.futures.TimeoutError:
            logger.debug(
                "Controller runtime read_holding_registers timed out after 0.25s",
            )
            return [None] * n
        except Exception as exc:
            logger.debug(
                "Controller runtime read_holding_registers result failed: %s",
                exc,
            )
            return [None] * n

    def _clear_refs_unlocked(self) -> None:
        self._thread = None
        self._loop = None
        self._modbus = None
        self._doypack = None
        self._port = None

    def _join_stale_thread_unlocked(self) -> None:
        """Join a dead worker thread left from a failed start, if any."""
        if self._thread is None:
            return
        if self._thread.is_alive():
            return
        self._thread.join(timeout=0.0)
        self._clear_refs_unlocked()
