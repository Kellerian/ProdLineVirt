from pydantic import BaseModel, ConfigDict


class CameraParams(BaseModel):
    model_config = ConfigDict(strict=True)

    packet_size: int = 1
    interval: int = 250
    gen_no_read: bool = False
    no_read_perc: int = 0
    gen_duplicates: bool = False
    duplicates_perc: int = 0
    gen_grade: bool = False
    grade_perc: int = 0


class CameraConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    port: int
    config: CameraParams
