"""Тесты извлечения GS1 из заданий печати."""

from core.printing.extract import (
    extract_barcode_value_from_template,
    extract_codes_from_job,
    extract_sppl_field_values,
    normalize_printer_escapes,
    process_barcode,
)


class TestProcessBarcode:
    def test_strips_tilde_one_prefix(self) -> None:
        assert process_barcode("~10123456789012") == "0123456789012"


class TestNormalizePrinterEscapes:
    def test_tilde_d_decimal(self) -> None:
        assert normalize_printer_escapes('~d034') == '"'

    def test_double_tilde(self) -> None:
        assert normalize_printer_escapes("a~~b") == "a~b"


class TestSpplExtraction:
    def test_amq_non_barcode_field(self) -> None:
        msg = (
            "~SPLAMQ{serial~gt~01234567890123~gt~qty~gt~1}^"
        )
        codes = extract_barcode_value_from_template(msg)
        assert codes == ["01234567890123"]

    def test_extract_sppl_field_values_multiple(self) -> None:
        body = "barcode~gt~short~gt~gtin~gt~0123456789012345"
        assert extract_sppl_field_values(body) == ["0123456789012345"]

    def test_spltds_data_element(self) -> None:
        msg = (
            '~SPLTDS{<Label><Data>0123456789012345</Data></Label>}^'
        )
        assert extract_barcode_value_from_template(msg) == [
            "0123456789012345"
        ]


class TestLineFormats:
    def test_ezpl_xrb_next_line(self) -> None:
        template = """
XRB21,15,6,0,35
aolih489au894auj894atu0ajr
"""
        assert extract_barcode_value_from_template(template) == [
            "aolih489au894au"
        ]

    def test_tspl_dmatrix_quoted(self) -> None:
        row = 'DMATRIX 10,10,"01234567890123"'
        assert extract_barcode_value_from_template(row) == [
            "01234567890123"
        ]

    def test_zpl_fh_fd_tilde(self) -> None:
        row = "^FH^FD_7e01234567890123^FS"
        assert extract_barcode_value_from_template(row) == [
            "~01234567890123"
        ]

    def test_zpl_fd_plain(self) -> None:
        row = "^XA^FD01234567890123^FS^XZ"
        assert extract_barcode_value_from_template(row) == [
            "01234567890123"
        ]

    def test_zpl_fh_custom_indicator_hex(self) -> None:
        row = "^FHA^FDA4101234567890123^FS"
        assert extract_barcode_value_from_template(row) == [
            "A01234567890123"
        ]

    def test_zpl_gfa_hex_not_used_as_text_code(self) -> None:
        job = "^XA^GFA,10,10,1,FFFFFFFFFFFFFFFFFFFF^FS^XZ"
        assert extract_barcode_value_from_template(job) == []

    def test_barcode_eq_with_escape(self) -> None:
        row = "BARCODE=~d03401234567890123~d034"
        assert extract_barcode_value_from_template(row) == [
            '"01234567890123"'
        ]


class TestRasterExtraction:
    def test_invalid_raster_does_not_raise(self) -> None:
        job = b"BITMAP 0,0,2,2,0,\x00\x00\x00\x00\r\nPRINT 1,1"
        assert extract_codes_from_job(job) == []
