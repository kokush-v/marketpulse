"""change alert retrigger behavior runtime fields

Revision ID: b7f7e5a4d921
Revises: 6b91c3cb63c1
Create Date: 2026-06-09 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "b7f7e5a4d921"
down_revision = "6b91c3cb63c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    alert_rules = sa.table(
        "alert_rules",
        sa.column("time_behavior", sa.String()),
        sa.column("status", sa.String()),
        sa.column("last_triggered_on", sa.Date()),
        sa.column("last_triggered_at", sa.DateTime(timezone=True)),
    )

    op.add_column(
        "alert_rules",
        sa.Column("arm_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "alert_rules",
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.get_bind().execute(
        sa.update(alert_rules)
        .where(alert_rules.c.last_triggered_on.is_not(None))
        .values(
            last_triggered_at=sa.func.timezone(
                "UTC",
                sa.cast(alert_rules.c.last_triggered_on, sa.DateTime()),
            )
        )
    )
    op.get_bind().execute(
        sa.update(alert_rules)
        .where(
            alert_rules.c.time_behavior == "one_time",
            alert_rules.c.last_triggered_on.is_not(None),
        )
        .values(status="paused")
    )

    op.alter_column("alert_rules", "arm_version", server_default=None)


def downgrade() -> None:
    op.drop_column("alert_rules", "last_triggered_at")
    op.drop_column("alert_rules", "arm_version")
