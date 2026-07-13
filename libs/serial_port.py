"""Утилиты для работы с COM-портами через pyserial (без Qt)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import serial
from serial.tools import list_ports

if TYPE_CHECKING:
    from serial import Serial


BYTESIZE_MAP: dict[int, int] = {
    5: serial.FIVEBITS,
    6: serial.SIXBITS,
    7: serial.SEVENBITS,
    8: serial.EIGHTBITS,
}

PARITY_MAP: dict[str, str] = {
    "N": serial.PARITY_NONE,
    "E": serial.PARITY_EVEN,
    "O": serial.PARITY_ODD,
    "M": serial.PARITY_MARK,
    "S": serial.PARITY_SPACE,
}

STOPBITS_MAP: dict[int, float] = {
    1: serial.STOPBITS_ONE,
    1.5: serial.STOPBITS_ONE_POINT_FIVE,
    2: serial.STOPBITS_TWO,
}


class SerialPortError(Exception):
    """Ошибка открытия или записи в COM-порт."""


@dataclass(frozen=True)
class SerialPortConfig:
    """Параметры COM-порта для эмулятора сканера."""

    port_name: str
    baud_rate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: float = 1
    suffix: str = "\r\n"


def list_available_ports() -> list[str]:
    """Возвращает список имён доступных COM-портов ОС.

    Returns:
        Имена портов (например, ``COM3``) в порядке обнаружения системой.
    """
    return [port.device for port in list_ports.comports()]


def open_serial_port(config: SerialPortConfig) -> Serial:
    """Открывает COM-порт с параметрами из конфигурации.

    Args:
        config: Параметры порта.

    Returns:
        Открытый экземпляр ``serial.Serial``.

    Raises:
        SerialPortError: Порт недоступен или параметры некорректны.
    """
    try:
        bytesize = BYTESIZE_MAP[config.bytesize]
        parity = PARITY_MAP[config.parity.upper()]
        stopbits = STOPBITS_MAP[config.stopbits]
    except KeyError as exc:
        raise SerialPortError(
            f"Некорректный параметр COM-порта: {exc.args[0]}"
        ) from exc

    try:
        return serial.Serial(
            port=config.port_name,
            baudrate=config.baud_rate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=0.1,
        )
    except serial.SerialException as exc:
        raise SerialPortError(
            f"Не удалось открыть {config.port_name}: {exc}"
        ) from exc


def write_barcode(port: Serial, code: str, suffix: str = "\r\n") -> None:
    """Записывает штрихкод в COM-порт с заданным суффиксом.

    Args:
        port: Открытый COM-порт.
        code: Текст штрихкода.
        suffix: Суффикс окончания сканирования (по умолчанию ``\\r\\n``).

    Raises:
        SerialPortError: Ошибка записи или порт закрыт.
    """
    if not port.is_open:
        raise SerialPortError("COM-порт закрыт")

    payload = f"{code}{suffix}".encode("utf-8")
    try:
        port.write(payload)
        port.flush()
    except serial.SerialException as exc:
        raise SerialPortError(f"Ошибка записи в {port.port}: {exc}") from exc
