from datetime import date

from pydantic import BaseModel, Field


class EcoTextParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


class ParsedEngineeringChange(BaseModel):
    change_type: str | None = None
    old_part: str | None = None
    new_part: str | None = None
    reason: str | None = None
    effective_date: date | None = None
    source: str
    confidence: float = Field(ge=0, le=1)
