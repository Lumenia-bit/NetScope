from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT_DIR / "data" / "netscope.db"

DEFAULT_PORTS = [
    22,
    23,
    53,
    80,
    110,
    139,
    143,
    443,
    445,
    3306,
    3389,
    5432,
    5900,
    8000,
    8080,
    8443,
]

SERVICE_NAMES = {
    22: "SSH",
    23: "Telnet",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    8000: "HTTP-alt",
    8080: "HTTP-alt",
    8443: "HTTPS-alt",
}

MAC_PATTERN = re.compile(r"^[0-9A-F]{2}(?::[0-9A-F]{2}){5}$")


@dataclass(slots=True)
class Settings:
    subnet: str | None
    ports: list[int]
    scan_timeout: float
    resolve_hostnames: bool
    vendor_lookup: bool


def validate_subnet(value: str) -> str:
    try:
        network = ipaddress.ip_network(value.strip(), strict=False)
    except ValueError as exc:
        raise ValueError("Enter a valid IPv4 subnet, such as 192.168.1.0/24") from exc

    if network.version != 4:
        raise ValueError("Only IPv4 networks are supported")
    if network.num_addresses > 65_536:
        raise ValueError("Subnet is too large; use /16 or a smaller network")
    if network.is_multicast or network.is_unspecified or network.is_loopback:
        raise ValueError("Subnet must be a local unicast network")
    if network.is_global:
        raise ValueError("Only private or locally routed networks can be scanned")
    return str(network)


def validate_ports(values: Iterable[int]) -> list[int]:
    ports: list[int] = []
    seen: set[int] = set()
    for raw in values:
        if isinstance(raw, bool):
            raise ValueError("Ports must be integers between 1 and 65535")
        try:
            port = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("Ports must be integers between 1 and 65535") from exc
        if port < 1 or port > 65_535:
            raise ValueError(f"Port {port} is outside the valid range")
        if port not in seen:
            ports.append(port)
            seen.add(port)
    if not ports:
        raise ValueError("At least one port is required")
    if len(ports) > 128:
        raise ValueError("No more than 128 ports can be scanned at once")
    return sorted(ports)


def normalize_mac(value: str) -> str:
    mac = value.replace("-", ":").upper()
    if not MAC_PATTERN.fullmatch(mac):
        raise ValueError("Invalid MAC address")
    return mac

