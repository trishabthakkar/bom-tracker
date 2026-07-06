from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.impact import StructuredImpactReport


class PersistedImpactReportRequest(BaseModel):
    bom_upload_id: int
    eco_text: str = Field(min_length=1, max_length=20_000)


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
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ImpactReportDetail(ImpactReportRead):
    report: StructuredImpactReport


class ImpactReportListResponse(BaseModel):
    reports: list[ImpactReportRead] = Field(default_factory=list)
