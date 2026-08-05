from pathlib import Path

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.bom_importer import (
    get_import_parts,
    get_import_relationships,
    import_bom_upload,
)
from app.tests.conftest import MakeUpload


def test_import_bom_upload_persists_parts_relationships_and_graph(
    tmp_path: Path, db_session: Session, user: User, make_upload: MakeUpload
) -> None:
    path = tmp_path / "bom.csv"
    path.write_text(
        "Part Number,Description,Parent Assembly,Child Assembly,Revision\n"
        "PN-100,Valve,ASM-ROOT,ASM-CHILD,A\n"
        "PN-200,Sensor,ASM-CHILD,,B\n",
        encoding="utf-8",
    )
    db = db_session
    upload = make_upload(user=user, path=path)

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
