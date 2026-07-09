from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models.bom import AssemblyRelationship, BomImport, BomPart
from app.models.eco import EcoRecord
from app.models.graph_snapshot import GraphSnapshot
from app.models.job import Job
from app.models.report import ImpactReport
from app.models.upload import UploadedFile
from app.models.user import User
from app.services.file_storage import PROJECT_ROOT, get_upload_directory


MODELS_IN_DELETE_ORDER = [
    Job,
    ImpactReport,
    GraphSnapshot,
    AssemblyRelationship,
    BomPart,
    EcoRecord,
    BomImport,
    UploadedFile,
    User,
]


def reset_database() -> None:
    with SessionLocal() as db:
        for model in MODELS_IN_DELETE_ORDER:
            db.query(model).delete(synchronize_session=False)
        db.commit()


def clear_upload_files() -> None:
    upload_directories = {
        get_upload_directory(),
        PROJECT_ROOT / "uploads",
    }

    for upload_directory in upload_directories:
        if not upload_directory.exists():
            continue

        for path in upload_directory.iterdir():
            if path.is_file() and not path.name.startswith("."):
                path.unlink()


def main() -> None:
    try:
        reset_database()
    except SQLAlchemyError as error:
        raise SystemExit(
            "Unable to reset data because the database is unavailable. "
            "Start PostgreSQL with `sudo docker compose up -d postgres`, "
            "run `npm run db:migrate`, then rerun `npm run db:reset-data`."
        ) from error

    clear_upload_files()
    print("Development database rows and stored upload files have been cleared.")


if __name__ == "__main__":
    main()
