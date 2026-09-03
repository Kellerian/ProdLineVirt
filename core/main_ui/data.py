from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.barcode_scanner.data import ScannerConfig
from core.generator.data import GeneratorConfig
from core.printing.data import PrinterConfig
from core.scanning.data import CameraConfig
from core.transporting.data import TransporterConfig


class ConfigFile(BaseModel):
    """Root Line Emulator project file persisted as JSON."""

    model_config = ConfigDict(strict=True)

    printers: list[PrinterConfig] = Field(default=[])
    cameras: list[CameraConfig] = Field(default=[])
    scanners: list[ScannerConfig] = Field(default=[])
    transporters: list[TransporterConfig] = Field(default=[])
    generators: list[GeneratorConfig] = Field(default=[])
    sidebar_order: list[str] = Field(default=[])
    canvas_order: list[str] = Field(default=[])
    dock_state: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _apply_legacy_migration(cls, data: Any) -> Any:
        """Migrate legacy JSON payloads before strict validation."""
        from core.main_ui.config_migration import (
            enrich_legacy_config,
            needs_legacy_migration,
        )

        if isinstance(data, dict) and needs_legacy_migration(data):
            import copy

            return enrich_legacy_config(copy.deepcopy(data))
        return data
