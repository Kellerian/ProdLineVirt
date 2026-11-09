"""Pydantic models for controller device configuration in Line Emulator JSON."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.controller.addresses import normalize_register_token


class ControllerMode(str, Enum):
    """Doypack line mode for the controller card."""

    simplex = "simplex"
    duplex = "duplex"


class ControllerType(str, Enum):
    """PLC / register map variant for the controller card."""

    delta = "delta"
    xinje = "xinje"


class ControllerConfig(BaseModel):
    """Configuration for a Modbus TCP controller (Doypack) device on the line canvas."""

    model_config = ConfigDict(strict=True)

    name: str
    port: int
    queue_size: int = Field(default=10, ge=1, le=1000)
    mode: ControllerMode = ControllerMode.simplex
    controller_type: ControllerType = ControllerType.delta
    register_addresses: list[str | int] = Field(default_factory=list)

    @field_validator("register_addresses", mode="before")
    @classmethod
    def _normalize_register_addresses(cls, value: object) -> object:
        """Normalize list elements to ``str`` tokens or legacy ``int`` addresses."""
        if value is None:
            msg = "register_addresses must be a list, got None"
            raise ValueError(msg)
        if not isinstance(value, list):
            return value
        return [normalize_register_token(item) for item in value]

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
