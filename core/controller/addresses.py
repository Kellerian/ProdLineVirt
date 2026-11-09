"""Parse user-facing Modbus register tokens (D/M prefixes and bare numbers)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

RegisterKind = Literal["holding", "coil"]

HOLDING_ADDRESS_MIN = 0
HOLDING_ADDRESS_MAX = 10_000
COIL_ADDRESS_MIN = 0
COIL_ADDRESS_MAX = 5_000

HOLDING_PREFIX_BASE = 4096
COIL_PREFIX_BASE = 2048
BARE_COIL_ADDRESS_MIN = 2048
BARE_COIL_ADDRESS_MAX = 4095

_PARSE_ERROR = "недопустимый адрес переменной"

_RE_HOLDING_PREFIX = re.compile(r"^[Dd](\d+)$")
_RE_COIL_PREFIX = re.compile(r"^[Mm](\d+)$")
_RE_DECIMAL = re.compile(r"^\d+$")


@dataclass(frozen=True, slots=True)
class ParsedRegister:
    """Result of parsing a single register address token."""

    kind: RegisterKind
    address: int
    token: str


def parse_register_token(raw: str) -> ParsedRegister:
    """Parse a user token into register kind, numeric address, and stored token text.

    Args:
        raw: User input (leading/trailing whitespace is stripped).

    Returns:
        Parsed register metadata.

    Raises:
        ValueError: Invalid format or address outside datastore range for the kind.
    """
    token = raw.strip()
    if not token:
        raise ValueError(_PARSE_ERROR)

    holding_match = _RE_HOLDING_PREFIX.match(token)
    if holding_match is not None:
        address = HOLDING_PREFIX_BASE + int(holding_match.group(1))
        _validate_holding_address(address)
        return ParsedRegister(kind="holding", address=address, token=token)

    coil_match = _RE_COIL_PREFIX.match(token)
    if coil_match is not None:
        address = COIL_PREFIX_BASE + int(coil_match.group(1))
        _validate_coil_address(address)
        return ParsedRegister(kind="coil", address=address, token=token)

    if _RE_DECIMAL.match(token):
        address = int(token)
        if BARE_COIL_ADDRESS_MIN <= address <= BARE_COIL_ADDRESS_MAX:
            _validate_coil_address(address)
            return ParsedRegister(kind="coil", address=address, token=token)
        _validate_holding_address(address)
        return ParsedRegister(kind="holding", address=address, token=token)

    raise ValueError(_PARSE_ERROR)


def normalize_register_token(value: object) -> str | int:
    """Normalize a JSON list element to a stored ``str`` or legacy ``int``.

    Args:
        value: Element from ``register_addresses`` before pydantic typing.

    Returns:
        Stripped string token for ``str`` input, or the same ``int`` for legacy ints.

    Raises:
        ValueError: Unsupported type or invalid address.
    """
    if isinstance(value, str):
        return parse_register_token(value).token
    if isinstance(value, int) and not isinstance(value, bool):
        parse_register_token(str(value))
        return value
    msg = f"register_addresses element must be str or int, got {type(value).__name__}"
    raise ValueError(msg)


def _validate_holding_address(address: int) -> None:
    """Raise if holding address is outside the datastore range."""
    if not HOLDING_ADDRESS_MIN <= address <= HOLDING_ADDRESS_MAX:
        raise ValueError(_PARSE_ERROR)


def _validate_coil_address(address: int) -> None:
    """Raise if coil address is outside the datastore range."""
    if not COIL_ADDRESS_MIN <= address <= COIL_ADDRESS_MAX:
        raise ValueError(_PARSE_ERROR)
