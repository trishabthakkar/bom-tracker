from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class EngineeringDocument(Base):
    __tablename__ = "engineering_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="indexed", nullable=False)
    section_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    part_references: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("engineering_documents.id"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), index=True, nullable=False)
    section_index: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    part_references: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
