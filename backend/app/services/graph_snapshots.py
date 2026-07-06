import networkx as nx
from sqlalchemy.orm import Session

from app.models.bom import BomImport
from app.models.graph_snapshot import GraphSnapshot
from app.services.dependency_graph import (
    get_graph_edges,
    get_graph_statistics,
)


def create_graph_snapshot(
    *,
    db: Session,
    graph: nx.DiGraph,
    bom_import: BomImport,
    user_id: int,
) -> GraphSnapshot:
    statistics = get_graph_statistics(graph)
    snapshot = GraphSnapshot(
        user_id=user_id,
        bom_import_id=bom_import.id,
        upload_id=bom_import.upload_id,
        node_count=statistics.node_count,
        edge_count=statistics.edge_count,
        root_count=statistics.root_count,
        leaf_count=statistics.leaf_count,
        has_cycles=statistics.has_cycles,
        nodes=sorted(str(node) for node in graph.nodes),
        edges=[edge.__dict__ for edge in get_graph_edges(graph)],
    )

    db.add(snapshot)
    db.flush()
    return snapshot
