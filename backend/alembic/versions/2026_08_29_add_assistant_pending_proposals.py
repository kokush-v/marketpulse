"""add assistant pending proposals

Revision ID: a7e4c9d2f351
Revises: f4c2a9d7e861
Create Date: 2026-08-29 14:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a7e4c9d2f351"
down_revision = "f4c2a9d7e861"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assistant_messages",
        sa.Column("pending_action", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "assistant_pending_actions",
        sa.Column(
            "display_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(
                '\'{"title": "Pending action", '
                '"details": ["Review this proposed action."]}\'::jsonb'
            ),
        ),
    )
    op.add_column(
        "assistant_pending_actions",
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_assistant_pending_actions_message_id",
        "assistant_pending_actions",
        "assistant_messages",
        ["message_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_assistant_pending_actions_message_id",
        "assistant_pending_actions",
        ["message_id"],
    )
    op.drop_constraint("ck_assistant_pending_actions_type", "assistant_pending_actions")
    op.create_check_constraint(
        "ck_assistant_pending_actions_type",
        "assistant_pending_actions",
        "action_type IN ('add_watchlist_asset', 'remove_watchlist_asset', 'create_alert', "
        "'update_alert', 'pause_alert', 'resume_alert', 'delete_alert')",
    )
    op.drop_constraint("ck_assistant_pending_actions_status", "assistant_pending_actions")
    op.create_check_constraint(
        "ck_assistant_pending_actions_status",
        "assistant_pending_actions",
        "status IN ('pending', 'executing', 'confirmed', 'cancelled', 'expired')",
    )
    op.alter_column("assistant_pending_actions", "display_summary", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_assistant_pending_actions_status", "assistant_pending_actions")
    op.create_check_constraint(
        "ck_assistant_pending_actions_status",
        "assistant_pending_actions",
        "status IN ('pending', 'confirmed', 'cancelled', 'expired')",
    )
    op.drop_constraint("ck_assistant_pending_actions_type", "assistant_pending_actions")
    op.create_check_constraint(
        "ck_assistant_pending_actions_type",
        "assistant_pending_actions",
        "action_type IN ('delete_alert', 'remove_watchlist_asset')",
    )
    op.drop_constraint("uq_assistant_pending_actions_message_id", "assistant_pending_actions")
    op.drop_constraint("fk_assistant_pending_actions_message_id", "assistant_pending_actions")
    op.drop_column("assistant_pending_actions", "message_id")
    op.drop_column("assistant_pending_actions", "display_summary")
    op.drop_column("assistant_messages", "pending_action")
