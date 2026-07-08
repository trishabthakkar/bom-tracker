from pathlib import Path

from pypdf import PdfReader

from app.services.file_storage import resolve_storage_path


class PdfTextExtractionError(ValueError):
    pass


def extract_pdf_text(path: str | Path) -> str:
    file_path = resolve_storage_path(path)

    if not file_path.exists():
        raise PdfTextExtractionError("Uploaded PDF file is no longer available. Re-upload the file and try again.")

    try:
        reader = PdfReader(str(file_path))
    except Exception as error:
        raise PdfTextExtractionError("Unable to read PDF file.") from error

    page_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(page_text).strip()

    if not text:
        raise PdfTextExtractionError("PDF does not contain extractable text.")

    return text
