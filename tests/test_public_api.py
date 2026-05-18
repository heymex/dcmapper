import os

os.environ["DATABASE_URL"] = "sqlite:///./test_dcmapper.db"

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.models import EntityType, Location, SiteStatus
from app.db.session import Base, SessionLocal, engine
from app.main import app


def _reset_locations_table() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.execute(delete(Location))
        db.commit()
    finally:
        db.close()


def test_healthz_returns_ok():
    _reset_locations_table()
    client = TestClient(app)
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_locations_endpoint_exists():
    _reset_locations_table()
    client = TestClient(app)
    res = client.get("/api/locations")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_security_headers_present():
    _reset_locations_table()
    client = TestClient(app)
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "DENY"


def test_private_records_never_leak():
    _reset_locations_table()
    db = SessionLocal()
    public_id: str
    private_id: str
    try:
        public_record = Location(
            name="Public Test Site",
            entity_type=EntityType.colo,
            latitude=10.1234,
            longitude=20.5678,
            city="Test City",
            region="TC",
            country="US",
            status=SiteStatus.known,
            confidence=4,
            source="https://example.org/public-source",
            is_public=True,
            created_by="test",
            updated_by="test",
        )
        private_record = Location(
            name="Private Test Site",
            entity_type=EntityType.colo,
            latitude=11.1234,
            longitude=21.5678,
            city="Test City",
            region="TC",
            country="US",
            status=SiteStatus.known,
            confidence=4,
            source="https://example.org/private-source",
            is_public=False,
            created_by="test",
            updated_by="test",
        )
        db.add_all([public_record, private_record])
        db.commit()
        db.refresh(public_record)
        db.refresh(private_record)
        public_id = public_record.id
        private_id = private_record.id
    finally:
        db.close()

    client = TestClient(app)
    res = client.get("/api/locations")
    assert res.status_code == 200
    ids = [r["id"] for r in res.json()]
    assert public_id in ids
    assert private_id not in ids
