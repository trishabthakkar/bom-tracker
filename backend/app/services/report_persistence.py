from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bom import BomImport
from app.models.eco import EcoRecord
from app.models.graph_snapshot import GraphSnapshot
from app.models.report import ImpactReport
from app.models.upload import UploadedFile
from app.schemas.impact import StructuredImpactReport
from app.schemas.impact import DocumentSectionImpact
from app.services.bom_importer import (
    get_latest_bom_import_for_upload,
    import_bom_upload,
)
from app.services.dependency_graph import build_dependency_graph
from app.services.documents import find_sections_referencing_parts
from app.services.eco_records import create_eco_record, eco_record_to_parsed_change
from app.services.eco_parser import EngineeringChangeParser
from app.services.intelligence_layer import IntelligenceLayer
from app.services.bom_parser import BomParserError, parse_bom_file


class ReportPersistenceError(ValueError):
    pass


def generate_and_save_impact_report(
    *,
    db: Session,
    bom_upload: UploadedFile,
    eco_text: str,
    user_id: int,
) -> ImpactReport:
    if bom_upload.uploader_id != user_id:
        raise ReportPersistenceError("Uploaded BOM file was not found.")

    if bom_upload.file_extension not in {".csv", ".xlsx"}:
        raise ReportPersistenceError("Only CSV and XLSX uploads can be used for impact reports.")

    parsed_eco = EngineeringChangeParser().parse_text(eco_text)
    eco_record = create_eco_record(
        db=db,
        parsed=parsed_eco,
        user_id=user_id,
        source_type="text",
        source_text=eco_text,
    )
    return _generate_and_save_from_parsed_eco(
        db=db,
        bom_upload=bom_upload,
        parsed_eco=parsed_eco,
        eco_record=eco_record,
        user_id=user_id,
    )


def generate_and_save_impact_report_from_eco_record(
    *,
    db: Session,
    bom_upload: UploadedFile,
    eco_record: EcoRecord,
    user_id: int,
) -> ImpactReport:
    if eco_record.user_id != user_id:
        raise ReportPersistenceError("ECO record was not found.")

    if eco_record.workflow_status != "approved":
        raise ReportPersistenceError("Only approved ECO records can be used for report generation.")

    return _generate_and_save_from_parsed_eco(
        db=db,
        bom_upload=bom_upload,
        parsed_eco=eco_record_to_parsed_change(eco_record),
        eco_record=eco_record,
        user_id=user_id,
    )


def _generate_and_save_from_parsed_eco(
    *,
    db: Session,
    bom_upload: UploadedFile,
    parsed_eco,
    eco_record: EcoRecord,
    user_id: int,
) -> ImpactReport:
    if bom_upload.uploader_id != user_id:
        raise ReportPersistenceError("Uploaded BOM file was not found.")

    if bom_upload.file_extension not in {".csv", ".xlsx"}:
        raise ReportPersistenceError("Only CSV and XLSX uploads can be used for impact reports.")

    bom_import = get_latest_bom_import_for_upload(
        db=db,
        upload_id=bom_upload.id,
        user_id=user_id,
    )
    graph_snapshot: GraphSnapshot | None = None

    if bom_import is None:
        bom_import, graph_snapshot = import_bom_upload(
            db=db,
            upload=bom_upload,
            user_id=user_id,
        )
    else:
        graph_snapshot = db.scalar(
            select(GraphSnapshot)
            .where(GraphSnapshot.user_id == user_id)
            .where(GraphSnapshot.bom_import_id == bom_import.id)
            .order_by(GraphSnapshot.created_at.desc())
        )

    try:
        parsed_bom = parse_bom_file(bom_upload.storage_path)
    except BomParserError as error:
        raise ReportPersistenceError(str(error)) from error

    graph = build_dependency_graph(parsed_bom.rows)
    document_sections = _build_document_section_impacts(
        db=db,
        user_id=user_id,
        part_numbers=_candidate_document_parts(parsed_eco),
    )
    report = IntelligenceLayer().generate_report(
        graph=graph,
        eco=parsed_eco,
        document_sections=document_sections,
    )

    return save_impact_report(
        db=db,
        report=report,
        user_id=user_id,
        bom_import=bom_import,
        eco_record=eco_record,
        bom_upload=bom_upload,
        graph_snapshot=graph_snapshot,
    )


def save_impact_report(
    *,
    db: Session,
    report: StructuredImpactReport,
    user_id: int,
    bom_import: BomImport,
    eco_record: EcoRecord | None,
    bom_upload: UploadedFile,
    graph_snapshot: GraphSnapshot | None = None,
) -> ImpactReport:
    saved = ImpactReport(
        user_id=user_id,
        bom_import_id=bom_import.id,
        eco_record_id=eco_record.id if eco_record else None,
        graph_snapshot_id=graph_snapshot.id if graph_snapshot else None,
        bom_upload_id=bom_upload.id,
        summary=report.summary,
        affected_part=report.affected_part,
        effective_date=report.effective_date,
        risk_level=report.risk.level,
        risk_score=report.risk.score,
        report_json=report.model_dump(mode="json"),
        status="generated",
        review_status="draft",
        owner_user_id=user_id,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


def list_reports(*, db: Session, user_id: int) -> list[ImpactReport]:
    return list(
        db.scalars(
            select(ImpactReport)
            .where(ImpactReport.user_id == user_id)
            .where(ImpactReport.archived_at.is_(None))
            .order_by(ImpactReport.created_at.desc())
        )
    )


def get_report(*, db: Session, report_id: int, user_id: int) -> ImpactReport | None:
    report = db.get(ImpactReport, report_id)
    if report is None or report.user_id != user_id or report.archived_at is not None:
        return None

    return report


def archive_report(*, db: Session, report: ImpactReport) -> ImpactReport:
    report.status = "archived"
    report.archived_at = datetime.utcnow()
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def report_to_structured(report: ImpactReport) -> StructuredImpactReport:
    return StructuredImpactReport.model_validate(report.report_json)


def _candidate_document_parts(parsed_eco) -> list[str]:
    return [part for part in [parsed_eco.old_part, parsed_eco.new_part] if part]


def _build_document_section_impacts(
    *,
    db: Session,
    user_id: int,
    part_numbers: list[str],
) -> list[DocumentSectionImpact]:
    impacts: list[DocumentSectionImpact] = []

    for document, section, matched_parts in find_sections_referencing_parts(
        db=db,
        user_id=user_id,
        part_numbers=part_numbers,
    ):
        impacts.append(
            DocumentSectionImpact(
                document_id=document.id,
                document_title=document.title,
                filename=document.filename,
                document_type=document.document_type,
                section_id=section.id,
                heading=section.heading,
                matched_parts=matched_parts,
                excerpt=_excerpt(section.content),
                severity="high" if document.document_type in {"service_manual", "installation_guide"} else "medium",
            )
        )

    return impacts


def _excerpt(content: str, limit: int = 260) -> str:
    cleaned = " ".join(content.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3]}..."
