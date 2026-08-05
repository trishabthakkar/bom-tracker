from datetime import date

from app.schemas.eco import ParsedEngineeringChange
from app.services.bom_parser import ParsedBomItem
from app.services.dependency_graph import build_dependency_graph
from app.services.intelligence_layer import MAX_DEPENDENCY_PATHS, IntelligenceLayer


def build_sample_graph():
    rows = [
        ParsedBomItem(
            row_number=2,
            part_number="PN-100",
            description="Legacy pump",
            parent_assembly="ROOT",
            child_assembly="A-100",
            revision="A",
        ),
        ParsedBomItem(
            row_number=3,
            part_number="PN-300",
            description="Sensor",
            parent_assembly="A-100",
            child_assembly=None,
            revision="B",
        ),
    ]
    return build_dependency_graph(rows)


def test_replacement_generates_high_or_medium_impact() -> None:
    eco = ParsedEngineeringChange(
        change_type="replacement",
        old_part="PN-100",
        new_part="PN-200",
        reason="supplier obsolescence",
        effective_date=date(2026, 8, 15),
        source="test",
        confidence=1,
    )

    report = IntelligenceLayer().generate_report(graph=build_sample_graph(), eco=eco)

    assert report.affected_part == "PN-100"
    assert report.risk.level in {"Medium", "High"}
    assert report.downstream_records
    assert any(update.area == "procurement" for update in report.suggested_updates)


def test_revision_generates_medium_impact_for_matched_part() -> None:
    eco = ParsedEngineeringChange(
        change_type="revision",
        old_part="PN-300",
        new_part=None,
        reason="field issue",
        effective_date=None,
        source="test",
        confidence=0.8,
    )

    report = IntelligenceLayer().generate_report(graph=build_sample_graph(), eco=eco)

    assert report.affected_assemblies[0].affected_parents == ["A-100", "PN-100", "ROOT"]
    assert report.risk.level == "Medium"


def test_no_graph_match_generates_low_risk_signal() -> None:
    eco = ParsedEngineeringChange(
        change_type=None,
        old_part="UNKNOWN-999",
        new_part=None,
        reason=None,
        effective_date=None,
        source="test",
        confidence=0.2,
    )

    report = IntelligenceLayer().generate_report(graph=build_sample_graph(), eco=eco)

    assert report.affected_assemblies == []
    assert report.risk.level == "Low"
    assert "No matching part" in " ".join(report.risk.reasons)
    assert {record.severity for record in report.downstream_records} == {"low"}


def test_downstream_records_include_execution_documents() -> None:
    eco = ParsedEngineeringChange(
        change_type="obsolescence",
        old_part="PN-100",
        new_part=None,
        reason="vendor discontinued supply",
        effective_date=None,
        source="test",
        confidence=0.9,
    )

    report = IntelligenceLayer().generate_report(graph=build_sample_graph(), eco=eco)
    record_types = {record.record_type for record in report.downstream_records}

    assert "procurement" in record_types
    assert "installation_guides" in record_types
    assert "commissioning_procedures" in record_types
    assert "service_manuals" in record_types


def build_lattice_graph(levels: int, fanout: int):
    """A BOM where a common part sits under many sibling sub-assemblies.
    The number of simple paths from the top to the common part grows
    combinatorially with levels/fanout - this is what previously made
    dependency-path enumeration unbounded for realistic (non-pathological)
    BOM shapes."""
    rows: list[ParsedBomItem] = []
    row_number = 0

    for level in range(levels - 1):
        for parent_index in range(fanout):
            for child_index in range(fanout):
                row_number += 1
                rows.append(
                    ParsedBomItem(
                        row_number=row_number,
                        part_number=f"L{level + 1}-{child_index}",
                        description=None,
                        parent_assembly=f"L{level}-{parent_index}",
                        child_assembly=None,
                        revision=None,
                    )
                )

    for parent_index in range(fanout):
        row_number += 1
        rows.append(
            ParsedBomItem(
                row_number=row_number,
                part_number="PN-COMMON",
                description=None,
                parent_assembly=f"L{levels - 1}-{parent_index}",
                child_assembly=None,
                revision=None,
            )
        )

    return build_dependency_graph(rows)


def test_dependency_paths_are_capped_on_high_fanout_graphs() -> None:
    # levels=6, fanout=4 produces 5,460 simple paths uncapped - comfortably
    # over the cap, while staying fast enough for a unit test either way.
    graph = build_lattice_graph(levels=6, fanout=4)
    eco = ParsedEngineeringChange(
        change_type="replacement",
        old_part="PN-COMMON",
        new_part=None,
        reason="supplier obsolescence",
        effective_date=None,
        source="test",
        confidence=1,
    )

    report = IntelligenceLayer().generate_report(graph=graph, eco=eco)
    assembly = report.affected_assemblies[0]

    assert len(assembly.dependency_paths) == MAX_DEPENDENCY_PATHS
    assert assembly.dependency_path_count == MAX_DEPENDENCY_PATHS
    assert assembly.dependency_paths_truncated is True


def test_dependency_paths_are_not_marked_truncated_when_under_the_cap() -> None:
    report = IntelligenceLayer().generate_report(
        graph=build_sample_graph(),
        eco=ParsedEngineeringChange(
            change_type="revision",
            old_part="PN-300",
            new_part=None,
            reason="field issue",
            effective_date=None,
            source="test",
            confidence=0.8,
        ),
    )
    assembly = report.affected_assemblies[0]

    assert assembly.dependency_path_count == len(assembly.dependency_paths)
    assert assembly.dependency_paths_truncated is False
