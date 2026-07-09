import json
from datetime import date
from typing import Any

import httpx
from pydantic import ValidationError

from app.schemas.eco import ParsedEngineeringChange
from app.services.llm.base import BaseLLMProvider, LLMProviderError

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"

ECO_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "change_type": {
            "type": ["string", "null"],
            "enum": ["replacement", "revision", "obsolescence", "addition", "removal", None],
        },
        "old_part": {"type": ["string", "null"]},
        "new_part": {"type": ["string", "null"]},
        "reason": {"type": ["string", "null"]},
        "effective_date": {
            "type": ["string", "null"],
            "description": "ISO 8601 date in YYYY-MM-DD format when present.",
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "change_type",
        "old_part",
        "new_part",
        "reason",
        "effective_date",
        "confidence",
    ],
}


class OpenAILLMProvider(BaseLLMProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.client = client

    def parse_engineering_change(self, text: str) -> ParsedEngineeringChange:
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "Extract structured engineering change order fields. "
                        "Return only data supported by the supplied JSON schema. "
                        "Use null when the text does not provide a field."
                    ),
                },
                {"role": "user", "content": text},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "engineering_change_order",
                    "strict": True,
                    "schema": ECO_JSON_SCHEMA,
                }
            },
        }

        response_json = self._post(payload)
        extracted = _extract_response_json(response_json)

        try:
            effective_date = extracted.get("effective_date")
            return ParsedEngineeringChange(
                change_type=extracted.get("change_type"),
                old_part=_normalize_part(extracted.get("old_part")),
                new_part=_normalize_part(extracted.get("new_part")),
                reason=extracted.get("reason"),
                effective_date=date.fromisoformat(effective_date) if effective_date else None,
                source=f"openai:{self.model}",
                confidence=extracted.get("confidence", 0),
            )
        except (TypeError, ValueError, ValidationError) as error:
            raise LLMProviderError("OpenAI response did not match the expected ECO schema.") from error

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            if self.client is not None:
                response = self.client.post(OPENAI_RESPONSES_URL, headers=headers, json=payload)
            else:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(OPENAI_RESPONSES_URL, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise LLMProviderError("OpenAI request failed.") from error

        return response.json()


def _extract_response_json(response_json: dict[str, Any]) -> dict[str, Any]:
    output_text = response_json.get("output_text")
    if isinstance(output_text, str):
        return _load_json_object(output_text)

    for output_item in response_json.get("output", []):
        if not isinstance(output_item, dict):
            continue
        for content_item in output_item.get("content", []):
            if not isinstance(content_item, dict):
                continue
            text = content_item.get("text")
            if isinstance(text, str):
                return _load_json_object(text)

    raise LLMProviderError("OpenAI response did not contain structured text output.")


def _load_json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise LLMProviderError("OpenAI response was not valid JSON.") from error

    if not isinstance(parsed, dict):
        raise LLMProviderError("OpenAI response JSON was not an object.")

    return parsed


def _normalize_part(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    return cleaned.upper() or None
