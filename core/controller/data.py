"""Pydantic models for controller device configuration in Line Emulator JSON."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ControllerMode(str, Enum):
    """Doypack line mode for the controller card."""

    simplex = "simplex"
    duplex = "duplex"


class ControllerType(str, Enum):
    """PLC / register map variant for the controller card."""

    delta = "delta"
    xinje = "xinje"


RegisterAddress = Annotated[int, Field(ge=0, le=10_000)]


class ControllerConfig(BaseModel):
    """Configuration for a Modbus TCP controller (Doypack) device on the line canvas."""

    model_config = ConfigDict(strict=True)

    name: str
    port: int
    queue_size: int = Field(default=10, ge=1, le=1000)
    mode: ControllerMode = ControllerMode.simplex
    controller_type: ControllerType = ControllerType.delta
    register_addresses: list[RegisterAddress] = Field(default_factory=list)

    @field_validator("mode", mode="before")
    @classmethod
    def _coerce_mode(cls, value: object) -> ControllerMode:
        """Deserialize mode from JSON string when strict mode is enabled."""
        if isinstance(value, ControllerMode):
            return value
        if isinstance(value, str):
            return ControllerMode(value)
        msg = f"mode must be ControllerMode or str, got {type(value).__name__}"
        raise ValueError(msg)

    @field_validator("controller_type", mode="before")
    @classmethod
    def _coerce_controller_type(cls, value: object) -> ControllerType:
        """Deserialize controller_type from JSON string when strict mode is enabled."""
        if isinstance(value, ControllerType):
            return value
        if isinstance(value, str):
            return ControllerType(value)
        msg = (
            "controller_type must be ControllerType or str, "
            f"got {type(value).__name__}"
        )
        raise ValueError(msg)
