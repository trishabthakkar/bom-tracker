"""report summary source

Revision ID: 20260806_0009
Revises: 20260805_0008
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260806_0009"
down_revision: str | None = "20260805_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "impact_reports",
        sa.Column("summary_source", sa.String(length=60), server_default="rule_based", nullable=False),
    )
    op.alter_column("impact_reports", "summary_source", server_default=None)


def downgrade() -> None:
    op.drop_column("impact_reports", "summary_source")
