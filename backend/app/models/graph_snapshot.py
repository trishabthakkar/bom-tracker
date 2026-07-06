from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class GraphSnapshot(Base):
    __tablename__ = "graph_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    bom_import_id: Mapped[int] = mapped_column(ForeignKey("bom_imports.id"), index=True, nullable=False)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), index=True, nullable=False)
    node_count: Mapped[int] = mapped_column(Integer, nullable=False)
    edge_count: Mapped[int] = mapped_column(Integer, nullable=False)
    root_count: Mapped[int] = mapped_column(Integer, nullable=False)
    leaf_count: Mapped[int] = mapped_column(Integer, nullable=False)
    has_cycles: Mapped[bool] = mapped_column(Boolean, nullable=False)
    nodes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    edges: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
