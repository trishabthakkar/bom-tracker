from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GraphSnapshotRead(BaseModel):
    id: int
    bom_import_id: int
    upload_id: int
    node_count: int
    edge_count: int
    root_count: int
    leaf_count: int
    has_cycles: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphSnapshotDetail(GraphSnapshotRead):
    nodes: list[str] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
