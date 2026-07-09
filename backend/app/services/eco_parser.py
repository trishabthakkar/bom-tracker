from app.core.config import settings
from app.schemas.eco import ParsedEngineeringChange
from app.services.llm.base import BaseLLMProvider, LLMProviderError
from app.services.llm.providers import get_llm_provider
from app.services.llm.rule_based import RuleBasedLLMProvider


class EngineeringChangeParser:
    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self.provider = provider or get_llm_provider()
        self.fallback_provider = RuleBasedLLMProvider()

    def parse_text(self, text: str) -> ParsedEngineeringChange:
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Engineering change text cannot be empty.")

        try:
            return self.provider.parse_engineering_change(cleaned_text)
        except LLMProviderError:
            if settings.llm_fallback_to_rule_based:
                return self.fallback_provider.parse_engineering_change(cleaned_text)
            raise
