import json as json_module

import httpx

from app.schemas.document import PartCatalogEntry, SectionForExtraction
from app.schemas.eco import ParsedEngineeringChange
from app.schemas.impact import RiskAssessment, StructuredImpactReport
from app.services.llm.openai_provider import (
    MAX_SECTIONS_PER_REQUEST,
    OPENAI_RESPONSES_URL,
    OpenAILLMProvider,
)


class FakeClient:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.calls: list[dict] = []

    def post(self, url, *, headers, json):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return self.response


class SequencedFakeClient:
    """Returns a different response per call, for exercising batched requests."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def post(self, url, *, headers, json):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return self.responses[len(self.calls) - 1]


def json_response(payload: dict) -> httpx.Response:
    return httpx.Response(
        200,
        request=httpx.Request("POST", OPENAI_RESPONSES_URL),
        json={"output_text": json_module.dumps(payload)},
    )


CATALOG = [
    PartCatalogEntry(part_number="PN-1212", description="Pressure relief valve"),
    PartCatalogEntry(part_number="PN-1211", description="Stainless manifold block"),
]


def test_openai_provider_parses_structured_response() -> None:
    request = httpx.Request("POST", OPENAI_RESPONSES_URL)
    response = httpx.Response(
        200,
        request=request,
        json={
            "output_text": (
                '{"change_type":"replacement","old_part":"pn-1212","new_part":"pn-2212",'
                '"reason":"supplier obsolescence","effective_date":"2026-08-15","confidence":0.91}'
            )
        },
    )
    client = FakeClient(response)

    result = OpenAILLMProvider(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
        client=client,
    ).parse_engineering_change("Replace PN-1212 with PN-2212.")

    assert result.change_type == "replacement"
    assert result.old_part == "PN-1212"
    assert result.new_part == "PN-2212"
    assert result.reason == "supplier obsolescence"
    assert result.effective_date.isoformat() == "2026-08-15"
    assert result.confidence == 0.91
    assert result.source == "openai:test-model"
    assert client.calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert client.calls[0]["json"]["text"]["format"]["type"] == "json_schema"


def test_openai_provider_summarizes_impact_report() -> None:
    request = httpx.Request("POST", OPENAI_RESPONSES_URL)
    response = httpx.Response(
        200,
        request=request,
        json={"output_text": "Replacing PN-1212 with PN-2212 carries high risk to two assemblies."},
    )
    client = FakeClient(response)
    report = StructuredImpactReport(
        summary="template summary",
        eco=ParsedEngineeringChange(
            change_type="replacement",
            old_part="PN-1212",
            new_part="PN-2212",
            reason="supplier obsolescence",
            effective_date=None,
            source="rule_based",
            confidence=0.9,
        ),
        affected_part="PN-1212",
        effective_date=None,
        risk=RiskAssessment(level="High", score=90, reasons=["high impact change type"]),
    )

    result = OpenAILLMProvider(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
        client=client,
    ).summarize_impact_report(report)

    assert result.text == "Replacing PN-1212 with PN-2212 carries high risk to two assemblies."
    assert result.source == "openai:test-model"
    assert client.calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert "text" not in client.calls[0]["json"]


def build_provider(client) -> OpenAILLMProvider:
    return OpenAILLMProvider(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
        client=client,
    )


def test_extract_part_references_resolves_descriptive_mentions() -> None:
    client = FakeClient(
        json_response({"sections": [{"section_index": 1, "part_numbers": ["PN-1212"]}]})
    )
    sections = [
        SectionForExtraction(
            section_index=1,
            heading="Valve service",
            content="Replace the pressure relief valve before commissioning.",
        )
    ]

    result = build_provider(client).extract_part_references(sections=sections, catalog=CATALOG)

    assert result == {1: ["PN-1212"]}
    sent = json_module.loads(client.calls[0]["json"]["input"][1]["content"])
    assert sent["catalog"][0]["description"] == "Pressure relief valve"


def test_extract_part_references_drops_parts_absent_from_catalog() -> None:
    client = FakeClient(
        json_response(
            {
                "sections": [
                    {"section_index": 1, "part_numbers": ["PN-1212", "PN-9999", "INVENTED-1"]}
                ]
            }
        )
    )
    sections = [
        SectionForExtraction(section_index=1, heading="Valve", content="Service the valve.")
    ]

    result = build_provider(client).extract_part_references(sections=sections, catalog=CATALOG)

    assert result == {1: ["PN-1212"]}


def test_extract_part_references_ignores_unknown_section_indexes() -> None:
    client = FakeClient(
        json_response(
            {
                "sections": [
                    {"section_index": 1, "part_numbers": ["PN-1212"]},
                    {"section_index": 77, "part_numbers": ["PN-1211"]},
                ]
            }
        )
    )
    sections = [
        SectionForExtraction(section_index=1, heading="Valve", content="Service the valve.")
    ]

    result = build_provider(client).extract_part_references(sections=sections, catalog=CATALOG)

    assert result == {1: ["PN-1212"]}


def test_extract_part_references_normalizes_case_to_catalog_spelling() -> None:
    client = FakeClient(
        json_response({"sections": [{"section_index": 1, "part_numbers": ["pn-1212"]}]})
    )
    sections = [
        SectionForExtraction(section_index=1, heading="Valve", content="Service the valve.")
    ]

    result = build_provider(client).extract_part_references(sections=sections, catalog=CATALOG)

    assert result == {1: ["PN-1212"]}


def test_extract_part_references_batches_large_documents() -> None:
    section_count = MAX_SECTIONS_PER_REQUEST + 3
    sections = [
        SectionForExtraction(section_index=index, heading=f"Section {index}", content="Valve.")
        for index in range(1, section_count + 1)
    ]
    client = SequencedFakeClient(
        [
            json_response({"sections": [{"section_index": 1, "part_numbers": ["PN-1212"]}]}),
            json_response(
                {"sections": [{"section_index": section_count, "part_numbers": ["PN-1211"]}]}
            ),
        ]
    )

    result = build_provider(client).extract_part_references(sections=sections, catalog=CATALOG)

    assert len(client.calls) == 2
    assert result == {1: ["PN-1212"], section_count: ["PN-1211"]}


def test_extract_part_references_makes_no_request_without_catalog() -> None:
    client = FakeClient(json_response({"sections": []}))
    sections = [
        SectionForExtraction(section_index=1, heading="Valve", content="Service the valve.")
    ]

    result = build_provider(client).extract_part_references(sections=sections, catalog=[])

    assert result == {}
    assert client.calls == []
