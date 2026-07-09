from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import DocumentSection, EngineeringDocument
from app.models.upload import UploadedFile
from app.services.document_parser import DocumentParserError, parse_document_text
from app.services.pdf_text_extractor import PdfTextExtractionError, extract_pdf_text


class DocumentIndexError(ValueError):
    pass


def index_document_upload(
    *,
    db: Session,
    upload: UploadedFile,
    user_id: int,
) -> EngineeringDocument:
    if upload.uploader_id != user_id:
        raise DocumentIndexError("Uploaded document was not found.")

    if upload.file_extension != ".pdf":
        raise DocumentIndexError("Only PDF documents can be indexed in this MVP.")

    try:
        text = extract_pdf_text(upload.storage_path)
        parsed = parse_document_text(text)
    except (PdfTextExtractionError, DocumentParserError) as error:
        raise DocumentIndexError(str(error)) from error

    existing = get_latest_document_for_upload(db=db, upload_id=upload.id, user_id=user_id)
    if existing is not None:
        archive_document(db=db, document=existing)

    document = EngineeringDocument(
        user_id=user_id,
        upload_id=upload.id,
        filename=upload.original_filename,
        document_type=_infer_document_type(upload.original_filename, text),
        title=parsed.title,
        status="indexed",
        section_count=len(parsed.sections),
        part_references=parsed.part_references,
    )
    db.add(document)
    db.flush()

    db.add_all(
        [
            DocumentSection(
                document_id=document.id,
                user_id=user_id,
                upload_id=upload.id,
                section_index=section.section_index,
                heading=section.heading,
                content=section.content,
                part_references=section.part_references,
            )
            for section in parsed.sections
        ]
    )
    db.commit()
    db.refresh(document)
    return document


def list_documents(*, db: Session, user_id: int) -> list[EngineeringDocument]:
    return list(
        db.scalars(
            select(EngineeringDocument)
            .where(EngineeringDocument.user_id == user_id)
            .where(EngineeringDocument.archived_at.is_(None))
            .order_by(EngineeringDocument.created_at.desc())
        )
    )


def get_document(*, db: Session, document_id: int, user_id: int) -> EngineeringDocument | None:
    document = db.get(EngineeringDocument, document_id)
    if document is None or document.user_id != user_id or document.archived_at is not None:
        return None

    return document


def get_latest_document_for_upload(
    *,
    db: Session,
    upload_id: int,
    user_id: int,
) -> EngineeringDocument | None:
    return db.scalar(
        select(EngineeringDocument)
        .where(EngineeringDocument.user_id == user_id)
        .where(EngineeringDocument.upload_id == upload_id)
        .where(EngineeringDocument.archived_at.is_(None))
        .order_by(EngineeringDocument.created_at.desc())
    )


def get_document_sections(
    *,
    db: Session,
    document_id: int,
    user_id: int,
) -> list[DocumentSection]:
    return list(
        db.scalars(
            select(DocumentSection)
            .where(DocumentSection.user_id == user_id)
            .where(DocumentSection.document_id == document_id)
            .order_by(DocumentSection.section_index.asc())
        )
    )


def find_sections_referencing_parts(
    *,
    db: Session,
    user_id: int,
    part_numbers: list[str],
) -> list[tuple[EngineeringDocument, DocumentSection, list[str]]]:
    normalized_parts = {_normalize_part(part) for part in part_numbers if part}
    if not normalized_parts:
        return []

    documents = {
        document.id: document
        for document in list_documents(db=db, user_id=user_id)
    }
    if not documents:
        return []

    sections = list(
        db.scalars(
            select(DocumentSection)
            .where(DocumentSection.user_id == user_id)
            .where(DocumentSection.document_id.in_(list(documents.keys())))
            .order_by(DocumentSection.document_id.asc(), DocumentSection.section_index.asc())
        )
    )

    matches: list[tuple[EngineeringDocument, DocumentSection, list[str]]] = []
    for section in sections:
        matched_parts = sorted(normalized_parts.intersection(section.part_references or []))
        if matched_parts:
            matches.append((documents[section.document_id], section, matched_parts))

    return matches


def archive_document(*, db: Session, document: EngineeringDocument) -> EngineeringDocument:
    document.status = "archived"
    document.archived_at = datetime.utcnow()
    db.add(document)
    db.flush()
    return document


def _infer_document_type(filename: str, text: str) -> str:
    value = f"{filename} {text[:500]}".lower()
    if "install" in value:
        return "installation_guide"
    if "commission" in value:
        return "commissioning_procedure"
    if "service" in value or "maintenance" in value:
        return "service_manual"
    if "procurement" in value or "supplier" in value or "purchase" in value:
        return "procurement_record"
    return "engineering_document"


def _normalize_part(value: str) -> str:
    return value.strip().upper().replace(" ", "-").replace("_", "-")
