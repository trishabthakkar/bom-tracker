from abc import ABC, abstractmethod

from app.schemas.eco import ParsedEngineeringChange
from app.schemas.impact import ReportSummary, StructuredImpactReport


class LLMProviderError(RuntimeError):
    pass


class BaseLLMProvider(ABC):
    @abstractmethod
    def parse_engineering_change(self, text: str) -> ParsedEngineeringChange:
        """Return structured ECO data from natural-language change text."""

    @abstractmethod
    def summarize_impact_report(self, report: StructuredImpactReport) -> ReportSummary:
        """Return a plain-English executive summary for an already-computed impact report."""
