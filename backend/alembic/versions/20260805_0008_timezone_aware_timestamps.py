"""timezone aware timestamps

Revision ID: 20260805_0008
Revises: 20260709_0007
Create Date: 2026-08-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260805_0008"
down_revision: str | None = "20260709_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Every DateTime column in the schema. Existing values were written with
# datetime.utcnow() (naive, but always UTC in practice), so the conversion
# tells Postgres to interpret the stored value as UTC rather than the
# session's local timezone.
TIMESTAMP_COLUMNS: list[tuple[str, str]] = [
    ("users", "created_at"),
    ("users", "updated_at"),
    ("uploaded_files", "created_at"),
    ("bom_imports", "created_at"),
    ("bom_imports", "archived_at"),
    ("bom_parts", "created_at"),
    ("assembly_relationships", "created_at"),
    ("engineering_documents", "created_at"),
    ("engineering_documents", "archived_at"),
    ("document_sections", "created_at"),
    ("eco_records", "reviewed_at"),
    ("eco_records", "approved_at"),
    ("eco_records", "rejected_at"),
    ("eco_records", "created_at"),
    ("jobs", "created_at"),
    ("jobs", "updated_at"),
    ("jobs", "started_at"),
    ("jobs", "completed_at"),
    ("impact_reports", "reviewed_at"),
    ("impact_reports", "signed_off_at"),
    ("impact_reports", "created_at"),
    ("impact_reports", "updated_at"),
    ("impact_reports", "archived_at"),
    ("report_comments", "created_at"),
    ("graph_snapshots", "created_at"),
]


def upgrade() -> None:
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for table, column in reversed(TIMESTAMP_COLUMNS):
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=False),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
