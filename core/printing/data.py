from pydantic import BaseModel, ConfigDict


class PrinterConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    port: int
    buffer: int = 1
