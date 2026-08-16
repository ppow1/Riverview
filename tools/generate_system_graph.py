import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
from riverview.topology.graph import build_graph, validate_graph, write_graph

graph = build_graph(root / "config" / "modules")
errors = validate_graph(graph)
if errors:
    raise SystemExit("\n".join(errors))
write_graph(graph, root / "docs" / "architecture")
print(f"nodes={len(graph['nodes'])} edges={len(graph['edges'])}")
