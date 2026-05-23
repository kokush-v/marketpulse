"""add watchlist assets table

Revision ID: 0003_add_watchlist_assets_table
Revises: 0002_add_users_table_for_auth
Create Date: 2026-05-22 00:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003_add_watchlist_assets_table"
down_revision = "0002_add_users_table_for_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", sa.String(length=120), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "asset_id", name="uq_watchlist_assets_user_asset"),
    )
    op.create_index(
        op.f("ix_watchlist_assets_user_id"),
        "watchlist_assets",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_watchlist_assets_user_id"), table_name="watchlist_assets")
    op.drop_table("watchlist_assets")
