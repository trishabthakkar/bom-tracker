from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.report import (
    ImpactReportDetail,
    ImpactReportListResponse,
    ImpactReportRead,
    PersistedImpactReportRequest,
)
from app.services.report_persistence import (
    ReportPersistenceError,
    archive_report,
    generate_and_save_impact_report,
    get_report,
    list_reports,
    report_to_structured,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/impact-report", response_model=ImpactReportDetail)
def create_impact_report(
    payload: PersistedImpactReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImpactReportDetail:
    upload = db.get(UploadedFile, payload.bom_upload_id)

    if upload is None or upload.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded BOM file was not found.",
        )

    try:
        report = generate_and_save_impact_report(
            db=db,
            bom_upload=upload,
            eco_text=payload.eco_text,
            user_id=current_user.id,
        )
    except ReportPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _report_detail(report)


@router.get("", response_model=ImpactReportListResponse)
def read_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImpactReportListResponse:
    return ImpactReportListResponse(
        reports=[
            ImpactReportRead.model_validate(report)
            for report in list_reports(db=db, user_id=current_user.id)
        ]
    )


@router.get("/{report_id}", response_model=ImpactReportDetail)
def read_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImpactReportDetail:
    report = get_report(db=db, report_id=report_id, user_id=current_user.id)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact report was not found.",
        )

    return _report_detail(report)


@router.delete("/{report_id}", response_model=ImpactReportRead)
def archive_saved_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImpactReportRead:
    report = get_report(db=db, report_id=report_id, user_id=current_user.id)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact report was not found.",
        )

    return ImpactReportRead.model_validate(archive_report(db=db, report=report))


def _report_detail(report) -> ImpactReportDetail:
    return ImpactReportDetail(
        **ImpactReportRead.model_validate(report).model_dump(),
        report=report_to_structured(report),
    )
