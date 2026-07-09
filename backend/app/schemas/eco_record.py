from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.eco import ParsedEngineeringChange


class SavedEcoTextParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


class EcoRecordRead(BaseModel):
    id: int
    upload_id: int | None = None
    source_type: str
    change_type: str | None = None
    old_part: str | None = None
    new_part: str | None = None
    reason: str | None = None
    effective_date: date | None = None
    parser_source: str
    confidence: float
    workflow_status: str
    correction_notes: str | None = None
    approval_notes: str | None = None
    reviewed_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EcoRecordDetail(EcoRecordRead):
    source_text: str | None = None
    parsed: ParsedEngineeringChange


class EcoRecordListResponse(BaseModel):
    records: list[EcoRecordRead] = Field(default_factory=list)


class EcoRecordUpdateRequest(BaseModel):
    change_type: str | None = Field(default=None, max_length=80)
    old_part: str | None = Field(default=None, max_length=120)
    new_part: str | None = Field(default=None, max_length=120)
    reason: str | None = Field(default=None, max_length=10_000)
    effective_date: date | None = None
    correction_notes: str | None = Field(default=None, max_length=5_000)


class EcoRecordWorkflowRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=5_000)
