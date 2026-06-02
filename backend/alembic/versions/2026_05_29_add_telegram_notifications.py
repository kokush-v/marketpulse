"""add telegram connections and notifications

Revision ID: e5b7d2a9c418
Revises: d8a4c31f7b62
Create Date: 2026-05-29 00:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "e5b7d2a9c418"
down_revision = "d8a4c31f7b62"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telegram_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_username", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "connected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('active', 'disconnected')",
            name="ck_telegram_connections_status",
        ),
    )
    op.create_index(
        op.f("ix_telegram_connections_user_id"),
        "telegram_connections",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_connections_telegram_user_id"),
        "telegram_connections",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_index(
        "uq_telegram_connections_active_user",
        "telegram_connections",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "uq_telegram_connections_active_telegram_user",
        "telegram_connections",
        ["telegram_user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "telegram_connection_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_telegram_connection_tokens_user_id"),
        "telegram_connection_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_connection_tokens_token_hash"),
        "telegram_connection_tokens",
        ["token_hash"],
        unique=False,
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("related_alert_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notification_type", sa.String(length=32), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("delivery_status", sa.String(length=32), nullable=False),
        sa.Column("message_summary", sa.String(length=500), nullable=False),
        sa.Column("safe_error_message", sa.String(length=500), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("notification_type IN ('alert')", name="ck_notifications_type"),
        sa.CheckConstraint("channel IN ('telegram')", name="ck_notifications_channel"),
        sa.CheckConstraint(
            "delivery_status IN ('pending', 'delivered', 'failed')",
            name="ck_notifications_delivery_status",
        ),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(
        op.f("ix_telegram_connection_tokens_token_hash"),
        table_name="telegram_connection_tokens",
    )
    op.drop_index(
        op.f("ix_telegram_connection_tokens_user_id"),
        table_name="telegram_connection_tokens",
    )
    op.drop_table("telegram_connection_tokens")

    op.drop_index(
        "uq_telegram_connections_active_telegram_user",
        table_name="telegram_connections",
    )
    op.drop_index("uq_telegram_connections_active_user", table_name="telegram_connections")
    op.drop_index(
        op.f("ix_telegram_connections_telegram_user_id"),
        table_name="telegram_connections",
    )
    op.drop_index(
        op.f("ix_telegram_connections_user_id"),
        table_name="telegram_connections",
    )
    op.drop_table("telegram_connections")
