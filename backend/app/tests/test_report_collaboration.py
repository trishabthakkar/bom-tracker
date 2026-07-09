from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.eco import EcoRecord
from app.models.report import ImpactReport
from app.models.upload import UploadedFile
from app.models.user import User
from app.services.report_collaboration import add_report_comment, update_report_review
from app.services.report_exports import report_csv_bytes, report_pdf_bytes
from app.services.report_persistence import generate_and_save_impact_report_from_eco_record


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


def create_user_upload_and_eco(db: Session, path: Path) -> tuple[User, UploadedFile, EcoRecord]:
    user = User(
        email="collab@example.com",
        full_name="Collab User",
        hashed_password="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

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

    eco = EcoRecord(
        user_id=user.id,
        upload_id=None,
        source_type="text",
        source_text="Replace PN-1212 with PN-2212.",
        change_type="replacement",
        old_part="PN-1212",
        new_part="PN-2212",
        reason="Supplier obsolescence",
        effective_date=date(2026, 8, 15),
        parser_source="rule_based",
        confidence=0.9,
        workflow_status="approved",
    )
    db.add(eco)
    db.commit()
    db.refresh(eco)
    return user, upload, eco


def test_report_from_approved_eco_can_be_reviewed_commented_and_exported(tmp_path: Path) -> None:
    path = tmp_path / "bom.csv"
    path.write_text(
        "Part Number,Description,Parent Assembly,Child Assembly,Revision\n"
        "PN-1212,Pressure relief valve,ASM-1000,ASM-1210,C\n",
        encoding="utf-8",
    )
    db = build_session()
    user, upload, eco = create_user_upload_and_eco(db, path)

    report = generate_and_save_impact_report_from_eco_record(
        db=db,
        bom_upload=upload,
        eco_record=eco,
        user_id=user.id,
    )
    comment = add_report_comment(
        db=db,
        report=report,
        user_id=user.id,
        body="Ready for final review.",
    )
    reviewed = update_report_review(
        db=db,
        report=report,
        review_status="signed_off",
        assigned_user_id=user.id,
        signoff_notes="Approved for release.",
    )

    csv_bytes = report_csv_bytes(reviewed)
    pdf_bytes = report_pdf_bytes(reviewed)

    assert isinstance(reviewed, ImpactReport)
    assert report.eco_record_id == eco.id
    assert reviewed.review_status == "signed_off"
    assert reviewed.signed_off_at is not None
    assert comment.body == "Ready for final review."
    assert b"Impact Report" in csv_bytes
    assert pdf_bytes.startswith(b"%PDF-1.4")
