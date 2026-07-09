from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobRead(BaseModel):
    id: int
    job_type: str
    status: str
    progress_percent: int
    status_message: str | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    input_json: dict[str, Any]
    result_json: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    jobs: list[JobRead] = Field(default_factory=list)


class CreateReportJobRequest(BaseModel):
    bom_upload_id: int
    eco_text: str | None = Field(default=None, min_length=1, max_length=20_000)
    eco_record_id: int | None = None

    @model_validator(mode="after")
    def require_eco_source(self) -> "CreateReportJobRequest":
        if not self.eco_text and self.eco_record_id is None:
            raise ValueError("Provide ECO text or an approved ECO record id.")
        return self
