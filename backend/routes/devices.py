from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Request

from backend.config import SERVICE_NAMES
from backend.scanner.ports import scan_ports
from backend.schemas import PortScanRequest


router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
def list_devices(request: Request) -> list[dict[str, object]]:
    return request.app.state.database.list_devices()


@router.get("/{device_id}")
def get_device(device_id: int, request: Request) -> dict[str, object]:
    device = request.app.state.database.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device["open_ports"] = [
        {"port": port, "service": SERVICE_NAMES.get(port, "Unknown"), "state": "open"}
        for port in device["ports"]
    ]
    return device


@router.get("/{device_id}/history")
def get_device_history(device_id: int, request: Request) -> list[dict[str, object]]:
    if not request.app.state.database.get_device(device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    return request.app.state.database.get_history(device_id)


@router.post("/{device_id}/scan-ports")
async def scan_device_ports(
    device_id: int, payload: PortScanRequest, request: Request
) -> dict[str, object]:
    database = request.app.state.database
    device = database.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    settings = database.get_settings()
    ports = payload.ports or settings.ports
    open_ports = await asyncio.to_thread(
        scan_ports, device["ip"], ports, settings.scan_timeout
    )
    updated = database.update_device_ports(device_id, open_ports)
    return {
        "device_id": device_id,
        "ports": open_ports,
        "open_ports": [
            {"port": port, "service": SERVICE_NAMES.get(port, "Unknown"), "state": "open"}
            for port in open_ports
        ],
        "device": updated,
    }
