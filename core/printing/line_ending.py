"""Разбор опциональных окончаний строк (CR/LF) в протоколах принтера."""

from __future__ import annotations

_CR = 0x0D
_LF = 0x0A


def consume_optional_line_endings(data: bytes, start: int) -> int:
    """
    Пропустить ноль или более символов ``\\r`` и/или ``\\n`` с позиции ``start``.

    Поддерживаются любые сочетания: ``\\r``, ``\\n``, ``\\r\\n``, ``\\n\\r``, повторы.

    :param data: Буфер входящих байт.
    :param start: Индекс сразу после тела команды.
    :returns: Индекс в ``data`` после всех подряд идущих CR/LF.
    """
    pos = start
    while pos < len(data) and data[pos] in (_CR, _LF):
        pos += 1
    return pos


def try_take_exact_command(data: bytes, command: bytes) -> int | None:
    """
    Съесть ``command`` в начале ``data`` и опциональные окончания строки.

    :param data: Накопленные байты соединения.
    :param command: Тело команды без перевода строки.
    :returns: Длина съеденного префикса; ``None`` если буфер ещё неполный;
        ``0`` если префикс не совпадает или после команды идёт не CR/LF.
    """
    if len(data) < len(command):
        if command.startswith(data):
            return None
        return 0
    if data[: len(command)] != command:
        return 0
    rest_start = len(command)
    if len(data) == rest_start:
        return rest_start
    if data[rest_start] in (_CR, _LF):
        return consume_optional_line_endings(data, rest_start)
    return 0


def ensure_crlf_suffix(payload: bytes) -> bytes:
    """
    Добавить ``\\r\\n`` в конец ответа клиенту, если его ещё нет.

    :param payload: Тело ответа из диалекта.
    :returns: Байты для ``sendall`` (всегда с завершающим CR LF).
    """
    if payload.endswith(b"\r\n"):
        return payload
    return payload + b"\r\n"
