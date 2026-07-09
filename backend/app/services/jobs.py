from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.job import Job
from app.models.upload import UploadedFile
from app.services.bom_importer import BomImportError, import_bom_upload
from app.services.bom_parser import BomParserError, parse_bom_file
from app.services.dependency_graph import (
    build_dependency_graph,
    get_graph_edges,
    get_graph_statistics,
)
from app.services.eco_records import EcoRecordError, parse_upload_and_create_eco_record
from app.services.report_persistence import (
    ReportPersistenceError,
    generate_and_save_impact_report,
)

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"

JOB_TYPE_BOM_IMPORT = "bom_import"
JOB_TYPE_ECO_UPLOAD_PARSE = "eco_upload_parse"
JOB_TYPE_GRAPH_BUILD = "graph_build"
JOB_TYPE_IMPACT_REPORT = "impact_report"


class JobError(ValueError):
    pass


def create_job(
    *,
    db: Session,
    user_id: int,
    job_type: str,
    input_json: dict[str, Any],
    status_message: str,
) -> Job:
    job = Job(
        user_id=user_id,
        job_type=job_type,
        status=JOB_STATUS_QUEUED,
        progress_percent=0,
        status_message=status_message,
        input_json=input_json,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_jobs(*, db: Session, user_id: int) -> list[Job]:
    return list(
        db.scalars(
            select(Job)
            .where(Job.user_id == user_id)
            .order_by(Job.created_at.desc())
        )
    )


def get_job(*, db: Session, job_id: int, user_id: int) -> Job | None:
    job = db.get(Job, job_id)
    if job is None or job.user_id != user_id:
        return None

    return job


def run_bom_import_job(job_id: int) -> None:
    _run_job(job_id=job_id, handler=_handle_bom_import)


def run_eco_upload_parse_job(job_id: int) -> None:
    _run_job(job_id=job_id, handler=_handle_eco_upload_parse)


def run_graph_build_job(job_id: int) -> None:
    _run_job(job_id=job_id, handler=_handle_graph_build)


def run_impact_report_job(job_id: int) -> None:
    _run_job(job_id=job_id, handler=_handle_impact_report)


def _run_job(*, job_id: int, handler: Callable[[Session, Job], dict[str, Any]]) -> None:
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if job is None:
            return

        _mark_processing(db=db, job=job)

        try:
            result = handler(db, job)
        except Exception as error:
            db.rollback()
            _mark_failed(db=db, job_id=job_id, error_message=str(error))
            return

        _mark_completed(db=db, job=job, result=result)


def _mark_processing(*, db: Session, job: Job) -> None:
    job.status = JOB_STATUS_PROCESSING
    job.progress_percent = 10
    job.status_message = "Processing started."
    job.started_at = datetime.utcnow()
    db.add(job)
    db.commit()
    db.refresh(job)


def _mark_completed(*, db: Session, job: Job, result: dict[str, Any]) -> None:
    job.status = JOB_STATUS_COMPLETED
    job.progress_percent = 100
    job.status_message = "Processing completed."
    job.result_json = result
    job.error_message = None
    job.completed_at = datetime.utcnow()
    job.entity_type = result.get("entity_type")
    job.entity_id = result.get("entity_id")
    db.add(job)
    db.commit()


def _mark_failed(*, db: Session, job_id: int, error_message: str) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return

    job.status = JOB_STATUS_FAILED
    job.progress_percent = 100
    job.status_message = "Processing failed."
    job.error_message = error_message or "Job failed."
    job.completed_at = datetime.utcnow()
    db.add(job)
    db.commit()


def _handle_bom_import(db: Session, job: Job) -> dict[str, Any]:
    upload = _load_upload(
        db=db,
        upload_id=int(job.input_json["upload_id"]),
        user_id=job.user_id,
    )

    try:
        bom_import, graph_snapshot = import_bom_upload(
            db=db,
            upload=upload,
            user_id=job.user_id,
        )
    except BomImportError as error:
        raise JobError(str(error)) from error

    return {
        "entity_type": "bom_import",
        "entity_id": bom_import.id,
        "bom_import_id": bom_import.id,
        "upload_id": upload.id,
        "filename": bom_import.filename,
        "row_count": bom_import.row_count,
        "graph_snapshot_id": graph_snapshot.id,
    }


def _handle_eco_upload_parse(db: Session, job: Job) -> dict[str, Any]:
    upload = _load_upload(
        db=db,
        upload_id=int(job.input_json["upload_id"]),
        user_id=job.user_id,
    )

    try:
        record = parse_upload_and_create_eco_record(
            db=db,
            upload=upload,
            user_id=job.user_id,
        )
    except EcoRecordError as error:
        raise JobError(str(error)) from error

    return {
        "entity_type": "eco_record",
        "entity_id": record.id,
        "eco_record_id": record.id,
        "upload_id": upload.id,
        "old_part": record.old_part,
        "new_part": record.new_part,
        "change_type": record.change_type,
    }


def _handle_graph_build(db: Session, job: Job) -> dict[str, Any]:
    upload = _load_upload(
        db=db,
        upload_id=int(job.input_json["upload_id"]),
        user_id=job.user_id,
    )

    if upload.file_extension not in {".csv", ".xlsx"}:
        raise JobError("Only CSV and XLSX uploads can be converted into dependency graphs.")

    try:
        parsed = parse_bom_file(upload.storage_path)
    except BomParserError as error:
        raise JobError(str(error)) from error

    graph = build_dependency_graph(parsed.rows)
    statistics = get_graph_statistics(graph)

    return {
        "entity_type": "graph",
        "entity_id": upload.id,
        "upload_id": upload.id,
        "filename": upload.original_filename,
        "node_count": statistics.node_count,
        "edge_count": statistics.edge_count,
        "root_count": statistics.root_count,
        "leaf_count": statistics.leaf_count,
        "has_cycles": statistics.has_cycles,
        "edge_preview": [edge.__dict__ for edge in get_graph_edges(graph)[:25]],
    }


def _handle_impact_report(db: Session, job: Job) -> dict[str, Any]:
    upload = _load_upload(
        db=db,
        upload_id=int(job.input_json["bom_upload_id"]),
        user_id=job.user_id,
    )

    try:
        report = generate_and_save_impact_report(
            db=db,
            bom_upload=upload,
            eco_text=str(job.input_json["eco_text"]),
            user_id=job.user_id,
        )
    except ReportPersistenceError as error:
        raise JobError(str(error)) from error

    return {
        "entity_type": "impact_report",
        "entity_id": report.id,
        "report_id": report.id,
        "bom_upload_id": upload.id,
        "bom_import_id": report.bom_import_id,
        "eco_record_id": report.eco_record_id,
        "risk_level": report.risk_level,
        "risk_score": report.risk_score,
        "affected_part": report.affected_part,
    }


def _load_upload(*, db: Session, upload_id: int, user_id: int) -> UploadedFile:
    upload = db.get(UploadedFile, upload_id)
    if upload is None or upload.uploader_id != user_id or upload.status == "replaced":
        raise JobError("Uploaded file was not found.")

    return upload
