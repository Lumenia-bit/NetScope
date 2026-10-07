from __future__ import annotations

import threading
from dataclasses import asdict, dataclass

from backend.models import utc_now


@dataclass(slots=True)
class ScanSnapshot:
    status: str = "idle"
    progress: int = 0
    devices_discovered: int = 0
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None


class ScanState:
    def __init__(self) -> None:
        self._snapshot = ScanSnapshot()
        self._lock = threading.Lock()

    def begin(self) -> bool:
        with self._lock:
            if self._snapshot.status == "scanning":
                return False
            self._snapshot = ScanSnapshot(status="scanning", started_at=utc_now())
            return True

    def update(self, progress: int, devices_discovered: int) -> None:
        with self._lock:
            if self._snapshot.status == "scanning":
                self._snapshot.progress = max(0, min(100, progress))
                self._snapshot.devices_discovered = devices_discovered

    def finish(self) -> None:
        with self._lock:
            self._snapshot.status = "idle"
            self._snapshot.progress = 100
            self._snapshot.finished_at = utc_now()

    def fail(self, message: str) -> None:
        with self._lock:
            self._snapshot.status = "failed"
            self._snapshot.finished_at = utc_now()
            self._snapshot.error = message

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return asdict(self._snapshot)

