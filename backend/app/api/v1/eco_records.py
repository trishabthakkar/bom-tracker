from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.eco_record import (
    EcoRecordDetail,
    EcoRecordListResponse,
    EcoRecordRead,
    SavedEcoTextParseRequest,
)
from app.services.eco_records import (
    EcoRecordError,
    eco_record_to_parsed_change,
    get_eco_record,
    list_eco_records,
    parse_text_and_create_eco_record,
    parse_upload_and_create_eco_record,
)

router = APIRouter(prefix="/eco-records", tags=["eco-records"])


@router.post("/parse-text", response_model=EcoRecordDetail)
def save_parsed_eco_text(
    payload: SavedEcoTextParseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EcoRecordDetail:
    record = parse_text_and_create_eco_record(
        db=db,
        text=payload.text,
        user_id=current_user.id,
    )
    return _record_detail(record)


@router.post("/parse-upload/{upload_id}", response_model=EcoRecordDetail)
def save_parsed_eco_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EcoRecordDetail:
    upload = db.get(UploadedFile, upload_id)

    if upload is None or upload.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded ECO file was not found.",
        )

    try:
        record = parse_upload_and_create_eco_record(
            db=db,
            upload=upload,
            user_id=current_user.id,
        )
    except EcoRecordError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _record_detail(record)


@router.get("", response_model=EcoRecordListResponse)
def read_eco_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EcoRecordListResponse:
    return EcoRecordListResponse(
        records=[
            EcoRecordRead.model_validate(record)
            for record in list_eco_records(db=db, user_id=current_user.id)
        ]
    )


@router.get("/{record_id}", response_model=EcoRecordDetail)
def read_eco_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EcoRecordDetail:
    record = get_eco_record(db=db, record_id=record_id, user_id=current_user.id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ECO record was not found.",
        )

    return _record_detail(record)


def _record_detail(record) -> EcoRecordDetail:
    return EcoRecordDetail(
        **EcoRecordRead.model_validate(record).model_dump(),
        source_text=record.source_text,
        parsed=eco_record_to_parsed_change(record),
    )
