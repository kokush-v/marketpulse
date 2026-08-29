"""add assistant chart payload

Revision ID: f4c2a9d7e861
Revises: e3b1d8f4c602
Create Date: 2026-08-29 12:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "f4c2a9d7e861"
down_revision = "e3b1d8f4c602"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assistant_messages",
        sa.Column("chart_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("assistant_messages", "chart_payload")
