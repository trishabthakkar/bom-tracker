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
