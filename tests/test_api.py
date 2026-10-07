from fastapi.testclient import TestClient

from backend.main import create_app


def test_settings_validation_rejects_public_network(tmp_path) -> None:
    app = create_app(tmp_path / "api.db")
    with TestClient(app) as client:
        settings = client.get("/api/settings").json()
        settings["subnet"] = "8.8.8.0/24"
        response = client.put("/api/settings", json=settings)
    assert response.status_code == 422


def test_settings_can_be_updated(tmp_path) -> None:
    app = create_app(tmp_path / "api.db")
    with TestClient(app) as client:
        response = client.put(
            "/api/settings",
            json={
                "subnet": "192.168.50.16/24",
                "ports": [443, 22, 443],
                "scan_timeout": 0.25,
                "resolve_hostnames": False,
                "vendor_lookup": True,
            },
        )
        assert response.status_code == 200
        assert response.json()["subnet"] == "192.168.50.0/24"
        assert response.json()["ports"] == [22, 443]


def test_missing_device_returns_not_found(tmp_path) -> None:
    app = create_app(tmp_path / "api.db")
    with TestClient(app) as client:
        response = client.get("/api/devices/999")
    assert response.status_code == 404

