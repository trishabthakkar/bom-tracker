from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bom import AssemblyRelationship, BomImport, BomPart
from app.models.graph_snapshot import GraphSnapshot
from app.models.upload import UploadedFile
from app.services.bom_parser import BomParserError, ParsedBomItem, parse_bom_file
from app.services.dependency_graph import build_dependency_graph
from app.services.graph_snapshots import create_graph_snapshot


class BomImportError(ValueError):
    pass


def import_bom_upload(
    *,
    db: Session,
    upload: UploadedFile,
    user_id: int,
) -> tuple[BomImport, GraphSnapshot]:
    if upload.uploader_id != user_id:
        raise BomImportError("Uploaded BOM file was not found.")

    if upload.file_extension not in {".csv", ".xlsx"}:
        raise BomImportError("Only CSV and XLSX uploads can be imported as BOM files.")

    try:
        parsed = parse_bom_file(upload.storage_path)
    except BomParserError as error:
        raise BomImportError(str(error)) from error

    version_label, previous_import_id = _infer_next_version_metadata(
        db=db,
        filename=upload.original_filename,
        user_id=user_id,
    )
    bom_import = BomImport(
        user_id=user_id,
        upload_id=upload.id,
        filename=upload.original_filename,
        version_label=version_label,
        previous_import_id=previous_import_id,
        row_count=len(parsed.rows),
        status="imported",
    )
    db.add(bom_import)
    db.flush()

    db.add_all(_build_part_records(parsed.rows, bom_import, upload, user_id))
    db.add_all(_build_relationship_records(parsed.rows, bom_import, user_id))

    graph = build_dependency_graph(parsed.rows)
    snapshot = create_graph_snapshot(
        db=db,
        graph=graph,
        bom_import=bom_import,
        user_id=user_id,
    )

    db.commit()
    db.refresh(bom_import)
    db.refresh(snapshot)
    return bom_import, snapshot


def list_bom_imports(*, db: Session, user_id: int) -> list[BomImport]:
    return list(
        db.scalars(
            select(BomImport)
            .where(BomImport.user_id == user_id)
            .where(BomImport.archived_at.is_(None))
            .order_by(BomImport.created_at.desc())
        )
    )


def get_bom_import(*, db: Session, import_id: int, user_id: int) -> BomImport | None:
    bom_import = db.get(BomImport, import_id)
    if (
        bom_import is None
        or bom_import.user_id != user_id
        or bom_import.archived_at is not None
    ):
        return None

    return bom_import


def get_latest_bom_import_for_upload(
    *,
    db: Session,
    upload_id: int,
    user_id: int,
) -> BomImport | None:
    return db.scalar(
        select(BomImport)
        .where(BomImport.user_id == user_id)
        .where(BomImport.upload_id == upload_id)
        .where(BomImport.archived_at.is_(None))
        .order_by(BomImport.created_at.desc())
    )


def get_import_parts(*, db: Session, bom_import_id: int, user_id: int) -> list[BomPart]:
    return list(
        db.scalars(
            select(BomPart)
            .where(BomPart.user_id == user_id)
            .where(BomPart.bom_import_id == bom_import_id)
            .order_by(BomPart.row_number.asc())
        )
    )


def get_import_relationships(
    *,
    db: Session,
    bom_import_id: int,
    user_id: int,
) -> list[AssemblyRelationship]:
    return list(
        db.scalars(
            select(AssemblyRelationship)
            .where(AssemblyRelationship.user_id == user_id)
            .where(AssemblyRelationship.bom_import_id == bom_import_id)
            .order_by(AssemblyRelationship.parent_part_number.asc())
        )
    )


def archive_bom_import(*, db: Session, bom_import: BomImport) -> BomImport:
    bom_import.status = "archived"
    bom_import.archived_at = datetime.utcnow()
    db.add(bom_import)
    db.commit()
    db.refresh(bom_import)
    return bom_import


def _build_part_records(
    rows: list[ParsedBomItem],
    bom_import: BomImport,
    upload: UploadedFile,
    user_id: int,
) -> list[BomPart]:
    return [
        BomPart(
            bom_import_id=bom_import.id,
            user_id=user_id,
            upload_id=upload.id,
            row_number=row.row_number,
            part_number=row.part_number,
            description=row.description,
            parent_assembly=row.parent_assembly,
            child_assembly=row.child_assembly,
            revision=row.revision,
        )
        for row in rows
    ]


def _build_relationship_records(
    rows: list[ParsedBomItem],
    bom_import: BomImport,
    user_id: int,
) -> list[AssemblyRelationship]:
    relationships: dict[tuple[str, str], AssemblyRelationship] = {}

    for row in rows:
        if row.parent_assembly and row.child_assembly:
            relationships[(row.parent_assembly, row.child_assembly)] = AssemblyRelationship(
                bom_import_id=bom_import.id,
                user_id=user_id,
                parent_part_number=row.parent_assembly,
                child_part_number=row.child_assembly,
                relationship_type="assembly_to_assembly",
            )

        if row.child_assembly and row.child_assembly != row.part_number:
            relationships[(row.child_assembly, row.part_number)] = AssemblyRelationship(
                bom_import_id=bom_import.id,
                user_id=user_id,
                parent_part_number=row.child_assembly,
                child_part_number=row.part_number,
                relationship_type="assembly_to_part",
            )
        elif row.parent_assembly:
            relationships[(row.parent_assembly, row.part_number)] = AssemblyRelationship(
                bom_import_id=bom_import.id,
                user_id=user_id,
                parent_part_number=row.parent_assembly,
                child_part_number=row.part_number,
                relationship_type="assembly_to_part",
            )

    return list(relationships.values())


def _infer_next_version_metadata(
    *,
    db: Session,
    filename: str,
    user_id: int,
) -> tuple[str, int | None]:
    imports = list(
        db.scalars(
            select(BomImport)
            .where(BomImport.user_id == user_id)
            .where(BomImport.filename == filename)
            .where(BomImport.archived_at.is_(None))
            .order_by(BomImport.created_at.desc())
        )
    )
    previous = imports[0] if imports else None
    return f"v{len(imports) + 1}", previous.id if previous else None
