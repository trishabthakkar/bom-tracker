from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.bom import BomParseResponse, ParsedBomRow
from app.services.bom_parser import BomParserError, parse_bom_file

router = APIRouter(prefix="/bom", tags=["bom"])


@router.post("/parse/{upload_id}", response_model=BomParseResponse)
def parse_uploaded_bom(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BomParseResponse:
    upload = db.get(UploadedFile, upload_id)

    if upload is None or upload.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded BOM file was not found.",
        )

    if upload.file_extension not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV and XLSX uploads can be parsed as BOM files.",
        )

    try:
        parsed = parse_bom_file(upload.storage_path)
    except BomParserError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    rows = [ParsedBomRow.model_validate(row.__dict__) for row in parsed.rows]

    return BomParseResponse(
        upload_id=upload.id,
        filename=upload.original_filename,
        row_count=len(rows),
        rows=rows,
    )
