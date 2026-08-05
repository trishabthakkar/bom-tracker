from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.eco import EcoRecord
from app.models.report import ImpactReport
from app.models.user import User
from app.services.report_collaboration import add_report_comment, update_report_review
from app.services.report_exports import report_csv_bytes, report_pdf_bytes
from app.services.report_persistence import generate_and_save_impact_report_from_eco_record
from app.tests.conftest import MakeUpload


def create_eco(db: Session, user: User) -> EcoRecord:
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
    return eco


def test_report_from_approved_eco_can_be_reviewed_commented_and_exported(
    tmp_path: Path, db_session: Session, user: User, make_upload: MakeUpload
) -> None:
    path = tmp_path / "bom.csv"
    path.write_text(
        "Part Number,Description,Parent Assembly,Child Assembly,Revision\n"
        "PN-1212,Pressure relief valve,ASM-1000,ASM-1210,C\n",
        encoding="utf-8",
    )
    db = db_session
    upload = make_upload(user=user, path=path)
    eco = create_eco(db, user)

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
