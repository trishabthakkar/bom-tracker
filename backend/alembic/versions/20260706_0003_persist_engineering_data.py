"""persist engineering data

Revision ID: 20260706_0003
Revises: 20260706_0002
Create Date: 2026-07-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260706_0003"
down_revision: str | None = "20260706_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bom_imports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["upload_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bom_imports_id"), "bom_imports", ["id"], unique=False)
    op.create_index(op.f("ix_bom_imports_upload_id"), "bom_imports", ["upload_id"], unique=False)
    op.create_index(op.f("ix_bom_imports_user_id"), "bom_imports", ["user_id"], unique=False)

    op.create_table(
        "bom_parts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bom_import_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("part_number", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("parent_assembly", sa.String(length=120), nullable=True),
        sa.Column("child_assembly", sa.String(length=120), nullable=True),
        sa.Column("revision", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bom_import_id"], ["bom_imports.id"]),
        sa.ForeignKeyConstraint(["upload_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bom_parts_bom_import_id"), "bom_parts", ["bom_import_id"], unique=False)
    op.create_index(op.f("ix_bom_parts_child_assembly"), "bom_parts", ["child_assembly"], unique=False)
    op.create_index(op.f("ix_bom_parts_id"), "bom_parts", ["id"], unique=False)
    op.create_index(op.f("ix_bom_parts_parent_assembly"), "bom_parts", ["parent_assembly"], unique=False)
    op.create_index(op.f("ix_bom_parts_part_number"), "bom_parts", ["part_number"], unique=False)
    op.create_index(op.f("ix_bom_parts_upload_id"), "bom_parts", ["upload_id"], unique=False)
    op.create_index(op.f("ix_bom_parts_user_id"), "bom_parts", ["user_id"], unique=False)

    op.create_table(
        "assembly_relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bom_import_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("parent_part_number", sa.String(length=120), nullable=False),
        sa.Column("child_part_number", sa.String(length=120), nullable=False),
        sa.Column("relationship_type", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bom_import_id"], ["bom_imports.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assembly_relationships_bom_import_id"),
        "assembly_relationships",
        ["bom_import_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assembly_relationships_child_part_number"),
        "assembly_relationships",
        ["child_part_number"],
        unique=False,
    )
    op.create_index(op.f("ix_assembly_relationships_id"), "assembly_relationships", ["id"], unique=False)
    op.create_index(
        op.f("ix_assembly_relationships_parent_part_number"),
        "assembly_relationships",
        ["parent_part_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assembly_relationships_user_id"),
        "assembly_relationships",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "eco_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("change_type", sa.String(length=80), nullable=True),
        sa.Column("old_part", sa.String(length=120), nullable=True),
        sa.Column("new_part", sa.String(length=120), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("parser_source", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["upload_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_eco_records_change_type"), "eco_records", ["change_type"], unique=False)
    op.create_index(op.f("ix_eco_records_id"), "eco_records", ["id"], unique=False)
    op.create_index(op.f("ix_eco_records_new_part"), "eco_records", ["new_part"], unique=False)
    op.create_index(op.f("ix_eco_records_old_part"), "eco_records", ["old_part"], unique=False)
    op.create_index(op.f("ix_eco_records_user_id"), "eco_records", ["user_id"], unique=False)

    op.create_table(
        "graph_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bom_import_id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("node_count", sa.Integer(), nullable=False),
        sa.Column("edge_count", sa.Integer(), nullable=False),
        sa.Column("root_count", sa.Integer(), nullable=False),
        sa.Column("leaf_count", sa.Integer(), nullable=False),
        sa.Column("has_cycles", sa.Boolean(), nullable=False),
        sa.Column("nodes", sa.JSON(), nullable=False),
        sa.Column("edges", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bom_import_id"], ["bom_imports.id"]),
        sa.ForeignKeyConstraint(["upload_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_graph_snapshots_bom_import_id"), "graph_snapshots", ["bom_import_id"], unique=False)
    op.create_index(op.f("ix_graph_snapshots_id"), "graph_snapshots", ["id"], unique=False)
    op.create_index(op.f("ix_graph_snapshots_upload_id"), "graph_snapshots", ["upload_id"], unique=False)
    op.create_index(op.f("ix_graph_snapshots_user_id"), "graph_snapshots", ["user_id"], unique=False)

    op.create_table(
        "impact_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bom_import_id", sa.Integer(), nullable=False),
        sa.Column("eco_record_id", sa.Integer(), nullable=True),
        sa.Column("graph_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("bom_upload_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("affected_part", sa.String(length=120), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["bom_import_id"], ["bom_imports.id"]),
        sa.ForeignKeyConstraint(["bom_upload_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["eco_record_id"], ["eco_records.id"]),
        sa.ForeignKeyConstraint(["graph_snapshot_id"], ["graph_snapshots.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_impact_reports_affected_part"), "impact_reports", ["affected_part"], unique=False)
    op.create_index(op.f("ix_impact_reports_bom_upload_id"), "impact_reports", ["bom_upload_id"], unique=False)
    op.create_index(op.f("ix_impact_reports_id"), "impact_reports", ["id"], unique=False)
    op.create_index(op.f("ix_impact_reports_risk_level"), "impact_reports", ["risk_level"], unique=False)
    op.create_index(op.f("ix_impact_reports_user_id"), "impact_reports", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_impact_reports_user_id"), table_name="impact_reports")
    op.drop_index(op.f("ix_impact_reports_risk_level"), table_name="impact_reports")
    op.drop_index(op.f("ix_impact_reports_id"), table_name="impact_reports")
    op.drop_index(op.f("ix_impact_reports_bom_upload_id"), table_name="impact_reports")
    op.drop_index(op.f("ix_impact_reports_affected_part"), table_name="impact_reports")
    op.drop_table("impact_reports")

    op.drop_index(op.f("ix_graph_snapshots_user_id"), table_name="graph_snapshots")
    op.drop_index(op.f("ix_graph_snapshots_upload_id"), table_name="graph_snapshots")
    op.drop_index(op.f("ix_graph_snapshots_id"), table_name="graph_snapshots")
    op.drop_index(op.f("ix_graph_snapshots_bom_import_id"), table_name="graph_snapshots")
    op.drop_table("graph_snapshots")

    op.drop_index(op.f("ix_eco_records_user_id"), table_name="eco_records")
    op.drop_index(op.f("ix_eco_records_old_part"), table_name="eco_records")
    op.drop_index(op.f("ix_eco_records_new_part"), table_name="eco_records")
    op.drop_index(op.f("ix_eco_records_id"), table_name="eco_records")
    op.drop_index(op.f("ix_eco_records_change_type"), table_name="eco_records")
    op.drop_table("eco_records")

    op.drop_index(op.f("ix_assembly_relationships_user_id"), table_name="assembly_relationships")
    op.drop_index(op.f("ix_assembly_relationships_parent_part_number"), table_name="assembly_relationships")
    op.drop_index(op.f("ix_assembly_relationships_id"), table_name="assembly_relationships")
    op.drop_index(op.f("ix_assembly_relationships_child_part_number"), table_name="assembly_relationships")
    op.drop_index(op.f("ix_assembly_relationships_bom_import_id"), table_name="assembly_relationships")
    op.drop_table("assembly_relationships")

    op.drop_index(op.f("ix_bom_parts_user_id"), table_name="bom_parts")
    op.drop_index(op.f("ix_bom_parts_upload_id"), table_name="bom_parts")
    op.drop_index(op.f("ix_bom_parts_part_number"), table_name="bom_parts")
    op.drop_index(op.f("ix_bom_parts_parent_assembly"), table_name="bom_parts")
    op.drop_index(op.f("ix_bom_parts_id"), table_name="bom_parts")
    op.drop_index(op.f("ix_bom_parts_child_assembly"), table_name="bom_parts")
    op.drop_index(op.f("ix_bom_parts_bom_import_id"), table_name="bom_parts")
    op.drop_table("bom_parts")

    op.drop_index(op.f("ix_bom_imports_user_id"), table_name="bom_imports")
    op.drop_index(op.f("ix_bom_imports_upload_id"), table_name="bom_imports")
    op.drop_index(op.f("ix_bom_imports_id"), table_name="bom_imports")
    op.drop_table("bom_imports")
