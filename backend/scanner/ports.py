from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Iterable


def _is_open(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((ip, port)) == 0
    except OSError:
        return False


def scan_ports(ip: str, ports: Iterable[int], timeout: float) -> list[int]:
    candidates = list(ports)
    if not candidates:
        return []
    check = partial(_is_open, ip, timeout=timeout)
    with ThreadPoolExecutor(max_workers=min(32, len(candidates))) as executor:
        results = executor.map(check, candidates)
    return [port for port, is_open in zip(candidates, results) if is_open]

