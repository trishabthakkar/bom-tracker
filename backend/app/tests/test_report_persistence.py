from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.report import ImpactReport
from app.models.upload import UploadedFile
from app.models.user import User
from app.services.report_persistence import (
    generate_and_save_impact_report,
    get_report,
    list_reports,
    report_to_structured,
)


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


def create_bom_upload(db: Session, path: Path) -> tuple[User, UploadedFile]:
    user = User(
        email="report@example.com",
        full_name="Report User",
        hashed_password="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    upload = UploadedFile(
        uploader_id=user.id,
        original_filename="bom.csv",
        stored_filename="report-bom.csv",
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
    return user, upload


def test_generate_and_save_impact_report_persists_report(tmp_path: Path) -> None:
    path = tmp_path / "bom.csv"
    path.write_text(
        "Part Number,Description,Parent Assembly,Child Assembly,Revision\n"
        "PN-1212,Pressure relief valve,ASM-1000,ASM-1210,C\n",
        encoding="utf-8",
    )
    db = build_session()
    user, upload = create_bom_upload(db, path)

    report = generate_and_save_impact_report(
        db=db,
        bom_upload=upload,
        eco_text=(
            "Replace old part PN-1212 with new part PN-2212. "
            "Reason: supplier obsolescence. Effective date: 2026-08-15."
        ),
        user_id=user.id,
    )

    saved = get_report(db=db, report_id=report.id, user_id=user.id)
    reports = list_reports(db=db, user_id=user.id)
    structured = report_to_structured(report)

    assert isinstance(saved, ImpactReport)
    assert len(reports) == 1
    assert report.risk_level in {"Medium", "High"}
    assert report.affected_part == "PN-1212"
    assert structured.affected_part == "PN-1212"
    assert structured.downstream_records
