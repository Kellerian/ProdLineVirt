from enum import Enum

from pydantic import BaseModel, ConfigDict


class GeneratorConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    generator_type: str
    give_to: str
    interval: int = 250


class CodeType(Enum):
    UKZ = 'УКЗ'  # 019481043190000021255943532CAC

