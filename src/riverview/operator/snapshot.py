"""Bounded, redacted browser debug snapshot export."""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from typing import Any

from riverview.database import connect

MAX_CAPTURE_BYTES = 512_000
MAX_RENDERED_STATE_BYTES = 256_000
MAX_VISIBLE_STATE_BYTES = 256_000
MAX_VISIBLE_ITEMS = 100
MAX_VISIBLE_TEXT = 4_000
_SECRET_KEYS = {"token", "bearer", "authorization", "cookie", "set-cookie", "password", "secret", "api_key", "apikey"}
_SECRET_TEXT = re.compile(r"(?i)(bearer\s+)[^\s<\"']+|((?:token|authorization|cookie|password|secret)\s*[=:]\s*)[^\s,;}<\"']+")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if str(key).casefold().replace("-", "_") in _SECRET_KEYS else _redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return _SECRET_TEXT.sub(lambda match: (match.group(1) or match.group(2) or "") + "[REDACTED]", value)
    return value


def _safe_dom(dom: str) -> str:
    dom = _SECRET_TEXT.sub(lambda match: (match.group(1) or match.group(2) or "") + "[REDACTED]", dom)
    def redact_token_input(match: re.Match[str]) -> str:
        tag = match.group(0)
        if re.search(r'(?i)\bid=["\']token["\']', tag):
            return re.sub(r'(?i)\svalue=["\'][^"\']*["\']', ' value="[REDACTED]"', tag)
        return tag
    return re.sub(r'(?is)<input\b[^>]*>', redact_token_input, dom)


def _bound_visible_state(value: Any, *, path: str = "visible_state") -> tuple[Any, list[str]]:
    """Redact and bound client-visible state without silently losing evidence."""
    truncated: list[str] = []
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            bounded, nested = _bound_visible_state(item, path=f"{path}.{key}")
            result[str(key)] = bounded
            truncated.extend(nested)
        return result, truncated
    if isinstance(value, list):
        items = value
        if len(items) > MAX_VISIBLE_ITEMS:
            truncated.append(path)
            items = items[:MAX_VISIBLE_ITEMS]
        result = []
        for index, item in enumerate(items):
            bounded, nested = _bound_visible_state(item, path=f"{path}[{index}]")
            result.append(bounded)
            truncated.extend(nested)
        return result, truncated
    if isinstance(value, str) and len(value) > MAX_VISIBLE_TEXT:
        truncated.append(path)
        return value[:MAX_VISIBLE_TEXT], truncated
    return _redact(value), truncated


def _visible_state(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("visible_state", {})
    bounded, truncated = _bound_visible_state(raw)
    if not isinstance(bounded, dict):
        bounded = {"value": bounded}
        truncated.append("visible_state")
    bounded.setdefault("schema_version", "riverview-visible-state-v1")
    bounded["truncation"] = {"truncated": bool(truncated), "paths": truncated[:100]}
    encoded_size = len(json.dumps(bounded, default=str, separators=(",", ":")).encode("utf-8"))
    if encoded_size > MAX_VISIBLE_STATE_BYTES:
        # Preserve the view identity and the Activity projection first. The
        # omitted secondary projections are declared rather than silently
        # disappearing from the forensic artifact.
        preserved = {key: bounded[key] for key in ("schema_version", "captured_at", "primary_view", "secondary_view", "selected", "filters", "sort", "pagination", "loading", "errors", "empty") if key in bounded}
        views = bounded.get("views")
        if isinstance(views, dict) and isinstance(views.get("activity"), dict):
            preserved["views"] = {"activity": views["activity"]}
        preserved["truncation"] = {"truncated": True, "paths": [*truncated[:99], "visible_state.total_bytes"], "original_bytes": encoded_size}
        bounded = preserved
    return _redact(bounded)


def _git_sha() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=2, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _diagnostics() -> list[dict[str, Any]]:
    try:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT checkpoint_id,component,operation,severity,failure_class,summary,recovery_state,occurred_at
                             FROM diagnostic_events WHERE checkpoint_id LIKE 'RIV-UI-%' OR checkpoint_id LIKE 'RIV-RES-%' OR checkpoint_id LIKE 'RIV-REASON-%'
                             ORDER BY occurred_at DESC LIMIT 25""")
            columns = [item.name for item in cursor.description]
            return [_redact(dict(zip(columns, row, strict=True))) for row in cursor.fetchall()]
    except (OSError, RuntimeError, TypeError, ValueError):
        return []


def _events() -> list[dict[str, Any]]:
    """Return only bounded River lineage metadata; never event payloads."""
    try:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT event_id,event_type,aggregate_type,aggregate_id,correlation_id,causation_id,occurred_at
                             FROM river_events ORDER BY sequence_id DESC LIMIT 25""")
            columns = [item.name for item in cursor.description]
            return [_redact(dict(zip(columns, row, strict=True))) for row in cursor.fetchall()]
    except (OSError, RuntimeError, TypeError, ValueError):
        return []


def build_snapshot(payload: dict[str, Any], *, service_identity: str, service_url: str, pid: int | None = None) -> tuple[bytes, str]:
    generated = datetime.now(UTC)
    dom = _safe_dom(str(payload.get("current_dom", "")))
    if not dom or len(dom.encode("utf-8")) > MAX_CAPTURE_BYTES:
        raise ValueError("RIV-UI-0019: current DOM is missing or exceeds the bounded snapshot size.")
    safe_payload = _redact(payload)
    safe_payload.pop("current_dom", None)
    visible_state = _visible_state(payload)
    rendered_state = _safe_dom(str(payload.get("rendered_state_html", "")))
    rendered_state_truncated = False
    if len(rendered_state.encode("utf-8")) > MAX_RENDERED_STATE_BYTES:
        rendered_state = rendered_state.encode("utf-8")[:MAX_RENDERED_STATE_BYTES].decode("utf-8", errors="ignore")
        rendered_state += "\n<!-- RIV-UI-0019: rendered state truncated -->"
        rendered_state_truncated = True
    if not rendered_state:
        rendered_state = "<!-- RIV-UI-0019: rendered state was unavailable at capture time -->"
    safe_payload["page_url"] = str(payload.get("page_url") or service_url)
    room_state = safe_payload.get("room_state", {})
    if isinstance(room_state, dict) and room_state:
        participants = list(room_state.get("active_participant_ids", room_state.get("participants", ())) or ())
        profiles = list(room_state.get("participant_profiles", ()) or ())
        gateway = list(room_state.get("gateway_participant_ids", ()) or ())
        conversation_room_id = str(room_state.get("room_id", ""))
        active_room_id = str(safe_payload.get("resident_state", {}).get("active_room_id", room_state.get("active_room_id", conversation_room_id)) or conversation_room_id)
        room_state["consistency"] = {
            "membership_vs_gateway": participants == gateway,
            "membership_vs_profiles": len(participants) == len(profiles) and {str(item) for item in participants} == {str(item.get("resident_id")) for item in profiles if isinstance(item, dict)},
            "active_room_matches_conversation_room_id": not active_room_id or not conversation_room_id or active_room_id == conversation_room_id,
            "header_projection_matches_room_projection": int(room_state.get("participant_count", len(participants)) or 0) == len(participants),
            "room_projection_consistent": bool(room_state.get("room_projection_consistent", True)) and not bool(room_state.get("inconsistency_classes")),
        }
    runtime = {
        "capture_timestamp": generated.isoformat(), "service_identity": service_identity,
        "service_pid": pid or os.getpid(), "git_sha": _git_sha(), "working_directory": os.getcwd(),
        "service_url": service_url, "health": "live", "provider_identities": safe_payload.get("provider_identities", []),
        "resident_registry_summary": safe_payload.get("api_state", {}).get("residents", safe_payload.get("resident_state", {})), "room": safe_payload.get("room_state", {}),
        "diagnostic_checkpoint_ids": [row.get("checkpoint_id") for row in _diagnostics()],
        "recent_event_lineage": _events(),
    }
    resident_state = safe_payload.get("resident_state", {})
    files: dict[str, str] = {
        "README.txt": f"Riverview Operator manual debug snapshot.\nCaptured: {generated.isoformat()}\nURL: {safe_payload['page_url']}\nGit SHA: {runtime['git_sha']}\nSecrets and selected file bytes are excluded or redacted.\n",
        "current_dom.html": dom,
        "ui_state.json": json.dumps(safe_payload, indent=2, default=str, sort_keys=True),
        "runtime.json": json.dumps(_redact(runtime), indent=2, default=str, sort_keys=True),
        "resident_state.json": json.dumps(_redact(resident_state), indent=2, default=str, sort_keys=True),
        "room_state.json": json.dumps(_redact(room_state), indent=2, default=str, sort_keys=True),
        "diagnostics.json": json.dumps(_diagnostics(), indent=2, default=str, sort_keys=True),
        "api_state.json": json.dumps(_redact(safe_payload.get("api_state", {})), indent=2, default=str, sort_keys=True),
        "visible_state.json": json.dumps(visible_state, indent=2, default=str, sort_keys=True),
        "rendered_state.html": rendered_state,
    }
    manifest = {"schema_version": "riverview-snapshot-v2", "generated_at": generated.isoformat(), "service": service_identity,
                "git_sha": runtime["git_sha"], "page_url": safe_payload["page_url"], "capture_reason": "manual_operator_snapshot",
                "files": list(files) + ["manifest.json"], "redaction_applied": True,
                "visible_state": {"artifact": "visible_state.json", "schema_version": visible_state.get("schema_version"), "truncated": visible_state.get("truncation", {}).get("truncated", False)},
                "rendered_state": {"artifact": "rendered_state.html", "truncated": rendered_state_truncated},
                "provenance": {"client_capture_timestamp": visible_state.get("captured_at"), "server_capture_timestamp": generated.isoformat(), "atomic": False}}
    files["manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    filename = f"riverview-snapshot-{generated:%Y%m%d-%H%M%S}.zip"
    return output.getvalue(), filename
