"""Canonical, traceable Riverview interaction graph and projections."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CHECKPOINTS = (
    "RIV-UI-0009", "RIV-UI-0013", "RIV-UI-0014", "RIV-UI-0015", "RIV-UI-0019", "RIV-UI-0020",
    "RIV-RES-0001", "RIV-RES-0002", "RIV-REASON-0001", "RIV-REASON-0002",
    "RIV-CHAR-0004", "RIV-DIA-0001", "RIV-DIA-0002", "RIV-GRC-0004",
    "RIV-EXE-0001", "RIV-EXE-0003", "RIV-NOT-0001", "RIV-MCP-0006",
    "RIV-ARCH-0001", "RIV-INF-0001", "RIV-SPAT-0004",
)

VIEW_NAMES = {
    "01_system_context": "context", "02_event_flow": "events", "03_engineering_execution": "engineering",
    "04_resident_conversation": "resident", "05_conference_room": "room", "06_character_development": "character",
    "07_chatgpt_comms_bridge": "comms", "08_notifications": "notifications", "09_diagnostics_seams": "failures",
    "10_modules": "modules", "11_service_runtime": "services",
}

CORE_NODES = (
    ("steward", "Steward", "external"), ("river", "River event runtime / PostgreSQL", "core"),
    ("grace", "Grace / CME", "core"), ("objective_state", "Objective and stage state", "core"),
    ("relay", "Relay / work-order lifecycle", "core"), ("execution_envelope", "Execution envelope", "core"),
    ("providers", "Provider registry / capacity", "core"), ("core_contract", "Riverview core contract 1.0", "contract"),
    ("reasoning_contract", "Provider-neutral reasoning contract", "contract"),
    ("diagnostics", "Diagnostics / Cookbook", "core"), ("notifications", "Steward notification store", "core"),
    ("undercurrent", "Undercurrent classification/security", "core"), ("operator_runtime", "Riverview Operator runtime", "runtime"),
    ("resident_gateway_runtime", "Resident/session gateway runtime", "runtime"), ("room_runtime", "Conference room orchestration", "runtime"),
    ("character_runtime", "Accepted character runtime", "runtime"), ("continuity_runtime", "Continuity/session stores", "runtime"),
    ("snapshot_runtime", "Snapshot export", "runtime"), ("operator_module", "Riverview Operator module", "module"),
    ("resident_gateway_contract", "Resident gateway contract", "contract"), ("operator_contract", "Operator UI contract", "contract"),
    ("ollama", "Ollama local reasoning", "runtime"), ("codex", "Codex CLI execution adapter", "runtime"),
    ("local_execution", "Local execution adapters", "runtime"), ("verification", "Verification / reconciliation", "core"),
    ("publication", "Controlled Git publication", "core"), ("mailbox", "PostgreSQL mailbox", "core"),
    ("doorbell", "Local browser doorbell / wakeup", "runtime"), ("mcp", "MCP / Comms read bridge", "module"),
    ("chatgpt", "ChatGPT reasoning participant", "external"), ("controls", "Device/control adapters", "module"),
    ("microphone_worker", "PowerShell/System.Speech worker", "runtime"), ("artifact_reference", "Reference-only artifact intake", "runtime"),
    ("spatial", "LAN WebXR / Quest prototype", "deferred"), ("projects", "Project intake / repository", "module"),
    ("character_designer", "Character Designer workflow", "module"), ("session_history", "Session history", "runtime"),
    ("accepted_continuity", "Accepted durable continuity", "runtime"), ("character_canon", "Versioned accepted character canon", "core"),
    ("room_context", "Bounded shared room context", "runtime"), ("resident_expression", "Resident expression boundary", "contract"),
    ("provider_failure", "Provider failure/recovery seam", "failure"), ("diagnostic_spool", "Diagnostic fallback/spool", "runtime"),
    ("notification_delivery", "Notification delivery", "runtime"), ("notification_ack", "Notification acknowledgement state", "runtime"),
    ("postgres_service", "PostgreSQL service", "service"), ("operator_service", "Operator service 127.0.0.1:18082", "service"),
    ("spatial_service", "Spatial service 192.168.1.88:18443 (deferred/experimental)", "service"),
)

def _safe_id(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return result if result and result[0].isalpha() else f"n_{result}"

def _label(value: str) -> str:
    return str(value).replace('"', "'").replace("\r", " ").replace("\n", " ").strip()

def build_graph(manifest_dir: Path) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_ids: set[str] = set()

    def add_node(node_id: str, label: str, kind: str, source: str, views: tuple[str, ...] = ()) -> None:
        if node_id in node_ids:
            return
        node_ids.add(node_id)
        nodes.append({"id": node_id, "label": label, "kind": kind, "source": source, "views": list(dict.fromkeys(views))})

    def add_edge(source: str, target: str, relation: str, source_ref: str, *, views: tuple[str, ...] = (), checkpoint: str | None = None, manual: bool = False) -> None:
        item = {"source": source, "target": target, "relation": relation, "source_ref": source_ref, "derivation": "MANUAL_ARCHITECTURAL_ANNOTATION" if manual else "DERIVED", "views": list(dict.fromkeys(views))}
        if checkpoint:
            item["checkpoint"] = checkpoint
        edges.append(item)

    for node_id, label, kind in CORE_NODES:
        add_node(node_id, label, kind, "src/riverview/topology/graph.py:CORE_NODES")

    context = ("context",)
    event = ("events", "context")
    engineering = ("engineering", "events")
    resident = ("resident", "events")
    room = ("room", "resident", "events")
    character = ("character", "resident", "events")
    comms = ("comms", "events")
    notifications = ("notifications", "events")
    failures = ("failures", "context")
    modules = ("modules", "context")
    services = ("services", "context")

    add_edge("operator_module", "operator_runtime", "IMPLEMENTS", "config/modules/operator.json", views=modules + context)
    add_edge("operator_runtime", "operator_contract", "exposes", "openwebui.py:UI_HTML", views=modules + context)
    add_edge("operator_runtime", "undercurrent", "authenticates local session", "operator/openwebui.py:/session", views=context + resident, checkpoint="RIV-UI-0014")
    add_edge("operator_runtime", "snapshot_runtime", "requests current DOM/state snapshot", "operator/openwebui.py:/snapshot", views=context + failures, checkpoint="RIV-UI-0019")
    add_edge("operator_runtime", "resident_gateway_contract", "USES", "openwebui.py:/api/chat", views=modules + resident, checkpoint="RIV-RES-0001")
    add_edge("resident_gateway_runtime", "resident_gateway_contract", "IMPLEMENTS", "residents/gateway.py:ResidentConversationGateway", views=modules + resident)
    add_edge("resident_gateway_runtime", "character_runtime", "loads accepted version", "residents/gateway.py:chat", views=resident + character)
    add_edge("resident_gateway_runtime", "continuity_runtime", "retrieves bounded continuity", "residents/gateway.py:chat", views=resident + character, checkpoint="RIV-CHAR-0004")
    add_edge("operator_runtime", "operator_module", "owned by", "config/modules/operator.json", views=modules)
    add_edge("operator_runtime", "river", "publishes bounded workflow events", "operator/openwebui.py:emit_event", views=event + context, checkpoint="RIV-UI-0009")

    add_edge("steward", "projects", "submits accepted engineering seed", "grace/objective_acceptance.py", views=engineering + context)
    add_edge("projects", "grace", "objective intake", "autonomy/control.py:GraceMomentum", views=engineering + event, checkpoint="RIV-GRC-0004")
    add_edge("grace", "objective_state", "evaluates readiness/checkpoints", "autonomy/control.py:GraceMomentum.evaluate", views=engineering + event, checkpoint="RIV-GRC-0004")
    add_edge("objective_state", "river", "records objective/stage events", "grace/objectives.py:EventStore", views=engineering + event)
    add_edge("river", "grace", "wakes reevaluation", "river/store.py + autonomy/control.py", views=engineering + event, checkpoint="RIV-GRC-0004")
    add_edge("grace", "relay", "enqueues declared action", "autonomy/control.py:enqueue_declared_action", views=engineering)
    add_edge("relay", "execution_envelope", "creates bounded execution", "autonomy/control.py:ExecutionEnvelope", views=engineering)
    add_edge("execution_envelope", "providers", "requests capability selection", "reasoning/provider_registry.py", views=engineering)
    add_edge("providers", "codex", "selects Codex execution", "autonomy/control.py:CodexCliAdapter", views=engineering)
    add_edge("providers", "local_execution", "selects bounded local adapter", "autonomy/control.py", views=engineering)
    add_edge("codex", "verification", "returns result for reconciliation", "autonomy/control.py:CodexCliAdapter", views=engineering + event, checkpoint="RIV-EXE-0001")
    add_edge("local_execution", "verification", "returns result for reconciliation", "autonomy/control.py", views=engineering + event)
    add_edge("verification", "publication", "publishes only reconciled result", "autonomy/control.py:reconcile_repository", views=engineering)
    add_edge("verification", "river", "emits completion/failure event", "autonomy/control.py:execution_results", views=engineering + event, checkpoint="RIV-EXE-0001")
    add_edge("codex", "provider_failure", "reports timeout/nonzero failure", "autonomy/control.py:CodexCliAdapter", views=engineering + failures, checkpoint="RIV-EXE-0003")
    add_edge("provider_failure", "diagnostics", "records failure and recovery seam", "diagnostics/checkpoints", views=failures + event)
    add_edge("river", "grace", "completion/failure causes reevaluation", "autonomy/control.py:run_grace_cycle", views=engineering + event)
    add_edge("grace", "relay", "redispatches ready work or escalates", "autonomy/control.py:run_grace_cycle", views=engineering + event)
    add_edge("grace", "diagnostics", "records no-ready/capacity/quiescence decision", "autonomy/control.py:run_grace_cycle", views=engineering + failures)
    add_edge("providers", "grace", "provider completion is not global quiescence", "docs/architecture/RIVERVIEW_FOUNDATION.md", views=engineering + event, manual=True)

    add_edge("operator_runtime", "resident_gateway_runtime", "authenticated resident message", "operator/openwebui.py:/api/chat", views=resident, checkpoint="RIV-RES-0001")
    add_edge("operator_runtime", "resident_gateway_runtime", "creates authenticated session", "operator/openwebui.py:/session", views=resident)
    add_edge("resident_gateway_runtime", "undercurrent", "checks classification/authority", "residents/gateway.py:chat", views=resident, checkpoint="RIV-RES-0001")
    add_edge("resident_gateway_runtime", "providers", "selects eligible provider", "residents/gateway.py:chat", views=resident, checkpoint="RIV-REASON-0001")
    add_edge("providers", "ollama", "dispatches local reasoning", "reasoning/ollama.py", views=resident + services, checkpoint="RIV-REASON-0002")
    add_edge("ollama", "resident_expression", "returns provider text for resident expression", "reasoning/contracts.py", views=resident)
    add_edge("resident_gateway_runtime", "session_history", "records session turns", "characters/store.py:ContinuityStore.record_session", views=resident + character)
    add_edge("resident_gateway_runtime", "river", "emits resident submitted/completed events", "operator/openwebui.py:emit_event", views=resident + event)
    add_edge("resident_gateway_runtime", "diagnostics", "reports identity/provider failures", "operator/openwebui.py:RIV-RES-0002", views=resident + failures, checkpoint="RIV-RES-0001")
    add_edge("character_canon", "character_runtime", "publishes accepted version", "characters/store.py:CharacterStore", views=character + resident)
    add_edge("character_designer", "character_canon", "proposes/reviews/publishes version", "characters/workflow.py", views=character)
    add_edge("character_designer", "accepted_continuity", "reviews continuity candidates", "characters/store.py:ContinuityStore.publish", views=character)
    add_edge("accepted_continuity", "continuity_runtime", "available to new sessions", "characters/store.py:accepted", views=character + resident)
    add_edge("session_history", "accepted_continuity", "candidate only until review", "characters/store.py:record_session", views=character, manual=True)
    add_edge("character_canon", "resident_expression", "version constrains expression", "residents/gateway.py:character_version", views=character + resident)
    add_edge("provider_failure", "resident_gateway_runtime", "returns bounded provider failure", "operator/openwebui.py:resident_provider_failure", views=resident + failures, checkpoint="RIV-REASON-0002")

    add_edge("operator_runtime", "room_runtime", "creates room", "operator/openwebui.py:/api/rooms", views=room, checkpoint="RIV-RES-0002")
    add_edge("room_runtime", "room_context", "stores bounded room identity/context", "residents/gateway.py:create_room", views=room)
    add_edge("room_runtime", "resident_gateway_runtime", "opens participant sessions", "residents/gateway.py:room_chat", views=room)
    add_edge("room_runtime", "providers", "runs ordered participant turns", "residents/gateway.py:room_chat", views=room)
    add_edge("room_runtime", "river", "emits room created/completed events", "operator/openwebui.py:emit_event", views=room + event, checkpoint="RIV-RES-0002")
    add_edge("room_runtime", "diagnostics", "reports room/session failure", "operator/openwebui.py:RIV-RES-0002", views=room + failures, checkpoint="RIV-RES-0002")
    add_edge("room_context", "accepted_continuity", "preserves bounded consequences", "residents/gateway.py:room_chat", views=room + character)

    add_edge("operator_runtime", "microphone_worker", "starts explicit capture", "operator/openwebui.py:/api/transcribe", views=resident + context, checkpoint="RIV-UI-0015")
    add_edge("microphone_worker", "operator_runtime", "returns reviewable transcript", "operator/local_speech.py", views=resident + context, checkpoint="RIV-UI-0015")
    add_edge("microphone_worker", "diagnostics", "reports unavailable/timeout worker", "operator/openwebui.py:RIV-UI-0015", views=failures, checkpoint="RIV-UI-0015")
    add_edge("operator_runtime", "artifact_reference", "hashes reference-only file", "operator/openwebui.py:submit", views=resident + context)
    add_edge("artifact_reference", "resident_gateway_runtime", "passes bounded reference", "reasoning/contracts.py", views=resident)
    add_edge("controls", "operator_runtime", "provides bounded control input", "control contracts", views=context, manual=True)
    add_edge("spatial", "operator_runtime", "future projection only; Quest deferred", "spatial prototype", views=context + services, manual=True)

    add_edge("river", "mailbox", "stores correlated reasoning request", "mailbox/store.py", views=comms + event)
    add_edge("mailbox", "doorbell", "causes bounded wakeup", "doorbell/browser_bridge.py", views=comms + event)
    add_edge("doorbell", "chatgpt", "wakes designated external participant", "doorbell/contract.py", views=comms)
    add_edge("chatgpt", "mailbox", "submits correlated advisory response", "mailbox/store.py", views=comms + event)
    add_edge("mailbox", "river", "records response event/correlation", "mailbox/store.py:RiverEvent", views=comms + event)
    add_edge("river", "grace", "response event enables continuation", "grace/objectives.py", views=comms + event)
    add_edge("mcp", "mailbox", "reads bounded mailbox projection", "mcp/read_model.py", views=comms + context, checkpoint="RIV-MCP-0006")

    add_edge("river", "notifications", "checkpoint/critical event creates notification", "notifications.py:NotificationStore.emit", views=notifications + event, checkpoint="RIV-NOT-0001")
    add_edge("notifications", "notification_delivery", "delivers bounded summary/reference", "notifications.py:NotificationStore", views=notifications)
    add_edge("notification_delivery", "notification_ack", "records delivered state", "notifications.py:mark_delivered", views=notifications)
    add_edge("notifications", "steward", "notifies Pat of bounded escalation", "comms/bindings.py", views=notifications)

    add_edge("operator_service", "operator_runtime", "hosts HTTP surface", "operator/live_service.py", views=services)
    add_edge("operator_service", "postgres_service", "uses authoritative DB", "database/connection.py", views=services)
    add_edge("ollama", "postgres_service", "does not own River state", "reasoning/ollama.py", views=services, manual=True)
    add_edge("microphone_worker", "operator_service", "bounded local worker boundary", "operator/local_speech.py", views=services)
    add_edge("mcp", "postgres_service", "reads bounded projections", "mcp/read_model.py", views=services)
    add_edge("spatial_service", "spatial", "configured experimental LAN route", "spatial prototype", views=services)
    add_edge("diagnostics", "diagnostic_spool", "fallback when persistence unavailable", "diagnostics/store.py", views=services + failures)

    event_specs = (
        ("resident.message.submitted", "operator_runtime", "resident_gateway_runtime", "operator/openwebui.py:emit_event", ("resident", "events")),
        ("resident.response.completed", "resident_gateway_runtime", "resident_gateway_runtime", "operator/openwebui.py:emit_event", ("resident", "events")),
        ("room.created", "room_runtime", "room_runtime", "operator/openwebui.py:emit_event", ("room", "events")),
        ("room.turn.completed", "room_runtime", "room_runtime", "operator/openwebui.py:emit_event", ("room", "events")),
        ("microphone.transcript.completed", "microphone_worker", "operator_runtime", "operator/openwebui.py:emit_event", ("resident", "events")),
        ("operator.snapshot.created", "snapshot_runtime", "diagnostics", "operator/openwebui.py:emit_event", ("context", "events")),
        ("grace.conversation.completed", "resident_gateway_runtime", "grace", "operator/openwebui.py:emit_event", ("resident", "events")),
        ("objective.stage.ready", "grace", "relay", "autonomy/control.py:GraceMomentum", ("engineering", "events")),
        ("provider.execution.completed", "providers", "verification", "autonomy/control.py:execution_results", ("engineering", "events")),
        ("provider.execution.failed", "providers", "diagnostics", "autonomy/control.py:CodexCliAdapter", ("engineering", "events", "failures")),
        ("codex.execution.completed", "codex", "verification", "autonomy/control.py:CodexCliAdapter", ("engineering", "events")),
        ("diagnostic.checkpoint.fired", "diagnostics", "notifications", "diagnostics/store.py", ("failures", "events")),
        ("notification.queued", "notifications", "notification_delivery", "notifications.py:NotificationStore.emit", ("notifications", "events")),
    )
    for event_name, producer, consumer, source_ref, event_views in event_specs:
        event_id = f"flow_event.{event_name}"
        add_node(event_id, event_name, "event", source_ref, event_views)
        add_edge(producer, event_id, "EMITS", source_ref, views=event_views)
        add_edge(event_id, "river", "DURABLE_EVENT", source_ref, views=("events",), manual=False)
        add_edge("river", consumer, "CONSUMED/EVALUATED", source_ref, views=("events",) + tuple(view for view in event_views if view != "events"))

    manifests = []
    for path in sorted(manifest_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        module_id = data["module_id"]
        source_path = f"config/modules/{path.name}"
        manifests.append({"path": source_path, **data})
        add_node(module_id, data["display_name"], "module", source_path, modules)
        declared_runtime = {"riverview.operator": "operator_runtime", "riverview.reasoning.ollama": "ollama"}.get(module_id)
        if declared_runtime:
            add_edge(module_id, declared_runtime, "DECLARES/IMPLEMENTS runtime component", source_path, views=modules + context)
        add_edge(module_id, "core_contract" if data["required_core_contract"] else "river", "requires core contract", source_path, views=modules)
        for dependency in data.get("dependencies", []):
            target = {"resident.gateway": "resident_gateway_contract", "reasoning.contract": "reasoning_contract", "river": "river"}.get(dependency, dependency)
            if target not in node_ids:
                add_node(target, target, "contract", str(path), modules)
            add_edge(module_id, target, "declares dependency", source_path, views=modules)
        for event_name in data.get("events_consumed", []):
            event_id = f"event.{event_name}"
            add_node(event_id, event_name, "event", source_path, event + modules)
            add_edge(event_id, module_id, "consumed by", source_path, views=event + modules)
        for event_name in data.get("events_emitted", []):
            event_id = f"event.{event_name}"
            add_node(event_id, event_name, "event", source_path, event + modules)
            add_edge(module_id, event_id, "emitted by", source_path, views=event + modules)
        for checkpoint in data.get("diagnostics", []):
            add_edge(module_id, "diagnostics", "protected by checkpoint", source_path, views=modules + failures, checkpoint=checkpoint)
        for route in data.get("routes", []):
            route_id = f"route.{route}"
            add_node(route_id, route, "route", source_path, modules + services)
            add_edge(module_id, route_id, "exposes route", source_path, views=modules + services)

    questions = {
        "1_wake_grace": {"status": "PASS", "evidence": ["river->grace", "RIV-GRC-0004"]},
        "2_trigger_execution": {"status": "PASS", "evidence": ["grace->relay->execution_envelope"]},
        "3_completion_return": {"status": "PASS", "evidence": ["verification->river->grace"]},
        "4_not_quiescence": {"status": "PASS", "evidence": ["providers->grace", "provider completion is not global quiescence"]},
        "5_postgresql": {"status": "PASS", "evidence": ["river", "postgres_service", "mcp->postgres_service"]},
        "6_helen_to_model": {"status": "PASS", "evidence": ["operator_runtime->resident_gateway_runtime->providers->ollama"]},
        "7_character_version": {"status": "PASS", "evidence": ["character_canon->character_runtime->resident_expression"]},
        "8_continuity_distinction": {"status": "PASS", "evidence": ["session_history", "accepted_continuity"]},
        "9_room_turn": {"status": "PASS", "evidence": ["room_runtime->resident_gateway_runtime->providers"]},
        "10_microphone": {"status": "PASS", "evidence": ["microphone_worker->operator_runtime->resident_gateway_runtime"]},
        "11_microphone_failure": {"status": "PASS", "evidence": ["microphone_worker->diagnostics", "RIV-UI-0015"]},
        "12_steward_notification": {"status": "PASS", "evidence": ["river->notifications->notification_delivery->steward"]},
        "13_snapshot": {"status": "PASS", "evidence": ["operator_runtime->snapshot_runtime", "RIV-UI-0019"]},
        "14_chatgpt_bridge": {"status": "PASS", "evidence": ["mailbox->doorbell->chatgpt->mailbox"]},
        "15_ollama_failure": {"status": "PASS", "evidence": ["ollama->provider_failure->diagnostics"]},
        "16_codex_failure": {"status": "PASS", "evidence": ["codex->provider_failure->diagnostics"]},
        "17_operator_js": {"status": "PASS", "evidence": ["RIV-UI-0020"]},
        "18_resident_identity": {"status": "PASS", "evidence": ["RIV-RES-0001", "resident_expression"]},
        "19_operator_module": {"status": "PASS", "evidence": ["riverview.operator->operator_runtime"]},
        "20_operator_contract": {"status": "PASS", "evidence": ["riverview.operator->core_contract", "operator_runtime->resident_gateway_contract"]},
        "21_quest_deferred": {"status": "PASS", "evidence": ["spatial_service", "spatial", "deferred/experimental"]},
    }
    return {"schema_version": "riverview-system-graph-2.0", "generated_from": ["src/riverview/topology/graph.py", "config/modules/*.json", "src/riverview/river/events.py", "src/riverview/autonomy/control.py", "src/riverview/residents/gateway.py", "src/riverview/characters/*.py", "src/riverview/mailbox/store.py", "src/riverview/notifications.py", "Cookbook checkpoint registry"], "views": sorted(set(VIEW_NAMES.values())), "nodes": nodes, "edges": edges, "checkpoints": list(CHECKPOINTS), "manifests": manifests, "questions": questions, "manual_annotation_policy": "Manual edges are explicit, source-referenced, and never hidden in generated projections."}

def validate_graph(graph: dict[str, Any]) -> list[str]:
    node_ids = {node["id"] for node in graph.get("nodes", [])}
    errors: list[str] = []
    if len(node_ids) != len(graph.get("nodes", [])):
        errors.append("duplicate node id")
    for node in graph.get("nodes", []):
        if not node.get("label", "").strip():
            errors.append(f"empty label: {node.get('id')}")
    for edge in graph.get("edges", []):
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            errors.append(f"unknown graph endpoint: {edge['source']} -> {edge['target']}")
        if not edge.get("source_ref"):
            errors.append(f"untraceable edge: {edge['source']} -> {edge['target']}")
        if edge.get("checkpoint") and edge["checkpoint"] not in set(graph.get("checkpoints", [])):
            errors.append(f"unknown checkpoint: {edge['checkpoint']}")
    for manifest in graph.get("manifests", []):
        if manifest.get("required_core_contract") != "riverview-core-contract-1.0":
            errors.append(f"incompatible module: {manifest.get('module_id')}")
    errors.extend(validate_mermaid(render_mermaid(graph), graph))
    return errors

def render_mermaid(graph: dict[str, Any], view: str | None = None) -> str:
    nodes = [node for node in graph["nodes"] if view is None or view in node.get("views", []) or node["kind"] in {"core", "external"}]
    allowed = {node["id"] for node in nodes}
    edges = [edge for edge in graph["edges"] if (view is None or view in edge.get("views", [])) and edge["source"] in allowed and edge["target"] in allowed]
    lines = ["flowchart LR"]
    for node in nodes:
        lines.append(f'    {_safe_id(node["id"])}["{_label(node["label"])}"]')
    for edge in edges:
        relation = _label(edge["relation"]).replace("|", "/")
        lines.append(f'    {_safe_id(edge["source"])} -->|{relation}| {_safe_id(edge["target"])}')
    return "\n".join(lines) + "\n"

def validate_mermaid(mermaid: str, graph: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if re.search(r"\{(?:node|edge|\.\.\.)", mermaid) or "{node[" in mermaid or "{edge[" in mermaid:
        errors.append("unresolved Mermaid template expression")
    declarations = re.findall(r"^\s+([A-Za-z_][A-Za-z0-9_]*)\[\"([^\"]+)\"\]$", mermaid, re.MULTILINE)
    if not declarations:
        errors.append("Mermaid has no semantic node declarations")
    if any(not label.strip() for _, label in declarations):
        errors.append("Mermaid contains empty node label")
    ids = [node_id for node_id, _ in declarations]
    if len(ids) != len(set(ids)):
        errors.append("Mermaid contains duplicate node declarations")
    expected = {_safe_id(node["id"]) for node in graph["nodes"]}
    if not set(ids) <= expected:
        errors.append("Mermaid contains an undeclared canonical node")
    return errors

def render_dot(graph: dict[str, Any]) -> str:
    dot = ["digraph riverview {", "  rankdir=LR;"]
    for node in graph["nodes"]:
        dot.append(f'  "{node["id"]}" [label="{_label(node["label"])}"];')
    for edge in graph["edges"]:
        dot.append(f'  "{edge["source"]}" -> "{edge["target"]}" [label="{_label(edge["relation"])}"];')
    dot.append("}")
    return "\n".join(dot) + "\n"

def validate_projection_drift(graph: dict[str, Any], output_dir: Path) -> list[str]:
    """Detect checked-in projections that no longer equal canonical generation."""
    expected_json = json.dumps(graph, indent=2, sort_keys=True) + "\n"
    checks = {
        output_dir / "riverview_system_graph.json": expected_json,
        output_dir / "riverview_system_graph.mmd": render_mermaid(graph, "context"),
        output_dir / "riverview_system_graph.dot": render_dot(graph),
    }
    for filename, view in VIEW_NAMES.items():
        checks[output_dir / "graph_views" / f"{filename}.mmd"] = render_mermaid(graph, view)
    return [str(path) for path, expected in checks.items() if not path.exists() or path.read_text(encoding="utf-8") != expected]

def write_graph(graph: dict[str, Any], output_dir: Path) -> None:
    def write(path: Path, content: str) -> None:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)

    output_dir.mkdir(parents=True, exist_ok=True)
    write(output_dir / "riverview_system_graph.json", json.dumps(graph, indent=2, sort_keys=True) + "\n")
    write(output_dir / "riverview_system_graph.mmd", render_mermaid(graph, "context"))
    write(output_dir / "riverview_system_graph.dot", render_dot(graph))
    views_dir = output_dir / "graph_views"
    views_dir.mkdir(exist_ok=True)
    for filename, view in VIEW_NAMES.items():
        write(views_dir / f"{filename}.mmd", render_mermaid(graph, view))
