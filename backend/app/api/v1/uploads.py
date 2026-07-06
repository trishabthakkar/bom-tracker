from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.upload import UploadedFileRead, UploadListResponse
from app.services.file_storage import store_upload, validate_upload_category

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=UploadedFileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    upload_category: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadedFileRead:
    category = validate_upload_category(upload_category)
    stored_file = await store_upload(file)

    upload = UploadedFile(
        uploader_id=current_user.id,
        original_filename=stored_file.original_filename,
        stored_filename=stored_file.stored_filename,
        file_extension=stored_file.file_extension,
        content_type=stored_file.content_type,
        size_bytes=stored_file.size_bytes,
        storage_path=stored_file.storage_path,
        upload_category=category,
        status="stored",
    )

    db.add(upload)
    db.commit()
    db.refresh(upload)
    return UploadedFileRead.model_validate(upload)


@router.get("", response_model=UploadListResponse)
def list_uploads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadListResponse:
    uploads = db.scalars(
        select(UploadedFile)
        .where(UploadedFile.uploader_id == current_user.id)
        .order_by(UploadedFile.created_at.desc())
    ).all()

    return UploadListResponse(
        uploads=[UploadedFileRead.model_validate(upload) for upload in uploads]
    )
