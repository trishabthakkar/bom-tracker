import csv
import io
from datetime import datetime

from app.models.report import ImpactReport
from app.services.report_persistence import report_to_structured


def report_csv_bytes(report: ImpactReport) -> bytes:
    structured = report_to_structured(report)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Section", "Field", "Value"])
    writer.writerow(["Export", "Type", "Impact Report"])
    writer.writerow(["Summary", "Report ID", report.id])
    writer.writerow(["Summary", "Affected part", report.affected_part or ""])
    writer.writerow(["Summary", "Effective date", report.effective_date or ""])
    writer.writerow(["Summary", "Risk level", report.risk_level])
    writer.writerow(["Summary", "Risk score", report.risk_score])
    writer.writerow(["Summary", "Review status", report.review_status])
    writer.writerow(["Summary", "Generated at", report.created_at.isoformat()])

    for reason in structured.risk.reasons:
        writer.writerow(["Risk reason", "", reason])

    for assembly in structured.affected_assemblies:
        writer.writerow(["Affected assembly", "Part number", assembly.part_number])
        writer.writerow(["Affected assembly", "Parents", ", ".join(assembly.affected_parents)])
        writer.writerow(["Affected assembly", "Children", ", ".join(assembly.affected_children)])

    for record in structured.downstream_records:
        writer.writerow(["Downstream record", record.record_type, f"{record.severity}: {record.impact}"])

    for section in structured.affected_document_sections:
        writer.writerow(
            [
                "Document section",
                section.filename,
                f"{section.heading} | parts: {', '.join(section.matched_parts)} | {section.excerpt}",
            ]
        )

    for update in structured.suggested_updates:
        writer.writerow(["Suggested update", update.area, f"{update.priority}: {update.action}"])

    return output.getvalue().encode("utf-8")


def report_pdf_bytes(report: ImpactReport) -> bytes:
    structured = report_to_structured(report)
    lines = [
        f"Impact Report #{report.id}",
        f"Generated: {report.created_at.isoformat()}",
        f"Review status: {report.review_status}",
        f"Risk: {report.risk_level} ({report.risk_score}/100)",
        f"Affected part: {report.affected_part or '-'}",
        "",
        "Summary",
        _wrap_line(report.summary),
        "",
        "Risk Reasons",
        *[f"- {reason}" for reason in structured.risk.reasons],
        "",
        "Suggested Updates",
        *[f"- {update.area}: {update.action}" for update in structured.suggested_updates],
    ]

    if structured.affected_document_sections:
        lines.extend(
            [
                "",
                "Affected Document Sections",
                *[
                    f"- {section.filename} / {section.heading}: {', '.join(section.matched_parts)}"
                    for section in structured.affected_document_sections
                ],
            ]
        )

    return _simple_pdf(lines)


def export_filename(report: ImpactReport, extension: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    return f"impact-report-{report.id}-{timestamp}.{extension}"


def _simple_pdf(lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 10 Tf", "50 770 Td", "14 TL"]
    for line in lines:
        for wrapped in _split_for_pdf(line):
            content_lines.append(f"({_escape_pdf_text(wrapped)}) Tj")
            content_lines.append("T*")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    pdf = io.BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(pdf.tell())
        pdf.write(f"{index} 0 obj\n".encode())
        pdf.write(obj)
        pdf.write(b"\nendobj\n")

    xref_start = pdf.tell()
    pdf.write(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode())
    pdf.write(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode()
    )
    return pdf.getvalue()


def _split_for_pdf(line: str, width: int = 92) -> list[str]:
    if not line:
        return [""]
    words = line.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_line(value: str) -> str:
    return " ".join(value.split())
