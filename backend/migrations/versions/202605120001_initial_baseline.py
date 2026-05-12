"""Initial baseline without product tables.

Revision ID: 202605120001
Revises:
Create Date: 2026-05-12 00:00:00.000000
"""

from collections.abc import Sequence

revision: str = "202605120001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

