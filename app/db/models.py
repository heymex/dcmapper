import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EntityType(str, enum.Enum):
    enterprise = "enterprise"
    government = "government"
    colo = "colo"
    telco_co = "telco_co"
    other = "other"


class SiteStatus(str, enum.Enum):
    known = "known"
    suspected = "suspected"
    retired = "retired"


class JurisdictionType(str, enum.Enum):
    city = "city"
    county = "county"
    township = "township"
    state = "state"
    other = "other"


class RestrictionKind(str, enum.Enum):
    moratorium = "moratorium"
    ban = "ban"


class RestrictionLifecycle(str, enum.Enum):
    proposed = "proposed"
    active = "active"
    expired = "expired"


class GeographicRestriction(Base):
    __tablename__ = "geographic_restrictions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    jurisdiction_type: Mapped[JurisdictionType] = mapped_column(
        Enum(JurisdictionType, name="jurisdiction_type"), nullable=False
    )
    restriction_kind: Mapped[RestrictionKind] = mapped_column(
        Enum(RestrictionKind, name="restriction_kind"), nullable=False
    )
    lifecycle_status: Mapped[RestrictionLifecycle] = mapped_column(
        Enum(RestrictionLifecycle, name="restriction_lifecycle"),
        nullable=False,
        default=RestrictionLifecycle.active,
    )
    start_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    geometry_geojson: Mapped[str] = mapped_column(Text(), nullable=False)
    source: Mapped[str] = mapped_column(Text(), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="entity_type"), nullable=False
    )
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    address: Mapped[str | None] = mapped_column(Text(), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="US")
    operator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[SiteStatus] = mapped_column(
        Enum(SiteStatus, name="site_status"), nullable=False, default=SiteStatus.known
    )
    confidence: Mapped[int] = mapped_column(Integer(), nullable=False, default=3)
    source: Mapped[str] = mapped_column(Text(), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
