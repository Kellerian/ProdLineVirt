"""Диалект ZPL (Zebra): identity, host status, SGD odometer, задания ^GFA."""

from __future__ import annotations

import re

from core.printing.dialects.base import PrinterBusyPhase, PrinterDialect, PrinterDeviceState
from core.printing.extract import (
    _MIN_CODE_LENGTH,
    extract_codes_from_job,
    normalize_printer_escapes,
    process_barcode,
)
from core.printing.framing import try_take_zpl_gfa_job
from core.printing.line_ending import try_take_exact_command

_STX = b"\x02"
_ETX_CRLF = b"\x03\r\n"

_HI_RESPONSE = _STX + b"ZEBRA-EMU,1.0,8" + _ETX_CRLF

_SGD_ODOMETER_PREFIX = b'! U1 getvar "odometer.total_label_count"'

_ZPL_FD_RE = re.compile(r"\^FD(.+?)\^FS", re.IGNORECASE)


def _append_crlf_terminated_stx_frame(payload: str) -> bytes:
    """Собрать кадр ответа Zebra: STX + текст + ETX + CR LF."""
    return _STX + payload.encode("ascii") + _ETX_CRLF


def _format_hs_string1(state: PrinterDeviceState) -> str:
    """
    Host status string 1 — 12 полей (см. ZPL ``~HS`` / ``device.host_status``).

    Значения «готов» при отсутствии ошибок; ``h`` отражает незавершённый формат при busy.
    """
    errors = state.errors
    paper_out = 1 if errors.paper_out else 0
    pause = 1 if errors.pause else 0
    label_length = 1218
    formats_in_buffer = min(state.remaining, 999)
    buffer_full = 0
    diag_mode = 0
    partial_format = (
        1
        if state.busy_phase in (PrinterBusyPhase.processing, PrinterBusyPhase.printing)
        else 0
    )
    unused_iii = 0
    corrupt_ram = 1 if errors.other_error else 0
    under_temp = 0
    over_temp = 0
    return (
        f"000,{paper_out},{pause},{label_length:04d},{formats_in_buffer:03d},"
        f"{buffer_full},{diag_mode},{partial_format},{unused_iii:03d},"
        f"{corrupt_ram},{under_temp},{over_temp}"
    )


def _format_hs_string2(state: PrinterDeviceState) -> str:
    """Host status string 2 — 11 полей."""
    errors = state.errors
    head_up = 1 if errors.head_open else 0
    ribbon_out = 1 if errors.ribbon_out else 0
    labels_remaining = min(state.remaining, 99_999_999)
    return (
        f"000,0,{head_up},{ribbon_out},0,2,0,0,"
        f"{labels_remaining:08d},1,000"
    )


def _format_hs_string3() -> str:
    """Host status string 3 — непустой (пароль Link-OS 6 и признак RAM)."""
    return "0000,1"


def _build_hs_response(state: PrinterDeviceState) -> bytes:
    """Три кадра STX/ETX для ``~HS``."""
    parts = (
        _format_hs_string1(state),
        _format_hs_string2(state),
        _format_hs_string3(),
    )
    return b"".join(_append_crlf_terminated_stx_frame(part) for part in parts)


def _try_take_sgd_odometer_query(data: bytes) -> int | None:
    """
    Распознать SGD ``getvar "odometer.total_label_count"`` с завершающим CR/LF.

    :returns: Длина съеденного запроса или ``None`` / ``0`` как у ``_try_take_exact_command``.
    """
    prefix = _SGD_ODOMETER_PREFIX
    if data.startswith(prefix):
        rest = data[len(prefix) :]
        line_match = re.match(rb'^(?:\r\n|\n|\r)', rest)
        if line_match is None:
            if rest == b"":
                return None
            return 0
        return len(prefix) + line_match.end()
    if prefix.startswith(data):
        return None
    return 0


def _extract_zpl_fd_codes(frame: bytes) -> list[str]:
    """
    Коды из ``^FD…^FS`` в задании (в т.ч. когда ``^GFA`` на той же строке).

    ``extract_codes_from_job`` пропускает целую строку с ``^GFA``; для ZPL job
    поля ``^FD`` нужны отдельно.
    """
    text = frame.decode("latin-1", errors="replace")
    codes: list[str] = []
    for match in _ZPL_FD_RE.finditer(text):
        code = normalize_printer_escapes(match.group(1).strip())
        if len(code) >= _MIN_CODE_LENGTH:
            codes.append(code)
    return codes


def _merge_job_codes(frame: bytes) -> list[str]:
    """Растр ``^GFA`` и текстовые ``^FD`` без дубликатов (порядок сохранения)."""
    seen: set[str] = set()
    merged: list[str] = []
    for code in extract_codes_from_job(frame) + _extract_zpl_fd_codes(frame):
        if code in seen:
            continue
        seen.add(code)
        merged.append(code)
    return merged


class ZplDialect(PrinterDialect):
    """Эмуляция Zebra ZPL: ``~HI``, ``~HS``, SGD odometer и кадры ``^GFA``."""

    def __init__(self, state: PrinterDeviceState) -> None:
        """
        :param state: Общее состояние устройства (одометр, очередь, busy).
        """
        super().__init__(state)

    def complete_print(self, labels: int = 1) -> None:
        """
        Завершить печать (вызывается ядром ``PrinterEmul`` после задержки job).

        Инкрементирует одометр; уменьшает ``remaining`` не ниже нуля.
        """
        if labels <= 0:
            return
        self._state.odometer += labels
        self._state.remaining = max(0, self._state.remaining - labels)
        if self._state.remaining == 0:
            self._state.busy_phase = PrinterBusyPhase.idle

    def try_handle_query(self, buf: bytearray) -> tuple[int, bytes | None]:
        """
        Обработать ``~HI``, ``~HS`` или SGD-запрос одометра.

        :param buf: Накопленные байты соединения (с начала пакета).
        :returns: ``(consumed, response)``; ``(0, None)`` — не query или кадр неполный.
        """
        data = bytes(buf)
        if not data:
            return 0, None

        if data[0:1] == b"~":
            if len(data) < 3 and data in (b"~", b"~H"):
                return 0, None
            if data.startswith(b"~HS"):
                consumed = try_take_exact_command(data, b"~HS")
                if consumed is None:
                    return 0, None
                if consumed == 0:
                    return 0, None
                return consumed, _build_hs_response(self._state)
            if data.startswith(b"~HI"):
                consumed = try_take_exact_command(data, b"~HI")
                if consumed is None:
                    return 0, None
                if consumed == 0:
                    return 0, None
                return consumed, _HI_RESPONSE
            if data.startswith(b"~H") and len(data) < 3:
                return 0, None

        if data.startswith(b"!"):
            consumed = _try_take_sgd_odometer_query(data)
            if consumed is None:
                return 0, None
            if consumed == 0:
                return 0, None
            value = self._state.odometer
            response = f'"{value}"\r\n'.encode("ascii")
            return consumed, response

        return 0, None

    def try_handle_job(self, buf: bytearray) -> tuple[int, list[str]]:
        """
        Разобрать полное задание ``^XA`` … ``^GFA`` … ``^FS^PQ1^XZ``.

        :param buf: Накопленные байты соединения.
        :returns: ``(consumed, коды)``; ``(0, [])`` если кадр неполный.
        """
        consumed, frame = try_take_zpl_gfa_job(buf)
        if frame is None or consumed == 0:
            return 0, []

        codes = [process_barcode(code) for code in _merge_job_codes(frame)]
        self._state.emit_codes(codes)
        self._state.remaining += 1
        if self._state.busy_phase == PrinterBusyPhase.idle:
            self._state.busy_phase = PrinterBusyPhase.processing

        return consumed, codes
