import os

os.environ["DATABASE_URL"] = "sqlite:///./test_dcmapper.db"

from fastapi.testclient import TestClient

from app.main import app


def test_healthz_returns_ok():
    client = TestClient(app)
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_locations_endpoint_exists():
    client = TestClient(app)
    res = client.get("/api/locations")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_security_headers_present():
    client = TestClient(app)
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "DENY"
