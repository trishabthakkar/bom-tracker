from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class BomImport(Base):
    __tablename__ = "bom_imports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    upload_id: Mapped[int] = mapped_column(
        ForeignKey("uploaded_files.id"),
        index=True,
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="imported", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BomPart(Base):
    __tablename__ = "bom_parts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bom_import_id: Mapped[int] = mapped_column(
        ForeignKey("bom_imports.id"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), index=True, nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    part_number: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parent_assembly: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    child_assembly: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    revision: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AssemblyRelationship(Base):
    __tablename__ = "assembly_relationships"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bom_import_id: Mapped[int] = mapped_column(
        ForeignKey("bom_imports.id"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    parent_part_number: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    child_part_number: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
