from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models.document import DocumentSection
from app.models.user import User
from app.services.bom_importer import get_user_part_catalog, import_bom_upload
from app.services.documents import index_document_upload
from app.tests.conftest import MakeUpload, StubLLMProvider

BOM_ROWS = (
    "Part Number,Description,Parent Assembly,Child Assembly,Revision\n"
    "ASM-1000,Cooling Skid Final Assembly,,ASM-1200,A\n"
    "PN-1211,Stainless manifold block,ASM-1000,,B\n"
    "PN-1212,Pressure relief valve,ASM-1000,,C\n"
)

# No explicit part number anywhere in this text: the regex pass finds nothing.
MANUAL_TEXT = (
    "Cooling Skid Service Manual\n"
    "1. Valve Servicing\n"
    "Replace the pressure relief valve before commissioning the skid.\n"
)


def write_pdf(path: Path, text: str) -> None:
    """Minimal single-page PDF the bundled extractor can read back."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n"
    ).encode()
    path.write_bytes(bytes(out))


@pytest.fixture
def indexed_bom(tmp_path: Path, db_session: Session, user: User, make_upload: MakeUpload):
    bom_path = tmp_path / "bom.csv"
    bom_path.write_text(BOM_ROWS, encoding="utf-8")
    upload = make_upload(user=user, path=bom_path, filename="bom.csv", category="bom")
    import_bom_upload(db=db_session, upload=upload, user_id=user.id)
    return upload


def test_user_part_catalog_carries_descriptions(
    db_session: Session, user: User, indexed_bom
) -> None:
    catalog = get_user_part_catalog(db=db_session, user_id=user.id)

    by_part = {entry.part_number: entry.description for entry in catalog}
    assert by_part["PN-1212"] == "Pressure relief valve"
    assert by_part["PN-1211"] == "Stainless manifold block"


def test_indexing_stores_inferred_references_separately_from_explicit_ones(
    tmp_path: Path,
    db_session: Session,
    user: User,
    make_upload: MakeUpload,
    indexed_bom,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProvider(StubLLMProvider):
        def extract_part_references(self, *, sections, catalog):
            assert any(entry.part_number == "PN-1212" for entry in catalog)
            return {section.section_index: ["PN-1212"] for section in sections}

    monkeypatch.setattr(
        "app.services.part_reference_resolver.get_llm_provider", lambda: FakeProvider()
    )

    manual_path = tmp_path / "service-manual.pdf"
    write_pdf(manual_path, MANUAL_TEXT)
    manual_upload = make_upload(
        user=user, path=manual_path, filename="service-manual.pdf", category="document"
    )

    document = index_document_upload(db=db_session, upload=manual_upload, user_id=user.id)
    sections = db_session.query(DocumentSection).filter_by(document_id=document.id).all()

    assert document.part_references == []
    assert document.inferred_part_references == ["PN-1212"]
    assert any(section.inferred_part_references == ["PN-1212"] for section in sections)


def test_indexing_degrades_to_regex_references_when_provider_unavailable(
    tmp_path: Path,
    db_session: Session,
    user: User,
    make_upload: MakeUpload,
    indexed_bom,
) -> None:
    """The autouse fixture pins the rule-based provider, which infers nothing."""
    manual_path = tmp_path / "explicit-manual.pdf"
    write_pdf(manual_path, "Service Manual\n1. Valve\nInspect PN-1212 for wear.\n")
    manual_upload = make_upload(
        user=user, path=manual_path, filename="explicit-manual.pdf", category="document"
    )

    document = index_document_upload(db=db_session, upload=manual_upload, user_id=user.id)

    assert document.part_references == ["PN-1212"]
    assert document.inferred_part_references == []
