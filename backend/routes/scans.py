from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from backend.schemas import ScanRequest


router = APIRouter(prefix="/api/scan", tags=["scans"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def start_scan(payload: ScanRequest, request: Request) -> dict[str, object]:
    coordinator = request.app.state.scanner
    if not coordinator.start(payload.subnet, payload.ports):
        raise HTTPException(status_code=409, detail="A network scan is already running")
    return coordinator.state.snapshot()


@router.get("/status")
def scan_status(request: Request) -> dict[str, object]:
    return request.app.state.scanner.state.snapshot()

