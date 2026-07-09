"""advanced bom eco workflows

Revision ID: 20260709_0006
Revises: 20260709_0005
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260709_0006"
down_revision: str | None = "20260709_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bom_imports", sa.Column("version_label", sa.String(length=80), nullable=True))
    op.add_column("bom_imports", sa.Column("previous_import_id", sa.Integer(), nullable=True))
    op.add_column("bom_imports", sa.Column("import_notes", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_bom_imports_previous_import_id_bom_imports",
        "bom_imports",
        "bom_imports",
        ["previous_import_id"],
        ["id"],
    )

    op.add_column(
        "eco_records",
        sa.Column("workflow_status", sa.String(length=40), server_default="draft", nullable=False),
    )
    op.add_column("eco_records", sa.Column("correction_notes", sa.Text(), nullable=True))
    op.add_column("eco_records", sa.Column("approval_notes", sa.Text(), nullable=True))
    op.add_column("eco_records", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("eco_records", sa.Column("approved_at", sa.DateTime(), nullable=True))
    op.add_column("eco_records", sa.Column("rejected_at", sa.DateTime(), nullable=True))
    op.alter_column("eco_records", "workflow_status", server_default=None)


def downgrade() -> None:
    op.drop_column("eco_records", "rejected_at")
    op.drop_column("eco_records", "approved_at")
    op.drop_column("eco_records", "reviewed_at")
    op.drop_column("eco_records", "approval_notes")
    op.drop_column("eco_records", "correction_notes")
    op.drop_column("eco_records", "workflow_status")

    op.drop_constraint("fk_bom_imports_previous_import_id_bom_imports", "bom_imports", type_="foreignkey")
    op.drop_column("bom_imports", "import_notes")
    op.drop_column("bom_imports", "previous_import_id")
    op.drop_column("bom_imports", "version_label")
