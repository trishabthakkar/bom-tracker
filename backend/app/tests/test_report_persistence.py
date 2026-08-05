from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import DocumentSection, EngineeringDocument
from app.models.report import ImpactReport
from app.models.upload import UploadedFile
from app.models.user import User
from app.services.report_persistence import (
    generate_and_save_impact_report,
    get_report,
    list_reports,
    report_to_structured,
)
from app.tests.conftest import MakeUpload


def create_indexed_document(db: Session, user: User, upload: UploadedFile) -> EngineeringDocument:
    document = EngineeringDocument(
        user_id=user.id,
        upload_id=upload.id,
        filename="service-manual.pdf",
        document_type="service_manual",
        title="Cooling Skid Service Manual",
        status="indexed",
        section_count=1,
        part_references=["PN-1212"],
    )
    db.add(document)
    db.flush()
    db.add(
        DocumentSection(
            document_id=document.id,
            user_id=user.id,
            upload_id=upload.id,
            section_index=1,
            heading="Relief valve replacement",
            content="Replace PN-1212 after isolating the cooling manifold.",
            part_references=["PN-1212"],
        )
    )
    db.commit()
    db.refresh(document)
    return document


def test_generate_and_save_impact_report_persists_report(
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
    create_indexed_document(db, user, upload)

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
    assert len(structured.affected_document_sections) == 1
    assert structured.affected_document_sections[0].heading == "Relief valve replacement"
    assert structured.downstream_records
