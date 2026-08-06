from app.schemas.document import PartCatalogEntry, SectionForExtraction
from app.services.llm.base import BaseLLMProvider, LLMProviderError
from app.services.llm.providers import get_llm_provider


class PartReferenceResolver:
    """Finds document part references the regex pass cannot see.

    Falls back to no inferred references when the provider is unavailable, so
    indexing always succeeds with at least the regex-extracted references."""

    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self.provider = provider or get_llm_provider()

    def resolve(
        self,
        *,
        sections: list[SectionForExtraction],
        catalog: list[PartCatalogEntry],
    ) -> dict[int, list[str]]:
        if not sections or not catalog:
            return {}

        try:
            return self.provider.extract_part_references(sections=sections, catalog=catalog)
        except LLMProviderError:
            return {}
