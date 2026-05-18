"""Initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-27 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    entity_type = sa.Enum(
        "enterprise",
        "government",
        "colo",
        "telco_co",
        "other",
        name="entity_type",
        create_type=False,
    )
    site_status = sa.Enum(
        "known", "suspected", "retired", name="site_status", create_type=False
    )

    bind = op.get_bind()
    entity_type.create(bind, checkfirst=True)
    site_status.create(bind, checkfirst=True)

    op.create_table(
        "locations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", entity_type, nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("operator", sa.String(length=255), nullable=True),
        sa.Column("status", site_status, nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("updated_by", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_locations_entity_type", "locations", ["entity_type"])
    op.create_index("ix_locations_city", "locations", ["city"])
    op.create_index("ix_locations_is_public", "locations", ["is_public"])


def downgrade() -> None:
    op.drop_index("ix_locations_is_public", table_name="locations")
    op.drop_index("ix_locations_city", table_name="locations")
    op.drop_index("ix_locations_entity_type", table_name="locations")
    op.drop_table("locations")

    bind = op.get_bind()
    sa.Enum(name="site_status").drop(bind, checkfirst=True)
    sa.Enum(name="entity_type").drop(bind, checkfirst=True)
