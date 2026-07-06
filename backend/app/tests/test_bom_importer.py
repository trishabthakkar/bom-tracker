from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.upload import UploadedFile
from app.models.user import User
from app.services.bom_importer import (
    get_import_parts,
    get_import_relationships,
    import_bom_upload,
)


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


def create_upload(db: Session, path: Path) -> tuple[User, UploadedFile]:
    user = User(
        email="importer@example.com",
        full_name="Importer",
        hashed_password="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    upload = UploadedFile(
        uploader_id=user.id,
        original_filename="bom.csv",
        stored_filename="bom.csv",
        file_extension=".csv",
        content_type="text/csv",
        size_bytes=path.stat().st_size,
        storage_path=str(path),
        upload_category="bom",
        status="stored",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return user, upload


def test_import_bom_upload_persists_parts_relationships_and_graph(tmp_path: Path) -> None:
    path = tmp_path / "bom.csv"
    path.write_text(
        "Part Number,Description,Parent Assembly,Child Assembly,Revision\n"
        "PN-100,Valve,ASM-ROOT,ASM-CHILD,A\n"
        "PN-200,Sensor,ASM-CHILD,,B\n",
        encoding="utf-8",
    )
    db = build_session()
    user, upload = create_upload(db, path)

    bom_import, snapshot = import_bom_upload(db=db, upload=upload, user_id=user.id)

    parts = get_import_parts(db=db, bom_import_id=bom_import.id, user_id=user.id)
    relationships = get_import_relationships(
        db=db,
        bom_import_id=bom_import.id,
        user_id=user.id,
    )

    assert bom_import.row_count == 2
    assert len(parts) == 2
    assert {part.part_number for part in parts} == {"PN-100", "PN-200"}
    assert snapshot.node_count == 4
    assert snapshot.edge_count == 3
    assert {(item.parent_part_number, item.child_part_number) for item in relationships} == {
        ("ASM-ROOT", "ASM-CHILD"),
        ("ASM-CHILD", "PN-100"),
        ("ASM-CHILD", "PN-200"),
    }
