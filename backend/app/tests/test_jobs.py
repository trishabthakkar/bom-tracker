from pathlib import Path

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.user import User
from app.services.jobs import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_QUEUED,
    JOB_TYPE_BOM_IMPORT,
    create_job,
    list_jobs,
)
from app.tests.conftest import MakeUpload


def test_create_job_defaults_to_queued_status(db_session: Session, user: User) -> None:
    db = db_session

    job = create_job(
        db=db,
        user_id=user.id,
        job_type=JOB_TYPE_BOM_IMPORT,
        input_json={"upload_id": 1},
        status_message="Queued.",
    )

    assert job.status == JOB_STATUS_QUEUED
    assert job.progress_percent == 0
    assert job.input_json == {"upload_id": 1}
    assert list_jobs(db=db, user_id=user.id) == [job]


def test_completed_job_can_store_entity_and_result_metadata(
    tmp_path: Path, db_session: Session, user: User, make_upload: MakeUpload
) -> None:
    db = db_session
    path = tmp_path / "bom.csv"
    path.write_text("Part Number,Description\nPN-1,Valve\n", encoding="utf-8")
    upload = make_upload(user=user, path=path)

    job = create_job(
        db=db,
        user_id=user.id,
        job_type=JOB_TYPE_BOM_IMPORT,
        input_json={"upload_id": upload.id},
        status_message="Queued.",
    )
    job.status = JOB_STATUS_COMPLETED
    job.progress_percent = 100
    job.entity_type = "bom_import"
    job.entity_id = 123
    job.result_json = {"bom_import_id": 123, "upload_id": upload.id}
    db.add(job)
    db.commit()

    saved = db.get(Job, job.id)

    assert saved is not None
    assert saved.status == JOB_STATUS_COMPLETED
    assert saved.entity_type == "bom_import"
    assert saved.result_json == {"bom_import_id": 123, "upload_id": upload.id}
