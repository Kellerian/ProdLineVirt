from pydantic import BaseModel, ConfigDict


class TransporterConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    take_from: str
    give_to: str
    interval: int = 250
