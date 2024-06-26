from pydantic import BaseModel, ConfigDict

from core.printing.data import PrinterConfig
from core.scanning.data import CameraConfig
from core.transporting.data import TransporterConfig


class ConfigFile(BaseModel):
    model_config = ConfigDict(strict=True)

    printers: list[PrinterConfig]
    cameras: list[CameraConfig]
    transporters: list[TransporterConfig]
