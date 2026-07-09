from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.eco import EcoRecord
from app.models.upload import UploadedFile
from app.models.user import User
from app.schemas.report import (
    ImpactReportDetail,
    ImpactReportListResponse,
    ImpactReportRead,
    PersistedImpactReportRequest,
    ReportCommentCreateRequest,
    ReportCommentRead,
    ReportReviewUpdateRequest,
)
from app.services.report_collaboration import (
    ReportCollaborationError,
    add_report_comment,
    list_report_comments,
    update_report_review,
)
from app.services.report_exports import export_filename, report_csv_bytes, report_pdf_bytes
from app.services.report_persistence import (
    ReportPersistenceError,
    archive_report,
    generate_and_save_impact_report,
    generate_and_save_impact_report_from_eco_record,
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
        if payload.eco_record_id is not None:
            eco_record = db.get(EcoRecord, payload.eco_record_id)
            if eco_record is None or eco_record.user_id != current_user.id:
                raise ReportPersistenceError("ECO record was not found.")
            report = generate_and_save_impact_report_from_eco_record(
                db=db,
                bom_upload=upload,
                eco_record=eco_record,
                user_id=current_user.id,
            )
        else:
            report = generate_and_save_impact_report(
                db=db,
                bom_upload=upload,
                eco_text=payload.eco_text or "",
                user_id=current_user.id,
            )
    except ReportPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _report_detail(db=db, report=report)


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
    report = _get_owned_report(db=db, report_id=report_id, user_id=current_user.id)

    return _report_detail(db=db, report=report)


@router.get("/{report_id}/export.csv")
def export_report_csv(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    report = _get_owned_report(db=db, report_id=report_id, user_id=current_user.id)
    return Response(
        content=report_csv_bytes(report),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{export_filename(report, "csv")}"'},
    )


@router.get("/{report_id}/export.pdf")
def export_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    report = _get_owned_report(db=db, report_id=report_id, user_id=current_user.id)
    return Response(
        content=report_pdf_bytes(report),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{export_filename(report, "pdf")}"'},
    )


@router.patch("/{report_id}/review", response_model=ImpactReportDetail)
def update_report_review_status(
    report_id: int,
    payload: ReportReviewUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImpactReportDetail:
    report = _get_owned_report(db=db, report_id=report_id, user_id=current_user.id)
    try:
        updated = update_report_review(
            db=db,
            report=report,
            review_status=payload.review_status,
            assigned_user_id=payload.assigned_user_id,
            signoff_notes=payload.signoff_notes,
        )
    except ReportCollaborationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return _report_detail(db=db, report=updated)


@router.post("/{report_id}/comments", response_model=ReportCommentRead, status_code=status.HTTP_201_CREATED)
def create_report_comment(
    report_id: int,
    payload: ReportCommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportCommentRead:
    report = _get_owned_report(db=db, report_id=report_id, user_id=current_user.id)
    return ReportCommentRead.model_validate(
        add_report_comment(
            db=db,
            report=report,
            user_id=current_user.id,
            body=payload.body,
        )
    )


@router.delete("/{report_id}", response_model=ImpactReportRead)
def archive_saved_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImpactReportRead:
    report = _get_owned_report(db=db, report_id=report_id, user_id=current_user.id)

    return ImpactReportRead.model_validate(archive_report(db=db, report=report))


def _get_owned_report(*, db: Session, report_id: int, user_id: int):
    report = get_report(db=db, report_id=report_id, user_id=user_id)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact report was not found.",
        )

    return report


def _report_detail(*, db: Session, report) -> ImpactReportDetail:
    return ImpactReportDetail(
        **ImpactReportRead.model_validate(report).model_dump(),
        report=report_to_structured(report),
        comments=[
            ReportCommentRead.model_validate(comment)
            for comment in list_report_comments(
                db=db,
                report_id=report.id,
                user_id=report.user_id,
            )
        ],
    )
