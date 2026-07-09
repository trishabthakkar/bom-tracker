from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.job import CreateReportJobRequest, JobListResponse, JobRead
from app.services.jobs import (
    JOB_TYPE_BOM_IMPORT,
    JOB_TYPE_ECO_UPLOAD_PARSE,
    JOB_TYPE_GRAPH_BUILD,
    JOB_TYPE_IMPACT_REPORT,
    create_job,
    get_job,
    list_jobs,
    run_bom_import_job,
    run_eco_upload_parse_job,
    run_graph_build_job,
    run_impact_report_job,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/bom-imports/from-upload/{upload_id}", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def create_bom_import_job(
    upload_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    upload = _load_owned_upload(db=db, upload_id=upload_id, current_user=current_user)
    if upload.file_extension not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV and XLSX uploads can be imported as BOM files.",
        )

    job = create_job(
        db=db,
        user_id=current_user.id,
        job_type=JOB_TYPE_BOM_IMPORT,
        input_json={"upload_id": upload.id},
        status_message="BOM import queued.",
    )
    background_tasks.add_task(run_bom_import_job, job.id)
    return JobRead.model_validate(job)


@router.post("/eco-records/parse-upload/{upload_id}", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def create_eco_upload_parse_job(
    upload_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    upload = _load_owned_upload(db=db, upload_id=upload_id, current_user=current_user)
    if upload.file_extension != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only uploaded PDF files can be parsed into ECO records.",
        )

    job = create_job(
        db=db,
        user_id=current_user.id,
        job_type=JOB_TYPE_ECO_UPLOAD_PARSE,
        input_json={"upload_id": upload.id},
        status_message="ECO PDF parsing queued.",
    )
    background_tasks.add_task(run_eco_upload_parse_job, job.id)
    return JobRead.model_validate(job)


@router.post("/graph/build/{upload_id}", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def create_graph_build_job(
    upload_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    upload = _load_owned_upload(db=db, upload_id=upload_id, current_user=current_user)
    if upload.file_extension not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV and XLSX uploads can be converted into dependency graphs.",
        )

    job = create_job(
        db=db,
        user_id=current_user.id,
        job_type=JOB_TYPE_GRAPH_BUILD,
        input_json={"upload_id": upload.id},
        status_message="Graph build queued.",
    )
    background_tasks.add_task(run_graph_build_job, job.id)
    return JobRead.model_validate(job)


@router.post("/reports/impact-report", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def create_impact_report_job(
    payload: CreateReportJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    upload = _load_owned_upload(db=db, upload_id=payload.bom_upload_id, current_user=current_user)
    if upload.file_extension not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV and XLSX uploads can be used for impact reports.",
        )

    job = create_job(
        db=db,
        user_id=current_user.id,
        job_type=JOB_TYPE_IMPACT_REPORT,
        input_json={
            "bom_upload_id": upload.id,
            "eco_text": payload.eco_text,
        },
        status_message="Impact report generation queued.",
    )
    background_tasks.add_task(run_impact_report_job, job.id)
    return JobRead.model_validate(job)


@router.get("", response_model=JobListResponse)
def read_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobListResponse:
    return JobListResponse(
        jobs=[JobRead.model_validate(job) for job in list_jobs(db=db, user_id=current_user.id)]
    )


@router.get("/{job_id}", response_model=JobRead)
def read_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    job = get_job(db=db, job_id=job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job was not found.",
        )

    return JobRead.model_validate(job)


def _load_owned_upload(*, db: Session, upload_id: int, current_user: User) -> UploadedFile:
    upload = db.get(UploadedFile, upload_id)
    if upload is None or upload.uploader_id != current_user.id or upload.status == "replaced":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded file was not found.",
        )

    return upload
