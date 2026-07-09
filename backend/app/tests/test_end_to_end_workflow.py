from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.document import DocumentSection, EngineeringDocument
from app.models.upload import UploadedFile
from app.models.user import User
from app.services.bom_diff import compare_bom_imports
from app.services.bom_importer import import_bom_upload
from app.services.eco_records import approve_eco_record, parse_text_and_create_eco_record
from app.services.report_collaboration import add_report_comment, update_report_review
from app.services.report_exports import report_csv_bytes, report_pdf_bytes
from app.services.report_persistence import (
    generate_and_save_impact_report_from_eco_record,
    report_to_structured,
)


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


def create_user(db: Session) -> User:
    user = User(
        email="phase20@example.com",
        full_name="Phase 20 QA",
        hashed_password="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_upload(
    *,
    db: Session,
    user: User,
    path: Path,
    filename: str,
    category: str,
) -> UploadedFile:
    upload = UploadedFile(
        uploader_id=user.id,
        original_filename=filename,
        stored_filename=path.name,
        file_extension=path.suffix,
        content_type="text/csv" if path.suffix == ".csv" else "application/pdf",
        size_bytes=path.stat().st_size,
        storage_path=str(path),
        upload_category=category,
        status="stored",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def write_bom(path: Path, rows: list[str]) -> None:
    path.write_text(
        "Part Number,Description,Parent Assembly,Child Assembly,Revision\n"
        + "\n".join(rows)
        + "\n",
        encoding="utf-8",
    )


def index_service_manual(db: Session, user: User, upload: UploadedFile) -> EngineeringDocument:
    document = EngineeringDocument(
        user_id=user.id,
        upload_id=upload.id,
        filename=upload.original_filename,
        document_type="service_manual",
        title="Cooling Skid Service Manual",
        status="indexed",
        section_count=1,
        part_references=["PN-1212", "PN-2212"],
    )
    db.add(document)
    db.flush()
    db.add(
        DocumentSection(
            document_id=document.id,
            user_id=user.id,
            upload_id=upload.id,
            section_index=1,
            heading="Pressure Relief Valve Replacement",
            content=(
                "Before commissioning, verify PN-1212 pressure relief valve seating. "
                "Future revisions may reference PN-2212."
            ),
            part_references=["PN-1212", "PN-2212"],
        )
    )
    db.commit()
    db.refresh(document)
    return document


def test_complete_bom_eco_report_workflow_with_diff_documents_and_exports(tmp_path: Path) -> None:
    db = build_session()
    user = create_user(db)

    base_path = tmp_path / "demo-bom.csv"
    target_path = tmp_path / "demo-bom-v2.csv"
    manual_path = tmp_path / "service-manual.pdf"
    write_bom(
        base_path,
        [
            "ASM-1000,Cooling Skid Final Assembly,,ASM-1200,A",
            "ASM-1200,Cooling Manifold Assembly,ASM-1000,ASM-1210,B",
            "PN-1211,Stainless manifold block,ASM-1210,,B",
            "PN-1212,Pressure relief valve,ASM-1210,,C",
            "PN-1213,Temperature sensor,ASM-1210,,A",
        ],
    )
    write_bom(
        target_path,
        [
            "ASM-1000,Cooling Skid Final Assembly,,ASM-1200,B",
            "ASM-1200,Cooling Manifold Assembly,ASM-1000,ASM-1210,C",
            "PN-1211,Stainless manifold block,ASM-1210,,B",
            "PN-2212,Pressure relief valve reinforced,ASM-1210,,A",
            "PN-1213,Temperature sensor,ASM-1210,,B",
        ],
    )
    manual_path.write_bytes(b"%PDF-1.4\n% qa placeholder\n")

    base_upload = create_upload(
        db=db,
        user=user,
        path=base_path,
        filename="demo-bom.csv",
        category="bom",
    )
    target_upload = create_upload(
        db=db,
        user=user,
        path=target_path,
        filename="demo-bom.csv",
        category="bom",
    )
    manual_upload = create_upload(
        db=db,
        user=user,
        path=manual_path,
        filename="service-manual.pdf",
        category="document",
    )

    base_import, base_snapshot = import_bom_upload(
        db=db,
        upload=base_upload,
        user_id=user.id,
    )
    target_import, target_snapshot = import_bom_upload(
        db=db,
        upload=target_upload,
        user_id=user.id,
    )
    diff = compare_bom_imports(
        db=db,
        user_id=user.id,
        base_import_id=base_import.id,
        target_import_id=target_import.id,
    )
    index_service_manual(db, user, manual_upload)

    eco = parse_text_and_create_eco_record(
        db=db,
        user_id=user.id,
        text=(
            "Replace old part PN-1212 with new part PN-2212. "
            "Reason: supplier obsolescence. Effective date: 2026-08-15."
        ),
    )
    approved_eco = approve_eco_record(
        db=db,
        record=eco,
        notes="Approved for QA workflow coverage.",
    )
    report = generate_and_save_impact_report_from_eco_record(
        db=db,
        bom_upload=base_upload,
        eco_record=approved_eco,
        user_id=user.id,
    )
    comment = add_report_comment(
        db=db,
        report=report,
        user_id=user.id,
        body="QA workflow generated successfully.",
    )
    signed_report = update_report_review(
        db=db,
        report=report,
        review_status="signed_off",
        assigned_user_id=user.id,
        signoff_notes="Ready for pilot demo.",
    )
    structured = report_to_structured(signed_report)

    assert base_import.version_label == "v1"
    assert target_import.version_label == "v2"
    assert target_import.previous_import_id == base_import.id
    assert base_snapshot.node_count >= 4
    assert target_snapshot.edge_count >= 4
    assert diff.summary.added_count == 1
    assert diff.summary.removed_count == 1
    assert diff.summary.revised_count >= 2
    assert diff.summary.replacement_candidate_count == 1
    assert diff.replacement_candidates[0].removed_part.part_number == "PN-1212"
    assert diff.replacement_candidates[0].added_part.part_number == "PN-2212"
    assert approved_eco.workflow_status == "approved"
    assert approved_eco.old_part == "PN-1212"
    assert approved_eco.new_part == "PN-2212"
    assert approved_eco.effective_date == date(2026, 8, 15)
    assert signed_report.review_status == "signed_off"
    assert signed_report.signed_off_at is not None
    assert signed_report.eco_record_id == approved_eco.id
    assert comment.body == "QA workflow generated successfully."
    assert structured.affected_part == "PN-1212"
    assert structured.affected_assemblies[0].affected_parents == [
        "ASM-1000",
        "ASM-1200",
        "ASM-1210",
    ]
    assert structured.affected_document_sections[0].document_type == "service_manual"
    assert structured.risk.level == "High"
    assert b"Impact Report" in report_csv_bytes(signed_report)
    assert report_pdf_bytes(signed_report).startswith(b"%PDF-1.4")
