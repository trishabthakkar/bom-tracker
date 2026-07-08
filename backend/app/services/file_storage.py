from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".pdf"}
ALLOWED_MIME_TYPES = {
    ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"},
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
    ".pdf": {"application/pdf", "application/octet-stream"},
}
CHUNK_SIZE_BYTES = 1024 * 1024
BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class StoredFile:
    def __init__(
        self,
        *,
        original_filename: str,
        stored_filename: str,
        file_extension: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
    ) -> None:
        self.original_filename = original_filename
        self.stored_filename = stored_filename
        self.file_extension = file_extension
        self.content_type = content_type
        self.size_bytes = size_bytes
        self.storage_path = storage_path


def validate_upload_category(upload_category: str) -> str:
    normalized = upload_category.strip().lower()
    if normalized not in {"bom", "eco", "document"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload category must be one of: bom, eco, document.",
        )
    return normalized


def get_upload_directory() -> Path:
    upload_directory = Path(settings.upload_directory)
    if upload_directory.is_absolute():
        return upload_directory

    return BACKEND_ROOT / upload_directory


def resolve_storage_path(storage_path: str | Path) -> Path:
    path = Path(storage_path)
    if path.is_absolute():
        return path

    candidates = [
        Path.cwd() / path,
        BACKEND_ROOT / path,
        PROJECT_ROOT / path,
    ]

    if path.name:
        candidates.extend(
            [
                get_upload_directory() / path.name,
                PROJECT_ROOT / "uploads" / path.name,
                BACKEND_ROOT / "uploads" / path.name,
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


async def store_upload(file: UploadFile) -> StoredFile:
    original_filename = Path(file.filename or "").name
    extension = Path(original_filename).suffix.lower()
    content_type = file.content_type or "application/octet-stream"

    if not original_filename or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV, XLSX, and PDF files are supported.",
        )

    if content_type not in ALLOWED_MIME_TYPES[extension]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid content type for {extension} upload.",
        )

    upload_directory = get_upload_directory()
    upload_directory.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{extension}"
    storage_path = upload_directory / stored_filename
    size_bytes = 0

    try:
        with storage_path.open("wb") as output:
            while chunk := await file.read(CHUNK_SIZE_BYTES):
                size_bytes += len(chunk)
                if size_bytes > settings.max_upload_size_bytes:
                    output.close()
                    storage_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds the {settings.max_upload_size_mb} MB upload limit.",
                    )
                output.write(chunk)
    finally:
        await file.close()

    if size_bytes == 0:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    try:
        stored_path_value = str(storage_path.relative_to(BACKEND_ROOT))
    except ValueError:
        stored_path_value = str(storage_path)

    return StoredFile(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_extension=extension,
        content_type=content_type,
        size_bytes=size_bytes,
        storage_path=stored_path_value,
    )
