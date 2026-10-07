from backend.scanner.state import ScanState


def test_scan_state_prevents_overlap_and_recovers_after_failure() -> None:
    state = ScanState()
    assert state.begin() is True
    assert state.begin() is False

    state.update(45, 3)
    snapshot = state.snapshot()
    assert snapshot["status"] == "scanning"
    assert snapshot["progress"] == 45
    assert snapshot["devices_discovered"] == 3

    state.fail("permission denied")
    assert state.snapshot()["status"] == "failed"
    assert state.begin() is True
    state.finish()
    assert state.snapshot()["status"] == "idle"
    assert state.snapshot()["progress"] == 100

