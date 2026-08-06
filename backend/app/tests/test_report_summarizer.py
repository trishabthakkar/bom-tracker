from app.schemas.eco import ParsedEngineeringChange
from app.schemas.impact import ReportSummary, RiskAssessment, StructuredImpactReport
from app.services.llm.base import BaseLLMProvider, LLMProviderError
from app.services.llm.rule_based import RuleBasedLLMProvider
from app.services.report_summarizer import ReportSummarizer


def build_report(summary: str = "Replacement for PN-1212 has high risk.") -> StructuredImpactReport:
    return StructuredImpactReport(
        summary=summary,
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


def test_summarize_uses_rule_based_pass_through_summary() -> None:
    report = build_report()

    result = ReportSummarizer(provider=RuleBasedLLMProvider()).summarize(report)

    assert result.text == report.summary
    assert result.source == "rule_based"


def test_summarize_uses_provider_abstraction() -> None:
    class FakeProvider(BaseLLMProvider):
        def parse_engineering_change(self, text: str) -> ParsedEngineeringChange:
            raise NotImplementedError

        def summarize_impact_report(self, report: StructuredImpactReport) -> ReportSummary:
            return ReportSummary(text=f"AI summary for {report.affected_part}", source="fake")

    result = ReportSummarizer(provider=FakeProvider()).summarize(build_report())

    assert result.text == "AI summary for PN-1212"
    assert result.source == "fake"


def test_summarize_falls_back_to_rule_based_on_llm_failure() -> None:
    class FailingProvider(BaseLLMProvider):
        def parse_engineering_change(self, text: str) -> ParsedEngineeringChange:
            raise NotImplementedError

        def summarize_impact_report(self, report: StructuredImpactReport) -> ReportSummary:
            raise LLMProviderError("remote provider failed")

    report = build_report()
    result = ReportSummarizer(provider=FailingProvider()).summarize(report)

    assert result.source == "rule_based"
    assert result.text == report.summary
