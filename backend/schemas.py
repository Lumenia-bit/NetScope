from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from backend.config import validate_ports, validate_subnet


class SettingsPayload(BaseModel):
    subnet: str | None = None
    ports: list[int]
    scan_timeout: float = Field(ge=0.05, le=10)
    resolve_hostnames: bool
    vendor_lookup: bool

    @field_validator("subnet")
    @classmethod
    def subnet_is_valid(cls, value: str | None) -> str | None:
        return validate_subnet(value) if value else None

    @field_validator("ports")
    @classmethod
    def ports_are_valid(cls, value: list[int]) -> list[int]:
        return validate_ports(value)


class ScanRequest(BaseModel):
    subnet: str | None = None
    ports: list[int] | None = None

    @field_validator("subnet")
    @classmethod
    def subnet_is_valid(cls, value: str | None) -> str | None:
        return validate_subnet(value) if value else None

    @field_validator("ports")
    @classmethod
    def ports_are_valid(cls, value: list[int] | None) -> list[int] | None:
        return validate_ports(value) if value is not None else None


class PortScanRequest(BaseModel):
    ports: list[int] | None = None

    @field_validator("ports")
    @classmethod
    def ports_are_valid(cls, value: list[int] | None) -> list[int] | None:
        return validate_ports(value) if value is not None else None

