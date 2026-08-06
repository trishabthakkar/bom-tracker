from app.schemas.document import PartCatalogEntry, SectionForExtraction
from app.services.llm.base import LLMProviderError
from app.services.llm.rule_based import RuleBasedLLMProvider
from app.services.part_reference_resolver import PartReferenceResolver
from app.tests.conftest import StubLLMProvider

CATALOG = [
    PartCatalogEntry(part_number="PN-1212", description="Pressure relief valve"),
    PartCatalogEntry(part_number="PN-1211", description="Stainless manifold block"),
]
SECTIONS = [
    SectionForExtraction(
        section_index=1,
        heading="Valve service",
        content="Replace the pressure relief valve before commissioning.",
    )
]


def test_resolver_returns_provider_inferences() -> None:
    class FakeProvider(StubLLMProvider):
        def extract_part_references(self, *, sections, catalog):
            return {sections[0].section_index: ["PN-1212"]}

    result = PartReferenceResolver(provider=FakeProvider()).resolve(
        sections=SECTIONS, catalog=CATALOG
    )

    assert result == {1: ["PN-1212"]}


def test_resolver_returns_nothing_when_provider_fails() -> None:
    class FailingProvider(StubLLMProvider):
        def extract_part_references(self, *, sections, catalog):
            raise LLMProviderError("remote provider failed")

    result = PartReferenceResolver(provider=FailingProvider()).resolve(
        sections=SECTIONS, catalog=CATALOG
    )

    assert result == {}


def test_rule_based_provider_infers_nothing() -> None:
    result = PartReferenceResolver(provider=RuleBasedLLMProvider()).resolve(
        sections=SECTIONS, catalog=CATALOG
    )

    assert result == {}


def test_resolver_skips_provider_without_catalog() -> None:
    class ExplodingProvider(StubLLMProvider):
        def extract_part_references(self, *, sections, catalog):
            raise AssertionError("provider must not be called without a catalog")

    result = PartReferenceResolver(provider=ExplodingProvider()).resolve(
        sections=SECTIONS, catalog=[]
    )

    assert result == {}
