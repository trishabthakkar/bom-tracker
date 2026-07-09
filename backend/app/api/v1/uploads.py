from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.bom import BomImport
from app.models.report import ImpactReport
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.upload import UploadedFileRead, UploadListResponse
from app.services.file_storage import store_upload, validate_upload_category

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=UploadedFileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    upload_category: str = Form(...),
    replace_existing: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadedFileRead:
    category = validate_upload_category(upload_category)
    stored_file = await store_upload(file)

    if replace_existing:
        _mark_matching_uploads_replaced(
            db=db,
            user_id=current_user.id,
            original_filename=stored_file.original_filename,
            upload_category=category,
        )

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
        .where(UploadedFile.status != "replaced")
        .order_by(UploadedFile.created_at.desc())
    ).all()

    return UploadListResponse(
        uploads=[UploadedFileRead.model_validate(upload) for upload in uploads]
    )


def _mark_matching_uploads_replaced(
    *,
    db: Session,
    user_id: int,
    original_filename: str,
    upload_category: str,
) -> None:
    matching_uploads = list(
        db.scalars(
            select(UploadedFile)
            .where(UploadedFile.uploader_id == user_id)
            .where(UploadedFile.upload_category == upload_category)
            .where(UploadedFile.original_filename == original_filename)
            .where(UploadedFile.status != "replaced")
        )
    )

    if not matching_uploads:
        return

    upload_ids = [upload.id for upload in matching_uploads]
    now = datetime.utcnow()

    for upload in matching_uploads:
        upload.status = "replaced"
        db.add(upload)

    bom_imports = list(
        db.scalars(
            select(BomImport)
            .where(BomImport.user_id == user_id)
            .where(BomImport.upload_id.in_(upload_ids))
            .where(BomImport.archived_at.is_(None))
        )
    )
    for bom_import in bom_imports:
        bom_import.status = "archived"
        bom_import.archived_at = now
        db.add(bom_import)

    reports = list(
        db.scalars(
            select(ImpactReport)
            .where(ImpactReport.user_id == user_id)
            .where(ImpactReport.bom_upload_id.in_(upload_ids))
            .where(ImpactReport.archived_at.is_(None))
        )
    )
    for report in reports:
        report.status = "archived"
        report.archived_at = now
        db.add(report)

    db.flush()
