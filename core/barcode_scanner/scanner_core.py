"""Ядро эмулятора ручного сканера штрихкодов (COM, без Qt)."""

from __future__ import annotations

from collections import deque
from logging import getLogger
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING

from libs.loggers import SCANNER_LOGGER
from libs.serial_port import (
    SerialPortConfig,
    SerialPortError,
    open_serial_port,
    write_barcode,
)

if TYPE_CHECKING:
    from serial import Serial


class ScannerEmul:
    """Эмулятор сканера: очередь кодов и запись в COM-порт в фоновом потоке."""

    def __init__(self, name: str, config: SerialPortConfig) -> None:
        """Инициализирует эмулятор сканера.

        Args:
            name: Отображаемое имя устройства.
            config: Параметры COM-порта.
        """
        self.name = name
        self._config = config
        self._can_run = False
        self._t_processing: Thread | None = None
        self._serial: Serial | None = None
        self._log = getLogger(SCANNER_LOGGER)
        self._to_send: deque[str] = deque()
        self._sent: deque[str] = deque()
        self._open_error: str | None = None

    def start(self) -> None:
        """Запускает фоновый поток обработки и открытие COM-порта."""
        self._can_run = True
        self._t_processing = Thread(
            target=self._run_processing_thread,
            name=f"ScannerEmul-{self.name}",
        )
        self._t_processing.start()

    def stop(self) -> None:
        """Останавливает поток и закрывает COM-порт."""
        self._can_run = False
        if self._t_processing is not None:
            self._t_processing.join()
            self._t_processing = None

    def send(self, messages: list[str]) -> None:
        """Добавляет коды в очередь на отправку.

        Args:
            messages: Список штрихкодов для записи в COM-порт.
        """
        self._to_send.extend(messages)

    def get_sent_data(self) -> list[str]:
        """Возвращает и очищает список успешно отправленных кодов.

        Returns:
            Коды, записанные в COM-порт с момента предыдущего вызова.
        """
        data_list: list[str] = []
        while self._sent:
            data_list.append(self._sent.pop())
        return data_list

    def pop_open_error(self) -> str | None:
        """Возвращает и сбрасывает сообщение об ошибке открытия COM-порта.

        Returns:
            Текст ошибки, если фоновое открытие порта не удалось; иначе ``None``.
        """
        error = self._open_error
        self._open_error = None
        return error

    def clear_queues(self) -> None:
        """Очищает очереди на отправку и уже отправленных кодов."""
        self._to_send.clear()
        self._sent.clear()

    def _run_processing_thread(self) -> None:
        """Фоновый цикл: open COM → drain queue → close COM."""
        try:
            self._serial = open_serial_port(self._config)
            self._log.info(
                "[%s] COM-порт %s открыт",
                self.name,
                self._config.port_name,
            )
        except SerialPortError as exc:
            self._log.error("[%s] Не удалось открыть COM-порт: %s", self.name, exc)
            self._open_error = str(exc)
            self._can_run = False
            return

        try:
            while self._can_run:
                if not self._to_send:
                    sleep(0.01)
                    continue
                code = self._to_send.popleft()
                self._write_code(code)
        finally:
            self._close_serial()

    def _write_code(self, code: str) -> None:
        """Записывает один код в COM-порт и фиксирует успех в ``_sent``."""
        if self._serial is None:
            return
        try:
            write_barcode(self._serial, code, self._config.suffix)
            self._log.info("[%s] SENT: %s", self.name, code)
            self._sent.append(code)
        except SerialPortError as exc:
            self._log.error("[%s] Ошибка записи: %s", self.name, exc)

    def _close_serial(self) -> None:
        """Закрывает COM-порт, если он был открыт."""
        if self._serial is None:
            return
        if self._serial.is_open:
            self._serial.close()
            self._log.info(
                "[%s] COM-порт %s закрыт",
                self.name,
                self._config.port_name,
            )
        self._serial = None
