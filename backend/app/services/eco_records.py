from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.eco import EcoRecord
from app.models.upload import UploadedFile
from app.schemas.eco import ParsedEngineeringChange
from app.services.eco_parser import EngineeringChangeParser
from app.services.pdf_text_extractor import PdfTextExtractionError, extract_pdf_text


class EcoRecordError(ValueError):
    pass


def parse_text_and_create_eco_record(
    *,
    db: Session,
    text: str,
    user_id: int,
) -> EcoRecord:
    parsed = EngineeringChangeParser().parse_text(text)
    return create_eco_record(
        db=db,
        parsed=parsed,
        user_id=user_id,
        source_type="text",
        source_text=text,
    )


def parse_upload_and_create_eco_record(
    *,
    db: Session,
    upload: UploadedFile,
    user_id: int,
) -> EcoRecord:
    if upload.uploader_id != user_id:
        raise EcoRecordError("Uploaded ECO file was not found.")

    if upload.file_extension != ".pdf":
        raise EcoRecordError("Only uploaded PDF files can be parsed into ECO records.")

    try:
        text = extract_pdf_text(upload.storage_path)
    except PdfTextExtractionError as error:
        raise EcoRecordError(str(error)) from error

    parsed = EngineeringChangeParser().parse_text(text)
    return create_eco_record(
        db=db,
        parsed=parsed,
        user_id=user_id,
        source_type="pdf",
        upload_id=upload.id,
        source_text=text,
    )


def create_eco_record(
    *,
    db: Session,
    parsed: ParsedEngineeringChange,
    user_id: int,
    source_type: str,
    upload_id: int | None = None,
    source_text: str | None = None,
) -> EcoRecord:
    record = EcoRecord(
        user_id=user_id,
        upload_id=upload_id,
        source_type=source_type,
        source_text=source_text,
        change_type=parsed.change_type,
        old_part=parsed.old_part,
        new_part=parsed.new_part,
        reason=parsed.reason,
        effective_date=parsed.effective_date,
        parser_source=parsed.source,
        confidence=parsed.confidence,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_eco_records(*, db: Session, user_id: int) -> list[EcoRecord]:
    return list(
        db.scalars(
            select(EcoRecord)
            .where(EcoRecord.user_id == user_id)
            .order_by(EcoRecord.created_at.desc())
        )
    )


def get_eco_record(*, db: Session, record_id: int, user_id: int) -> EcoRecord | None:
    record = db.get(EcoRecord, record_id)
    if record is None or record.user_id != user_id:
        return None

    return record


def update_eco_record(
    *,
    db: Session,
    record: EcoRecord,
    change_type: str | None,
    old_part: str | None,
    new_part: str | None,
    reason: str | None,
    effective_date: date | None,
    correction_notes: str | None,
) -> EcoRecord:
    record.change_type = _clean_optional(change_type)
    record.old_part = _clean_part(old_part)
    record.new_part = _clean_part(new_part)
    record.reason = _clean_optional(reason)
    record.effective_date = effective_date
    record.correction_notes = _clean_optional(correction_notes)
    record.workflow_status = "reviewed"
    record.reviewed_at = datetime.utcnow()
    record.approved_at = None
    record.rejected_at = None
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def mark_eco_reviewed(*, db: Session, record: EcoRecord, notes: str | None = None) -> EcoRecord:
    record.workflow_status = "reviewed"
    record.correction_notes = _clean_optional(notes) or record.correction_notes
    record.reviewed_at = datetime.utcnow()
    record.approved_at = None
    record.rejected_at = None
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def approve_eco_record(*, db: Session, record: EcoRecord, notes: str | None = None) -> EcoRecord:
    record.workflow_status = "approved"
    record.approval_notes = _clean_optional(notes)
    record.reviewed_at = record.reviewed_at or datetime.utcnow()
    record.approved_at = datetime.utcnow()
    record.rejected_at = None
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def reject_eco_record(*, db: Session, record: EcoRecord, notes: str | None = None) -> EcoRecord:
    record.workflow_status = "rejected"
    record.approval_notes = _clean_optional(notes)
    record.reviewed_at = record.reviewed_at or datetime.utcnow()
    record.rejected_at = datetime.utcnow()
    record.approved_at = None
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def eco_record_to_parsed_change(record: EcoRecord) -> ParsedEngineeringChange:
    return ParsedEngineeringChange(
        change_type=record.change_type,
        old_part=record.old_part,
        new_part=record.new_part,
        reason=record.reason,
        effective_date=record.effective_date,
        source=record.parser_source,
        confidence=record.confidence,
    )


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None


def _clean_part(value: str | None) -> str | None:
    cleaned = _clean_optional(value)
    return cleaned.upper() if cleaned else None
