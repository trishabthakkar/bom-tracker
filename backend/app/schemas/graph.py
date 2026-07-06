from pydantic import BaseModel, Field


class GraphEdgeRead(BaseModel):
    source: str
    target: str


class GraphBuildResponse(BaseModel):
    upload_id: int
    filename: str
    nodes: list[str] = Field(default_factory=list)
    edges: list[GraphEdgeRead] = Field(default_factory=list)


class AffectedNodesResponse(BaseModel):
    upload_id: int
    part_number: str
    nodes: list[str] = Field(default_factory=list)


class DependencyPathsResponse(BaseModel):
    upload_id: int
    source: str
    target: str
    paths: list[list[str]] = Field(default_factory=list)


class GraphStatisticsResponse(BaseModel):
    upload_id: int
    node_count: int
    edge_count: int
    root_count: int
    leaf_count: int
    has_cycles: bool
