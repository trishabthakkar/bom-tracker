from pathlib import Path

from app.services.bom_parser import ParsedBomItem, parse_bom_file
from app.services.dependency_graph import (
    build_dependency_graph,
    get_affected_children,
    get_affected_parents,
    get_dependency_paths,
    get_graph_edges,
    get_graph_statistics,
)


def sample_rows() -> list[ParsedBomItem]:
    return [
        ParsedBomItem(
            row_number=2,
            part_number="ROOT",
            description="Top-level assembly",
            parent_assembly=None,
            child_assembly="P-100",
            revision="A",
        ),
        ParsedBomItem(
            row_number=3,
            part_number="P-100",
            description="Drive assembly",
            parent_assembly="ROOT",
            child_assembly="A-100",
            revision="A",
        ),
        ParsedBomItem(
            row_number=4,
            part_number="P-200",
            description="Motor bracket",
            parent_assembly="A-100",
            child_assembly="C-200",
            revision="B",
        ),
        ParsedBomItem(
            row_number=5,
            part_number="P-300",
            description="Sensor",
            parent_assembly="C-200",
            child_assembly=None,
            revision="C",
        ),
    ]


def test_build_dependency_graph() -> None:
    graph = build_dependency_graph(sample_rows())
    edges = get_graph_edges(graph)

    assert graph.number_of_nodes() == 6
    assert {edge.source for edge in edges} == {"ROOT", "P-100", "A-100", "P-200", "C-200"}
    assert ("ROOT", "P-100") in graph.edges
    assert ("P-100", "A-100") in graph.edges
    assert ("A-100", "P-200") in graph.edges
    assert ("P-200", "C-200") in graph.edges
    assert ("C-200", "P-300") in graph.edges


def test_get_affected_parents() -> None:
    graph = build_dependency_graph(sample_rows())

    assert get_affected_parents(graph, "P-300") == [
        "A-100",
        "C-200",
        "P-100",
        "P-200",
        "ROOT",
    ]


def test_get_affected_children() -> None:
    graph = build_dependency_graph(sample_rows())

    assert get_affected_children(graph, "ROOT") == [
        "A-100",
        "C-200",
        "P-100",
        "P-200",
        "P-300",
    ]


def test_get_dependency_paths() -> None:
    graph = build_dependency_graph(sample_rows())

    assert get_dependency_paths(graph, "ROOT", "P-300") == [
        ["ROOT", "P-100", "A-100", "P-200", "C-200", "P-300"]
    ]


def test_get_graph_statistics() -> None:
    graph = build_dependency_graph(sample_rows())
    statistics = get_graph_statistics(graph)

    assert statistics.node_count == 6
    assert statistics.edge_count == 5
    assert statistics.root_count == 1
    assert statistics.leaf_count == 1
    assert statistics.has_cycles is False


def test_demo_bom_v2_has_single_root_and_no_cycles() -> None:
    """Regression test for the parent/child edge-direction bug: a shipped demo
    BOM with a top-level assembly row (blank parent_assembly) previously
    produced a graph with 0 roots and a false-positive cycle."""
    demo_path = Path(__file__).resolve().parents[3] / "demo-files" / "demo-bom-v2.csv"
    parsed = parse_bom_file(demo_path)
    graph = build_dependency_graph(parsed.rows)
    statistics = get_graph_statistics(graph)

    assert statistics.root_count == 1
    assert statistics.has_cycles is False
