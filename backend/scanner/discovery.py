from __future__ import annotations

from backend.models import DiscoveredDevice


def discover_devices(subnet: str, timeout: float) -> list[DiscoveredDevice]:
    try:
        from scapy.all import ARP, Ether, srp
    except ImportError as exc:
        raise RuntimeError("Scapy is required for ARP discovery") from exc

    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
    try:
        answered, _ = srp(packet, timeout=timeout, verbose=False, retry=0)
    except PermissionError as exc:
        raise RuntimeError("ARP scanning requires root or CAP_NET_RAW permission") from exc
    except OSError as exc:
        raise RuntimeError(f"ARP scan failed: {exc}") from exc

    devices: dict[str, DiscoveredDevice] = {}
    for _, response in answered:
        mac = response.hwsrc.upper()
        devices[mac] = DiscoveredDevice(ip=response.psrc, mac=mac)
    return sorted(devices.values(), key=lambda item: tuple(map(int, item.ip.split("."))))

