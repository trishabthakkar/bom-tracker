from collections.abc import Iterator
from dataclasses import dataclass

import networkx as nx

from app.services.bom_parser import ParsedBomItem


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str


@dataclass(frozen=True)
class GraphStatistics:
    node_count: int
    edge_count: int
    root_count: int
    leaf_count: int
    has_cycles: bool


def build_dependency_graph(rows: list[ParsedBomItem]) -> nx.DiGraph:
    graph = nx.DiGraph()

    for row in rows:
        graph.add_node(row.part_number)

        if row.parent_assembly and row.parent_assembly != row.part_number:
            graph.add_node(row.parent_assembly)
            graph.add_edge(row.parent_assembly, row.part_number)

        if row.child_assembly and row.child_assembly != row.part_number:
            graph.add_node(row.child_assembly)
            graph.add_edge(row.part_number, row.child_assembly)

    return graph


def get_graph_edges(graph: nx.DiGraph) -> list[GraphEdge]:
    return [
        GraphEdge(source=str(source), target=str(target))
        for source, target in sorted(graph.edges())
    ]


def get_affected_parents(graph: nx.DiGraph, part_number: str) -> list[str]:
    if part_number not in graph:
        return []

    return sorted(str(node) for node in nx.ancestors(graph, part_number))


def get_affected_children(graph: nx.DiGraph, part_number: str) -> list[str]:
    if part_number not in graph:
        return []

    return sorted(str(node) for node in nx.descendants(graph, part_number))


def get_dependency_paths(
    graph: nx.DiGraph,
    source: str,
    target: str,
    max_depth: int = 10,
) -> list[list[str]]:
    return list(iter_dependency_paths(graph, source, target, max_depth=max_depth))


def iter_dependency_paths(
    graph: nx.DiGraph,
    source: str,
    target: str,
    max_depth: int = 10,
) -> Iterator[list[str]]:
    """Lazily yield simple paths one at a time.

    Path counts grow combinatorially with fan-out, so callers that only need
    a bounded sample (e.g. for a report) must consume this with something
    like itertools.islice rather than materializing it into a list first.
    """
    if source not in graph or target not in graph:
        return

    for path in nx.all_simple_paths(graph, source=source, target=target, cutoff=max_depth):
        yield [str(node) for node in path]


def get_graph_statistics(graph: nx.DiGraph) -> GraphStatistics:
    roots = [node for node in graph.nodes if graph.in_degree(node) == 0]
    leaves = [node for node in graph.nodes if graph.out_degree(node) == 0]

    return GraphStatistics(
        node_count=graph.number_of_nodes(),
        edge_count=graph.number_of_edges(),
        root_count=len(roots),
        leaf_count=len(leaves),
        has_cycles=not nx.is_directed_acyclic_graph(graph),
    )
