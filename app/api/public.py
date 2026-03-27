from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Location
from app.db.session import get_db

router = APIRouter(tags=["public"])


@router.get("/api/locations")
def list_locations(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(Location).where(Location.is_public.is_(True)).order_by(Location.name.asc())
    ).scalars()

    results: list[dict] = []
    for row in rows:
        results.append(
            {
                "id": row.id,
                "name": row.name,
                "entity_type": row.entity_type.value,
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "city": row.city,
                "region": row.region,
                "country": row.country,
                "operator": row.operator,
                "status": row.status.value,
                "confidence": row.confidence,
                "source": row.source,
                "notes": row.notes,
            }
        )
    return results


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
