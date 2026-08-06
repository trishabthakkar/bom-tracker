import httpx

from app.schemas.eco import ParsedEngineeringChange
from app.schemas.impact import RiskAssessment, StructuredImpactReport
from app.services.llm.openai_provider import OPENAI_RESPONSES_URL, OpenAILLMProvider


class FakeClient:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.calls: list[dict] = []

    def post(self, url, *, headers, json):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return self.response


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
