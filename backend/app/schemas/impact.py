from datetime import date

from pydantic import BaseModel, Field

from app.schemas.eco import ParsedEngineeringChange


class ImpactReportRequest(BaseModel):
    bom_upload_id: int
    eco_text: str = Field(min_length=1, max_length=20_000)


class AffectedAssembly(BaseModel):
    part_number: str
    affected_parents: list[str] = Field(default_factory=list)
    affected_children: list[str] = Field(default_factory=list)
    dependency_paths: list[list[str]] = Field(default_factory=list)


class DownstreamRecordImpact(BaseModel):
    record_type: str
    impact: str
    severity: str


class SuggestedUpdate(BaseModel):
    area: str
    action: str
    priority: str


class DocumentSectionImpact(BaseModel):
    document_id: int
    document_title: str | None = None
    filename: str
    document_type: str
    section_id: int
    heading: str
    matched_parts: list[str] = Field(default_factory=list)
    excerpt: str
    severity: str


class RiskAssessment(BaseModel):
    level: str
    score: int
    reasons: list[str] = Field(default_factory=list)


class StructuredImpactReport(BaseModel):
    summary: str
    eco: ParsedEngineeringChange
    affected_part: str | None
    effective_date: date | None
    affected_assemblies: list[AffectedAssembly] = Field(default_factory=list)
    downstream_records: list[DownstreamRecordImpact] = Field(default_factory=list)
    affected_document_sections: list[DocumentSectionImpact] = Field(default_factory=list)
    suggested_updates: list[SuggestedUpdate] = Field(default_factory=list)
    risk: RiskAssessment
