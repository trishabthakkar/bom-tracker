from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class ImpactReport(Base):
    __tablename__ = "impact_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    bom_import_id: Mapped[int] = mapped_column(ForeignKey("bom_imports.id"), index=True, nullable=False)
    eco_record_id: Mapped[int | None] = mapped_column(ForeignKey("eco_records.id"), nullable=True)
    graph_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("graph_snapshots.id"),
        nullable=True,
    )
    bom_upload_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), index=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    affected_part: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    report_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="generated", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
