from app.services.report_exports import MAX_PDF_LINES, _simple_pdf


def test_simple_pdf_stays_under_the_line_cap_untruncated() -> None:
    lines = [f"line {index}" for index in range(10)]

    pdf_bytes = _simple_pdf(lines)

    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"more line" not in pdf_bytes


def test_simple_pdf_truncates_content_past_the_line_cap() -> None:
    lines = [f"line {index}" for index in range(MAX_PDF_LINES + 20)]

    pdf_bytes = _simple_pdf(lines)

    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"20 more line" in pdf_bytes
    assert b"CSV export" in pdf_bytes
