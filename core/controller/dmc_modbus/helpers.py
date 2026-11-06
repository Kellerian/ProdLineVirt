"""Helpers to construct async Modbus clients from address strings."""

from __future__ import annotations

import ipaddress

from pymodbus.client import AsyncModbusTcpClient

from core.controller.dmc_modbus.exceptions import LineControllerException


def get_modbus(addr: str) -> AsyncModbusTcpClient:
    """Build an asynchronous Modbus TCP client from a host:port string.

    Parameters
    ----------
    addr
        TCP endpoint: ``hostname:port``, IPv4 ``a.b.c.d:port``, or IPv6 only as
        ``[addr]:port`` (unambiguous; raw IPv6 with multiple colons and no
        brackets is rejected).

    Returns
    -------
    AsyncModbusTcpClient
        Client configured with timeout 0.3 s and one retry.

    Raises
    ------
    LineControllerException
        If the address string is not a valid TCP endpoint description or the
        port is not in the range 1–65535.
    """
    stripped = addr.strip()
    if ":" not in stripped:
        msg = (
            f"Неверно указаны настройки подключения {addr}! "
            "Используйте формат 'host:502' или для IPv6 '[::1]:502'"
        )
        raise LineControllerException(msg)

    # Bracketed IPv6: [::1]:502 — единственный однозначный вид для IPv6.
    if stripped.startswith("["):
        bracket_end = stripped.find("]")
        if bracket_end < 0:
            msg = f"Неверно указаны настройки подключения {addr}! Ожидается '[addr]:port'"
            raise LineControllerException(msg)
        host = stripped[1:bracket_end]
        rest = stripped[bracket_end + 1 :].strip()
        if not rest.startswith(":"):
            msg = f"Неверно указаны настройки подключения {addr}! После ']' нужен ':port'"
            raise LineControllerException(msg)
        port_str = rest[1:].strip()
    else:
        # Несколько ':' без скобок — неоднозначно (сырой IPv6); требуем [addr]:port.
        if stripped.count(":") > 1:
            msg = (
                f"Неверно указаны настройки подключения {addr}! "
                "Для IPv6 используйте '[addr]:port'"
            )
            raise LineControllerException(msg)
        host_part, port_str = stripped.rsplit(":", 1)
        host = host_part

    host = host.strip()
    if not host:
        msg = (
            f"Неверно указаны настройки подключения {addr}! "
            "Хост не может быть пустым"
        )
        raise LineControllerException(msg)

    try:
        port = int(port_str)
    except ValueError as exc:
        msg = (
            f"Неверно указаны настройки подключения {addr}! "
            "Порт после ':' должен быть целым числом"
        )
        raise LineControllerException(msg) from exc

    if not (1 <= port <= 65535):
        msg = (
            f"Неверно указаны настройки подключения {addr}! "
            "Порт должен быть в диапазоне 1–65535"
        )
        raise LineControllerException(msg)

    try:
        ipaddress.ip_address(host)
    except ValueError:
        # Допускаем hostname без разрешения здесь; pymodbus/asyncio разрешит при connect.
        pass

    client = AsyncModbusTcpClient(
        host,
        port=port,
        timeout=0.3,
        name=addr,
        retries=1,
    )
    return client
