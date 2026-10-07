from __future__ import annotations

import ipaddress
from dataclasses import asdict, dataclass

from backend.config import validate_subnet


@dataclass(slots=True)
class NetworkInfo:
    interface: str
    address: str
    subnet: str
    gateway: str | None

    def as_dict(self) -> dict[str, str | None]:
        return asdict(self)


def network_from_route(network: int, netmask: int) -> ipaddress.IPv4Network:
    address_part = ipaddress.IPv4Address(network)
    mask_part = ipaddress.IPv4Address(netmask)
    return ipaddress.ip_network(f"{address_part}/{mask_part}", strict=False)


def detect_local_network() -> NetworkInfo:
    try:
        from scapy.all import conf

        interface, address, gateway = conf.route.route("0.0.0.0")
        if not address or address == "0.0.0.0":
            raise RuntimeError("No active IPv4 route was found")

        best_network: ipaddress.IPv4Network | None = None
        for network_int, mask_int, _gateway, route_interface, route_address, _metric in conf.route.routes:
            if route_interface != interface or route_address != address or not mask_int:
                continue
            candidate = network_from_route(network_int, mask_int)
            if ipaddress.ip_address(address) in candidate and (
                best_network is None or candidate.prefixlen > best_network.prefixlen
            ):
                best_network = candidate

        if best_network is None:
            best_network = ipaddress.ip_network(f"{address}/24", strict=False)

        subnet = validate_subnet(str(best_network))
        return NetworkInfo(str(interface), address, subnet, gateway or None)
    except ImportError as exc:
        raise RuntimeError("Scapy is not installed") from exc
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Could not detect the local IPv4 network: {exc}") from exc
