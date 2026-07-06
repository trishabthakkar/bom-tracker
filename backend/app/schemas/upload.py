from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadedFileRead(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    file_extension: str
    content_type: str
    size_bytes: int
    upload_category: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadListResponse(BaseModel):
    uploads: list[UploadedFileRead]
