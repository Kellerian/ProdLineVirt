from pydantic import BaseModel, ConfigDict


class PrinterConfig(BaseModel):
    """Persisted configuration of one printer emulator widget."""

    model_config = ConfigDict(strict=True)

    device_id: str
    name: str
    port: int
    buffer: int = 1
    advanced_expanded: bool = False
