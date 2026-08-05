from sqlalchemy.orm import Session

from app.api.v1.uploads import _mark_matching_uploads_replaced
from app.models.bom import BomImport
from app.models.report import ImpactReport
from app.models.user import User
from app.tests.conftest import MakeUpload


def test_mark_matching_uploads_replaced_archives_dependent_bom_records(
    db_session: Session, user: User, make_upload: MakeUpload
) -> None:
    db = db_session
    upload = make_upload(
        user=user,
        filename="demo-bom.csv",
        storage_path="uploads/stored-demo-bom.csv",
    )

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
