from pydantic import BaseModel, Field


class ParsedBomRow(BaseModel):
    row_number: int
    part_number: str
    description: str | None = None
    parent_assembly: str | None = None
    child_assembly: str | None = None
    revision: str | None = None


class BomParseResponse(BaseModel):
    upload_id: int
    filename: str
    row_count: int
    rows: list[ParsedBomRow] = Field(default_factory=list)
