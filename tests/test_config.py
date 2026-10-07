import pytest

from backend.config import validate_ports, validate_subnet


def test_subnet_is_normalized_to_network_address() -> None:
    assert validate_subnet("192.168.12.44/24") == "192.168.12.0/24"


@pytest.mark.parametrize(
    "subnet",
    ["not-a-network", "2001:db8::/64", "8.8.8.0/24", "10.0.0.0/8", "127.0.0.0/24"],
)
def test_invalid_or_unsafe_subnets_are_rejected(subnet: str) -> None:
    with pytest.raises(ValueError):
        validate_subnet(subnet)


def test_ports_are_sorted_and_deduplicated() -> None:
    assert validate_ports([443, 22, 443, 80]) == [22, 80, 443]


@pytest.mark.parametrize("ports", [[], [0], [65_536], list(range(1, 130))])
def test_invalid_port_lists_are_rejected(ports: list[int]) -> None:
    with pytest.raises(ValueError):
        validate_ports(ports)
