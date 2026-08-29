"""add assistant suggested replies

Revision ID: e3b1d8f4c602
Revises: c9a0d4e6f215
Create Date: 2026-08-26 00:30:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "e3b1d8f4c602"
down_revision = "c9a0d4e6f215"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assistant_messages",
        sa.Column(
            "suggested_replies",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("assistant_messages", "suggested_replies")
