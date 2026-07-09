from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.job import Job
from app.models.upload import UploadedFile
from app.models.user import User
from app.services.jobs import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_QUEUED,
    JOB_TYPE_BOM_IMPORT,
    create_job,
    list_jobs,
)


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


def create_user(db: Session) -> User:
    user = User(
        email="jobs@example.com",
        full_name="Jobs User",
        hashed_password="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_bom_upload(db: Session, user: User, path: Path) -> UploadedFile:
    upload = UploadedFile(
        uploader_id=user.id,
        original_filename="bom.csv",
        stored_filename="bom.csv",
        file_extension=".csv",
        content_type="text/csv",
        size_bytes=path.stat().st_size,
        storage_path=str(path),
        upload_category="bom",
        status="stored",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def test_create_job_defaults_to_queued_status() -> None:
    db = build_session()
    user = create_user(db)

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


def test_completed_job_can_store_entity_and_result_metadata(tmp_path: Path) -> None:
    db = build_session()
    user = create_user(db)
    path = tmp_path / "bom.csv"
    path.write_text("Part Number,Description\nPN-1,Valve\n", encoding="utf-8")
    upload = create_bom_upload(db, user, path)

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
