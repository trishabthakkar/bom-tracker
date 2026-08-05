from sqlalchemy.orm import Session

from app.api.v1.documents import read_affected_document_sections
from app.models.document import DocumentSection, EngineeringDocument
from app.models.user import User
from app.tests.conftest import MakeUpload


def test_read_affected_document_sections_returns_matches(
    db_session: Session, user: User, make_upload: MakeUpload
) -> None:
    db = db_session
    upload = make_upload(
        user=user,
        filename="service-manual.pdf",
        category="document",
        storage_path="uploads/service-manual.pdf",
    )

    document = EngineeringDocument(
        user_id=user.id,
        upload_id=upload.id,
        filename=upload.original_filename,
        document_type="service_manual",
        title="Service Manual",
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
            content="Replace PN-1212 after isolating the manifold.",
            part_references=["PN-1212"],
        )
    )
    db.commit()

    response = read_affected_document_sections(
        part_number="PN-1212",
        db=db,
        current_user=user,
    )

    assert response.part_number == "PN-1212"
    assert response.sections[0].heading == "Relief valve replacement"
    assert response.sections[0].matched_parts == ["PN-1212"]
