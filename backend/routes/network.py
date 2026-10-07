from __future__ import annotations

from fastapi import APIRouter, Request

from backend.scanner.network import detect_local_network


router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("")
def get_network(request: Request) -> dict[str, object]:
    settings = request.app.state.database.get_settings()
    try:
        detected = detect_local_network().as_dict()
        detection_error = None
    except RuntimeError as exc:
        detected = None
        detection_error = str(exc)
    return {
        "detected": detected,
        "configured_subnet": settings.subnet,
        "effective_subnet": settings.subnet or (detected["subnet"] if detected else None),
        "detection_error": detection_error,
    }

