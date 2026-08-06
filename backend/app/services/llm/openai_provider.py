import json
from datetime import date
from typing import Any

import httpx
from pydantic import ValidationError

from app.schemas.document import PartCatalogEntry, SectionForExtraction
from app.schemas.eco import ParsedEngineeringChange
from app.schemas.impact import ReportSummary, StructuredImpactReport
from app.services.llm.base import BaseLLMProvider, LLMProviderError

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"

# Bounds keep a single large document from turning into an unbounded number of
# tokens or requests. Sections beyond the cap keep their regex references only.
MAX_CATALOG_ENTRIES = 400
MAX_SECTIONS_PER_REQUEST = 20
MAX_SECTION_CHARS = 1_500

PART_REFERENCE_SYSTEM_PROMPT = (
    "You link engineering document sections to parts from a bill of materials. "
    "You are given a catalog of parts (part_number and description) and document "
    "sections. For each section, return every catalog part_number the section "
    "refers to, including references made only by description "
    '(for example "the pressure relief valve" refers to the catalog part whose '
    "description is a pressure relief valve). "
    "Only return part_number values that appear verbatim in the supplied catalog. "
    "Never invent a part number. Return an empty list for sections that refer to no "
    "catalog part."
)

SUMMARY_SYSTEM_PROMPT = (
    "You write concise executive summaries of engineering change impact reports "
    "for non-engineer stakeholders (program managers, procurement). You are given "
    "structured impact data as JSON. Write 2-4 plain-English sentences covering "
    "what changed, the risk level, and the most important downstream impact. "
    "Only state facts present in the JSON. Do not use markdown or bullet points."
)

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


PART_REFERENCE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "section_index": {"type": "integer"},
                    "part_numbers": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["section_index", "part_numbers"],
            },
        }
    },
    "required": ["sections"],
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

    def summarize_impact_report(self, report: StructuredImpactReport) -> ReportSummary:
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(_summary_context(report))},
            ],
        }

        response_json = self._post(payload)
        text = _extract_response_text(response_json).strip()
        if not text:
            raise LLMProviderError("OpenAI response did not contain a summary.")

        return ReportSummary(text=text, source=f"openai:{self.model}")

    def extract_part_references(
        self,
        *,
        sections: list[SectionForExtraction],
        catalog: list[PartCatalogEntry],
    ) -> dict[int, list[str]]:
        if not sections or not catalog:
            return {}

        bounded_catalog = catalog[:MAX_CATALOG_ENTRIES]
        # Case-insensitive lookup back to the catalog's own spelling, so a model
        # that echoes a part in a different case still resolves to a real part.
        known_parts = {entry.part_number.upper(): entry.part_number for entry in bounded_catalog}
        catalog_payload = [
            {"part_number": entry.part_number, "description": entry.description or ""}
            for entry in bounded_catalog
        ]

        references: dict[int, list[str]] = {}
        for batch_start in range(0, len(sections), MAX_SECTIONS_PER_REQUEST):
            batch = sections[batch_start : batch_start + MAX_SECTIONS_PER_REQUEST]
            references.update(self._extract_batch(batch, catalog_payload, known_parts))

        return references

    def _extract_batch(
        self,
        sections: list[SectionForExtraction],
        catalog_payload: list[dict[str, str]],
        known_parts: dict[str, str],
    ) -> dict[int, list[str]]:
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": PART_REFERENCE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "catalog": catalog_payload,
                            "sections": [
                                {
                                    "section_index": section.section_index,
                                    "heading": section.heading,
                                    "content": section.content[:MAX_SECTION_CHARS],
                                }
                                for section in sections
                            ],
                        }
                    ),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "part_references",
                    "strict": True,
                    "schema": PART_REFERENCE_JSON_SCHEMA,
                }
            },
        }

        extracted = _load_json_object(_extract_response_text(self._post(payload)))
        valid_indexes = {section.section_index for section in sections}
        results: dict[int, list[str]] = {}

        for item in extracted.get("sections", []):
            if not isinstance(item, dict):
                continue

            section_index = item.get("section_index")
            if section_index not in valid_indexes:
                continue

            resolved = sorted(
                {
                    known_parts[part.strip().upper()]
                    for part in item.get("part_numbers", [])
                    if isinstance(part, str) and part.strip().upper() in known_parts
                }
            )
            if resolved:
                results[section_index] = resolved

        return results

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


def _extract_response_text(response_json: dict[str, Any]) -> str:
    output_text = response_json.get("output_text")
    if isinstance(output_text, str):
        return output_text

    for output_item in response_json.get("output", []):
        if not isinstance(output_item, dict):
            continue
        for content_item in output_item.get("content", []):
            if not isinstance(content_item, dict):
                continue
            text = content_item.get("text")
            if isinstance(text, str):
                return text

    raise LLMProviderError("OpenAI response did not contain text output.")


def _summary_context(report: StructuredImpactReport) -> dict[str, Any]:
    return {
        "change_type": report.eco.change_type,
        "affected_part": report.affected_part,
        "effective_date": report.effective_date.isoformat() if report.effective_date else None,
        "reason": report.eco.reason,
        "risk": {
            "level": report.risk.level,
            "score": report.risk.score,
            "reasons": report.risk.reasons,
        },
        "affected_assemblies": [
            {
                "part_number": assembly.part_number,
                "affected_parent_count": len(assembly.affected_parents),
                "affected_child_count": len(assembly.affected_children),
            }
            for assembly in report.affected_assemblies
        ],
        "downstream_records": [
            {"record_type": record.record_type, "impact": record.impact, "severity": record.severity}
            for record in report.downstream_records
        ],
        "affected_document_sections": [
            {"document_type": section.document_type, "heading": section.heading, "severity": section.severity}
            for section in report.affected_document_sections
        ],
    }


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
