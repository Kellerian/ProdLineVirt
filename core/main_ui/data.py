from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from core.barcode_scanner.data import ScannerConfig
from core.generator.data import GeneratorConfig
from core.printing.data import PrinterConfig
from core.scanning.data import CameraConfig
from core.transporting.data import TransporterConfig


class ConfigFile(BaseModel):
    model_config = ConfigDict(strict=True)

    printers: list[PrinterConfig] = Field(default=[])
    cameras: list[CameraConfig] = Field(default=[])
    scanners: list[ScannerConfig] = Field(default=[])
    transporters: list[TransporterConfig] = Field(default=[])
    generators: list[GeneratorConfig] = Field(default=[])
