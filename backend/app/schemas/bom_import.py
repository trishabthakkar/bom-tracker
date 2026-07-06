from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BomPartRead(BaseModel):
    id: int
    row_number: int
    part_number: str
    description: str | None = None
    parent_assembly: str | None = None
    child_assembly: str | None = None
    revision: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AssemblyRelationshipRead(BaseModel):
    id: int
    parent_part_number: str
    child_part_number: str
    relationship_type: str

    model_config = ConfigDict(from_attributes=True)


class BomImportRead(BaseModel):
    id: int
    upload_id: int
    filename: str
    row_count: int
    status: str
    created_at: datetime
    archived_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BomImportDetail(BomImportRead):
    parts: list[BomPartRead] = Field(default_factory=list)
    relationships: list[AssemblyRelationshipRead] = Field(default_factory=list)


class BomImportListResponse(BaseModel):
    imports: list[BomImportRead] = Field(default_factory=list)
