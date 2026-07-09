"""report collaboration exports

Revision ID: 20260709_0007
Revises: 20260709_0006
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260709_0007"
down_revision: str | None = "20260709_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "impact_reports",
        sa.Column("review_status", sa.String(length=40), server_default="draft", nullable=False),
    )
    op.add_column("impact_reports", sa.Column("owner_user_id", sa.Integer(), nullable=True))
    op.add_column("impact_reports", sa.Column("assigned_user_id", sa.Integer(), nullable=True))
    op.add_column("impact_reports", sa.Column("signoff_notes", sa.Text(), nullable=True))
    op.add_column("impact_reports", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("impact_reports", sa.Column("signed_off_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_impact_reports_owner_user_id_users",
        "impact_reports",
        "users",
        ["owner_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_impact_reports_assigned_user_id_users",
        "impact_reports",
        "users",
        ["assigned_user_id"],
        ["id"],
    )
    op.create_index(op.f("ix_impact_reports_review_status"), "impact_reports", ["review_status"], unique=False)
    op.alter_column("impact_reports", "review_status", server_default=None)

    op.create_table(
        "report_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["impact_reports.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_report_comments_id"), "report_comments", ["id"], unique=False)
    op.create_index(op.f("ix_report_comments_report_id"), "report_comments", ["report_id"], unique=False)
    op.create_index(op.f("ix_report_comments_user_id"), "report_comments", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_report_comments_user_id"), table_name="report_comments")
    op.drop_index(op.f("ix_report_comments_report_id"), table_name="report_comments")
    op.drop_index(op.f("ix_report_comments_id"), table_name="report_comments")
    op.drop_table("report_comments")

    op.drop_index(op.f("ix_impact_reports_review_status"), table_name="impact_reports")
    op.drop_constraint("fk_impact_reports_assigned_user_id_users", "impact_reports", type_="foreignkey")
    op.drop_constraint("fk_impact_reports_owner_user_id_users", "impact_reports", type_="foreignkey")
    op.drop_column("impact_reports", "signed_off_at")
    op.drop_column("impact_reports", "reviewed_at")
    op.drop_column("impact_reports", "signoff_notes")
    op.drop_column("impact_reports", "assigned_user_id")
    op.drop_column("impact_reports", "owner_user_id")
    op.drop_column("impact_reports", "review_status")
