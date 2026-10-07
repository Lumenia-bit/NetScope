from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from backend.config import DEFAULT_PORTS, Settings, normalize_mac
from backend.models import DiscoveredDevice, device_from_row, utc_now


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")

    def close(self) -> None:
        self._connection.close()

    def initialize(self) -> None:
        with self._lock, self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac TEXT NOT NULL UNIQUE,
                    ip TEXT NOT NULL,
                    hostname TEXT,
                    vendor TEXT NOT NULL DEFAULT 'Unknown',
                    status TEXT NOT NULL CHECK(status IN ('online', 'offline')),
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    is_new INTEGER NOT NULL DEFAULT 1,
                    ports TEXT NOT NULL DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS device_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
                    event TEXT NOT NULL,
                    detail TEXT,
                    occurred_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    subnet TEXT,
                    ports TEXT NOT NULL,
                    scan_timeout REAL NOT NULL,
                    resolve_hostnames INTEGER NOT NULL,
                    vendor_lookup INTEGER NOT NULL
                );

                """,
            )
            self._connection.execute(
                """
                INSERT OR IGNORE INTO settings
                    (id, subnet, ports, scan_timeout, resolve_hostnames, vendor_lookup)
                VALUES (1, NULL, ?, 0.5, 1, 1)
                """,
                (json.dumps(DEFAULT_PORTS),),
            )

    def get_settings(self) -> Settings:
        with self._lock:
            row = self._connection.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        return Settings(
            subnet=row["subnet"],
            ports=json.loads(row["ports"]),
            scan_timeout=row["scan_timeout"],
            resolve_hostnames=bool(row["resolve_hostnames"]),
            vendor_lookup=bool(row["vendor_lookup"]),
        )

    def update_settings(self, settings: Settings) -> Settings:
        with self._lock, self._connection:
            self._connection.execute(
                """
                UPDATE settings
                SET subnet = ?, ports = ?, scan_timeout = ?,
                    resolve_hostnames = ?, vendor_lookup = ?
                WHERE id = 1
                """,
                (
                    settings.subnet,
                    json.dumps(settings.ports),
                    settings.scan_timeout,
                    settings.resolve_hostnames,
                    settings.vendor_lookup,
                ),
            )
        return self.get_settings()

    def list_devices(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM devices ORDER BY status DESC, ip"
            ).fetchall()
        return [device_from_row(row) for row in rows]

    def get_device(self, device_id: int) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM devices WHERE id = ?", (device_id,)
            ).fetchone()
        return device_from_row(row) if row else None

    def begin_scan(self) -> None:
        with self._lock, self._connection:
            self._connection.execute("UPDATE devices SET is_new = 0")

    def upsert_device(
        self, device: DiscoveredDevice, seen_at: str | None = None
    ) -> dict[str, Any]:
        seen_at = seen_at or utc_now()
        mac = normalize_mac(device.mac)
        with self._lock, self._connection:
            existing = self._connection.execute(
                "SELECT * FROM devices WHERE mac = ?", (mac,)
            ).fetchone()

            if existing is None:
                cursor = self._connection.execute(
                    """
                    INSERT INTO devices
                        (mac, ip, hostname, vendor, status, first_seen, last_seen, is_new, ports)
                    VALUES (?, ?, ?, ?, 'online', ?, ?, 1, ?)
                    """,
                    (
                        mac,
                        device.ip,
                        device.hostname,
                        device.vendor,
                        seen_at,
                        seen_at,
                        json.dumps(device.ports or []),
                    ),
                )
                device_id = cursor.lastrowid
                self._add_event(device_id, "first_seen", f"Discovered at {device.ip}", seen_at)
            else:
                device_id = existing["id"]
                hostname = device.hostname or existing["hostname"]
                vendor = device.vendor if device.vendor != "Unknown" else existing["vendor"]
                ports = device.ports if device.ports is not None else json.loads(existing["ports"])
                if existing["status"] == "offline":
                    self._add_event(device_id, "online", "Device returned to the network", seen_at)
                if existing["ip"] != device.ip:
                    self._add_event(
                        device_id,
                        "ip_changed",
                        f"IP changed from {existing['ip']} to {device.ip}",
                        seen_at,
                    )
                self._connection.execute(
                    """
                    UPDATE devices
                    SET ip = ?, hostname = ?, vendor = ?, status = 'online',
                        last_seen = ?, ports = ?
                    WHERE id = ?
                    """,
                    (device.ip, hostname, vendor, seen_at, json.dumps(ports), device_id),
                )
        return self.get_device(device_id)  # type: ignore[arg-type,return-value]

    def mark_missing_offline(self, seen_macs: set[str], occurred_at: str | None = None) -> None:
        occurred_at = occurred_at or utc_now()
        normalized = {normalize_mac(mac) for mac in seen_macs}
        with self._lock, self._connection:
            online = self._connection.execute(
                "SELECT id, mac FROM devices WHERE status = 'online'"
            ).fetchall()
            for row in online:
                if row["mac"] not in normalized:
                    self._connection.execute(
                        "UPDATE devices SET status = 'offline' WHERE id = ?", (row["id"],)
                    )
                    self._add_event(
                        row["id"], "offline", "Device was not seen in the latest scan", occurred_at
                    )

    def update_device_ports(self, device_id: int, ports: list[int]) -> dict[str, Any] | None:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "UPDATE devices SET ports = ? WHERE id = ?", (json.dumps(ports), device_id)
            )
            if cursor.rowcount:
                self._add_event(
                    device_id,
                    "ports_scanned",
                    f"Open ports: {', '.join(map(str, ports)) if ports else 'none'}",
                    utc_now(),
                )
        return self.get_device(device_id)

    def get_history(self, device_id: int) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT id, event, detail, occurred_at
                FROM device_events WHERE device_id = ?
                ORDER BY occurred_at ASC, id ASC
                """,
                (device_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _add_event(self, device_id: int, event: str, detail: str, occurred_at: str) -> None:
        self._connection.execute(
            """
            INSERT INTO device_events (device_id, event, detail, occurred_at)
            VALUES (?, ?, ?, ?)
            """,
            (device_id, event, detail, occurred_at),
        )
