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
    version_label: str | None = None
    previous_import_id: int | None = None
    import_notes: str | None = None
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


class BomDiffRequest(BaseModel):
    base_import_id: int
    target_import_id: int


class BomDiffPart(BaseModel):
    part_number: str
    description: str | None = None
    parent_assembly: str | None = None
    child_assembly: str | None = None
    revision: str | None = None


class BomRevisionChange(BaseModel):
    part_number: str
    base_revision: str | None = None
    target_revision: str | None = None
    description_changed: bool = False
    parent_changed: bool = False
    child_changed: bool = False


class BomReplacementCandidate(BaseModel):
    removed_part: BomDiffPart
    added_part: BomDiffPart
    confidence: float
    reason: str


class BomDiffSummary(BaseModel):
    added_count: int
    removed_count: int
    revised_count: int
    replacement_candidate_count: int
    unchanged_count: int


class BomDiffResponse(BaseModel):
    base_import: BomImportRead
    target_import: BomImportRead
    summary: BomDiffSummary
    added_parts: list[BomDiffPart] = Field(default_factory=list)
    removed_parts: list[BomDiffPart] = Field(default_factory=list)
    revised_parts: list[BomRevisionChange] = Field(default_factory=list)
    replacement_candidates: list[BomReplacementCandidate] = Field(default_factory=list)
