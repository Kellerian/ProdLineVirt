"""Unit tests for GoDEX EZPL dialect queries."""

from __future__ import annotations

import unittest

from core.printing.dialects.base import PrinterDeviceState
from core.printing.dialects.ezpl import EzplDialect, format_ezpl_label_remaining


class TestFormatEzplLabelRemaining(unittest.TestCase):
    """Ответ ~S,LABEL — 3–5 цифр."""

    def test_zero(self) -> None:
        self.assertEqual(format_ezpl_label_remaining(0), "000")

    def test_psm_padding(self) -> None:
        self.assertEqual(format_ezpl_label_remaining(15), "015")


class TestEzplLabelQueryLineEndings(unittest.TestCase):
    """~S,LABEL принимает опциональные CR/LF."""

    def setUp(self) -> None:
        self.dialect = EzplDialect(PrinterDeviceState(remaining=7))

    def _label_response(self, query: bytes) -> tuple[int, bytes]:
        buf = bytearray(query)
        consumed, response = self.dialect.try_handle_query(buf)
        return consumed, response or b""

    def test_no_line_ending(self) -> None:
        consumed, response = self._label_response(b"~S,LABEL")
        self.assertEqual(consumed, len(b"~S,LABEL"))
        self.assertEqual(response, b"007")

    def test_crlf(self) -> None:
        consumed, response = self._label_response(b"~S,LABEL\r\n")
        self.assertEqual(consumed, len(b"~S,LABEL\r\n"))
        self.assertEqual(response, b"007")

    def test_lf_only(self) -> None:
        consumed, response = self._label_response(b"~S,LABEL\n")
        self.assertEqual(consumed, len(b"~S,LABEL\n"))
        self.assertEqual(response, b"007")

    def test_cr_only(self) -> None:
        consumed, response = self._label_response(b"~S,LABEL\r")
        self.assertEqual(consumed, len(b"~S,LABEL\r"))
        self.assertEqual(response, b"007")

    def test_mixed_repeat_endings(self) -> None:
        query = b"~S,LABEL\r\n\n"
        consumed, response = self._label_response(query)
        self.assertEqual(consumed, len(query))
        self.assertEqual(response, b"007")


class TestEzplStatusQueryLineEndings(unittest.TestCase):
    """~S,STATUS с теми же правилами окончания строки."""

    def setUp(self) -> None:
        self.dialect = EzplDialect(PrinterDeviceState(remaining=3))

    def test_lf_only(self) -> None:
        buf = bytearray(b"~S,STATUS\n")
        consumed, response = self.dialect.try_handle_query(buf)
        self.assertEqual(consumed, len(b"~S,STATUS\n"))
        self.assertEqual(response, b"00,00003\r\n")


if __name__ == "__main__":
    unittest.main()
