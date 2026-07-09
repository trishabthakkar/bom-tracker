from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.eco import EcoRecord
from app.models.user import User
from app.services.eco_records import approve_eco_record, reject_eco_record, update_eco_record


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


def create_record(db: Session) -> EcoRecord:
    user = User(email="eco-flow@example.com", full_name="ECO Flow", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    record = EcoRecord(
        user_id=user.id,
        upload_id=None,
        source_type="text",
        source_text="Replace PN-1 with PN-2.",
        change_type="replacement",
        old_part="PN-1",
        new_part="PN-2",
        reason="Obsolescence",
        effective_date=date(2026, 8, 15),
        parser_source="rule_based",
        confidence=0.8,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_update_eco_record_marks_record_reviewed() -> None:
    db = build_session()
    record = create_record(db)

    updated = update_eco_record(
        db=db,
        record=record,
        change_type="replacement",
        old_part="pn-100",
        new_part="pn-200",
        reason="Supplier obsolescence",
        effective_date=date(2026, 9, 1),
        correction_notes="Corrected part numbers.",
    )

    assert updated.workflow_status == "reviewed"
    assert updated.old_part == "PN-100"
    assert updated.new_part == "PN-200"
    assert updated.reviewed_at is not None


def test_approve_and_reject_eco_record_set_decision_timestamps() -> None:
    db = build_session()
    record = create_record(db)

    approved = approve_eco_record(db=db, record=record, notes="Looks good.")

    assert approved.workflow_status == "approved"
    assert approved.approved_at is not None
    assert approved.rejected_at is None

    rejected = reject_eco_record(db=db, record=approved, notes="Superseded.")

    assert rejected.workflow_status == "rejected"
    assert rejected.rejected_at is not None
    assert rejected.approved_at is None
