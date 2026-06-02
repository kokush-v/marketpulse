"""add alert time behavior fields

Revision ID: d8a4c31f7b62
Revises: c2f7a4d8e931
Create Date: 2026-05-27 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "d8a4c31f7b62"
down_revision = "c2f7a4d8e931"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alert_rules",
        sa.Column(
            "time_behavior",
            sa.String(length=32),
            server_default=sa.text("'one_time'"),
            nullable=False,
        ),
    )
    op.add_column("alert_rules", sa.Column("recurring_start_date", sa.Date(), nullable=True))
    op.add_column("alert_rules", sa.Column("recurring_end_date", sa.Date(), nullable=True))
    op.add_column("alert_rules", sa.Column("last_triggered_on", sa.Date(), nullable=True))

    op.create_check_constraint(
        "ck_alert_rules_time_behavior",
        "alert_rules",
        "time_behavior IN ('one_time', 'daily_recurring')",
    )
    op.create_check_constraint(
        "ck_alert_rules_recurring_window",
        "alert_rules",
        (
            "(time_behavior = 'one_time' AND recurring_start_date IS NULL "
            "AND recurring_end_date IS NULL) "
            "OR (time_behavior = 'daily_recurring' AND recurring_start_date IS NOT NULL "
            "AND recurring_end_date IS NOT NULL AND recurring_end_date >= recurring_start_date)"
        ),
    )

    op.alter_column("alert_rules", "time_behavior", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_alert_rules_recurring_window", "alert_rules", type_="check")
    op.drop_constraint("ck_alert_rules_time_behavior", "alert_rules", type_="check")
    op.drop_column("alert_rules", "last_triggered_on")
    op.drop_column("alert_rules", "recurring_end_date")
    op.drop_column("alert_rules", "recurring_start_date")
    op.drop_column("alert_rules", "time_behavior")
