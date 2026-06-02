"""add alert rules table

Revision ID: c2f7a4d8e931
Revises: b91d4e6a2c73
Create Date: 2026-05-26 00:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c2f7a4d8e931"
down_revision = "b91d4e6a2c73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", sa.String(length=120), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("scenario_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('active', 'paused')", name="ck_alert_rules_status"),
        sa.CheckConstraint("symbol = upper(symbol)", name="ck_alert_rules_symbol_uppercase"),
        sa.CheckConstraint(
            "jsonb_typeof(scenario_payload) = 'object'",
            name="ck_alert_rules_scenario_object",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alert_rules_user_id"), "alert_rules", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alert_rules_user_id"), table_name="alert_rules")
    op.drop_table("alert_rules")
