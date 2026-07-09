import re
from dataclasses import dataclass

SECTION_HEADING_PATTERN = re.compile(
    r"^(?:section\s+)?\d+(?:\.\d+)*[\).\s-]+.+$|^[A-Z][A-Z0-9 /,&()_-]{6,}$",
    flags=re.IGNORECASE,
)
PART_REFERENCE_PATTERN = re.compile(
    r"\b(?:PN[\s_-]?\d{3,}|[A-Z][A-Z0-9]+[\s_-]\d{3,})\b",
    flags=re.IGNORECASE,
)


class DocumentParserError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedDocumentSection:
    section_index: int
    heading: str
    content: str
    part_references: list[str]


@dataclass(frozen=True)
class ParsedDocument:
    title: str | None
    sections: list[ParsedDocumentSection]
    part_references: list[str]


def parse_document_text(text: str) -> ParsedDocument:
    cleaned = text.strip()
    if not cleaned:
        raise DocumentParserError("Document does not contain extractable text.")

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        raise DocumentParserError("Document does not contain extractable text.")

    title = lines[0][:255] if lines else None
    body_lines = lines[1:] if len(lines) > 1 else lines
    section_blocks = _split_sections(body_lines)
    sections = [
        ParsedDocumentSection(
            section_index=index,
            heading=heading[:255],
            content=content,
            part_references=extract_part_references(content),
        )
        for index, (heading, content) in enumerate(section_blocks, start=1)
    ]

    if not sections:
        sections = [
            ParsedDocumentSection(
                section_index=1,
                heading=title or "Document",
                content=cleaned,
                part_references=extract_part_references(cleaned),
            )
        ]

    part_references = sorted({part for section in sections for part in section.part_references})
    return ParsedDocument(title=title, sections=sections, part_references=part_references)


def extract_part_references(text: str) -> list[str]:
    return sorted({_normalize_part(match.group(0)) for match in re.finditer(PART_REFERENCE_PATTERN, text)})


def _split_sections(lines: list[str]) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    current_heading = "Overview"
    current_lines: list[str] = []

    for line in lines:
        if _looks_like_heading(line) and current_lines:
            sections.append((current_heading, current_lines))
            current_heading = line
            current_lines = []
            continue

        if _looks_like_heading(line) and not current_lines and current_heading == "Overview":
            current_heading = line
            continue

        current_lines.append(line)

    if current_lines:
        sections.append((current_heading, current_lines))

    return [
        (heading, "\n".join(content_lines).strip())
        for heading, content_lines in sections
        if "\n".join(content_lines).strip()
    ]


def _looks_like_heading(line: str) -> bool:
    if len(line) > 100:
        return False

    return bool(SECTION_HEADING_PATTERN.match(line))


def _normalize_part(value: str) -> str:
    normalized = value.upper().replace(" ", "-").replace("_", "-")
    if normalized.startswith("PN") and not normalized.startswith("PN-"):
        return f"PN-{normalized[2:]}"
    return normalized
