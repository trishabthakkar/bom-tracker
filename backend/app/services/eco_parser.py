from app.schemas.eco import ParsedEngineeringChange
from app.services.llm.base import BaseLLMProvider
from app.services.llm.rule_based import RuleBasedLLMProvider


class EngineeringChangeParser:
    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self.provider = provider or RuleBasedLLMProvider()

    def parse_text(self, text: str) -> ParsedEngineeringChange:
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Engineering change text cannot be empty.")

        return self.provider.parse_engineering_change(cleaned_text)
