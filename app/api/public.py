import json
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import GeographicRestriction, Location
from app.db.session import get_db
from app.geo import restriction_display_status

router = APIRouter(tags=["public"])


class FacilityPublic(BaseModel):
    id: UUID
    name: str
    entity_type: str
    latitude: float
    longitude: float
    city: str | None
    region: str | None
    country: str
    operator: str | None
    status: str
    confidence: int
    source: str
    notes: str | None

    class Config:
        from_attributes = True


class RestrictionPublic(BaseModel):
    id: UUID
    name: str
    jurisdiction_type: str
    restriction_kind: str
    lifecycle_status: str
    display_status: str
    start_date: date | None
    end_date: date | None
    source: str
    notes: str | None
    geometry: dict

    class Config:
        from_attributes = True


@router.get("/api/locations")
def list_locations(db: Session = Depends(get_db)) -> list[FacilityPublic]:
    rows = db.execute(
        select(Location).where(Location.is_public.is_(True)).order_by(Location.name.asc())
    ).scalars()

    results: list[FacilityPublic] = []
    for row in rows:
        results.append(
            FacilityPublic(
                id=UUID(row.id),
                name=row.name,
                entity_type=row.entity_type.value,
                latitude=float(row.latitude),
                longitude=float(row.longitude),
                city=row.city,
                region=row.region,
                country=row.country,
                operator=row.operator,
                status=row.status.value,
                confidence=row.confidence,
                source=row.source,
                notes=row.notes,
            )
        )
    return results


@router.get("/api/restrictions")
def list_restrictions(db: Session = Depends(get_db)) -> list[RestrictionPublic]:
    rows = db.execute(
        select(GeographicRestriction)
        .where(GeographicRestriction.is_public.is_(True))
        .order_by(GeographicRestriction.name.asc())
    ).scalars()

    results: list[RestrictionPublic] = []
    for row in rows:
        results.append(
            RestrictionPublic(
                id=UUID(row.id),
                name=row.name,
                jurisdiction_type=row.jurisdiction_type.value,
                restriction_kind=row.restriction_kind.value,
                lifecycle_status=row.lifecycle_status.value,
                display_status=restriction_display_status(
                    lifecycle_status=row.lifecycle_status.value,
                    start_date=row.start_date,
                    end_date=row.end_date,
                ),
                start_date=row.start_date,
                end_date=row.end_date,
                source=row.source,
                notes=row.notes,
                geometry=json.loads(row.geometry_geojson),
            )
        )
    return results


@router.get("/healthz")
def healthz(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
