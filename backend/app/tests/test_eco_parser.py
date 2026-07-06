from datetime import date

import pytest

from app.schemas.eco import ParsedEngineeringChange
from app.services.eco_parser import EngineeringChangeParser
from app.services.llm.base import BaseLLMProvider


def test_parse_replacement_change() -> None:
    text = (
        "Replace old part PN-100 with new part PN-200. "
        "Reason: supplier obsolescence. Effective date: 2026-08-15."
    )

    result = EngineeringChangeParser().parse_text(text)

    assert result.change_type == "replacement"
    assert result.old_part == "PN-100"
    assert result.new_part == "PN-200"
    assert result.reason == "supplier obsolescence"
    assert result.effective_date == date(2026, 8, 15)
    assert result.source == "rule_based"


def test_parse_reason_from_due_to_phrase() -> None:
    text = "Revision update for old part VALVE-100 due to field leakage effective 07/31/2026"

    result = EngineeringChangeParser().parse_text(text)

    assert result.change_type == "revision"
    assert result.reason == "field leakage"
    assert result.effective_date == date(2026, 7, 31)


def test_parse_obsolescence_change_type() -> None:
    text = "Part PUMP-777 is obsolete because vendor discontinued supply."

    result = EngineeringChangeParser().parse_text(text)

    assert result.change_type == "obsolescence"
    assert result.reason == "vendor discontinued supply"


def test_empty_text_raises_error() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        EngineeringChangeParser().parse_text("   ")


def test_parser_uses_provider_abstraction() -> None:
    class FakeProvider(BaseLLMProvider):
        def parse_engineering_change(self, text: str) -> ParsedEngineeringChange:
            return ParsedEngineeringChange(
                change_type="replacement",
                old_part="OLD-1",
                new_part="NEW-1",
                reason=f"parsed {text}",
                effective_date=None,
                source="fake",
                confidence=1,
            )

    result = EngineeringChangeParser(provider=FakeProvider()).parse_text("input")

    assert result.old_part == "OLD-1"
    assert result.new_part == "NEW-1"
    assert result.reason == "parsed input"
    assert result.source == "fake"
