"""Geographic moratorium and ban restrictions

Revision ID: 0002_geographic_restrictions
Revises: 0001_initial_schema
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_geographic_restrictions"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    jurisdiction_type = sa.Enum(
        "city",
        "county",
        "township",
        "state",
        "other",
        name="jurisdiction_type",
        create_type=False,
    )
    restriction_kind = sa.Enum(
        "moratorium",
        "ban",
        name="restriction_kind",
        create_type=False,
    )
    restriction_lifecycle = sa.Enum(
        "proposed",
        "active",
        "expired",
        name="restriction_lifecycle",
        create_type=False,
    )

    bind = op.get_bind()
    jurisdiction_type.create(bind, checkfirst=True)
    restriction_kind.create(bind, checkfirst=True)
    restriction_lifecycle.create(bind, checkfirst=True)

    op.create_table(
        "geographic_restrictions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("jurisdiction_type", jurisdiction_type, nullable=False),
        sa.Column("restriction_kind", restriction_kind, nullable=False),
        sa.Column("lifecycle_status", restriction_lifecycle, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("geometry_geojson", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("updated_by", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_geographic_restrictions_kind",
        "geographic_restrictions",
        ["restriction_kind"],
    )
    op.create_index(
        "ix_geographic_restrictions_public",
        "geographic_restrictions",
        ["is_public"],
    )


def downgrade() -> None:
    op.drop_index("ix_geographic_restrictions_public", table_name="geographic_restrictions")
    op.drop_index("ix_geographic_restrictions_kind", table_name="geographic_restrictions")
    op.drop_table("geographic_restrictions")

    bind = op.get_bind()
    sa.Enum(name="restriction_lifecycle").drop(bind, checkfirst=True)
    sa.Enum(name="restriction_kind").drop(bind, checkfirst=True)
    sa.Enum(name="jurisdiction_type").drop(bind, checkfirst=True)
