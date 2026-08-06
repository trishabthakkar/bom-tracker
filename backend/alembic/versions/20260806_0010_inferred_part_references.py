"""inferred part references

Revision ID: 20260806_0010
Revises: 20260806_0009
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260806_0010"
down_revision: str | None = "20260806_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("engineering_documents", "document_sections")


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "inferred_part_references",
                sa.JSON(),
                server_default=sa.text("'[]'"),
                nullable=False,
            ),
        )
        op.alter_column(table, "inferred_part_references", server_default=None)


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, "inferred_part_references")
