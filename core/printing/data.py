from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class PrinterLanguage(str, Enum):
    """Эмулируемый язык/протокол принтера."""

    legacy = "legacy"
    tspl2 = "tspl2"
    ezpl = "ezpl"
    zpl = "zpl"
    sppl = "sppl"


class PrinterConfig(BaseModel):
    """Конфигурация TCP-эмулятора принтера в линии."""

    model_config = ConfigDict(strict=True)

    name: str
    port: int
    buffer: int = 1
    language: PrinterLanguage = PrinterLanguage.legacy

    @field_validator("language", mode="before")
    @classmethod
    def _coerce_language(cls, value: object) -> PrinterLanguage:
        """Deserialize language from JSON string when strict mode is enabled."""
        if isinstance(value, PrinterLanguage):
            return value
        if isinstance(value, str):
            return PrinterLanguage(value)
        msg = f"language must be PrinterLanguage or str, got {type(value).__name__}"
        raise ValueError(msg)
