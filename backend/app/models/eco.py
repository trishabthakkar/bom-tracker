from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class EcoRecord(Base):
    __tablename__ = "eco_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    upload_id: Mapped[int | None] = mapped_column(ForeignKey("uploaded_files.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_type: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    old_part: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    new_part: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    parser_source: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
