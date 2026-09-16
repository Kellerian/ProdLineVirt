"""Диалекты языков принтера (TSPL2, EZPL, ZPL, SPPL, Legacy)."""

from core.printing.dialects.base import (
    CodesCallback,
    PrinterBusyPhase,
    PrinterDeviceState,
    PrinterDialect,
    PrinterErrorFlags,
)

__all__ = [
    "CodesCallback",
    "PrinterBusyPhase",
    "PrinterDeviceState",
    "PrinterDialect",
    "PrinterErrorFlags",
]
