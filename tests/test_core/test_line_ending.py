"""Unit tests for CR/LF helpers in printer protocols."""

from __future__ import annotations

import unittest

from core.printing.line_ending import ensure_crlf_suffix


class TestEnsureCrlfSuffix(unittest.TestCase):
    """Ответы клиенту через PrinterEmul всегда завершаются CR LF."""

    def test_appends_to_bare_payload(self) -> None:
        self.assertEqual(ensure_crlf_suffix(b"000"), b"000\r\n")

    def test_unchanged_if_already_crlf(self) -> None:
        self.assertEqual(ensure_crlf_suffix(b"00,00000\r\n"), b"00,00000\r\n")

    def test_empty_becomes_crlf_only(self) -> None:
        self.assertEqual(ensure_crlf_suffix(b""), b"\r\n")


if __name__ == "__main__":
    unittest.main()
