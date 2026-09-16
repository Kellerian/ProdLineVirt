"""Unit tests for TSPL2 printer dialect."""

from __future__ import annotations

import unittest

from core.printing.dialects.base import (
    PrinterBusyPhase,
    PrinterDeviceState,
    PrinterErrorFlags,
)
from core.printing.dialects.tspl2 import Tspl2Dialect, tspl2_status_byte
from core.printing.framing import try_take_tspl2_bitmap_job


class TestTspl2StatusByte(unittest.TestCase):
    """ESC !? response flags."""

    def test_ready_is_single_zero_byte(self) -> None:
        state = PrinterDeviceState()
        self.assertEqual(tspl2_status_byte(state), 0x00)

    def test_error_masks(self) -> None:
        state = PrinterDeviceState(
            errors=PrinterErrorFlags(
                head_open=True,
                paper_jam=True,
                paper_out=True,
                ribbon_out=True,
                pause=True,
                other_error=True,
            ),
            busy_phase=PrinterBusyPhase.printing,
        )
        self.assertEqual(tspl2_status_byte(state), 0x01 | 0x02 | 0x04 | 0x08 | 0x10 | 0x20 | 0x80)


class TestTspl2Queries(unittest.TestCase):
    """try_handle_query: ESC !?, PSM_LABEL; no ~HI."""

    def setUp(self) -> None:
        self.emitted: list[str] = []
        self.state = PrinterDeviceState(
            odometer=42,
            on_codes=lambda codes: self.emitted.extend(codes),
        )
        self.dialect = Tspl2Dialect(self.state)

    def test_esc_status_query_one_byte_not_ascii(self) -> None:
        buf = bytearray(b"\x1b!?")
        consumed, response = self.dialect.try_handle_query(buf)
        self.assertEqual(consumed, 3)
        self.assertEqual(response, b"\x00")
        self.assertEqual(len(response), 1)

    def test_esc_status_partial_waits(self) -> None:
        buf = bytearray(b"\x1b!")
        consumed, response = self.dialect.try_handle_query(buf)
        self.assertEqual(consumed, 0)
        self.assertIsNone(response)

    def test_psm_label_odometer(self) -> None:
        query = b'OUT NET "PSM_LABEL=";STR$(LABEL)\r\n'
        consumed, response = self.dialect.try_handle_query(bytearray(query))
        self.assertEqual(consumed, len(query))
        self.assertEqual(response, b"PSM_LABEL=42\r\n")

    def test_psm_label_partial(self) -> None:
        partial = b'OUT NET "PSM_LABEL=";STR$(L'
        consumed, response = self.dialect.try_handle_query(bytearray(partial))
        self.assertEqual(consumed, 0)
        self.assertIsNone(response)

    def test_no_response_to_hi(self) -> None:
        consumed, response = self.dialect.try_handle_query(bytearray(b"~HI\r\n"))
        self.assertEqual(consumed, 0)
        self.assertIsNone(response)

    def test_no_response_to_godex_status(self) -> None:
        consumed, response = self.dialect.try_handle_query(bytearray(b"~S,STATUS\r\n"))
        self.assertEqual(consumed, 0)
        self.assertIsNone(response)


class TestTspl2BitmapJob(unittest.TestCase):
    """BITMAP job via framing + extract; PRINT inside raster is not a second job."""

    def setUp(self) -> None:
        self.emitted: list[str] = []
        self.state = PrinterDeviceState(on_codes=lambda codes: self.emitted.extend(codes))
        self.dialect = Tspl2Dialect(self.state)

    def _psm_bitmap_job(self) -> bytes:
        header = (
            b"SIZE 40 mm,30 mm\r\nCLS\r\n"
            b'DMATRIX 10,10,"01234567890123"\r\n'
            b"BITMAP 0,0,16,16,0,"
        )
        raster = bytearray(256)
        raster[40:45] = b"PRINT"
        return header + bytes(raster) + b"\r\nPRINT 1,1\r\n"

    def test_job_consumed_once_remaining_incremented(self) -> None:
        job = self._psm_bitmap_job()
        consumed, codes = self.dialect.try_handle_job(bytearray(job))
        self.assertEqual(consumed, len(job))
        self.assertIn("01234567890123", codes)
        self.assertEqual(self.state.remaining, 1)
        self.assertEqual(self.emitted, ["01234567890123"])
        self.assertEqual(self.state.odometer, 0)

    def test_cls_does_not_reset_odometer(self) -> None:
        self.state.odometer = 99
        job = self._psm_bitmap_job()
        self.dialect.try_handle_job(bytearray(job))
        self.assertEqual(self.state.odometer, 99)

    def test_framing_single_frame_with_print_inside_raster(self) -> None:
        job = self._psm_bitmap_job()
        consumed, frame = try_take_tspl2_bitmap_job(job)
        self.assertEqual(consumed, len(job))
        self.assertIsNotNone(frame)
        second, frame2 = try_take_tspl2_bitmap_job(job[consumed:])
        self.assertEqual(second, 0)
        self.assertIsNone(frame2)


if __name__ == "__main__":
    unittest.main()
