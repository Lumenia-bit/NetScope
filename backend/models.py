from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(slots=True)
class DiscoveredDevice:
    ip: str
    mac: str
    hostname: str | None = None
    vendor: str = "Unknown"
    ports: list[int] | None = None


def device_from_row(row: Any) -> dict[str, Any]:
    import json

    return {
        "id": row["id"],
        "mac": row["mac"],
        "ip": row["ip"],
        "hostname": row["hostname"],
        "vendor": row["vendor"],
        "status": row["status"],
        "first_seen": row["first_seen"],
        "last_seen": row["last_seen"],
        "is_new": bool(row["is_new"]),
        "ports": json.loads(row["ports"]),
    }

