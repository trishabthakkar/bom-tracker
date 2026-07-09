from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentSectionRead(BaseModel):
    id: int
    document_id: int
    upload_id: int
    section_index: int
    heading: str
    content: str
    part_references: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EngineeringDocumentRead(BaseModel):
    id: int
    upload_id: int
    filename: str
    document_type: str
    title: str | None = None
    status: str
    section_count: int
    part_references: list[str] = Field(default_factory=list)
    created_at: datetime
    archived_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EngineeringDocumentDetail(EngineeringDocumentRead):
    sections: list[DocumentSectionRead] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    documents: list[EngineeringDocumentRead] = Field(default_factory=list)


class AffectedDocumentSection(BaseModel):
    document_id: int
    document_title: str | None = None
    filename: str
    document_type: str
    section_id: int
    heading: str
    matched_parts: list[str] = Field(default_factory=list)
    excerpt: str


class AffectedDocumentSectionsResponse(BaseModel):
    part_number: str
    sections: list[AffectedDocumentSection] = Field(default_factory=list)
