"""Сборка бинарных кадров заданий печати (TSPL2, EZPL, ZPL, SPPL)."""

from __future__ import annotations

import re
from enum import Enum

from core.printing.data import PrinterLanguage

_TSPL_BITMAP_HEADER = re.compile(
    rb"BITMAP\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,",
    re.IGNORECASE,
)
_TSPL_PRINT_SUFFIX = re.compile(rb"^\r\nPRINT[^\r\n]*\r\n")
_TSPL_PRINT_PREFIX = b"\r\nPRINT"

_EZPL_Q_HEADER = re.compile(rb"Q(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\r\n")
_EZPL_END_SUFFIX = b"\r\nE\r\n"

_ZPL_JOB_START = b"^XA"
_ZPL_GFA_HEADER = re.compile(rb"\^GFA\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,", re.IGNORECASE)
_ZPL_JOB_SUFFIX = b"^FS^PQ1^XZ\r\n"
_HEX_DIGITS = re.compile(rb"^[0-9A-Fa-f]*$")


class JobFrameKind(str, Enum):
    """Тип распознанного кадра задания."""

    tspl2_bitmap = "tspl2_bitmap"
    ezpl_raster = "ezpl_raster"
    zpl_gfa = "zpl_gfa"
    sppl = "sppl"


def try_take_tspl2_bitmap_job(buf: bytes | bytearray) -> tuple[int, bytes | None]:
    """
    Извлечь полный кадр TSPL2: ``BITMAP …`` + ``B×H`` байт растра + ``\\r\\nPRINT``.

    Команды внутри растра не сканируются. Неполный кадр → ``(0, None)``.

    :param buf: Накопленные байты соединения (с начала задания).
    :returns: ``(сколько_байт_снять_с_начала_buf, кадр_или_None)``.
    """
    data = bytes(buf)
    match = _TSPL_BITMAP_HEADER.search(data)
    if match is None:
        return 0, None

    width = int(match.group(3))
    height = int(match.group(4))
    raster_size = width * height
    raster_start = match.end()
    raster_end = raster_start + raster_size
    if len(data) < raster_end:
        return 0, None

    suffix = data[raster_end:]
    print_match = _TSPL_PRINT_SUFFIX.match(suffix)
    if print_match is None:
        if _TSPL_PRINT_PREFIX.startswith(suffix) or (
            suffix.startswith(_TSPL_PRINT_PREFIX)
            and not suffix.endswith(b"\r\n")
        ):
            return 0, None
        return 0, None

    frame_end = raster_end + print_match.end()
    return frame_end, data[:frame_end]


def try_take_ezpl_raster_job(buf: bytes | bytearray) -> tuple[int, bytes | None]:
    """
    Извлечь полный кадр EZPL: ``Q…,B,H\\r\\n`` + ``B×H`` байт + ``\\r\\nE\\r\\n``.

    :param buf: Накопленные байты соединения.
    :returns: ``(consumed, frame)`` или ``(0, None)`` если кадр неполный.
    """
    data = bytes(buf)
    match = _EZPL_Q_HEADER.search(data)
    if match is None:
        return 0, None

    width = int(match.group(3))
    height = int(match.group(4))
    raster_size = width * height
    raster_start = match.end()
    raster_end = raster_start + raster_size
    if len(data) < raster_end:
        return 0, None

    suffix = data[raster_end:]
    if len(suffix) < len(_EZPL_END_SUFFIX):
        if _EZPL_END_SUFFIX.startswith(suffix):
            return 0, None
        return 0, None
    if not suffix.startswith(_EZPL_END_SUFFIX):
        return 0, None

    frame_end = raster_end + len(_EZPL_END_SUFFIX)
    return frame_end, data[:frame_end]


def try_take_zpl_gfa_job(buf: bytes | bytearray) -> tuple[int, bytes | None]:
    """
    Извлечь полный кадр ZPL: ``^XA`` … ``^GFA,N,…`` + ``2×N`` hex + ``^FS^PQ1^XZ\\r\\n``.

    :param buf: Накопленные байты соединения.
    :returns: ``(consumed, frame)`` или ``(0, None)`` если кадр неполный.
    """
    data = bytes(buf)
    xa_pos = data.find(_ZPL_JOB_START)
    if xa_pos == -1:
        return 0, None

    gfa_match = _ZPL_GFA_HEADER.search(data, xa_pos)
    if gfa_match is None:
        return 0, None

    total_bytes = int(gfa_match.group(1))
    hex_len = total_bytes * 2
    hex_start = gfa_match.end()
    hex_end = hex_start + hex_len
    if len(data) < hex_end:
        return 0, None

    hex_chunk = data[hex_start:hex_end]
    if len(hex_chunk) != hex_len or not _HEX_DIGITS.match(hex_chunk):
        return 0, None

    suffix = data[hex_end:]
    if len(suffix) < len(_ZPL_JOB_SUFFIX):
        if _ZPL_JOB_SUFFIX.startswith(suffix):
            return 0, None
        return 0, None
    if not suffix.startswith(_ZPL_JOB_SUFFIX):
        return 0, None

    frame_end = hex_end + len(_ZPL_JOB_SUFFIX)
    return frame_end, data[:frame_end]


def try_take_sppl_frame(buf: bytes | bytearray) -> tuple[int, bytes | None]:
    """
    Извлечь кадр SPPL: ``~…^`` (цепочки ``|``), без разреза внутри ``{…}``.

    Кадр должен начинаться с ``~`` в начале буфера.

    :param buf: Накопленные байты соединения.
    :returns: ``(consumed, frame)`` или ``(0, None)`` если кадр неполный.
    """
    data = bytes(buf)
    if not data or data[0] != ord("~"):
        return 0, None

    brace_depth = 0
    for index in range(1, len(data)):
        byte = data[index]
        if byte == ord("{"):
            brace_depth += 1
        elif byte == ord("}"):
            if brace_depth > 0:
                brace_depth -= 1
        elif byte == ord("^") and brace_depth == 0:
            frame_end = index + 1
            return frame_end, data[:frame_end]

    return 0, None


def try_take_job_frame(
    buf: bytes | bytearray,
    language: PrinterLanguage,
) -> tuple[int, bytes | None, JobFrameKind | None]:
    """
    Извлечь полный кадр задания для выбранного языка.

    :param buf: Накопленные байты соединения.
    :param language: Язык эмулятора.
    :returns: ``(consumed, frame, kind)``; при неполном кадре ``(0, None, None)``.
    """
    if language == PrinterLanguage.tspl2:
        consumed, frame = try_take_tspl2_bitmap_job(buf)
        kind = JobFrameKind.tspl2_bitmap if frame else None
        return consumed, frame, kind
    if language == PrinterLanguage.ezpl:
        consumed, frame = try_take_ezpl_raster_job(buf)
        kind = JobFrameKind.ezpl_raster if frame else None
        return consumed, frame, kind
    if language == PrinterLanguage.zpl:
        consumed, frame = try_take_zpl_gfa_job(buf)
        kind = JobFrameKind.zpl_gfa if frame else None
        return consumed, frame, kind
    if language == PrinterLanguage.sppl:
        consumed, frame = try_take_sppl_frame(buf)
        kind = JobFrameKind.sppl if frame else None
        return consumed, frame, kind
    return 0, None, None
