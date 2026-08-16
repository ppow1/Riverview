"""Diffable, bounded Riverview topology graph derived from contracts and manifests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CHECKPOINTS = ("RIV-UI-0009", "RIV-UI-0013", "RIV-UI-0014", "RIV-UI-0015", "RIV-UI-0019", "RIV-UI-0020", "RIV-RES-0001", "RIV-RES-0002", "RIV-REASON-0001", "RIV-REASON-0002", "RIV-DIA-0001", "RIV-DIA-0002", "RIV-GRC-0004", "RIV-NOT-0001", "RIV-MCP-0006")

CORE_NODES = (
    ("river", "River event runtime / PostgreSQL", "core"),
    ("grace", "Grace / CME", "core"),
    ("relay", "Relay / work orders", "core"),
    ("providers", "Provider registry / capacity", "core"),
    ("diagnostics", "Diagnostics / Cookbook", "core"),
    ("notifications", "Notification contract", "core"),
    ("operator", "Riverview Operator", "module"),
    ("residents", "Resident/session gateway", "module"),
    ("room", "Conference room orchestration", "module"),
    ("snapshot", "Snapshot export", "module"),
    ("ollama", "Local Ollama provider", "module"),
    ("mcp", "MCP / Comms bridge", "module"),
    ("projects", "Projects / engineering intake", "module"),
    ("undercurrent", "Undercurrent security broker", "core"),
    ("controls", "Controls / device adapters", "module"),
    ("spatial", "Spatial / Quest (deferred)", "module"),
    ("reasoning.contract", "Provider-neutral reasoning contract", "contract"),
    ("resident.gateway", "Resident gateway contract", "contract"),
    ("steward", "Steward", "external"),
)

def build_graph(manifest_dir: Path) -> dict[str, Any]:
    manifests = []
    for path in sorted(manifest_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        manifests.append({"path": str(path), "module_id": data["module_id"], "display_name": data["display_name"], "required_core_contract": data["required_core_contract"], "dependencies": data.get("dependencies", []), "events_consumed": data.get("events_consumed", []), "events_emitted": data.get("events_emitted", []), "routes": data.get("routes", []), "diagnostics": data.get("diagnostics", [])})
    nodes = [{"id": node_id, "label": label, "kind": kind, "source": "graph.py:CORE_NODES"} for node_id, label, kind in CORE_NODES]
    edges: list[dict[str, Any]] = []
    def edge(source: str, target: str, relation: str, source_ref: str, derived: bool = True, checkpoint: str | None = None) -> None:
        item = {"source": source, "target": target, "relation": relation, "source_ref": source_ref, "derivation": "derived" if derived else "manual"}
        if checkpoint:
            item["checkpoint"] = checkpoint
        edges.append(item)
    edge("operator", "river", "publishes operator/resident/room events", "openwebui.py:emit_event", checkpoint="RIV-UI-0009")
    edge("operator", "residents", "submits bounded resident requests", "openwebui.py:/api/chat", checkpoint="RIV-RES-0001")
    edge("operator", "room", "submits room turns", "openwebui.py:/api/rooms", checkpoint="RIV-RES-0002")
    edge("operator", "snapshot", "requests diagnostic bundle", "openwebui.py:/snapshot", checkpoint="RIV-UI-0019")
    edge("operator", "controls", "receives browser/microphone input", "openwebui.py:/api/transcribe", checkpoint="RIV-UI-0015")
    edge("residents", "undercurrent", "checks classification and bounded references", "residents/gateway.py", checkpoint="RIV-RES-0001")
    edge("residents", "providers", "selects eligible provider", "reasoning/contract.py", checkpoint="RIV-REASON-0001")
    edge("room", "residents", "orchestrates participant sessions", "residents/gateway.py:room_chat", checkpoint="RIV-RES-0002")
    edge("providers", "ollama", "dispatches local reasoning", "reasoning/provider_registry.py", checkpoint="RIV-REASON-0002")
    edge("river", "grace", "wakes CME on durable events", "river/events.py + grace", checkpoint="RIV-GRC-0004")
    edge("grace", "relay", "evaluates ready objective stages", "grace/objectives.py", checkpoint="RIV-GRC-0004")
    edge("relay", "providers", "dispatches execution work", "relay/work_orders.py", checkpoint="RIV-REASON-0001")
    edge("river", "diagnostics", "records event/checkpoint lineage", "river/store.py", checkpoint="RIV-DIA-0001")
    edge("diagnostics", "notifications", "routes bounded escalation", "notifications", checkpoint="RIV-NOT-0001")
    edge("mcp", "river", "reads bounded Comms/mailbox state", "mcp", checkpoint="RIV-MCP-0006")
    edge("steward", "mcp", "addresses Grace and accepts bounded decisions", "Comms / Steward boundary", False)
    edge("projects", "grace", "promotes explicit engineering seed", "grace/objective_acceptance.py", False)
    edge("undercurrent", "river", "protects classified state boundary", "classification contracts", False)
    edge("spatial", "operator", "future spatial projection", "spatial prototype (deferred)", False)
    for manifest in manifests:
        node_id = manifest["module_id"]
        nodes.append({"id": node_id, "label": manifest["display_name"], "kind": "declared-module", "source": manifest["path"], "contract": manifest["required_core_contract"]})
        for dependency in manifest["dependencies"]:
            edge(node_id, dependency, "declares dependency", manifest["path"])
        for checkpoint in manifest["diagnostics"]:
            edge(node_id, "diagnostics", "uses checkpoint", manifest["path"], checkpoint=checkpoint)
    return {"schema_version": "riverview-system-graph-1.0", "generated_from": ["src/riverview/topology/graph.py", "config/modules/*.json", "River event contract", "Cookbook checkpoint registry"], "views": ["context", "events", "services", "failures", "modules", "resident", "room", "engineering", "mcp", "notifications"], "nodes": nodes, "edges": edges, "checkpoints": list(CHECKPOINTS), "manual_annotation_policy": "manual edges are explicit and source-referenced"}

def validate_graph(graph: dict[str, Any]) -> list[str]:
    node_ids = {node["id"] for node in graph.get("nodes", [])}
    errors = []
    for edge in graph.get("edges", []):
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            errors.append(f"unknown graph endpoint: {edge['source']} -> {edge['target']}")
    known = set(graph.get("checkpoints", []))
    for edge in graph.get("edges", []):
        if edge.get("checkpoint") and edge["checkpoint"] not in known:
            errors.append(f"unknown checkpoint: {edge['checkpoint']}")
    return errors

def write_graph(graph: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "riverview_system_graph.json").write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["flowchart LR"]
    for node in graph["nodes"]:
        lines.append(f'    {node["id"].replace(".", "_")}['"'"'{node["label"]}'"'"']')
    for item in graph["edges"]:
        lines.append(f'    {item["source"].replace(".", "_")} -->|{item["relation"]}| {item["target"].replace(".", "_")}')
    (output_dir / "riverview_system_graph.mmd").write_text("\n".join(lines) + "\n", encoding="utf-8")
    dot = ["digraph riverview {", "  rankdir=LR;"]
    for node in graph["nodes"]:
        dot.append(f'  "{node["id"]}" [label="{node["label"].replace(chr(34), chr(39))}"];')
    for item in graph["edges"]:
        dot.append(f'  "{item["source"]}" -> "{item["target"]}" [label="{item["relation"].replace(chr(34), chr(39))}"];')
    dot.append("}")
    (output_dir / "riverview_system_graph.dot").write_text("\n".join(dot) + "\n", encoding="utf-8")
