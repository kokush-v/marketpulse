"""add assistant message sources

Revision ID: b5d8e2f4a917
Revises: a7e4c9d2f351
Create Date: 2026-11-03 12:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b5d8e2f4a917"
down_revision = "a7e4c9d2f351"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assistant_messages",
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("assistant_messages", "sources")
