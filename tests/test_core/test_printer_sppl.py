"""Unit-тесты диалекта SAVEMA SPPL."""

from __future__ import annotations

from collections import deque

from core.printing.dialects.base import PrinterDeviceState
from core.printing.dialects.sppl import SpplDialect


class _CodeCollector:
    """Собирает коды из ``on_codes``."""

    def __init__(self) -> None:
        self.codes: list[str] = []

    def __call__(self, codes: list[str]) -> None:
        self.codes.extend(codes)


def _dialect(
    *,
    on_clear: bool = False,
) -> tuple[SpplDialect, PrinterDeviceState, _CodeCollector]:
    state = PrinterDeviceState()
    collector = _CodeCollector()
    state.on_codes = collector
    cleared: list[str] = []

    def clear_line() -> None:
        cleared.append("cleared")

    dialect = SpplDialect(
        state,
        on_clear_line_buffer=clear_line if on_clear else None,
    )
    return dialect, state, collector


class TestSpplAmq:
    def test_amq_non_barcode_field_emits_code(self) -> None:
        dialect, _state, collector = _dialect()
        frame = (
            "~SPLAMQ{serial~gt~01234567890123~gt~qty~gt~1}^"
        ).encode("latin-1")
        buf = bytearray(frame)
        consumed, response = dialect.try_handle_query(buf)
        assert consumed == len(frame)
        assert response == b"~SPGRES{SPLAMQ:OK}^"
        assert collector.codes == ["01234567890123"]

    def test_gmq_reflects_amq_fifo_depth(self) -> None:
        dialect, state, _collector = _dialect()
        amq = b"~SPLAMQ{serial~gt~01234567890123}^"
        dialect.try_handle_query(bytearray(amq))
        assert len(state.sppl_queues["serial"]) == 1
        _consumed, response = dialect.try_handle_query(
            bytearray(b"~SPLGMQ{serial}^")
        )
        assert response == b"~SPGRES{SPLGMQ:serial=1}^"


class TestSpplCmq:
    def test_cmq_spgres_not_clear_buffer_text(self) -> None:
        dialect, state, _collector = _dialect(on_clear=True)
        state.sppl_queues["serial"] = deque(["01234567890123"])
        frame = b"~SPLCMQ{serial~gt~01234567890123}^"
        consumed, response = dialect.try_handle_query(bytearray(frame))
        assert consumed == len(frame)
        assert response == b"~SPGRES{SPLCMQ:OK}^"
        assert "serial" not in state.sppl_queues


class TestSpplSta:
    def test_sta_without_working_suffix(self) -> None:
        dialect, state, _collector = _dialect()
        state.savema_state = "RUNNING"
        frame = b"~SPPSTA^"
        _consumed, response = dialect.try_handle_query(bytearray(frame))
        assert response == b"~SPGRES{SPPSTA:RUNNING<}^"
        assert b"WORKING" not in response


class TestSpplChain:
    def test_slq_then_sap_in_one_frame(self) -> None:
        dialect, state, _collector = _dialect()
        state.savema_state = "WAITING"
        frame = b"~SPPSLQ{1000}|SPPSAP^"
        consumed, response = dialect.try_handle_query(bytearray(frame))
        assert consumed == len(frame)
        assert response == (
            b"~SPGRES{SPPSLQ:OK}^~SPGRES{SPPSAP:OK}^"
        )
        assert state.savema_state == "RUNNING"


class TestSpplFixesFromLegacy:
    def test_splddf_command_name(self) -> None:
        dialect, _state, _collector = _dialect()
        frame = b"~SPLDDF{foo}^"
        _consumed, response = dialect.try_handle_query(bytearray(frame))
        assert response == b"~SPGRES{SPLDDF:OK}^"
        assert b"SPLFFG" not in (response or b"")

    def test_splgsd_spgres_format(self) -> None:
        dialect, _state, _collector = _dialect()
        frame = b"~SPLGSD^"
        _consumed, response = dialect.try_handle_query(bytearray(frame))
        assert response == b"~SPGRES{SPLGSD:a.csv<b.csv}^"

    def test_spggfw_alias_uses_spggfv_name(self) -> None:
        dialect, _state, _collector = _dialect()
        frame = b"~SPGGFW^"
        _consumed, response = dialect.try_handle_query(bytearray(frame))
        assert response == b"~SPGRES{SPGGFV:(v3.29)}^"


class TestSpplGmq:
    def test_gmq_multiple_fields(self) -> None:
        dialect, state, _collector = _dialect()
        state.sppl_queues["F1"] = deque(
            ["01234567890123", "01234567890124"]
        )
        state.sppl_queues["F2"] = deque()
        frame = b"~SPLGMQ{F1<F2}^"
        _consumed, response = dialect.try_handle_query(bytearray(frame))
        assert response == b"~SPGRES{SPLGMQ:F1=2<F2=0}^"


class TestSpplIncomplete:
    def test_partial_frame_not_consumed(self) -> None:
        dialect, _state, _collector = _dialect()
        buf = bytearray(b"~SPLAMQ{serial~gt~012")
        consumed, response = dialect.try_handle_query(buf)
        assert consumed == 0
        assert response is None
        assert len(buf) == len(b"~SPLAMQ{serial~gt~012")
