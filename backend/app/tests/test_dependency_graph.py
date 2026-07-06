from app.services.bom_parser import ParsedBomItem
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
            part_number="P-100",
            description="Drive assembly",
            parent_assembly="ROOT",
            child_assembly="A-100",
            revision="A",
        ),
        ParsedBomItem(
            row_number=3,
            part_number="P-200",
            description="Motor bracket",
            parent_assembly="A-100",
            child_assembly="C-200",
            revision="B",
        ),
        ParsedBomItem(
            row_number=4,
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
    assert {edge.source for edge in edges} == {"ROOT", "A-100", "C-200"}
    assert ("ROOT", "A-100") in graph.edges
    assert ("A-100", "P-100") in graph.edges
    assert ("A-100", "C-200") in graph.edges
    assert ("C-200", "P-200") in graph.edges
    assert ("C-200", "P-300") in graph.edges


def test_get_affected_parents() -> None:
    graph = build_dependency_graph(sample_rows())

    assert get_affected_parents(graph, "P-300") == ["A-100", "C-200", "ROOT"]


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
        ["ROOT", "A-100", "C-200", "P-300"]
    ]


def test_get_graph_statistics() -> None:
    graph = build_dependency_graph(sample_rows())
    statistics = get_graph_statistics(graph)

    assert statistics.node_count == 6
    assert statistics.edge_count == 5
    assert statistics.root_count == 1
    assert statistics.leaf_count == 3
    assert statistics.has_cycles is False
