from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.eco import EcoTextParseRequest, ParsedEngineeringChange
from app.services.eco_parser import EngineeringChangeParser
from app.services.pdf_text_extractor import PdfTextExtractionError, extract_pdf_text

router = APIRouter(prefix="/eco", tags=["eco"])


@router.post("/parse-text", response_model=ParsedEngineeringChange)
def parse_eco_text(
    payload: EcoTextParseRequest,
    current_user: User = Depends(get_current_user),
) -> ParsedEngineeringChange:
    del current_user
    return EngineeringChangeParser().parse_text(payload.text)


@router.post("/parse-upload/{upload_id}", response_model=ParsedEngineeringChange)
def parse_uploaded_eco(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ParsedEngineeringChange:
    upload = db.get(UploadedFile, upload_id)

    if upload is None or upload.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded ECO file was not found.",
        )

    if upload.file_extension != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only uploaded PDF files can be parsed through this endpoint.",
        )

    try:
        text = extract_pdf_text(upload.storage_path)
    except PdfTextExtractionError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return EngineeringChangeParser().parse_text(text)
