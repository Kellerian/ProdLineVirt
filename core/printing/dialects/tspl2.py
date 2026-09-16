"""Диалект TSC TSPL2 для эмулятора принтера (Print Station Mini)."""

from __future__ import annotations

from core.printing.dialects.base import PrinterBusyPhase, PrinterDialect, PrinterDeviceState
from core.printing.extract import extract_codes_from_job
from core.printing.framing import try_take_tspl2_bitmap_job

_ESC_STATUS_QUERY = b"\x1b!?"
_PSM_LABEL_QUERY = b'OUT NET "PSM_LABEL=";STR$(LABEL)\r\n'


def tspl2_status_byte(state: PrinterDeviceState) -> int:
    """
    Собрать один байт ответа на ``ESC !?`` (маски TSC TSPL2).

    Ready = ``0x00``. Биты: ``01`` head, ``02`` jam, ``04`` paper, ``08`` ribbon,
    ``10`` pause, ``20`` printing, ``80`` other.

    :param state: Состояние устройства.
    :returns: Значение байта флагов.
    """
    flags = 0
    errors = state.errors
    if errors.head_open:
        flags |= 0x01
    if errors.paper_jam:
        flags |= 0x02
    if errors.paper_out:
        flags |= 0x04
    if errors.ribbon_out:
        flags |= 0x08
    if errors.pause:
        flags |= 0x10
    if state.busy_phase == PrinterBusyPhase.printing:
        flags |= 0x20
    if errors.other_error:
        flags |= 0x80
    return flags


class Tspl2Dialect(PrinterDialect):
    """TSPL2: ``ESC !?``, ``OUT NET`` PSM_LABEL, задания ``BITMAP`` + ``PRINT``."""

    def try_handle_query(self, buf: bytearray) -> tuple[int, bytes | None]:
        """
        Обработать запрос статуса или счётчика PSM.

        Не обрабатывает ``~HI`` / ``~S,STATUS`` (другие языки).

        :param buf: Накопленные байты соединения.
        :returns: ``(consumed, response)`` или ``(0, None)``.
        """
        if not buf:
            return 0, None

        if buf[0] == 0x1B:
            if len(buf) < len(_ESC_STATUS_QUERY):
                if _ESC_STATUS_QUERY.startswith(bytes(buf)):
                    return 0, None
                return 0, None
            if bytes(buf[: len(_ESC_STATUS_QUERY)]) == _ESC_STATUS_QUERY:
                return len(_ESC_STATUS_QUERY), bytes([tspl2_status_byte(self._state)])
            return 0, None

        consumed, response = _try_psm_label_query(buf, self._state.odometer)
        if consumed:
            return consumed, response

        if bytes(buf).startswith(b"~HI") or bytes(buf).startswith(b"~S,STATUS"):
            return 0, None

        return 0, None

    def try_handle_job(self, buf: bytearray) -> tuple[int, list[str]]:
        """
        Разобрать полный кадр ``BITMAP`` + растр + ``\\r\\nPRINT``.

        :param buf: Накопленные байты соединения.
        :returns: ``(consumed, codes)``; ``(0, [])`` если кадр неполный.
        """
        consumed, frame = try_take_tspl2_bitmap_job(buf)
        if frame is None:
            return 0, []

        codes = extract_codes_from_job(frame)
        self._state.remaining += 1
        self._state.emit_codes(codes)
        return consumed, codes


def _try_psm_label_query(buf: bytearray, odometer: int) -> tuple[int, bytes | None]:
    """
    Запрос ``OUT NET "PSM_LABEL=";STR$(LABEL)\\r\\n`` → ``PSM_LABEL={n}\\r\\n``.

    :param buf: Буфер соединения с начала запроса.
    :param odometer: Текущий одометр (LABEL).
    :returns: ``(consumed, response)`` или ``(0, None)``.
    """
    data = bytes(buf)
    if len(data) < len(_PSM_LABEL_QUERY):
        if _PSM_LABEL_QUERY.startswith(data):
            return 0, None
        return 0, None
    if not data.startswith(_PSM_LABEL_QUERY):
        return 0, None
    body = f"PSM_LABEL={odometer}\r\n".encode("ascii")
    return len(_PSM_LABEL_QUERY), body
