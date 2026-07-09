from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.bom import BomImport, BomPart
from app.models.user import User
from app.services.bom_diff import compare_bom_imports


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()


def create_user(db: Session) -> User:
    user = User(email="diff@example.com", full_name="Diff User", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_import(db: Session, user: User, import_id_offset: int, parts: list[dict]) -> BomImport:
    bom_import = BomImport(
        user_id=user.id,
        upload_id=import_id_offset,
        filename="demo-bom.csv",
        version_label=f"v{import_id_offset}",
        row_count=len(parts),
        status="imported",
    )
    db.add(bom_import)
    db.flush()

    db.add_all(
        [
            BomPart(
                bom_import_id=bom_import.id,
                user_id=user.id,
                upload_id=import_id_offset,
                row_number=index,
                part_number=part["part_number"],
                description=part.get("description"),
                parent_assembly=part.get("parent_assembly"),
                child_assembly=part.get("child_assembly"),
                revision=part.get("revision"),
            )
            for index, part in enumerate(parts, start=1)
        ]
    )
    db.commit()
    db.refresh(bom_import)
    return bom_import


def test_compare_bom_imports_detects_added_removed_revised_and_replacements() -> None:
    db = build_session()
    user = create_user(db)
    base = create_import(
        db,
        user,
        1,
        [
            {
                "part_number": "PN-100",
                "description": "Pressure relief valve",
                "parent_assembly": "ASM-1",
                "revision": "A",
            },
            {
                "part_number": "PN-200",
                "description": "Cooling hose",
                "parent_assembly": "ASM-2",
                "revision": "A",
            },
        ],
    )
    target = create_import(
        db,
        user,
        2,
        [
            {
                "part_number": "PN-100",
                "description": "Pressure relief valve",
                "parent_assembly": "ASM-1",
                "revision": "B",
            },
            {
                "part_number": "PN-300",
                "description": "Cooling hose reinforced",
                "parent_assembly": "ASM-2",
                "revision": "A",
            },
        ],
    )

    diff = compare_bom_imports(
        db=db,
        user_id=user.id,
        base_import_id=base.id,
        target_import_id=target.id,
    )

    assert diff.summary.added_count == 1
    assert diff.summary.removed_count == 1
    assert diff.summary.revised_count == 1
    assert diff.summary.replacement_candidate_count == 1
    assert diff.added_parts[0].part_number == "PN-300"
    assert diff.removed_parts[0].part_number == "PN-200"
    assert diff.revised_parts[0].part_number == "PN-100"
