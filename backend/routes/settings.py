from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Request

from backend.config import Settings
from backend.schemas import SettingsPayload


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings(request: Request) -> dict[str, object]:
    return asdict(request.app.state.database.get_settings())


@router.put("")
def update_settings(payload: SettingsPayload, request: Request) -> dict[str, object]:
    settings = Settings(**payload.model_dump())
    return asdict(request.app.state.database.update_settings(settings))

