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


def build_snapshot(payload: dict[str, Any], *, service_identity: str, service_url: str, pid: int | None = None) -> tuple[bytes, str]:
    generated = datetime.now(UTC)
    dom = _safe_dom(str(payload.get("current_dom", "")))
    if not dom or len(dom.encode("utf-8")) > MAX_CAPTURE_BYTES:
        raise ValueError("RIV-UI-0019: current DOM is missing or exceeds the bounded snapshot size.")
    safe_payload = _redact(payload)
    safe_payload.pop("current_dom", None)
    safe_payload["page_url"] = str(payload.get("page_url") or service_url)
    runtime = {
        "capture_timestamp": generated.isoformat(), "service_identity": service_identity,
        "service_pid": pid or os.getpid(), "git_sha": _git_sha(), "working_directory": os.getcwd(),
        "service_url": service_url, "health": "live", "provider_identities": safe_payload.get("provider_identities", []),
        "resident_registry_summary": safe_payload.get("api_state", {}).get("residents", safe_payload.get("resident_state", {})), "room": safe_payload.get("room_state", {}),
        "diagnostic_checkpoint_ids": [row.get("checkpoint_id") for row in _diagnostics()],
    }
    resident_state = safe_payload.get("resident_state", {})
    room_state = safe_payload.get("room_state", {})
    files: dict[str, str] = {
        "README.txt": f"Riverview Operator manual debug snapshot.\nCaptured: {generated.isoformat()}\nURL: {safe_payload['page_url']}\nGit SHA: {runtime['git_sha']}\nSecrets and selected file bytes are excluded or redacted.\n",
        "current_dom.html": dom,
        "ui_state.json": json.dumps(safe_payload, indent=2, default=str, sort_keys=True),
        "runtime.json": json.dumps(_redact(runtime), indent=2, default=str, sort_keys=True),
        "resident_state.json": json.dumps(_redact(resident_state), indent=2, default=str, sort_keys=True),
        "room_state.json": json.dumps(_redact(room_state), indent=2, default=str, sort_keys=True),
        "diagnostics.json": json.dumps(_diagnostics(), indent=2, default=str, sort_keys=True),
        "api_state.json": json.dumps(_redact(safe_payload.get("api_state", {})), indent=2, default=str, sort_keys=True),
    }
    manifest = {"schema_version": "riverview-snapshot-v1", "generated_at": generated.isoformat(), "service": service_identity,
                "git_sha": runtime["git_sha"], "page_url": safe_payload["page_url"], "capture_reason": "manual_operator_snapshot",
                "files": list(files) + ["manifest.json"], "redaction_applied": True}
    files["manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    filename = f"riverview-snapshot-{generated:%Y%m%d-%H%M%S}.zip"
    return output.getvalue(), filename
