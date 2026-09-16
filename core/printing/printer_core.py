"""TCP-эмулятор принтера: приём bytes, диалекты, буфер кодов линии."""

from __future__ import annotations

import random
import socket
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from logging import getLogger
from threading import Thread
from time import monotonic, sleep

from core.printing.data import PrinterLanguage
from core.printing.dialects.base import (
    PrinterBusyPhase,
    PrinterDeviceState,
    PrinterDialect,
)
from core.printing.dialects.ezpl import EzplDialect
from core.printing.dialects.legacy import LegacyDialect
from core.printing.dialects.sppl import SpplDialect
from core.printing.dialects.tspl2 import Tspl2Dialect
from core.printing.dialects.zpl import ZplDialect
from core.printing.framing import try_take_sppl_frame
from libs.loggers import PRINTER_LOGGER
from libs.sockets import DEFAULT_RECV_SIZE, get_server_socket
from core.printing.line_ending import ensure_crlf_suffix
from libs.template_parsers import (
    extract_barcode_value_from_template,
    process_barcode,
)

_BUSY_PROCESSING_DELAY_S = 0.02
_BUSY_PRINTING_DELAY_S = 0.04
_ZPL_COMPLETE_DELAY_S = 0.04
_TSPL_PRINTING_DELAY_S = 0.04
_ORPHAN_BUFFER_LOG_THRESHOLD = 4096


@dataclass
class _ScheduledAction:
    """Отложенное изменение busy/одометра после задания печати."""

    run_at: float
    action: Callable[[], None]


class PrinterEmul:
    """
    Эмулятор TCP-принтера (порт raw): статус и задания по выбранному языку.

    Состояние устройства (одометр, SPPL-очереди, ``savema_state``) живёт в
    ``PrinterDeviceState`` и не сбрасывается при переподключении клиента.
    """

    def __init__(
        self,
        name: str,
        port: int,
        buffer_size: int,
        language: PrinterLanguage = PrinterLanguage.legacy,
    ) -> None:
        """
        :param name: Имя устройства в линии (для логов).
        :param port: TCP-порт прослушивания.
        :param buffer_size: Максимальный размер буфера кодов линии (зарезерв.).
        :param language: Эмулируемый язык протокола.
        """
        self.name = name
        self._language = language
        self.server = get_server_socket(port)
        self._can_run = True
        self._t_processing = Thread(target=self._run_processing_thread)
        self._t_server = Thread(target=self._run_login_thread)
        self._connections: list[socket.socket] = []
        self._recv_buffers: dict[socket.socket, bytearray] = {}
        self._log = getLogger(PRINTER_LOGGER)
        self._max_size = buffer_size
        self._print_buffer: deque[str] = deque([])
        self._printed = 0
        self._mac: str = "02:00:00:%02x:%02x:%02x" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        self._device_state = PrinterDeviceState(savema_state="RUNNING")
        self._device_state.on_codes = self._on_codes_from_dialect
        self._dialect: PrinterDialect = self._build_dialect()
        self._scheduled: deque[_ScheduledAction] = deque()
        self._active_client: socket.socket | None = None
        self._orphan_warn_step: dict[socket.socket, int] = {}

    def start(self) -> None:
        """Запустить потоки accept и обработки соединений."""
        self._can_run = True
        self._t_processing = Thread(target=self._run_processing_thread)
        self._t_server = Thread(target=self._run_login_thread)
        self._t_processing.start()
        self._t_server.start()

    def stop(self) -> None:
        """Остановить эмулятор и закрыть клиентские сокеты."""
        self._can_run = False
        self._t_server.join()
        self._t_processing.join()

    def buffer_size(self) -> int:
        """Число кодов в буфере линии."""
        return len(self._print_buffer)

    def clear_buffer(self) -> None:
        """Очистить буфер кодов линии."""
        self._print_buffer.clear()

    def set_buffer_size(self, size: int) -> None:
        """Задать лимит буфера (для совместимости с виджетом)."""
        self._max_size = size

    def buffer_data(self) -> list[str]:
        """Снимок кодов в буфере линии."""
        return list(self._print_buffer)

    def remove(self, code: str) -> None:
        """Удалить один код из буфера линии."""
        self._print_buffer.remove(code)

    def _build_dialect(self) -> PrinterDialect:
        """Создать диалект по ``language`` с callback'ами ядра."""
        state = self._device_state
        on_clear: Callable[[], None] = self.clear_buffer
        line_size: Callable[[], int] = lambda: len(self._print_buffer)

        if self._language == PrinterLanguage.legacy:
            sppl = SpplDialect(state, on_clear_line_buffer=on_clear)
            return LegacyDialect(
                state,
                sppl=sppl,
                on_clear_line_buffer=on_clear,
                line_buffer_size=line_size,
                on_raw_send=self._raw_send_for_client,
                mac=self._mac,
            )
        if self._language == PrinterLanguage.tspl2:
            return Tspl2Dialect(state)
        if self._language == PrinterLanguage.ezpl:
            return EzplDialect(state)
        if self._language == PrinterLanguage.zpl:
            return ZplDialect(state)
        if self._language == PrinterLanguage.sppl:
            return SpplDialect(state, on_clear_line_buffer=on_clear)
        return LegacyDialect(
            state,
            on_clear_line_buffer=on_clear,
            line_buffer_size=line_size,
            mac=self._mac,
        )

    def _raw_send_for_client(self, payload: bytes) -> None:
        """
        Отправить bytes активному клиенту (legacy ``STOP``).

        Использует последнее соединение в списке — как при одиночном клиенте PSM.
        """
        client = self._active_client
        if client is None:
            return
        try:
            client.sendall(ensure_crlf_suffix(payload))
        except OSError as exc:
            self._log.critical(
                f"<{self.name}> raw send failed {client}: {exc}",
                exc_info=True,
            )

    def _on_codes_from_dialect(self, codes: list[str]) -> None:
        """Callback диалекта: положить коды в ``_print_buffer``."""
        if not codes:
            return
        processed = [process_barcode(code) for code in codes]
        self._printed += len(processed)
        if self._language in (PrinterLanguage.legacy, PrinterLanguage.tspl2):
            self._device_state.odometer = self._printed
        self._log.info(f"[{self.name}] BARCODES: {processed}")
        for code in processed:
            self._add_barcode_to_buffer(code)

    def _add_barcode_to_buffer(self, barcode: str) -> None:
        """Добавить один код в deque буфера линии."""
        self._print_buffer.append(barcode)
        self._log.info(
            f"[{self.name}] <{self._printed}> PRINTED: {barcode}"
        )

    def _run_login_thread(self) -> None:
        """Accept новых TCP-клиентов (non-blocking)."""
        while self._can_run:
            try:
                connected_client, address = self.server.accept()
                connected_client.setblocking(True)
                self._connections.append(connected_client)
                self._recv_buffers[connected_client] = bytearray()
                self._log.info(
                    f"[{self.name}] NEW CLIENT from {address} {connected_client}"
                )
            except BlockingIOError:
                sleep(0.01)
        for client in self._connections.copy():
            self._disconnect_client(client)

    def _run_processing_thread(self) -> None:
        """Обработка recv, диалектов и отложенных busy-переходов."""
        while self._can_run:
            self._run_scheduled_actions()
            for client in self._connections.copy():
                self._process_client(client)
            else:
                sleep(0.01)
        for client in self._connections.copy():
            self._disconnect_client(client)

    def _run_scheduled_actions(self) -> None:
        """Выполнить действия, время которых наступило (EZPL 50→00 и др.)."""
        now = monotonic()
        while self._scheduled and self._scheduled[0].run_at <= now:
            item = self._scheduled.popleft()
            try:
                item.action()
            except Exception as exc:
                self._log.error(
                    f"[{self.name}] scheduled action failed: {exc}",
                    exc_info=True,
                )

    def _process_client(self, client: socket.socket) -> None:
        """Прочитать доступные bytes и разобрать буфер соединения."""
        self._active_client = client
        buf = self._recv_buffers.get(client)
        if buf is None:
            self._recv_buffers[client] = bytearray()
            buf = self._recv_buffers[client]
        try:
            self._recv_available(client, buf)
        except (ConnectionError, OSError) as exc:
            self._log.critical(f"<{self.name}> {client} {exc}")
            self._disconnect_client(client)
            return
        while self._dispatch_buffer(client, buf):
            pass

    def _recv_available(self, client: socket.socket, buf: bytearray) -> None:
        """
        Дочитать сокет в накопитель (аналог ``get_data_from_socket``, но bytes).

        :raises ConnectionError: пустой ``recv`` — разрыв соединения.
        """
        while True:
            try:
                client.settimeout(0.0)
                chunk = client.recv(DEFAULT_RECV_SIZE)
            except (BlockingIOError, TimeoutError):
                break
            if chunk == b"":
                raise ConnectionError("Соединение разорвано!")
            buf.extend(chunk)
            if len(chunk) < DEFAULT_RECV_SIZE:
                break

    def _dispatch_buffer(self, client: socket.socket, buf: bytearray) -> bool:
        """
        Один проход разбора буфера: query, job или legacy-шаблон.

        :returns: ``True``, если буфер изменился и можно повторить цикл.
        """
        if not buf:
            return False

        consumed, response = self._dialect.try_handle_query(buf)
        if consumed > 0:
            del buf[:consumed]
            if response is not None:
                if not self._send_to_client(client, response):
                    return False
            return True

        consumed, codes = self._dialect.try_handle_job(buf)
        if consumed > 0:
            del buf[:consumed]
            self._log.debug(
                f"[{self.name}] JOB FROM {client.getsockname()}: "
                f"{len(codes)} code(s)"
            )
            self._schedule_after_job(len(codes))
            return True

        if self._language == PrinterLanguage.legacy:
            legacy_consumed = self._try_consume_legacy_template(buf)
            if legacy_consumed > 0:
                del buf[:legacy_consumed]
                return True

        self._maybe_log_orphan_buffer(client, buf)
        return False

    def _send_to_client(self, client: socket.socket, payload: bytes) -> bool:
        """
        Отправить bytes клиенту.

        :returns: ``False`` если соединение закрыто из-за ошибки отправки.
        """
        try:
            client.sendall(ensure_crlf_suffix(payload))
            return True
        except OSError as exc:
            self._log.critical(
                f"<{self.name}> send failed {client}: {exc}",
                exc_info=True,
            )
            self._disconnect_client(client)
            return False

    def _maybe_log_orphan_buffer(
        self, client: socket.socket, buf: bytearray
    ) -> None:
        """DEBUG при «застрявшем» буфере в non-legacy (без бесконечного спама)."""
        if self._language == PrinterLanguage.legacy:
            return
        size = len(buf)
        if size < _ORPHAN_BUFFER_LOG_THRESHOLD:
            return
        step = size // _ORPHAN_BUFFER_LOG_THRESHOLD
        if self._orphan_warn_step.get(client, 0) >= step:
            return
        self._orphan_warn_step[client] = step
        self._log.debug(
            f"[{self.name}] non-legacy recv buffer undispatched "
            f"({size} bytes)"
        )

    def _try_consume_legacy_template(self, buf: bytearray) -> int:
        """
        Разбор текстового задания в режиме Legacy (без бинарного framing).

        :returns: Сколько байт съесть; ``0`` — ждём данные (неполный SPPL и т.п.).
        """
        if not buf:
            return 0
        data = bytes(buf)
        if data.startswith(b"~"):
            frame_consumed, frame = try_take_sppl_frame(buf)
            if frame_consumed == 0 and self._pending_sppl_prefix(data):
                return 0
            if frame_consumed > 0 and frame is not None:
                self._log.debug(
                    f"[{self.name}] discarding unhandled SPPL frame "
                    f"({frame_consumed} bytes)"
                )
                return frame_consumed

        try:
            text = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="replace").strip()

        if not text:
            return len(buf)

        self._log.debug(
            f"[{self.name}] LEGACY TEMPLATE ({len(data)} bytes)"
        )
        dm_extracted = extract_barcode_value_from_template(text)
        if dm_extracted:
            self._printed += len(dm_extracted)
            self._device_state.odometer = self._printed
            self._log.info(f"[{self.name}] BARCODES: {dm_extracted}")
            for code in dm_extracted:
                self._add_barcode_to_buffer(process_barcode(code))
        return len(buf)

    @staticmethod
    def _pending_sppl_prefix(data: bytes) -> bool:
        """Незавершённый кадр ``~SP…`` без ``^``."""
        text = data.decode("latin-1", errors="replace")
        if not text.startswith("~") or "^" in text:
            return False
        for segment in text[1:].split("|"):
            name = segment.strip().upper()
            if name.startswith("SP") and len(name) >= 4:
                return True
        return False

    def _schedule_after_job(self, code_count: int) -> None:
        """Запланировать busy/complete после принятого задания."""
        now = monotonic()
        labels = max(1, code_count)

        if isinstance(self._dialect, EzplDialect):
            self._scheduled.append(
                _ScheduledAction(
                    now + _BUSY_PROCESSING_DELAY_S,
                    self._dialect.advance_busy_to_printing,
                )
            )
            self._scheduled.append(
                _ScheduledAction(
                    now + _BUSY_PRINTING_DELAY_S,
                    self._dialect.complete_print_job,
                )
            )
            return

        if isinstance(self._dialect, ZplDialect):
            self._scheduled.append(
                _ScheduledAction(
                    now + _ZPL_COMPLETE_DELAY_S,
                    lambda: self._dialect.complete_print(labels),
                )
            )
            return

        if isinstance(self._dialect, Tspl2Dialect):
            self._device_state.busy_phase = PrinterBusyPhase.printing
            self._scheduled.append(
                _ScheduledAction(
                    now + _TSPL_PRINTING_DELAY_S,
                    self._set_busy_idle,
                )
            )

    def _set_busy_idle(self) -> None:
        """Сбросить busy в idle (TSPL ``ESC !?``)."""
        self._device_state.busy_phase = PrinterBusyPhase.idle

    def _disconnect_client(self, client: socket.socket) -> None:
        """Закрыть сокет и убрать из списков (буфер соединения не трогаем)."""
        try:
            client.close()
        except OSError:
            pass
        if client in self._connections:
            self._connections.remove(client)
        self._recv_buffers.pop(client, None)
        self._orphan_warn_step.pop(client, None)
