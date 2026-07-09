from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

from app.services.bom_parser import parse_bom_file
from app.services.dependency_graph import build_dependency_graph, get_graph_statistics


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


if __name__ == "__main__":
    main()
