from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.bom_import import (
    AssemblyRelationshipRead,
    BomDiffRequest,
    BomDiffResponse,
    BomImportDetail,
    BomImportListResponse,
    BomImportRead,
    BomPartRead,
)
from app.services.bom_diff import BomDiffError, compare_bom_imports
from app.services.bom_importer import (
    BomImportError,
    archive_bom_import,
    get_bom_import,
    get_import_parts,
    get_import_relationships,
    import_bom_upload,
    list_bom_imports,
)

router = APIRouter(prefix="/bom-imports", tags=["bom-imports"])


@router.post("/from-upload/{upload_id}", response_model=BomImportDetail)
def import_uploaded_bom(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BomImportDetail:
    upload = db.get(UploadedFile, upload_id)

    if upload is None or upload.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded BOM file was not found.",
        )

    try:
        bom_import, _ = import_bom_upload(db=db, upload=upload, user_id=current_user.id)
    except BomImportError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _build_import_detail(db=db, bom_import_id=bom_import.id, user_id=current_user.id)


@router.get("", response_model=BomImportListResponse)
def read_bom_imports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BomImportListResponse:
    return BomImportListResponse(
        imports=[
            BomImportRead.model_validate(bom_import)
            for bom_import in list_bom_imports(db=db, user_id=current_user.id)
        ]
    )


@router.post("/diff", response_model=BomDiffResponse)
def diff_bom_imports(
    payload: BomDiffRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BomDiffResponse:
    try:
        return compare_bom_imports(
            db=db,
            user_id=current_user.id,
            base_import_id=payload.base_import_id,
            target_import_id=payload.target_import_id,
        )
    except BomDiffError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.get("/{import_id}", response_model=BomImportDetail)
def read_bom_import(
    import_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BomImportDetail:
    bom_import = get_bom_import(db=db, import_id=import_id, user_id=current_user.id)

    if bom_import is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM import was not found.",
        )

    return _build_import_detail(db=db, bom_import_id=bom_import.id, user_id=current_user.id)


@router.delete("/{import_id}", response_model=BomImportRead)
def archive_import(
    import_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BomImportRead:
    bom_import = get_bom_import(db=db, import_id=import_id, user_id=current_user.id)

    if bom_import is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM import was not found.",
        )

    return BomImportRead.model_validate(archive_bom_import(db=db, bom_import=bom_import))


def _build_import_detail(
    *,
    db: Session,
    bom_import_id: int,
    user_id: int,
) -> BomImportDetail:
    bom_import = get_bom_import(db=db, import_id=bom_import_id, user_id=user_id)
    if bom_import is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM import was not found.",
        )

    return BomImportDetail(
        **BomImportRead.model_validate(bom_import).model_dump(),
        parts=[
            BomPartRead.model_validate(part)
            for part in get_import_parts(db=db, bom_import_id=bom_import.id, user_id=user_id)
        ],
        relationships=[
            AssemblyRelationshipRead.model_validate(relationship)
            for relationship in get_import_relationships(
                db=db,
                bom_import_id=bom_import.id,
                user_id=user_id,
            )
        ],
    )
