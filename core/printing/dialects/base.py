"""Базовый контракт диалектов принтера и общее состояние устройства."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

CodesCallback = Callable[[list[str]], None]


class PrinterBusyPhase(str, Enum):
    """Фаза занятости принтера для STATUS-ответов (EZPL и др.)."""

    idle = "idle"
    processing = "processing"
    printing = "printing"


@dataclass
class PrinterErrorFlags:
    """Флаги ошибок/состояния (маски совместимы с TSPL ESC !?)."""

    head_open: bool = False
    paper_jam: bool = False
    paper_out: bool = False
    ribbon_out: bool = False
    pause: bool = False
    other_error: bool = False


@dataclass
class PrinterDeviceState:
    """
    Состояние эмулятора, разделяемое диалектами.

    Буфер кодов линии (`_print_buffer` в ``PrinterEmul``) сюда не входит —
    диалект передаёт извлечённые коды через ``on_codes``.
    """

    odometer: int = 0
    remaining: int = 0
    busy_phase: PrinterBusyPhase = PrinterBusyPhase.idle
    errors: PrinterErrorFlags = field(default_factory=PrinterErrorFlags)
    savema_state: str = "RUNNING"
    sppl_queues: dict[str, deque[str]] = field(default_factory=dict)
    on_codes: CodesCallback | None = None

    def emit_codes(self, codes: list[str]) -> None:
        """
        Передать извлечённые коды в буфер линии через callback.

        :param codes: GS1/штрихкоды для постановки в очередь печати.
        """
        if not codes or self.on_codes is None:
            return
        self.on_codes(codes)


class PrinterDialect(ABC):
    """Абстрактный диалект: разбор запросов статуса и заданий печати."""

    def __init__(self, state: PrinterDeviceState) -> None:
        """
        :param state: Общее состояние устройства (одометр, очереди SPPL).
        """
        self._state = state

    @abstractmethod
    def try_handle_query(self, buf: bytearray) -> tuple[int, bytes | None]:
        """
        Попытаться обработать запрос статуса/идентификации.

        :param buf: Накопленные байты соединения.
        :returns: ``(сколько_байт_съесть, ответ)``; ``(0, None)`` — не query
            или кадр ещё неполный.
        """

    @abstractmethod
    def try_handle_job(self, buf: bytearray) -> tuple[int, list[str]]:
        """
        Попытаться разобрать полное задание печати.

        :param buf: Накопленные байты соединения.
        :returns: ``(сколько_байт_съесть, коды)``; ``(0, [])`` — кадр неполный.
            ACK на формат не отправляется на этом уровне.
        """
