import zipfile
from io import BytesIO

import pytest

from riverview.operator.snapshot import build_snapshot


def payload():
    return {
        "current_dom": '<html><input id="token" value="Bearer TOP-SECRET"><select id="resident">Helen</select><pre id="result">correlation_id=abc</pre></html>',
        "title": "Riverview Operator", "visible_status": "Completed", "selected_resident": "RES-000003",
        "active_resident_display": "Helen · session: session-1", "composer": "Good evening, Helen.",
        "result": '{"correlation_id":"abc","response":"safe"}', "correlation_ids": ["abc"],
        "artifact_refs": ["browser-artifact:photo.png:hash"], "room_id": "room-1",
        "room_state": {"room_id": "room-1", "participants": ["Helen", "Alfred"]},
        "resident_state": {"selected_resident": "RES-000003", "session_ids": {"RES-000003": "session-1"}},
        "provider_identities": ["ollama:qwen"], "authorization": "Bearer TOP-SECRET", "cookie": "rv_session=SECRET",
    }


def test_snapshot_contains_live_state_and_redacts_secrets_without_payload_bytes():
    archive, filename = build_snapshot(payload(), service_identity="riverview-openwebui", service_url="http://127.0.0.1:18082/", pid=123)
    assert filename.startswith("riverview-snapshot-") and filename.endswith(".zip")
    with zipfile.ZipFile(BytesIO(archive)) as bundle:
        names = set(bundle.namelist())
        assert {"README.txt", "manifest.json", "current_dom.html", "ui_state.json", "runtime.json", "resident_state.json", "room_state.json", "diagnostics.json", "api_state.json"} <= names
        contents = "\n".join(bundle.read(name).decode("utf-8") for name in names)
        assert "TOP-SECRET" not in contents
        assert "rv_session=SECRET" not in contents
        assert "photo.png" in contents
        assert "correlation_id" in contents
        assert "Helen" in contents
        assert b"TOP-SECRET" not in archive


def test_snapshot_rejects_missing_or_oversized_dom():
    with pytest.raises(ValueError):
        build_snapshot({"current_dom": ""}, service_identity="riverview-openwebui", service_url="http://127.0.0.1:18082/")
    with pytest.raises(ValueError):
        build_snapshot({"current_dom": "x" * 512_001}, service_identity="riverview-openwebui", service_url="http://127.0.0.1:18082/")
