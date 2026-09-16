"""Диалект GoDEX EZPL: identity, STATUS/LABEL и растровые задания Q…E."""

from __future__ import annotations

from core.printing.dialects.base import (
    PrinterBusyPhase,
    PrinterDeviceState,
    PrinterDialect,
)
from core.printing.extract import extract_codes_from_job
from core.printing.framing import try_take_ezpl_raster_job
from core.printing.line_ending import try_take_exact_command

_HI_RESPONSE = b"\x02EZ2350i,V1.151p,12,1014KB\x03\r\n"
_QUERY_HI = b"~HI"
_QUERY_STATUS = b"~S,STATUS"
_QUERY_LABEL = b"~S,LABEL"


def format_ezpl_label_remaining(remaining: int) -> str:
    """
    Формат ответа ``~S,LABEL`` — 3–5 цифр с ведущими нулями (PSM: ``015``).

    :param remaining: Число этикеток в очереди печати принтера.
    :returns: Строка длиной от 3 до 5 символов.
    """
    count = max(0, remaining)
    if count == 0:
        return "000"
    width = max(3, len(str(count)))
    width = min(width, 5)
    return f"{count:0{width}d}"


def format_ezpl_status_line(state: PrinterDeviceState) -> str:
    """
    Формат ответа ``~S,STATUS`` — ``aa,nnnnn`` (PSM §8.6).

    ``aa``: ``00`` idle, ``50`` printing, ``60`` processing.
    ``nnnnn`` — ``remaining`` (согласовано с ``~S,LABEL``).
    """
    phase = state.busy_phase
    if phase == PrinterBusyPhase.printing:
        status_code = "50"
    elif phase == PrinterBusyPhase.processing:
        status_code = "60"
    else:
        status_code = "00"
    return f"{status_code},{state.remaining:05d}\r\n"


class EzplDialect(PrinterDialect):
    """Эмуляция запросов GoDEX EZPL и приёма растровых заданий Q…E."""

    def try_handle_query(self, buf: bytearray) -> tuple[int, bytes | None]:
        """
        Обработать ``~HI``, ``~S,STATUS`` или ``~S,LABEL`` (CR/LF опциональны).

        :param buf: Накопленные байты (с начала необработанного хвоста).
        :returns: ``(consumed, response_bytes)`` или ``(0, None)``.
        """
        data = bytes(buf)
        if not data:
            return 0, None

        consumed = try_take_exact_command(data, _QUERY_HI)
        if consumed is None:
            return 0, None
        if consumed > 0:
            return consumed, _HI_RESPONSE

        consumed = try_take_exact_command(data, _QUERY_STATUS)
        if consumed is None:
            return 0, None
        if consumed > 0:
            response = format_ezpl_status_line(self._state).encode("ascii")
            return consumed, response

        consumed = try_take_exact_command(data, _QUERY_LABEL)
        if consumed is None:
            return 0, None
        if consumed > 0:
            label_text = format_ezpl_label_remaining(self._state.remaining)
            return consumed, label_text.encode("ascii")

        return 0, None

    def try_handle_job(self, buf: bytearray) -> tuple[int, list[str]]:
        """
        Разобрать полное EZPL-задание (конверт + Q + растр + ``\\r\\nE\\r\\n``).

        После разбора: ``on_codes``, ``remaining++``, ``busy_phase=processing``.
        Дальше #10 вызывает ``advance_busy_to_printing`` / ``complete_print_job``.

        :param buf: Накопленные байты соединения.
        :returns: ``(consumed, codes)``; ``(0, [])`` если кадр неполный.
        """
        consumed, frame = try_take_ezpl_raster_job(buf)
        if frame is None:
            return 0, []

        codes = extract_codes_from_job(frame)
        self._state.remaining += 1
        self._state.busy_phase = PrinterBusyPhase.processing
        self._state.emit_codes(codes)
        return consumed, codes

    def advance_busy_to_printing(self) -> None:
        """Перевести busy в printing (STATUS ``50``) после processing."""
        if self._state.busy_phase == PrinterBusyPhase.processing:
            self._state.busy_phase = PrinterBusyPhase.printing

    def complete_print_job(self) -> None:
        """
        Завершить симуляцию печати: ``remaining--``, idle (STATUS ``00``).

        Вызывается из ``PrinterEmul`` после задержки (#10).
        """
        if self._state.remaining > 0:
            self._state.remaining -= 1
        self._state.busy_phase = PrinterBusyPhase.idle
