from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from backend.config import Settings, validate_subnet
from backend.database import Database
from backend.models import DiscoveredDevice
from backend.scanner.discovery import discover_devices
from backend.scanner.hostname import resolve_hostname
from backend.scanner.network import detect_local_network
from backend.scanner.ports import scan_ports
from backend.scanner.state import ScanState
from backend.scanner.vendor import VendorLookup


logger = logging.getLogger(__name__)


class ScanCoordinator:
    def __init__(self, database: Database, oui_path: str | Path) -> None:
        self.database = database
        self.state = ScanState()
        self.vendor_lookup = VendorLookup(oui_path)
        self._task: asyncio.Task[None] | None = None

    def start(self, subnet: str | None = None, ports: list[int] | None = None) -> bool:
        if not self.state.begin():
            return False
        self._task = asyncio.create_task(self._run(subnet, ports))
        return True

    async def _run(self, subnet: str | None, ports: list[int] | None) -> None:
        try:
            settings = self.database.get_settings()
            target = validate_subnet(subnet or settings.subnet or detect_local_network().subnet)
            selected_ports = ports or settings.ports
            self.state.update(5, 0)

            discovered = await asyncio.to_thread(discover_devices, target, settings.scan_timeout)
            self.database.begin_scan()
            self.state.update(15, len(discovered))
            await self._inspect_devices(discovered, settings, selected_ports)

            seen_macs = {device.mac for device in discovered}
            self.database.mark_missing_offline(seen_macs)
            self.state.finish()
        except (RuntimeError, ValueError) as exc:
            logger.warning("Network scan failed: %s", exc)
            self.state.fail(str(exc))
        except Exception:
            logger.exception("Unexpected error during network scan")
            self.state.fail("Unexpected error during scan; check the server log")

    async def _inspect_devices(
        self, devices: list[DiscoveredDevice], settings: Settings, ports: list[int]
    ) -> None:
        if not devices:
            return
        semaphore = asyncio.Semaphore(6)
        completed = 0
        completed_lock = asyncio.Lock()

        async def inspect(device: DiscoveredDevice) -> None:
            nonlocal completed
            async with semaphore:
                hostname_task = (
                    asyncio.to_thread(resolve_hostname, device.ip)
                    if settings.resolve_hostnames
                    else None
                )
                ports_task = asyncio.to_thread(
                    scan_ports, device.ip, ports, settings.scan_timeout
                )
                if hostname_task:
                    device.hostname, device.ports = await asyncio.gather(
                        hostname_task, ports_task
                    )
                else:
                    device.ports = await ports_task
                if settings.vendor_lookup:
                    device.vendor = self.vendor_lookup.find(device.mac)
                self.database.upsert_device(device)

            async with completed_lock:
                completed += 1
                progress = 15 + round((completed / len(devices)) * 80)
                self.state.update(progress, len(devices))

        await asyncio.gather(*(inspect(device) for device in devices))
