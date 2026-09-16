"""Unit tests for ZPL printer dialect (~HI, ~HS, SGD, ^GFA job)."""

from __future__ import annotations

import re
import unittest

from core.printing.dialects.base import PrinterDeviceState
from core.printing.dialects.zpl import ZplDialect
from core.printing.framing import try_take_zpl_gfa_job

_ETX_FRAME_RE = re.compile(rb"\x02[^\x02]*\x03\r\n")


class TestZplDialectQueries(unittest.TestCase):
    """Identity, host status и SGD odometer."""

    def setUp(self) -> None:
        self.state = PrinterDeviceState(odometer=123, remaining=2)
        self.dialect = ZplDialect(self.state)

    def test_hi_response(self) -> None:
        buf = bytearray(b"~HI\r\n")
        consumed, response = self.dialect.try_handle_query(buf)
        self.assertEqual(consumed, len(buf))
        self.assertEqual(response, b"\x02ZEBRA-EMU,1.0,8\x03\r\n")
        self.assertNotIn(b"EZ2350", response or b"")

    def test_hs_three_stx_etx_frames(self) -> None:
        buf = bytearray(b"~HS\r\n")
        consumed, response = self.dialect.try_handle_query(buf)
        self.assertEqual(consumed, len(buf))
        self.assertIsNotNone(response)
        frames = _ETX_FRAME_RE.findall(response or b"")
        self.assertEqual(len(frames), 3)
        body1 = frames[0][1:-3].decode("ascii")
        body2 = frames[1][1:-3].decode("ascii")
        body3 = frames[2][1:-3].decode("ascii")
        self.assertEqual(len(body1.split(",")), 12)
        self.assertEqual(len(body2.split(",")), 11)
        self.assertTrue(body3)
        for field in body1.split(","):
            int(field)
        for field in body2.split(","):
            int(field)

    def test_sgd_odometer_quoted(self) -> None:
        query = b'! U1 getvar "odometer.total_label_count"\r\n'
        consumed, response = self.dialect.try_handle_query(bytearray(query))
        self.assertEqual(consumed, len(query))
        self.assertEqual(response, b'"123"\r\n')

    def test_complete_print_increments_odometer(self) -> None:
        self.state.remaining = 1
        self.dialect.complete_print()
        self.assertEqual(self.state.odometer, 124)
        self.assertEqual(self.state.remaining, 0)


class TestZplDialectJob(unittest.TestCase):
    """^GFA job через framing + extract."""

    def test_gfa_job_emits_fd_code(self) -> None:
        gs1 = "010460406000301021N4N57RTWUUKL"
        job = (
            f"^XA^FO10,10^FD{gs1}^FS^FO0,0^GFA,1,1,1,FF^FS^PQ1^XZ\r\n"
        ).encode()
        consumed, frame = try_take_zpl_gfa_job(job)
        self.assertEqual(consumed, len(job))

        emitted: list[str] = []
        state = PrinterDeviceState(on_codes=lambda codes: emitted.extend(codes))
        dialect = ZplDialect(state)
        job_consumed, codes = dialect.try_handle_job(bytearray(job))
        self.assertEqual(job_consumed, len(job))
        self.assertIn(gs1, codes)
        self.assertIn(gs1, emitted)
        self.assertEqual(state.remaining, 1)


if __name__ == "__main__":
    unittest.main()
