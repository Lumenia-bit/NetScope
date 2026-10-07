from backend.database import Database
from backend.models import DiscoveredDevice


def test_device_is_updated_by_mac_without_losing_first_seen(tmp_path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()

    first = database.upsert_device(
        DiscoveredDevice("192.168.1.10", "aa:bb:cc:dd:ee:ff", "desk", "Acme", [22]),
        "2026-01-01T10:00:00+00:00",
    )
    second = database.upsert_device(
        DiscoveredDevice("192.168.1.22", "AA:BB:CC:DD:EE:FF", "desktop", "Acme", [22, 80]),
        "2026-01-01T11:00:00+00:00",
    )

    assert first["id"] == second["id"]
    assert second["first_seen"] == "2026-01-01T10:00:00+00:00"
    assert second["last_seen"] == "2026-01-01T11:00:00+00:00"
    assert second["ip"] == "192.168.1.22"
    assert second["ports"] == [22, 80]
    assert len(database.list_devices()) == 1
    assert {event["event"] for event in database.get_history(first["id"])} == {
        "first_seen",
        "ip_changed",
    }
    database.close()


def test_missing_devices_become_offline_and_record_a_transition(tmp_path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()
    device = database.upsert_device(
        DiscoveredDevice("192.168.1.2", "AA:BB:CC:00:00:01"),
        "2026-01-01T10:00:00+00:00",
    )

    database.mark_missing_offline(set(), "2026-01-01T10:05:00+00:00")
    assert database.get_device(device["id"])["status"] == "offline"
    assert database.get_history(device["id"])[-1]["event"] == "offline"

    database.upsert_device(
        DiscoveredDevice("192.168.1.2", "AA:BB:CC:00:00:01"),
        "2026-01-01T10:10:00+00:00",
    )
    assert database.get_device(device["id"])["status"] == "online"
    assert database.get_history(device["id"])[-1]["event"] == "online"
    database.close()


def test_begin_scan_only_clears_new_marker(tmp_path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()
    device = database.upsert_device(DiscoveredDevice("10.0.0.2", "AA:BB:CC:00:00:02"))
    assert device["is_new"] is True
    database.begin_scan()
    assert database.get_device(device["id"])["is_new"] is False
    database.close()
