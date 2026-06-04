"""add scheduled alert evaluation runtime state

Revision ID: 6b91c3cb63c1
Revises: f1c8e4b6a293
Create Date: 2026-06-04 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "6b91c3cb63c1"
down_revision = "f1c8e4b6a293"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("event_key", sa.String(length=255), nullable=True))
    op.add_column(
        "notifications",
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_notifications_event_key",
        "notifications",
        ["event_key"],
    )

    op.drop_constraint("ck_notifications_channel", "notifications", type_="check")
    op.drop_constraint("ck_notifications_delivery_status", "notifications", type_="check")
    op.create_check_constraint(
        "ck_notifications_channel",
        "notifications",
        "channel IN ('telegram', 'internal')",
    )
    op.create_check_constraint(
        "ck_notifications_delivery_status",
        "notifications",
        "delivery_status IN ('recorded', 'pending', 'delivered', 'failed')",
    )

    op.create_table(
        "background_job_cursors",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("last_processed_window_end", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("name"),
    )


def downgrade() -> None:
    op.drop_table("background_job_cursors")

    op.drop_constraint("ck_notifications_delivery_status", "notifications", type_="check")
    op.drop_constraint("ck_notifications_channel", "notifications", type_="check")
    op.create_check_constraint(
        "ck_notifications_channel",
        "notifications",
        "channel IN ('telegram')",
    )
    op.create_check_constraint(
        "ck_notifications_delivery_status",
        "notifications",
        "delivery_status IN ('pending', 'delivered', 'failed')",
    )
    op.drop_constraint("uq_notifications_event_key", "notifications", type_="unique")
    op.drop_column("notifications", "event_timestamp")
    op.drop_column("notifications", "event_key")
