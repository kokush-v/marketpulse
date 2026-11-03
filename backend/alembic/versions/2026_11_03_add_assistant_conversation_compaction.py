"""add assistant conversation compaction

Revision ID: d8b2e5c7f163
Revises: c3f9a1d6e842
Create Date: 2026-11-03 18:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "d8b2e5c7f163"
down_revision = "c3f9a1d6e842"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assistant_conversations",
        sa.Column("context_summary", sa.String(), nullable=True),
    )
    op.add_column(
        "assistant_conversations",
        sa.Column("summarized_through_sequence", sa.Integer(), nullable=True),
    )
    op.drop_constraint("ck_assistant_messages_role", "assistant_messages", type_="check")
    op.create_check_constraint(
        "ck_assistant_messages_role",
        "assistant_messages",
        "role IN ('user', 'assistant', 'tool', 'compaction')",
    )


def downgrade() -> None:
    op.execute("DELETE FROM assistant_messages WHERE role = 'compaction'")
    op.drop_constraint("ck_assistant_messages_role", "assistant_messages", type_="check")
    op.create_check_constraint(
        "ck_assistant_messages_role",
        "assistant_messages",
        "role IN ('user', 'assistant', 'tool')",
    )
    op.drop_column("assistant_conversations", "summarized_through_sequence")
    op.drop_column("assistant_conversations", "context_summary")
