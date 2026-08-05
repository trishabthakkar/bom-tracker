from pathlib import Path
from typing import Protocol

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.upload import UploadedFile
from app.models.user import User


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


@pytest.fixture
def user(db_session: Session) -> User:
    new_user = User(email="test@example.com", full_name="Test User", hashed_password="hashed")
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)
    return new_user


class MakeUpload(Protocol):
    def __call__(
        self,
        *,
        user: User,
        path: Path | None = None,
        filename: str = "bom.csv",
        category: str = "bom",
        size_bytes: int = 100,
        storage_path: str | None = None,
    ) -> UploadedFile: ...


@pytest.fixture
def make_upload(db_session: Session) -> MakeUpload:
    """Factory fixture rather than a plain `upload` fixture: callers need a
    real on-disk path (for services that read the file back, e.g.
    import_bom_upload), or a fake placeholder upload with a specific
    filename/category, and pytest fixtures can't take per-test arguments
    directly."""

    def _make_upload(
        *,
        user: User,
        path: Path | None = None,
        filename: str = "bom.csv",
        category: str = "bom",
        size_bytes: int = 100,
        storage_path: str | None = None,
    ) -> UploadedFile:
        extension = path.suffix if path is not None else Path(filename).suffix
        upload = UploadedFile(
            uploader_id=user.id,
            original_filename=filename,
            stored_filename=path.name if path is not None else filename,
            file_extension=extension,
            content_type="application/pdf" if extension == ".pdf" else "text/csv",
            size_bytes=path.stat().st_size if path is not None else size_bytes,
            storage_path=str(path) if path is not None else (storage_path or f"uploads/{filename}"),
            upload_category=category,
            status="stored",
        )
        db_session.add(upload)
        db_session.commit()
        db_session.refresh(upload)
        return upload

    return _make_upload
