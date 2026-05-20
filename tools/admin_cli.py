import os
import csv
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

import typer
from sqlalchemy import select

from app.db.models import (
    EntityType,
    GeographicRestriction,
    JurisdictionType,
    Location,
    RestrictionKind,
    RestrictionLifecycle,
    SiteStatus,
)
from app.db.session import Base, SessionLocal, engine
from app.geo import circle_polygon, parse_geometry_geojson

cli = typer.Typer(help="Admin-only CLI for dcmapper data management.")


def validate_latitude(value: float) -> float:
    if value < -90 or value > 90:
        raise typer.BadParameter("Latitude must be between -90 and 90.")
    return value


def validate_longitude(value: float) -> float:
    if value < -180 or value > 180:
        raise typer.BadParameter("Longitude must be between -180 and 180.")
    return value


def validate_source(value: str) -> str:
    source = value.strip()
    if not source:
        raise typer.BadParameter("Source / citation cannot be empty.")
    if source.startswith(("http://", "https://")):
        parsed = urlparse(source)
        if not parsed.netloc:
            raise typer.BadParameter("Source URL must include a valid host.")
    return source


def _ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise typer.BadParameter(f"Invalid boolean value: {value}")


def _location_from_dict(record: dict, admin: str) -> Location:
    name = str(record["name"]).strip()
    entity_type = EntityType(str(record["entity_type"]).strip())
    latitude = Decimal(str(validate_latitude(float(record["latitude"]))))
    longitude = Decimal(str(validate_longitude(float(record["longitude"]))))
    source = validate_source(str(record["source"]))
    status = SiteStatus(str(record.get("status", "known")).strip())
    confidence = int(record.get("confidence", 3))
    if confidence < 1 or confidence > 5:
        raise typer.BadParameter("Confidence must be between 1 and 5.")

    return Location(
        name=name,
        entity_type=entity_type,
        latitude=latitude,
        longitude=longitude,
        address=(record.get("address") or None),
        city=(record.get("city") or None),
        region=(record.get("region") or None),
        country=str(record.get("country", "US")).strip().upper(),
        operator=(record.get("operator") or None),
        status=status,
        confidence=confidence,
        source=source,
        notes=(record.get("notes") or None),
        is_public=_parse_bool(record.get("is_public", True)),
        created_by=admin,
        updated_by=admin,
    )


def _parse_optional_date(value: str | None) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    return date.fromisoformat(str(value).strip())


def _restriction_from_dict(record: dict, admin: str) -> GeographicRestriction:
    name = str(record["name"]).strip()
    jurisdiction_type = JurisdictionType(str(record["jurisdiction_type"]).strip())
    restriction_kind = RestrictionKind(str(record["restriction_kind"]).strip())
    lifecycle_status = RestrictionLifecycle(
        str(record.get("lifecycle_status", "active")).strip()
    )
    start_date = _parse_optional_date(record.get("start_date"))
    end_date = _parse_optional_date(record.get("end_date"))
    source = validate_source(str(record["source"]))

    if record.get("geometry_geojson"):
        geometry = parse_geometry_geojson(str(record["geometry_geojson"]))
    else:
        latitude = validate_latitude(float(record["center_latitude"]))
        longitude = validate_longitude(float(record["center_longitude"]))
        radius_km = float(record.get("radius_km", 5))
        if radius_km <= 0:
            raise typer.BadParameter("radius_km must be positive.")
        geometry = circle_polygon(latitude, longitude, radius_km)

    return GeographicRestriction(
        name=name,
        jurisdiction_type=jurisdiction_type,
        restriction_kind=restriction_kind,
        lifecycle_status=lifecycle_status,
        start_date=start_date,
        end_date=end_date,
        geometry_geojson=json.dumps(geometry),
        source=source,
        notes=(record.get("notes") or None),
        is_public=_parse_bool(record.get("is_public", True)),
        created_by=admin,
        updated_by=admin,
    )


@cli.command("add-location")
def add_location() -> None:
    _ensure_schema()

    admin = os.getenv("DCMAPPER_ADMIN_NAME") or typer.prompt("Admin name")
    name = typer.prompt("Facility name").strip()
    entity_type = typer.prompt(
        "Entity type (enterprise/government/colo/telco_co/other)"
    ).strip()
    latitude = validate_latitude(typer.prompt("Latitude", type=float))
    longitude = validate_longitude(typer.prompt("Longitude", type=float))
    source = validate_source(typer.prompt("Source / citation"))

    city = typer.prompt("City", default="").strip() or None
    region = typer.prompt("Region/State", default="").strip() or None
    country = typer.prompt("Country code", default="US").strip().upper()
    operator = typer.prompt("Operator", default="").strip() or None
    notes = typer.prompt("Notes", default="").strip() or None
    confidence = typer.prompt("Confidence (1-5)", type=int, default=3)
    status = typer.prompt("Status (known/suspected/retired)", default="known").strip()
    is_public = typer.confirm("Publish publicly?", default=True)

    if confidence < 1 or confidence > 5:
        raise typer.BadParameter("Confidence must be between 1 and 5.")

    try:
        typed_entity = EntityType(entity_type)
    except ValueError as exc:
        raise typer.BadParameter("Invalid entity_type.") from exc

    try:
        typed_status = SiteStatus(status)
    except ValueError as exc:
        raise typer.BadParameter("Invalid status.") from exc

    typer.echo("\nReview entry:")
    typer.echo(f"- name: {name}")
    typer.echo(f"- type: {typed_entity.value}")
    typer.echo(f"- coordinates: {latitude}, {longitude}")
    typer.echo(f"- source: {source}")
    typer.echo(f"- public: {is_public}")

    if not typer.confirm("Insert this record?", default=True):
        typer.echo("Cancelled.")
        raise typer.Exit(code=0)

    db = SessionLocal()
    try:
        location = Location(
            name=name,
            entity_type=typed_entity,
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            city=city,
            region=region,
            country=country,
            operator=operator,
            source=source,
            notes=notes,
            confidence=confidence,
            status=typed_status,
            is_public=is_public,
            created_by=admin,
            updated_by=admin,
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        typer.echo(f"Inserted location: {location.id}")
    finally:
        db.close()


@cli.command("seed")
def seed_data(
    path: Path = typer.Argument(..., exists=True, readable=True, resolve_path=True),
) -> None:
    _ensure_schema()

    admin = os.getenv("DCMAPPER_ADMIN_NAME") or typer.prompt("Admin name")

    suffix = path.suffix.lower()
    records: list[dict]
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, list):
            raise typer.BadParameter("JSON seed file must contain a list of records.")
        records = loaded
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            records = list(csv.DictReader(handle))
    else:
        raise typer.BadParameter("Seed file must be .json or .csv")

    if not records:
        typer.echo("No records found in seed file.")
        raise typer.Exit(code=0)

    db = SessionLocal()
    inserted = 0
    try:
        for idx, record in enumerate(records, start=1):
            try:
                db.add(_location_from_dict(record, admin))
                inserted += 1
            except Exception as exc:
                raise typer.BadParameter(f"Invalid record at row {idx}: {exc}") from exc

        db.commit()
        typer.echo(f"Inserted {inserted} locations from {path.name}.")
    finally:
        db.close()


@cli.command("seed-restrictions")
def seed_restrictions(
    path: Path = typer.Argument(..., exists=True, readable=True, resolve_path=True),
) -> None:
    _ensure_schema()

    admin = os.getenv("DCMAPPER_ADMIN_NAME") or typer.prompt("Admin name")

    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, list):
        raise typer.BadParameter("JSON seed file must contain a list of records.")

    db = SessionLocal()
    inserted = 0
    try:
        for idx, record in enumerate(loaded, start=1):
            try:
                db.add(_restriction_from_dict(record, admin))
                inserted += 1
            except Exception as exc:
                raise typer.BadParameter(f"Invalid record at row {idx}: {exc}") from exc
        db.commit()
        typer.echo(f"Inserted {inserted} geographic restrictions from {path.name}.")
    finally:
        db.close()


@cli.command("list-locations")
def list_locations() -> None:
    _ensure_schema()
    db = SessionLocal()
    try:
        rows = db.execute(select(Location).order_by(Location.name.asc())).scalars().all()
        if not rows:
            typer.echo("No locations found.")
            return
        for row in rows:
            typer.echo(
                f"{row.id} | {row.name} | {row.entity_type.value} | "
                f"{row.latitude},{row.longitude} | public={row.is_public}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    cli()
