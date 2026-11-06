"""Test package bootstrap: stub ``pylibdmtx`` when the native DLL is unavailable."""

from __future__ import annotations

import sys
import types


def _ensure_pylibdmtx_stub() -> None:
    """Allow imports of printing stack without ``libdmtx-64.dll`` on PATH.

    Some developer machines lack the pylibdmtx wheel DLL; core code imports
    ``decode`` at module load. Unit tests that do not exercise DataMatrix
    decoding still need those modules importable.
    """
    try:
        import pylibdmtx.pylibdmtx  # noqa: F401
    except (ImportError, OSError, FileNotFoundError):
        root = types.ModuleType("pylibdmtx")
        sub = types.ModuleType("pylibdmtx.pylibdmtx")

        def decode(*_args: object, **_kwargs: object) -> list[object]:
            return []

        class _Encoded:
            """Minimal stand-in for pylibdmtx ``encode`` return value."""

            __slots__ = ("width", "height", "pixels")

            def __init__(self, width: int, height: int, pixels: bytes) -> None:
                self.width = width
                self.height = height
                self.pixels = pixels

        def encode(_data: bytes, **_kwargs: object) -> _Encoded:
            return _Encoded(1, 1, b"\x00\x00\x00")

        sub.decode = decode
        sub.encode = encode
        root.pylibdmtx = sub
        sys.modules.setdefault("pylibdmtx", root)
        sys.modules.setdefault("pylibdmtx.pylibdmtx", sub)


_ensure_pylibdmtx_stub()
