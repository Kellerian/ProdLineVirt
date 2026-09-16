"""Unit tests for binary print-job framing (TSPL2 / EZPL / ZPL / SPPL)."""

from __future__ import annotations

import unittest

from core.printing.data import PrinterLanguage
from core.printing.framing import (
    JobFrameKind,
    try_take_ezpl_raster_job,
    try_take_job_frame,
    try_take_sppl_frame,
    try_take_tspl2_bitmap_job,
    try_take_zpl_gfa_job,
)


def _feed_one_byte(
    payload: bytes,
    take_fn,
) -> tuple[int, bytes | None]:
    """
    Подать payload по одному байту и вернуть результат последнего вызова take_fn.

    :param payload: Полный кадр.
    :param take_fn: ``try_take_*`` с сигнатурой ``(buf) -> (int, bytes|None)``.
    """
    buf = bytearray()
    last: tuple[int, bytes | None] = (0, None)
    for byte in payload:
        buf.extend((byte,))
        last = take_fn(buf)
    return last


class TestTspl2BitmapFraming(unittest.TestCase):
    """TSPL2 BITMAP + binary raster + CRLF PRINT."""

    def _build_psm_tspl_job(self) -> bytes:
        """PSM-style 16×16 raster (256 bytes) with decoy PRINT / CR / NUL inside."""
        header = b"SIZE 40 mm,30 mm\r\nCLS\r\nBITMAP 0,0,16,16,0,"
        raster = bytearray(256)
        raster[0:4] = bytes.fromhex("00000000")
        raster[-2:] = bytes.fromhex("1FFF")
        raster[40:45] = b"PRINT"
        raster[80] = 0
        raster[120:122] = b"\r\n"
        footer = b"\r\nPRINT 1,1\r\n"
        return header + bytes(raster) + footer

    def test_full_frame_at_once(self) -> None:
        """Полный кадр извлекается одним вызовом."""
        job = self._build_psm_tspl_job()
        consumed, frame = try_take_tspl2_bitmap_job(job)
        self.assertEqual(consumed, len(job))
        self.assertEqual(frame, job)

    def test_one_byte_chunks(self) -> None:
        """Нарезка по 1 байту даёт кадр только в конце."""
        job = self._build_psm_tspl_job()
        buf = bytearray()
        ready_at: int | None = None
        for index, byte in enumerate(job):
            buf.append(byte)
            consumed, frame = try_take_tspl2_bitmap_job(buf)
            if frame is not None:
                ready_at = index
                self.assertEqual(consumed, len(job))
                self.assertEqual(frame, job)
            else:
                self.assertEqual(consumed, 0)
        self.assertEqual(ready_at, len(job) - 1)

    def test_no_early_print_inside_raster(self) -> None:
        """Подстрока PRINT внутри растра не завершает кадр раньше времени."""
        header = b"BITMAP 0,0,2,8,0,"
        raster = b"PRINT" + b"\x47" * 11
        partial = header + raster
        consumed, frame = try_take_tspl2_bitmap_job(partial)
        self.assertEqual(consumed, 0)
        self.assertIsNone(frame)

        full = partial + b"\r\nPRINT\r\n"
        consumed, frame = try_take_tspl2_bitmap_job(full)
        self.assertEqual(consumed, len(full))
        self.assertEqual(frame, full)


class TestEzplRasterFraming(unittest.TestCase):
    """EZPL Q0,0,B,H + raster + \\r\\nE\\r\\n (PSM B=2, H=8)."""

    def _build_psm_ezpl_job(self) -> bytes:
        envelope = (
            b"^Q40,3\r\n^W40\r\n^P1\r\n^C1\r\n^R0\r\n~R200\r\n^L\r\n"
        )
        header = b"Q0,0,2,8\r\n"
        raster = bytes([0x47] * 16)
        raster_with_trap = bytearray(raster)
        raster_with_trap[4:6] = b"\r\n"
        raster_with_trap[10] = ord("E")  # decoy inside 16-byte raster (B=2, H=8)
        footer = b"\r\nE\r\n"
        return envelope + header + bytes(raster_with_trap) + footer

    def test_full_frame(self) -> None:
        job = self._build_psm_ezpl_job()
        consumed, frame = try_take_ezpl_raster_job(job)
        self.assertEqual(consumed, len(job))
        self.assertEqual(frame, job)

    def test_one_byte_chunks(self) -> None:
        job = self._build_psm_ezpl_job()
        consumed, frame = _feed_one_byte(job, try_take_ezpl_raster_job)
        self.assertEqual(consumed, len(job))
        self.assertEqual(frame, job)

    def test_no_early_e_inside_raster(self) -> None:
        """Байт E и CRLF внутри растра не завершают кадр."""
        header = b"Q0,0,2,8\r\n"
        raster = b"\r\nE" + bytes([0x47] * 13)
        partial = header + raster
        self.assertEqual(try_take_ezpl_raster_job(partial), (0, None))
        full = partial + b"\r\nE\r\n"
        consumed, frame = try_take_ezpl_raster_job(full)
        self.assertEqual(consumed, len(full))
        self.assertEqual(frame, full)


class TestZplGfaFraming(unittest.TestCase):
    """ZPL ^XA … ^GFA + hex + ^FS^PQ1^XZ."""

    def _build_zpl_job(self, hex_payload: str) -> bytes:
        total = len(hex_payload) // 2
        prefix = b"^XA^FO0,0^GFA," + str(total).encode() + b"," + str(total).encode()
        prefix += b",1,"
        return prefix + hex_payload.encode() + b"^FS^PQ1^XZ\r\n"

    def test_full_frame(self) -> None:
        job = self._build_zpl_job("AB" * 8)
        consumed, frame = try_take_zpl_gfa_job(job)
        self.assertEqual(consumed, len(job))
        self.assertEqual(frame, job)

    def test_one_byte_chunks(self) -> None:
        job = self._build_zpl_job("FF00" * 4)
        consumed, frame = _feed_one_byte(job, try_take_zpl_gfa_job)
        self.assertEqual(consumed, len(job))
        self.assertEqual(frame, job)


class TestSpplFraming(unittest.TestCase):
    """SPPL ~…^ chains; braces guard."""

    def test_chain_with_braces(self) -> None:
        frame = b"~SPPSLQ{1000}|SPPSAP^"
        consumed, data = try_take_sppl_frame(frame)
        self.assertEqual(consumed, len(frame))
        self.assertEqual(data, frame)

    def test_brace_does_not_close_on_caret_inside(self) -> None:
        """Символ ^ внутри {…} не завершает кадр."""
        partial = b"~SPLAMQ{key:value^still}"
        self.assertEqual(try_take_sppl_frame(partial), (0, None))
        full = partial + b"^"
        consumed, data = try_take_sppl_frame(full)
        self.assertEqual(consumed, len(full))
        self.assertEqual(data, full)

    def test_one_byte_chunks(self) -> None:
        frame = b"~SPGRES{SPLAMQ:OK}^"
        consumed, data = _feed_one_byte(frame, try_take_sppl_frame)
        self.assertEqual(consumed, len(frame))
        self.assertEqual(data, frame)

    def test_requires_leading_tilde(self) -> None:
        self.assertEqual(try_take_sppl_frame(b"junk~SPLAMQ^"), (0, None))


class TestTryTakeJobFrameDispatcher(unittest.TestCase):
    """Диспетчер try_take_job_frame по PrinterLanguage."""

    def test_tspl2_kind(self) -> None:
        job = b"BITMAP 0,0,2,8,0," + b"\x00" * 16 + b"\r\nPRINT\r\n"
        consumed, frame, kind = try_take_job_frame(job, PrinterLanguage.tspl2)
        self.assertEqual(kind, JobFrameKind.tspl2_bitmap)
        self.assertEqual(frame, job)
        self.assertEqual(consumed, len(job))

    def test_legacy_not_ready(self) -> None:
        self.assertEqual(
            try_take_job_frame(b"anything", PrinterLanguage.legacy),
            (0, None, None),
        )


if __name__ == "__main__":
    unittest.main()
