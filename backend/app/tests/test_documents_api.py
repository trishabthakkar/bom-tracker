from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.api.v1.documents import read_affected_document_sections
from app.models.document import DocumentSection, EngineeringDocument
from app.models.upload import UploadedFile
from app.models.user import User


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


def test_read_affected_document_sections_returns_matches() -> None:
    db = build_session()
    user = User(
        email="docs@example.com",
        full_name="Docs User",
        hashed_password="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    upload = UploadedFile(
        uploader_id=user.id,
        original_filename="service-manual.pdf",
        stored_filename="service-manual.pdf",
        file_extension=".pdf",
        content_type="application/pdf",
        size_bytes=100,
        storage_path="uploads/service-manual.pdf",
        upload_category="document",
        status="stored",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

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
