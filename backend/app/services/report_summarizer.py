from app.core.config import settings
from app.schemas.impact import ReportSummary, StructuredImpactReport
from app.services.llm.base import BaseLLMProvider, LLMProviderError
from app.services.llm.providers import get_llm_provider
from app.services.llm.rule_based import RuleBasedLLMProvider


class ReportSummarizer:
    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self.provider = provider or get_llm_provider()
        self.fallback_provider = RuleBasedLLMProvider()

    def summarize(self, report: StructuredImpactReport) -> ReportSummary:
        try:
            return self.provider.summarize_impact_report(report)
        except LLMProviderError:
            if settings.llm_fallback_to_rule_based:
                return self.fallback_provider.summarize_impact_report(report)
            raise
