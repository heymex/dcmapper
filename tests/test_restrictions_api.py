import json
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_dcmapper_restrictions.db"

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.models import GeographicRestriction, JurisdictionType, RestrictionKind, RestrictionLifecycle
from app.db.session import Base, SessionLocal, engine
from app.geo import circle_polygon
from app.main import app


def _reset_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.execute(delete(GeographicRestriction))
        db.commit()
    finally:
        db.close()


def test_restrictions_endpoint_returns_public_only():
    _reset_db()
    db = SessionLocal()
    public_id: str
    try:
        public_row = GeographicRestriction(
            name="Test City, MN",
            jurisdiction_type=JurisdictionType.city,
            restriction_kind=RestrictionKind.moratorium,
            lifecycle_status=RestrictionLifecycle.active,
            start_date=None,
            end_date=None,
            geometry_geojson=json.dumps(circle_polygon(44.0, -93.0, 3)),
            source="https://example.org/test",
            is_public=True,
            created_by="test",
            updated_by="test",
        )
        private_row = GeographicRestriction(
            name="Hidden City, MN",
            jurisdiction_type=JurisdictionType.city,
            restriction_kind=RestrictionKind.ban,
            lifecycle_status=RestrictionLifecycle.active,
            start_date=None,
            end_date=None,
            geometry_geojson=json.dumps(circle_polygon(45.0, -94.0, 3)),
            source="https://example.org/private",
            is_public=False,
            created_by="test",
            updated_by="test",
        )
        db.add_all([public_row, private_row])
        db.commit()
        db.refresh(public_row)
        public_id = public_row.id
    finally:
        db.close()

    client = TestClient(app)
    res = client.get("/api/restrictions")
    assert res.status_code == 200
    payload = res.json()
    assert len(payload) == 1
    assert payload[0]["id"] == public_id
    assert payload[0]["geometry"]["type"] == "Polygon"
    assert payload[0]["display_status"] == "active"
