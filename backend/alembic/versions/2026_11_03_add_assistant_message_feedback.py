"""add assistant message feedback

Revision ID: c3f9a1d6e842
Revises: b5d8e2f4a917
Create Date: 2026-11-03 15:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c3f9a1d6e842"
down_revision = "b5d8e2f4a917"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assistant_message_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assistant_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rating IN ('positive', 'negative')",
            name="ck_assistant_message_feedback_rating",
        ),
        sa.UniqueConstraint("message_id", name="uq_assistant_message_feedback_message_id"),
    )
    op.create_index(
        "ix_assistant_message_feedback_user_id",
        "assistant_message_feedback",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_assistant_message_feedback_user_id",
        table_name="assistant_message_feedback",
    )
    op.drop_table("assistant_message_feedback")
