from __future__ import annotations

import csv
from pathlib import Path


class VendorLookup:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self._vendors: dict[str, str] | None = None

    def find(self, mac: str) -> str:
        if self._vendors is None:
            self._vendors = self._load()
        prefix = mac.upper().replace(":", "").replace("-", "")[:6]
        return self._vendors.get(prefix, "Unknown")

    def _load(self) -> dict[str, str]:
        if not self.database_path.exists():
            return {}
        with self.database_path.open(encoding="utf-8", newline="") as source:
            rows = csv.DictReader(source)
            return {
                row["prefix"].upper().replace(":", "").replace("-", ""): row["vendor"]
                for row in rows
                if row.get("prefix") and row.get("vendor")
            }

