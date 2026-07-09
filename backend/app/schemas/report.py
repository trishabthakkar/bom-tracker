from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.impact import StructuredImpactReport


class PersistedImpactReportRequest(BaseModel):
    bom_upload_id: int
    eco_text: str | None = Field(default=None, min_length=1, max_length=20_000)
    eco_record_id: int | None = None

    @model_validator(mode="after")
    def require_eco_source(self) -> "PersistedImpactReportRequest":
        if not self.eco_text and self.eco_record_id is None:
            raise ValueError("Provide ECO text or an approved ECO record id.")
        return self


class ImpactReportRead(BaseModel):
    id: int
    bom_import_id: int
    eco_record_id: int | None = None
    graph_snapshot_id: int | None = None
    bom_upload_id: int
    summary: str
    affected_part: str | None = None
    effective_date: date | None = None
    risk_level: str
    risk_score: int
    status: str
    review_status: str
    owner_user_id: int | None = None
    assigned_user_id: int | None = None
    signoff_notes: str | None = None
    reviewed_at: datetime | None = None
    signed_off_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ReportCommentRead(BaseModel):
    id: int
    report_id: int
    user_id: int
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImpactReportDetail(ImpactReportRead):
    report: StructuredImpactReport
    comments: list[ReportCommentRead] = Field(default_factory=list)


class ImpactReportListResponse(BaseModel):
    reports: list[ImpactReportRead] = Field(default_factory=list)


class ReportCommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5_000)


class ReportReviewUpdateRequest(BaseModel):
    review_status: str = Field(pattern="^(draft|in_review|changes_requested|signed_off)$")
    assigned_user_id: int | None = None
    signoff_notes: str | None = Field(default=None, max_length=5_000)
