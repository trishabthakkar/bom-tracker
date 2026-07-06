import re
from datetime import date, datetime

from app.schemas.eco import ParsedEngineeringChange
from app.services.llm.base import BaseLLMProvider

PART_PATTERN = r"[A-Z]{1,8}[-_ ]?\d{2,8}[A-Z]?"


class RuleBasedLLMProvider(BaseLLMProvider):
    """Local provider that mimics an LLM extraction contract without external calls."""

    def parse_engineering_change(self, text: str) -> ParsedEngineeringChange:
        normalized = " ".join(text.split())

        return ParsedEngineeringChange(
            change_type=_extract_change_type(normalized),
            old_part=_extract_labeled_part(normalized, ["old part", "from part", "replace"]),
            new_part=_extract_labeled_part(normalized, ["new part", "to part", "with"]),
            reason=_extract_reason(normalized),
            effective_date=_extract_effective_date(normalized),
            source="rule_based",
            confidence=_calculate_confidence(normalized),
        )


def _extract_change_type(text: str) -> str | None:
    lowered = text.lower()

    if any(term in lowered for term in ["replace", "replacement", "supersede"]):
        return "replacement"
    if any(term in lowered for term in ["obsolete", "obsolescence", "retire"]):
        return "obsolescence"
    if any(term in lowered for term in ["revise", "revision", "update"]):
        return "revision"
    if any(term in lowered for term in ["add", "introduce", "new part"]):
        return "addition"
    if any(term in lowered for term in ["remove", "delete"]):
        return "removal"

    return None


def _extract_labeled_part(text: str, labels: list[str]) -> str | None:
    for label in labels:
        pattern = rf"{re.escape(label)}\s*(?:number|no\.?|#|:)?\s*({PART_PATTERN})"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _normalize_part(match.group(1))

    if "replace" in [label.lower() for label in labels]:
        match = re.search(
            rf"replace\s+({PART_PATTERN})\s+(?:with|by|to)\s+({PART_PATTERN})",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return _normalize_part(match.group(1))

    if "with" in [label.lower() for label in labels]:
        match = re.search(
            rf"replace\s+({PART_PATTERN})\s+(?:with|by|to)\s+({PART_PATTERN})",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return _normalize_part(match.group(2))

    return None


def _extract_reason(text: str) -> str | None:
    patterns = [
        r"reason\s*:\s*(.+?)(?:effective date|effective|$)",
        r"because\s+(.+?)(?:effective date|effective|$)",
        r"due to\s+(.+?)(?:effective date|effective|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" .;")

    return None


def _extract_effective_date(text: str) -> date | None:
    patterns = [
        r"effective date\s*:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})",
        r"effective\s+([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})",
    ]
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y"]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue

        raw_date = match.group(1)
        for date_format in formats:
            try:
                return datetime.strptime(raw_date, date_format).date()
            except ValueError:
                continue

    return None


def _calculate_confidence(text: str) -> float:
    signals = [
        _extract_change_type(text),
        _extract_labeled_part(text, ["old part", "from part", "replace"]),
        _extract_labeled_part(text, ["new part", "to part", "with"]),
        _extract_reason(text),
        _extract_effective_date(text),
    ]
    found = sum(1 for signal in signals if signal)
    return round(found / len(signals), 2)


def _normalize_part(value: str) -> str:
    return value.upper().replace(" ", "-").replace("_", "-")
