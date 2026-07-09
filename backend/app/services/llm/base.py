from abc import ABC, abstractmethod

from app.schemas.eco import ParsedEngineeringChange


class LLMProviderError(RuntimeError):
    pass


class BaseLLMProvider(ABC):
    @abstractmethod
    def parse_engineering_change(self, text: str) -> ParsedEngineeringChange:
        """Return structured ECO data from natural-language change text."""
