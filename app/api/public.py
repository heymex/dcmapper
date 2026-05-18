from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Location
from app.db.session import get_db

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


@router.get("/healthz")
def healthz(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
