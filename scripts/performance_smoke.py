from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

from app.schemas.eco import ParsedEngineeringChange
from app.services.bom_parser import ParsedBomItem, parse_bom_file
from app.services.dependency_graph import build_dependency_graph, get_graph_statistics
from app.services.intelligence_layer import IntelligenceLayer

# A report-generation time budget well above what the capped path search
# should ever need. Regressing to the old uncapped nx.all_simple_paths
# behavior blows this past several seconds on the lattice case below.
REPORT_TIME_BUDGET_SECONDS = 2.0


def write_large_bom(path: Path, row_count: int) -> None:
    lines = ["Part Number,Description,Parent Assembly,Child Assembly,Revision"]
    module_count = max(1, row_count // 100)

    for module_index in range(1, module_count + 1):
        module = f"ASM-{module_index:04d}"
        child = f"ASM-{module_index:04d}-SUB"
        lines.append(f"{module},Generated module {module_index},ROOT,{child},A")

        for part_index in range(1, 101):
            part_number = f"PN-{module_index:04d}-{part_index:03d}"
            lines.append(
                f"{part_number},Generated component {part_index},{child},,A"
            )
            if len(lines) - 1 >= row_count:
                break

        if len(lines) - 1 >= row_count:
            break

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_lattice_rows(levels: int, fanout: int) -> list[ParsedBomItem]:
    """Build a BOM shaped like a lattice: every node at level N is a parent
    of every node at level N+1, and a common part hangs off every node at
    the deepest level. This is not a pathological BOM - a single part reused
    across several sibling sub-assemblies is a normal real-world shape - but
    the number of simple paths between the common part and the root grows
    combinatorially with depth and fanout."""
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

    return rows


def main() -> None:
    row_count = int(os.getenv("PERF_BOM_ROWS", "1000"))
    with tempfile.TemporaryDirectory(prefix="bom-perf-") as directory:
        path = Path(directory) / "large-bom.csv"
        write_large_bom(path, row_count)

        parse_start = time.perf_counter()
        parsed = parse_bom_file(str(path))
        parse_seconds = time.perf_counter() - parse_start

        graph_start = time.perf_counter()
        graph = build_dependency_graph(parsed.rows)
        graph_seconds = time.perf_counter() - graph_start

        stats = get_graph_statistics(graph)

    print("BOM performance smoke")
    print(f"rows={len(parsed.rows)}")
    print(f"parse_seconds={parse_seconds:.4f}")
    print(f"graph_seconds={graph_seconds:.4f}")
    print(f"nodes={stats.node_count}")
    print(f"edges={stats.edge_count}")
    print(f"roots={stats.root_count}")
    print(f"leaves={stats.leaf_count}")
    print(f"has_cycles={stats.has_cycles}")

    lattice_levels = int(os.getenv("PERF_LATTICE_LEVELS", "10"))
    lattice_fanout = int(os.getenv("PERF_LATTICE_FANOUT", "4"))
    lattice_graph = build_dependency_graph(build_lattice_rows(lattice_levels, lattice_fanout))

    eco = ParsedEngineeringChange(
        change_type="replacement",
        old_part="PN-COMMON",
        new_part=None,
        reason="performance smoke test",
        effective_date=None,
        source="perf_smoke",
        confidence=1.0,
    )

    report_start = time.perf_counter()
    report = IntelligenceLayer().generate_report(graph=lattice_graph, eco=eco)
    report_seconds = time.perf_counter() - report_start
    assembly = report.affected_assemblies[0]

    print("Lattice report performance smoke")
    print(f"lattice_levels={lattice_levels}")
    print(f"lattice_fanout={lattice_fanout}")
    print(f"lattice_nodes={lattice_graph.number_of_nodes()}")
    print(f"report_seconds={report_seconds:.4f}")
    print(f"dependency_path_count={assembly.dependency_path_count}")
    print(f"dependency_paths_truncated={assembly.dependency_paths_truncated}")

    if report_seconds > REPORT_TIME_BUDGET_SECONDS:
        raise SystemExit(
            f"Report generation took {report_seconds:.2f}s, exceeding the "
            f"{REPORT_TIME_BUDGET_SECONDS}s budget on a {lattice_levels}-level "
            f"lattice BOM. Dependency path enumeration may no longer be bounded."
        )


if __name__ == "__main__":
    main()
