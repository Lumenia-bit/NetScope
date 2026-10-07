from backend.scanner.network import network_from_route


def test_integer_route_mask_can_form_an_ipv4_network() -> None:
    network = network_from_route(0xC0A80100, 0xFFFFFF00)
    assert str(network) == "192.168.1.0/24"
