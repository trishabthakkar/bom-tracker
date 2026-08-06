from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.document import (
    AffectedDocumentSection,
    AffectedDocumentSectionsResponse,
    DocumentListResponse,
    DocumentSectionRead,
    EngineeringDocumentDetail,
    EngineeringDocumentRead,
)
from app.services.documents import (
    DocumentIndexError,
    find_sections_referencing_parts,
    get_document,
    get_document_sections,
    index_document_upload,
    list_documents,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/from-upload/{upload_id}", response_model=EngineeringDocumentDetail)
def index_uploaded_document(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EngineeringDocumentDetail:
    upload = db.get(UploadedFile, upload_id)

    if upload is None or upload.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded document was not found.",
        )

    try:
        document = index_document_upload(db=db, upload=upload, user_id=current_user.id)
    except DocumentIndexError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _document_detail(db=db, document_id=document.id, user_id=current_user.id)


@router.get("", response_model=DocumentListResponse)
def read_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    return DocumentListResponse(
        documents=[
            EngineeringDocumentRead.model_validate(document)
            for document in list_documents(db=db, user_id=current_user.id)
        ]
    )


@router.get("/affected/{part_number}", response_model=AffectedDocumentSectionsResponse)
def read_affected_document_sections(
    part_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AffectedDocumentSectionsResponse:
    matches = find_sections_referencing_parts(
        db=db,
        user_id=current_user.id,
        part_numbers=[part_number],
    )

    return AffectedDocumentSectionsResponse(
        part_number=part_number,
        sections=[
            AffectedDocumentSection(
                document_id=match.document.id,
                document_title=match.document.title,
                filename=match.document.filename,
                document_type=match.document.document_type,
                section_id=match.section.id,
                heading=match.section.heading,
                matched_parts=match.matched_parts,
                inferred_parts=match.inferred_parts,
                excerpt=_excerpt(match.section.content),
            )
            for match in matches
        ],
    )


@router.get("/{document_id}", response_model=EngineeringDocumentDetail)
def read_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EngineeringDocumentDetail:
    return _document_detail(db=db, document_id=document_id, user_id=current_user.id)


def _document_detail(
    *,
    db: Session,
    document_id: int,
    user_id: int,
) -> EngineeringDocumentDetail:
    document = get_document(db=db, document_id=document_id, user_id=user_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engineering document was not found.",
        )

    return EngineeringDocumentDetail(
        **EngineeringDocumentRead.model_validate(document).model_dump(),
        sections=[
            DocumentSectionRead.model_validate(section)
            for section in get_document_sections(db=db, document_id=document.id, user_id=user_id)
        ],
    )


def _excerpt(content: str, limit: int = 260) -> str:
    cleaned = " ".join(content.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3]}..."
