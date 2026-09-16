"""Диалект SAVEMA SPPL (~SP…^, цепочки через ``|``)."""

from __future__ import annotations

import re
from collections import deque
from collections.abc import Callable

from core.printing.dialects.base import PrinterDeviceState, PrinterDialect
from core.printing.extract import extract_codes_from_job, normalize_printer_escapes
from core.printing.framing import try_take_sppl_frame

ClearBufferCallback = Callable[[], None]

_SPPL_CMD_RE = re.compile(r"^([A-Z0-9]+)")
_GENERIC_GET_RE = re.compile(r"^SP[CLMPGT]", re.IGNORECASE)

_SPMG_COMMANDS = frozenset(
    {
        "SPMC2D",
        "SPMCBV",
        "SPMCSV",
        "SPMCTV",
    }
)

_AMQ_COMMANDS = frozenset({"SPLAMQ", "SPLAQD"})
_GMQ_COMMANDS = frozenset({"SPLGMQ", "SPLGQC"})
_CMQ_COMMANDS = frozenset({"SPLCMQ", "SPLCQD"})
_OK_STUB_COMMANDS = frozenset({"SPLTDS", "SPLLTF", "SPLCDF"})
_PROCESS_COMMANDS = frozenset({"SPPSAP", "SPPSTP", "SPPSLQ"})
_VERSION_COMMANDS = frozenset({"SPGGFV", "SPGGFW"})
_GG_NUM_COMMANDS = frozenset({"SPGGTP", "SPGGCP"})


def _spgres(cmd: str, payload: str) -> str:
    """Сформировать кадр ответа ``~SPGRES{CMD:payload}^``."""
    return f"~SPGRES{{{cmd}:{payload}}}^"


def _split_chain(frame: str) -> list[str]:
    """
    Разбить кадр SPPL на сегменты команд (``|`` вне ``{…}``).

    :param frame: Полный кадр включая ведущий ``~`` и завершающий ``^``.
    """
    if not frame.endswith("^"):
        return []
    inner = frame[:-1]
    if not inner.startswith("~"):
        return []
    segments: list[str] = []
    brace_depth = 0
    start = 1
    for index in range(1, len(inner)):
        char = inner[index]
        if char == "{":
            brace_depth += 1
        elif char == "}":
            if brace_depth > 0:
                brace_depth -= 1
        elif char == "|" and brace_depth == 0:
            segment = inner[start:index].strip()
            if segment:
                segments.append(segment)
            start = index + 1
    tail = inner[start:].strip()
    if tail:
        segments.append(tail)
    return segments


def _parse_command(segment: str) -> tuple[str, str | None]:
    """
    Разобрать один сегмент цепочки в имя команды и тело ``{…}``.

    :returns: ``(COMMAND, body_or_none)``.
    """
    match = _SPPL_CMD_RE.match(segment)
    if not match:
        return segment.upper(), None
    name = match.group(1).upper()
    rest = segment[match.end() :]
    if rest.startswith("{"):
        depth = 0
        for index, char in enumerate(rest):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    body = rest[1:index]
                    return name, body
        return name, rest[1:]
    return name, None


def _parse_gt_field_pairs(body: str) -> list[tuple[str, str]]:
    """Пары ``field~gt~value`` из тела AMQ/CMQ."""
    tokens = body.split("~gt~")
    if tokens and tokens[0] == "":
        tokens = tokens[1:]
    pairs: list[tuple[str, str]] = []
    index = 0
    while index + 1 < len(tokens):
        field_name = tokens[index].strip()
        value = normalize_printer_escapes(tokens[index + 1].strip())
        if field_name:
            pairs.append((field_name, value))
        index += 2
    return pairs


def _queue_for_field(
    queues: dict[str, deque[str]], field_name: str
) -> deque[str]:
    """Получить или создать FIFO для имени поля."""
    key = field_name.strip()
    if key not in queues:
        queues[key] = deque()
    return queues[key]


class SpplDialect(PrinterDialect):
    """Обработка команд SAVEMA SPPL Rev.11."""

    def __init__(
        self,
        state: PrinterDeviceState,
        *,
        on_clear_line_buffer: ClearBufferCallback | None = None,
        gsdl_left: str = "a.csv",
        gsdl_right: str = "b.csv",
        firmware_version: str = "(v3.29)",
        gg_tp_value: str = "0",
        gg_cp_value: str = "0",
    ) -> None:
        """
        :param state: Общее состояние (``savema_state``, ``sppl_queues``).
        :param on_clear_line_buffer: Очистка буфера кодов линии (``SPLCMQ``).
        :param gsdl_left: Левый файл в ответе ``SPLGSD``.
        :param gsdl_right: Правый файл в ответе ``SPLGSD``.
        :param firmware_version: Payload ``SPGGFV`` / ``SPGGFW``.
        :param gg_tp_value: Payload ``SPGGTP``.
        :param gg_cp_value: Payload ``SPGGCP``.
        """
        super().__init__(state)
        self._on_clear_line_buffer = on_clear_line_buffer
        self._gsdl_left = gsdl_left
        self._gsdl_right = gsdl_right
        self._firmware_version = firmware_version
        self._gg_tp_value = gg_tp_value
        self._gg_cp_value = gg_cp_value

    def try_handle_query(self, buf: bytearray) -> tuple[int, bytes | None]:
        """
        Разобрать полный кадр ``~…^``, ответить ``~SPGRES…^``, положить коды в линию.

        :param buf: Накопленные байты соединения.
        :returns: ``(consumed, response_bytes)`` или ``(0, None)`` если кадр неполный
            или это не SPPL-команда.
        """
        consumed, frame = try_take_sppl_frame(buf)
        if consumed == 0 or frame is None:
            return 0, None

        text = frame.decode("latin-1", errors="replace")
        if not self._looks_like_sppl_command(text):
            return 0, None

        responses: list[str] = []
        codes_to_emit: list[str] = []
        for segment in _split_chain(text):
            response, codes = self._dispatch_segment(segment, text)
            if response:
                responses.append(response)
            codes_to_emit.extend(codes)

        if codes_to_emit:
            self._state.emit_codes(codes_to_emit)

        if not responses:
            return consumed, None

        payload = "".join(responses).encode("latin-1")
        return consumed, payload

    def try_handle_job(self, buf: bytearray) -> tuple[int, list[str]]:
        """
        SPPL не разделяет job и query: см. ``try_handle_query``.

        :param buf: Накопленные байты соединения.
        :returns: ``(0, [])`` — коды передаются через ``on_codes`` в query-обработчике.
        """
        return 0, []

    def _looks_like_sppl_command(self, frame: str) -> bool:
        """Кадр от клиента SAVEMA (не эcho ``~SPGRES``)."""
        for segment in _split_chain(frame):
            name, _ = _parse_command(segment)
            if name == "SPGRES":
                continue
            if name.startswith("SP"):
                return True
        return False

    def _dispatch_segment(
        self, segment: str, full_frame: str
    ) -> tuple[str, list[str]]:
        """
        Обработать одну команду цепочки.

        :returns: ``(response_text, codes_for_line_buffer)``.
        """
        name, body = _parse_command(segment)
        codes: list[str] = []

        if name in _AMQ_COMMANDS:
            if body:
                for field_name, value in _parse_gt_field_pairs(body):
                    _queue_for_field(self._state.sppl_queues, field_name).append(
                        value
                    )
            codes = extract_codes_from_job(full_frame)
            return _spgres(name, "OK"), codes

        if name in _GMQ_COMMANDS:
            fields = (
                [part.strip() for part in body.split("<") if part.strip()]
                if body
                else []
            )
            if not fields and body:
                fields = [body.strip()]
            parts: list[str] = []
            for field_name in fields:
                queue = self._state.sppl_queues.get(field_name)
                count = len(queue) if queue is not None else 0
                parts.append(f"{field_name}={count}")
            payload = "<".join(parts) if parts else "0"
            return _spgres(name, payload), []

        if name in _CMQ_COMMANDS:
            if body:
                for field_name, _value in _parse_gt_field_pairs(body):
                    self._state.sppl_queues.pop(field_name.strip(), None)
            if self._on_clear_line_buffer is not None:
                self._on_clear_line_buffer()
            return _spgres(name, "OK"), []

        if name in _SPMG_COMMANDS:
            wrapped = f"~{segment}^"
            codes = extract_codes_from_job(wrapped)
            return _spgres(name, "OK"), codes

        if name in _PROCESS_COMMANDS:
            return self._handle_process_command(name, body), []

        if name == "SPPSTA":
            state = self._state.savema_state or "RUNNING"
            return _spgres("SPPSTA", f"{state}<"), []

        if name in _VERSION_COMMANDS:
            return _spgres("SPGGFV", self._firmware_version), []

        if name in _GG_NUM_COMMANDS:
            value = (
                self._gg_tp_value if name == "SPGGTP" else self._gg_cp_value
            )
            return _spgres(name, value), []

        if name == "SPLGSD":
            payload = f"{self._gsdl_left}<{self._gsdl_right}"
            return _spgres("SPLGSD", payload), []

        if name == "SPLDDF":
            return _spgres("SPLDDF", "OK"), []

        if name in _OK_STUB_COMMANDS:
            return _spgres(name, "OK"), []

        if _GENERIC_GET_RE.match(name):
            return _spgres(name, "0"), []

        return "", []

    def _handle_process_command(
        self, name: str, body: str | None
    ) -> str:
        """``SPPSAP`` / ``SPPSTP`` / ``SPPSLQ``."""
        if name == "SPPSAP":
            self._state.savema_state = "RUNNING"
            return _spgres("SPPSAP", "OK")
        if name == "SPPSTP":
            self._state.savema_state = "WAITING"
            return _spgres("SPPSTP", "OK")
        if name == "SPPSLQ":
            if body is not None and body.strip().isdigit():
                return _spgres("SPPSLQ", "OK")
            return _spgres("SPPSLQ", "FAIL")
        return _spgres(name, "FAIL")
