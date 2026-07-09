from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    eco_text: str = Field(min_length=1, max_length=20_000)
