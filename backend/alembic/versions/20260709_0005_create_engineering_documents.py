"""create engineering documents

Revision ID: 20260709_0005
Revises: 20260709_0004
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260709_0005"
down_revision: str | None = "20260709_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("section_count", sa.Integer(), nullable=False),
        sa.Column("part_references", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["upload_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_engineering_documents_document_type"), "engineering_documents", ["document_type"], unique=False)
    op.create_index(op.f("ix_engineering_documents_id"), "engineering_documents", ["id"], unique=False)
    op.create_index(op.f("ix_engineering_documents_upload_id"), "engineering_documents", ["upload_id"], unique=False)
    op.create_index(op.f("ix_engineering_documents_user_id"), "engineering_documents", ["user_id"], unique=False)

    op.create_table(
        "document_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("section_index", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("part_references", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["engineering_documents.id"]),
        sa.ForeignKeyConstraint(["upload_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_sections_document_id"), "document_sections", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_sections_id"), "document_sections", ["id"], unique=False)
    op.create_index(op.f("ix_document_sections_upload_id"), "document_sections", ["upload_id"], unique=False)
    op.create_index(op.f("ix_document_sections_user_id"), "document_sections", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_sections_user_id"), table_name="document_sections")
    op.drop_index(op.f("ix_document_sections_upload_id"), table_name="document_sections")
    op.drop_index(op.f("ix_document_sections_id"), table_name="document_sections")
    op.drop_index(op.f("ix_document_sections_document_id"), table_name="document_sections")
    op.drop_table("document_sections")

    op.drop_index(op.f("ix_engineering_documents_user_id"), table_name="engineering_documents")
    op.drop_index(op.f("ix_engineering_documents_upload_id"), table_name="engineering_documents")
    op.drop_index(op.f("ix_engineering_documents_id"), table_name="engineering_documents")
    op.drop_index(op.f("ix_engineering_documents_document_type"), table_name="engineering_documents")
    op.drop_table("engineering_documents")
