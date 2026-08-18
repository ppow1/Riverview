import json
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


def test_snapshot_exports_room_consistency_assertions():
    archive, _ = build_snapshot({
        "current_dom": "<html></html>",
        "resident_state": {"active_room_id": "room-1"},
        "room_state": {
            "room_id": "room-1", "participants": ["grace", "alfred"],
            "participant_profiles": [{"resident_id": "grace"}, {"resident_id": "alfred"}],
            "gateway_participant_ids": ["grace", "alfred"], "participant_count": 2,
            "room_projection_consistent": True, "inconsistency_classes": [],
        },
    }, service_identity="riverview-openwebui", service_url="http://127.0.0.1:18082/")
    with zipfile.ZipFile(BytesIO(archive)) as bundle:
        room = json.loads(bundle.read("room_state.json"))
        assert room["consistency"]["membership_vs_gateway"] is True
        assert room["consistency"]["membership_vs_profiles"] is True
        assert room["consistency"]["room_projection_consistent"] is True


def test_snapshot_preserves_activity_visible_projection_and_rendered_state() -> None:
    archive, _ = build_snapshot({
        "current_dom": "<html><body><div id='app'>shell</div><script>application source</script></body></html>",
        "rendered_state_html": "<div class='layout'><main id='primary'><h1>Activity</h1><li data-activity-id='2'>newest</li><li data-activity-id='1'>older</li></main></div>",
        "visible_state": {
            "schema_version": "riverview-visible-state-v1",
            "captured_at": "2026-08-18T12:00:00Z",
            "primary_view": "activity",
            "filters": {"activity_category": "work"},
            "pagination": {"activity": {"cursor": 42, "has_more": True}},
            "loading": {"activity": False},
            "errors": {"activity": None},
            "empty": {"activity": False},
            "views": {"activity": {"loaded_items": [{"activity_id": 1}, {"activity_id": 2}], "visible_items": [{"activity_id": 2}, {"activity_id": 1}]}},
        },
    }, service_identity="riverview-openwebui", service_url="http://127.0.0.1:18082/")
    with zipfile.ZipFile(BytesIO(archive)) as bundle:
        visible = json.loads(bundle.read("visible_state.json"))
        manifest = json.loads(bundle.read("manifest.json"))
        rendered = bundle.read("rendered_state.html").decode()
        assert visible["primary_view"] == "activity"
        assert visible["views"]["activity"]["visible_items"] == [{"activity_id": 2}, {"activity_id": 1}]
        assert visible["pagination"]["activity"]["has_more"] is True
        assert "data-activity-id='2'" in rendered
        assert manifest["schema_version"] == "riverview-snapshot-v2"
        assert manifest["rendered_state"]["artifact"] == "rendered_state.html"


def test_snapshot_declares_visible_state_truncation() -> None:
    archive, _ = build_snapshot({
        "current_dom": "<html></html>",
        "visible_state": {"primary_view": "activity", "views": {"activity": {"loaded_items": list(range(101))}}},
    }, service_identity="riverview-openwebui", service_url="http://127.0.0.1:18082/")
    with zipfile.ZipFile(BytesIO(archive)) as bundle:
        visible = json.loads(bundle.read("visible_state.json"))
        assert visible["truncation"]["truncated"] is True
        assert visible["truncation"]["paths"]


def test_snapshot_declares_total_visible_state_bound() -> None:
    archive, _ = build_snapshot({
        "current_dom": "<html></html>",
        "visible_state": {"primary_view": "activity", "views": {"activity": {"loaded_items": [{"summary": "x" * 4000} for _ in range(100)]}}},
    }, service_identity="riverview-openwebui", service_url="http://127.0.0.1:18082/")
    with zipfile.ZipFile(BytesIO(archive)) as bundle:
        visible = json.loads(bundle.read("visible_state.json"))
        assert visible["truncation"]["truncated"] is True
        assert "visible_state.total_bytes" in visible["truncation"]["paths"]
