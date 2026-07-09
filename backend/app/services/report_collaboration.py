from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import ImpactReport, ReportComment


class ReportCollaborationError(ValueError):
    pass


VALID_REVIEW_STATUSES = {"draft", "in_review", "changes_requested", "signed_off"}


def list_report_comments(*, db: Session, report_id: int, user_id: int) -> list[ReportComment]:
    report = db.get(ImpactReport, report_id)
    if report is None or report.user_id != user_id or report.archived_at is not None:
        raise ReportCollaborationError("Impact report was not found.")

    return list(
        db.scalars(
            select(ReportComment)
            .where(ReportComment.report_id == report_id)
            .order_by(ReportComment.created_at.asc())
        )
    )


def add_report_comment(
    *,
    db: Session,
    report: ImpactReport,
    user_id: int,
    body: str,
) -> ReportComment:
    comment = ReportComment(
        report_id=report.id,
        user_id=user_id,
        body=body.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def update_report_review(
    *,
    db: Session,
    report: ImpactReport,
    review_status: str,
    assigned_user_id: int | None,
    signoff_notes: str | None,
) -> ImpactReport:
    if review_status not in VALID_REVIEW_STATUSES:
        raise ReportCollaborationError("Unsupported report review status.")

    now = datetime.utcnow()
    report.review_status = review_status
    report.assigned_user_id = assigned_user_id
    report.signoff_notes = signoff_notes.strip() if signoff_notes else None

    if review_status in {"in_review", "changes_requested", "signed_off"}:
        report.reviewed_at = report.reviewed_at or now
    if review_status == "signed_off":
        report.signed_off_at = now
    else:
        report.signed_off_at = None

    db.add(report)
    db.commit()
    db.refresh(report)
    return report
