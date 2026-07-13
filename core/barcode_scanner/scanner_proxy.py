"""Qt-мост между UI и ядром эмулятора сканера."""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from core.barcode_scanner.scanner_core import ScannerEmul
from libs.serial_port import SerialPortConfig


class ScannerProxy(QObject):
    """Прокси: делегирует работу ``ScannerEmul`` и эмитит ``scanned`` в UI-поток."""

    scanned = Signal(list)
    open_failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._scanner: ScannerEmul | None = None
        self._t_sent = self._get_timer()
        self._t_sent.timeout.connect(self._get_scanned_data)

    @staticmethod
    def _get_timer() -> QTimer:
        """Создаёт таймер опроса отправленных кодов (250 мс)."""
        timer = QTimer()
        timer.setInterval(250)
        return timer

    def start(self, name: str, config: SerialPortConfig) -> None:
        """Запускает эмулятор сканера и таймер опроса.

        Args:
            name: Имя устройства.
            config: Параметры COM-порта.
        """
        self._scanner = ScannerEmul(name, config)
        self._scanner.start()
        self._t_sent.start()

    def stop(self) -> None:
        """Останавливает эмулятор и таймер опроса."""
        if self._scanner is None:
            return
        self._scanner.stop()
        self._t_sent.stop()
        self._scanner = None

    def send_data(self, messages: list[str]) -> None:
        """Передаёт коды в очередь эмулятора.

        Args:
            messages: Штрихкоды для отправки в COM-порт.
        """
        if self._scanner is None:
            return
        self._scanner.send(messages)

    def clear_queues(self) -> None:
        """Сбрасывает очереди отправки и отправленных кодов в ядре."""
        if self._scanner is None:
            return
        self._scanner.clear_queues()

    def _get_scanned_data(self) -> None:
        """Опрашивает ядро: ошибки открытия COM и отправленные коды."""
        if self._scanner is None:
            return
        open_error = self._scanner.pop_open_error()
        if open_error is not None:
            self.open_failed.emit(open_error)
            return
        sent_data = self._scanner.get_sent_data()
        if not sent_data:
            return
        self.scanned.emit(sent_data)
