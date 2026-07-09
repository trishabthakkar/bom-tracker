from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.uploads import _mark_matching_uploads_replaced
from app.db.base import Base
from app.models.bom import BomImport
from app.models.report import ImpactReport
from app.models.upload import UploadedFile
from app.models.user import User


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


def create_user(db: Session) -> User:
    user = User(
        email="replace@example.com",
        full_name="Replace User",
        hashed_password="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_upload(db: Session, user: User) -> UploadedFile:
    upload = UploadedFile(
        uploader_id=user.id,
        original_filename="demo-bom.csv",
        stored_filename="stored-demo-bom.csv",
        file_extension=".csv",
        content_type="text/csv",
        size_bytes=100,
        storage_path="uploads/stored-demo-bom.csv",
        upload_category="bom",
        status="stored",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def test_mark_matching_uploads_replaced_archives_dependent_bom_records() -> None:
    db = build_session()
    user = create_user(db)
    upload = create_upload(db, user)

    bom_import = BomImport(
        user_id=user.id,
        upload_id=upload.id,
        filename=upload.original_filename,
        row_count=1,
        status="imported",
    )
    db.add(bom_import)
    db.commit()
    db.refresh(bom_import)

    report = ImpactReport(
        user_id=user.id,
        bom_import_id=bom_import.id,
        eco_record_id=None,
        graph_snapshot_id=None,
        bom_upload_id=upload.id,
        summary="Impact report",
        affected_part="PN-1",
        effective_date=None,
        risk_level="Low",
        risk_score=10,
        report_json={"summary": "Impact report"},
        status="generated",
    )
    db.add(report)
    db.commit()

    _mark_matching_uploads_replaced(
        db=db,
        user_id=user.id,
        original_filename="demo-bom.csv",
        upload_category="bom",
    )
    db.commit()
    db.refresh(upload)
    db.refresh(bom_import)
    db.refresh(report)

    assert upload.status == "replaced"
    assert bom_import.status == "archived"
    assert bom_import.archived_at is not None
    assert report.status == "archived"
    assert report.archived_at is not None
