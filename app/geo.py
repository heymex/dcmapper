import json
import math
from datetime import date
from typing import Any


def circle_polygon(
    latitude: float, longitude: float, radius_km: float, points: int = 32
) -> dict[str, Any]:
    """Approximate a circle as a GeoJSON Polygon (lon, lat order)."""
    coords: list[list[float]] = []
    lat_rad = math.radians(latitude)
    km_per_deg_lat = 111.32
    km_per_deg_lon = max(111.32 * math.cos(lat_rad), 0.01)

    for i in range(points + 1):
        angle = 2 * math.pi * i / points
        dlat = (radius_km / km_per_deg_lat) * math.cos(angle)
        dlon = (radius_km / km_per_deg_lon) * math.sin(angle)
        coords.append([longitude + dlon, latitude + dlat])

    return {"type": "Polygon", "coordinates": [coords]}


def parse_geometry_geojson(raw: str) -> dict[str, Any]:
    geometry = json.loads(raw)
    if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("geometry must be a GeoJSON Polygon or MultiPolygon")
    return geometry


def restriction_display_status(
    *,
    lifecycle_status: str,
    start_date: date | None,
    end_date: date | None,
    on_date: date | None = None,
) -> str:
    """Return UI/API status: proposed, active, upcoming, or expired."""
    if lifecycle_status == "proposed":
        return "proposed"

    today = on_date or date.today()
    if start_date and today < start_date:
        return "upcoming"
    if end_date and today > end_date:
        return "expired"
    if start_date and (end_date is None or today <= end_date):
        return "active"
    return lifecycle_status
