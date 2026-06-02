"""add telegram test message tracking

Revision ID: f1c8e4b6a293
Revises: e5b7d2a9c418
Create Date: 2026-06-02 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "f1c8e4b6a293"
down_revision = "e5b7d2a9c418"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "telegram_connections",
        sa.Column("last_test_message_id", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("telegram_connections", "last_test_message_id")
