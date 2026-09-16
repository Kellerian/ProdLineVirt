"""Извлечение GS1 / штрихкодов из заданий печати (TSPL2, EZPL, ZPL, SPPL)."""

from __future__ import annotations

import re
from logging import getLogger
from typing import Iterable

from PIL import Image
from pylibdmtx.pylibdmtx import decode as dmtx_decode

from libs.loggers import PRINTER_LOGGER

_MIN_CODE_LENGTH = 13

_LOG = getLogger(PRINTER_LOGGER)

_SPPL_AMQ_PREFIXES = ("~SPLAMQ", "~SPLAQD")
_SPPL_SPMC_PREFIXES = (
    "~SPMC2D",
    "~SPMCBV",
    "~SPMCSV",
    "~SPMCTV",
)
_SPLTDS_DATA_RE = re.compile(
    r"<Data[^>]*>([^<]+)</Data>",
    re.IGNORECASE,
)

_TSPL_BITMAP_RE = re.compile(
    rb"BITMAP\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,",
    re.IGNORECASE,
)
_EZPL_Q_RASTER_RE = re.compile(
    rb"Q0\s*,\s*0\s*,\s*(\d+)\s*,\s*(\d+)\s*\r?\n",
    re.IGNORECASE,
)
_ZPL_GFA_RE = re.compile(
    rb"\^GFA\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,",
    re.IGNORECASE,
)
_XRB_LINE_RE = re.compile(r"^XRB[^,]*,(\d+),", re.IGNORECASE)
_ZPL_FD_RE = re.compile(r"\^FD(.+?)\^FS", re.IGNORECASE)
_ZPL_FH_CMD_RE = re.compile(r"\^FH", re.IGNORECASE)
_HEX_PAIR_RE = re.compile(r"^[0-9A-Fa-f]{2}$")


def _zpl_fh_indicator_at(row: str, fh_index: int) -> str:
    """
    Символ-индикатор hex после ``^FH`` (по умолчанию ``_``).

    ``^FH^FD`` — индикатор по умолчанию; ``^FHA^FD`` — индикатор ``A``.
    """
    after = fh_index + 3
    if after < len(row) and row[after] != "^":
        return row[after]
    return "_"


def _zpl_fh_indicator_before_fd(row: str, fd_start: int) -> str | None:
    """Индикатор последнего ``^FH`` перед позицией ``^FD``, если есть."""
    indicator: str | None = None
    for match in _ZPL_FH_CMD_RE.finditer(row):
        if match.start() >= fd_start:
            break
        indicator = _zpl_fh_indicator_at(row, match.start())
    return indicator


def _decode_zpl_fh_field_data(raw: str, indicator: str) -> str:
    """
    Раскодировать поле ``^FD`` после ``^FH`` (``indicator`` + 2 hex → символ).
    """
    if not raw:
        return raw
    parts: list[str] = []
    index = 0
    while index < len(raw):
        if raw[index] == indicator and index + 2 < len(raw):
            hex_part = raw[index + 1 : index + 3]
            if _HEX_PAIR_RE.match(hex_part):
                parts.append(chr(int(hex_part, 16)))
                index += 3
                continue
        parts.append(raw[index])
        index += 1
    return "".join(parts)


def normalize_printer_escapes(text: str) -> str:
    """
    Раскодировать escape-последовательности TSPL/SPPL в тексте поля.

    Поддерживаются ``~~``, ``~dNNN`` (десятичный код символа).
    Префикс ``~1`` (FNC1) снимается в ``process_barcode``.
    """
    normalized = text.replace("~~", "~")
    return re.sub(
        r"~d(\d{3})",
        lambda match: chr(int(match.group(1))),
        normalized,
    )


def extract_sppl_field_values(text: str) -> list[str]:
    """
    Извлечь все значения из пар ``Field~gt~value`` в SPPL-теле.

    Поддерживает ``field~gt~value~gt~…`` и ``~gt~field~gt~value``.
    Не ограничивается полем ``barcode`` — любое значение длиной ≥13.
    """
    tokens = text.split("~gt~")
    if tokens and tokens[0] == "":
        tokens = tokens[1:]
    values: list[str] = []
    for index in range(1, len(tokens), 2):
        value = normalize_printer_escapes(tokens[index].strip())
        if len(value) >= _MIN_CODE_LENGTH:
            values.append(value)
    return values


def _extract_sppl_from_text(text: str) -> list[str]:
    """Коды из SPLAMQ/SPLAQD, SPMC* и XML SPLTDS."""
    collected: list[str] = []
    for line in text.split("\n"):
        row = line.strip()
        if any(row.startswith(prefix) for prefix in _SPPL_AMQ_PREFIXES):
            collected.extend(extract_sppl_field_values(row))
        elif any(row.startswith(prefix) for prefix in _SPPL_SPMC_PREFIXES):
            brace = re.search(r"\{(.+)\}", row)
            if brace:
                body = brace.group(1)
                pairs = extract_sppl_field_values(body)
                if pairs:
                    collected.extend(pairs)
                else:
                    code = normalize_printer_escapes(body.strip())
                    if len(code) >= _MIN_CODE_LENGTH:
                        collected.append(code)
    for raw_data in _SPLTDS_DATA_RE.findall(text):
        code = normalize_printer_escapes(raw_data.strip())
        if len(code) >= _MIN_CODE_LENGTH:
            collected.append(code)
    return collected


def _extract_line_text_codes(text: str) -> list[str]:
    """Текстовые поля TSPL2 / EZPL / ZPL (без растра)."""
    rows = text.split("\n")
    collected: list[str] = []
    skip_next_xrb_data = False

    for index, raw_row in enumerate(rows):
        row = raw_row.strip()
        if skip_next_xrb_data:
            skip_next_xrb_data = False
            continue

        if row.startswith("BARCODE="):
            code = normalize_printer_escapes(
                row.replace("BARCODE=", "", 1).strip()
            )
            if len(code) >= _MIN_CODE_LENGTH:
                collected.append(code)
            continue

        if row.startswith("DMATRIX") or row.startswith("BARCODE "):
            parts = row.split('"')
            if "DMATRIX" in row and len(parts) > 1:
                payload = parts[1]
            elif len(parts) >= 2:
                payload = parts[-2]
            else:
                continue
            code = normalize_printer_escapes(payload.strip())
            if len(code) >= _MIN_CODE_LENGTH:
                collected.append(code)
            continue

        if row.upper().startswith("XRB"):
            length_match = _XRB_LINE_RE.match(row)
            if index + 1 < len(rows):
                data_line = rows[index + 1]
                if length_match:
                    length = int(length_match.group(1))
                    code = data_line[:length]
                else:
                    code = data_line.strip()
                code = normalize_printer_escapes(code)
                if len(code) >= _MIN_CODE_LENGTH:
                    collected.append(code)
                skip_next_xrb_data = True
            continue

        if row.startswith("BR,"):
            payload = row.split(",", 8)[-1] if row.count(",") >= 8 else row
            if payload == row:
                payload = re.sub(r"^BR,\d+(?:,\d+)*,", "", row)
            code = normalize_printer_escapes(payload.strip())
            if len(code) >= _MIN_CODE_LENGTH:
                collected.append(code)
            continue

        if "^GFA" in row.upper():
            continue

        for match in _ZPL_FD_RE.finditer(row):
            raw_field = match.group(1)
            fh_indicator = _zpl_fh_indicator_before_fd(row, match.start())
            if fh_indicator is not None:
                raw_field = _decode_zpl_fh_field_data(raw_field, fh_indicator)
            code = normalize_printer_escapes(raw_field.strip())
            if len(code) >= _MIN_CODE_LENGTH:
                collected.append(code)

    return collected


def _packed_bytes_to_image(
    data: bytes,
    width_bytes: int,
    height: int,
    *,
    zero_is_black: bool,
) -> Image.Image:
    """Собрать монохромное изображение из упакованных по битам строк."""
    width_px = width_bytes * 8
    image = Image.new("L", (width_px, height), 255)
    pixels = image.load()
    offset = 0
    for y in range(height):
        for x_byte in range(width_bytes):
            if offset >= len(data):
                break
            value = data[offset]
            offset += 1
            for bit in range(8):
                x = x_byte * 8 + bit
                bit_on = (value >> (7 - bit)) & 1
                if zero_is_black:
                    pixels[x, y] = 0 if bit_on == 0 else 255
                else:
                    pixels[x, y] = 0 if bit_on == 1 else 255
    return image


def _decode_datamatrix_from_image(image: Image.Image) -> list[str]:
    """Декодировать Data Matrix; ошибка декодирования не пробрасывается."""
    try:
        decoded = dmtx_decode(image)
    except Exception:
        _LOG.debug("Data Matrix decode failed", exc_info=True)
        return []
    codes: list[str] = []
    for item in decoded:
        try:
            codes.append(item.data.decode("utf-8", errors="replace"))
        except Exception:
            _LOG.debug("Data Matrix payload decode failed", exc_info=True)
    return codes


def _extract_from_raster(raw: bytes) -> list[str]:
    """Растр TSPL BITMAP, EZPL Q…E, ZPL ^GFA."""
    codes: list[str] = []

    for match in _TSPL_BITMAP_RE.finditer(raw):
        width_bytes = int(match.group(3))
        height = int(match.group(4))
        size = width_bytes * height
        start = match.end()
        chunk = raw[start : start + size]
        if len(chunk) < size:
            continue
        image = _packed_bytes_to_image(
            chunk, width_bytes, height, zero_is_black=True
        )
        codes.extend(_decode_datamatrix_from_image(image))

    for match in _EZPL_Q_RASTER_RE.finditer(raw):
        width_bytes = int(match.group(1))
        height = int(match.group(2))
        size = width_bytes * height
        start = match.end()
        chunk = raw[start : start + size]
        if len(chunk) < size:
            continue
        image = _packed_bytes_to_image(
            chunk, width_bytes, height, zero_is_black=False
        )
        codes.extend(_decode_datamatrix_from_image(image))

    for match in _ZPL_GFA_RE.finditer(raw):
        total_bytes = int(match.group(1))
        bytes_per_row = int(match.group(3))
        hex_len = total_bytes * 2
        start = match.end()
        hex_payload = raw[start : start + hex_len]
        if len(hex_payload) < hex_len:
            continue
        try:
            hex_text = hex_payload.decode("ascii")
            raster = bytes.fromhex(hex_text)
        except (UnicodeDecodeError, ValueError):
            continue
        height = total_bytes // bytes_per_row if bytes_per_row else 0
        if height <= 0:
            continue
        image = _packed_bytes_to_image(
            raster, bytes_per_row, height, zero_is_black=False
        )
        codes.extend(_decode_datamatrix_from_image(image))

    return codes


def _unique_ordered(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def extract_codes_from_job(job: str | bytes) -> list[str]:
    """
    Извлечь коды из полного задания печати (текст и/или бинарный растр).

    Возвращает значения длиной не менее 13 символов без дубликатов.
    """
    if isinstance(job, bytes):
        raw = job
        text = job.decode("latin-1", errors="replace")
    else:
        raw = job.encode("latin-1")
        text = job

    parts: list[str] = []
    parts.extend(_extract_from_raster(raw))
    parts.extend(_extract_sppl_from_text(text))
    parts.extend(_extract_line_text_codes(text))
    return _unique_ordered(
        [code for code in parts if len(code.strip()) >= _MIN_CODE_LENGTH]
    )


def extract_barcode_value_from_template(msg_received: str) -> list[str]:
    """Совместимый API: извлечение кодов из шаблона/задания (строка)."""
    return extract_codes_from_job(msg_received)


def process_barcode(barcode: str) -> str:
    """Нормализация кода перед помещением в буфер линии (снять префикс ``~1``)."""
    if barcode.startswith("~1"):
        return barcode[2:]
    return barcode
