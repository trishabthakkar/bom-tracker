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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EcoRecordDetail(EcoRecordRead):
    source_text: str | None = None
    parsed: ParsedEngineeringChange


class EcoRecordListResponse(BaseModel):
    records: list[EcoRecordRead] = Field(default_factory=list)
