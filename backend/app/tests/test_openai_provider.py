import httpx

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
