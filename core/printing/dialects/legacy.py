"""Диалект Legacy: старые status/query (кроме SPPL)."""

from __future__ import annotations

from collections.abc import Callable

from core.printing.chw import get_chw_codes
from core.printing.dialects.base import PrinterDeviceState, PrinterDialect
from core.printing.dialects.sppl import SpplDialect
from core.printing.framing import try_take_sppl_frame
from libs.template_parsers import process_barcode

LineBufferSizeCallback = Callable[[], int]
ClearBufferCallback = Callable[[], None]
RawSendCallback = Callable[[bytes], None]

_ESC_STATUS_QUERY = b"\x1b!?"
_ESC_CLEAR_QUERY = b"\x1b!."
_MAC_QUERY = b'OUT GETSETTING$("CONFIG", "NET", "MAC ADDRESS")'
_MAC_QUERY_ALT = b"^NMACADDR"


class LegacyDialect(PrinterDialect):
    """
    Старый набор status/query-команд и CHW (``START`` / ``ORDER`` / …).

    Кадры ``~SP…^`` делегируются в ``SpplDialect``; остальная логика — как в
    ``PrinterEmul._process_status_requests`` до выноса SPPL.
    """

    def __init__(
        self,
        state: PrinterDeviceState,
        *,
        sppl: SpplDialect | None = None,
        on_clear_line_buffer: ClearBufferCallback | None = None,
        line_buffer_size: LineBufferSizeCallback | None = None,
        on_raw_send: RawSendCallback | None = None,
        mac: str = "02:00:00:00:00:00",
        chw_host: str = "127.0.0.1",
        chw_port: int = 6432,
        chw_dbname: str = "ekoniva_chw",
    ) -> None:
        """
        :param state: Общее состояние (одометр, ``savema_state`` для SPPL).
        :param sppl: Экземпляр SPPL; при ``None`` создаётся с тем же ``state``.
        :param on_clear_line_buffer: Очистка буфера линии (``BUFCLR``, ESC ``!.``).
        :param line_buffer_size: Размер буфера линии (``STATUS`` / ``LABEL``).
        :param on_raw_send: Доп. отправка (две части ответа ``STOP``).
        :param mac: Ответ на запрос MAC-адреса.
        :param chw_host: Хост БД чеквейра для ``ORDER``.
        :param chw_port: Порт БД чеквейра.
        :param chw_dbname: Имя БД чеквейра.
        """
        super().__init__(state)
        self._on_clear_line_buffer = on_clear_line_buffer
        self._line_buffer_size = line_buffer_size
        self._on_raw_send = on_raw_send
        self._mac = mac
        self._chw_host = chw_host
        self._chw_port = chw_port
        self._chw_dbname = chw_dbname
        self._files_list: list[str] = []
        self._sppl = sppl or SpplDialect(
            state, on_clear_line_buffer=on_clear_line_buffer
        )

    def try_handle_query(self, buf: bytearray) -> tuple[int, bytes | None]:
        """
        Обработать legacy status/query или полный кадр SPPL.

        :param buf: Накопленные байты соединения.
        :returns: ``(consumed, response)``; ``(0, None)`` если не query.
        """
        if not buf:
            return 0, None

        data = bytes(buf)
        if data[0] == ord("~"):
            consumed, frame = try_take_sppl_frame(buf)
            if consumed == 0 or frame is None:
                return self._try_legacy_tilde_query(buf)
            return self._sppl.try_handle_query(buf)

        return self._try_legacy_query(buf)

    def try_handle_job(self, buf: bytearray) -> tuple[int, list[str]]:
        """
        Legacy не выделяет бинарные кадры — разбор шаблонов у интегратора.

        :param buf: Накопленные байты соединения.
        :returns: ``(0, [])``.
        """
        return 0, []

    def _buffer_size(self) -> int:
        """Размер буфера кодов линии для ``~S,STATUS`` / ``~S,LABEL``."""
        if self._line_buffer_size is not None:
            return self._line_buffer_size()
        return 0

    def _try_legacy_tilde_query(
        self, buf: bytearray
    ) -> tuple[int, bytes | None]:
        """
        Запросы на ``~``, не являющиеся полным SPPL-кадром (``~HS``, ``~S,…``).

        Неполный ``~SP…`` без ``^`` не обрабатывается — ждём данные.
        """
        data = bytes(buf)
        text = data.decode("latin-1", errors="replace")
        if self._looks_like_incomplete_sppl(text):
            return 0, None
        return self._try_legacy_query(buf)

    def _looks_like_incomplete_sppl(self, text: str) -> bool:
        """Незавершённый кадр SAVEMA (``~SP…`` без ``^``)."""
        if not text.startswith("~"):
            return False
        if "^" in text:
            return False
        for segment in text[1:].split("|"):
            name = segment.strip().upper()
            if name.startswith("SP") and len(name) >= 4:
                return True
        return False

    def _try_legacy_query(self, buf: bytearray) -> tuple[int, bytes | None]:
        """Разбор legacy-команд (без веток SPPL)."""
        data = bytes(buf)
        text = data.decode("latin-1", errors="replace")
        current_buffer_size = self._buffer_size()
        response: str | bytes | None = None
        clear_buffer = False

        if _ESC_STATUS_QUERY in data:
            response = bytes([0x20 if current_buffer_size else 0x00])
        elif _ESC_CLEAR_QUERY in data:
            response = b"CLEAR BUFFER"
            clear_buffer = True
        elif "~!F" in text:
            response = (
                "\r".join(self._files_list) if self._files_list else chr(26)
            )
        elif "DOWNLOAD F" in text:
            parts = text.split(",")
            if len(parts) > 1:
                self._files_list.append(parts[1])
            response = ""
        elif "~S,CHECK" in text:
            response = "00"
        elif "~S,STATUS" in text:
            response = f"00,{current_buffer_size:05d}"
        elif "OUT @LABEL" in text:
            response = f"{self._state.odometer}"
        elif "~HS" in text:
            response = f"0,0,0,0,{self._state.odometer}"
        elif "~S,LABEL" in text:
            response = f"{current_buffer_size}"
        elif "START" in text:
            response = "START ON"
        elif "STOP" in text:
            return self._handle_stop(len(buf))
        elif "ORDER" in text:
            response = self._handle_order(text)
        elif "STATE=1" in text:
            response = "STATE 0x248A = RUNNING"
        elif "STATE" in text:
            response = "STATE 0x248A = RUNNING"
        elif "BOXCLOSE" in text:
            response = "OK"
        elif "SPLIT" in text:
            response = "OK"
        elif "~S,BUFCLR" in text:
            response = "CLEAR BUFFER"
            clear_buffer = True
        elif data in (_MAC_QUERY, _MAC_QUERY_ALT) or text in (
            'OUT GETSETTING$("CONFIG", "NET", "MAC ADDRESS")',
            "^NMACADDR",
        ):
            response = self._mac
        elif "~S,FEED" in text:
            return len(buf), None
        else:
            return 0, None

        if clear_buffer:
            self._clear_line_buffer()

        if response is None:
            return len(buf), None
        if isinstance(response, bytes):
            return len(buf), response
        return len(buf), response.encode("latin-1")

    def _handle_stop(self, consumed: int) -> tuple[int, bytes | None]:
        """Две части ответа ``STOP`` (как в ``printer_core``)."""
        if self._on_raw_send is not None:
            self._on_raw_send(b"STOP CMD")
            self._on_raw_send(b"STOP LINE")
            return consumed, None
        return consumed, b"STOP CMD"

    def _handle_order(self, text: str) -> str:
        """
        Загрузить коды заказа CHW в буфер линии.

        :param text: Сообщение с ``ORDER=…``.
        :returns: Текст ответа клиенту.
        """
        order_id = int(text.split("=")[1])
        codes = get_chw_codes(
            order_id,
            self._chw_host,
            self._chw_port,
            self._chw_dbname,
        )
        if codes:
            processed = [process_barcode(code) for code in codes]
            self._state.emit_codes(processed)
            return f"ORDER SELECT={order_id}"
        return f"Отсутствуют коды в БД для заказа {order_id}"

    def _clear_line_buffer(self) -> None:
        """Очистить буфер кодов линии через callback."""
        if self._on_clear_line_buffer is not None:
            self._on_clear_line_buffer()
