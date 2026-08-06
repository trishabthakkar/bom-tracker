from abc import ABC, abstractmethod

from app.schemas.document import PartCatalogEntry, SectionForExtraction
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

    @abstractmethod
    def extract_part_references(
        self,
        *,
        sections: list[SectionForExtraction],
        catalog: list[PartCatalogEntry],
    ) -> dict[int, list[str]]:
        """Map section_index to catalog part numbers the section refers to.

        Covers references the regex pass cannot see: descriptive mentions
        ("the pressure relief valve") and part numbers whose shape the
        pattern rejects. Implementations must only return part numbers
        present in the supplied catalog."""
