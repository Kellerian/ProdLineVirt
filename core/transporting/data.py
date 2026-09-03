from pydantic import BaseModel, ConfigDict


class TransporterConfig(BaseModel):
    """Persisted configuration of one transporter emulator widget."""

    model_config = ConfigDict(strict=True)

    device_id: str
    take_from: str
    give_to: str
    interval: int = 250
    advanced_expanded: bool = False
