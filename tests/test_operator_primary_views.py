import json
from urllib.request import Request, urlopen
from uuid import uuid4

from riverview.operator.openwebui import OpenWebUIConfig, RiverviewOpenWebUIService


def _session(port: int) -> str:
    with urlopen(Request(f"http://127.0.0.1:{port}/session", method="POST")) as response:
        return response.headers["Set-Cookie"].split(";", 1)[0]


def test_clean_operator_template_owns_mutually_exclusive_primary_views() -> None:
    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18091, bearer_token="view-test"), lambda model, request: None)
    service.start()
    try:
        cookie = _session(18091)
        with urlopen(Request("http://127.0.0.1:18091/", headers={"Cookie": cookie})) as response:
            html = response.read().decode()
        assert "const validViews=new Set" in html
        assert "function renderApp()" in html
        assert "showRoomDialog2" not in html
        assert "sendRoomAware2" not in html
        assert "stopImmediatePropagation" not in html
        assert "Authoritative work projection is not available" not in html
        assert '<div id="app"></div>' in html
        assert html.count("function renderPrimaryView(") == 1
        assert "data-primary-view" in html
        assert "recentPrimaryMutations" in html
        assert "function mountPrimary(" in html
        assert "MutationObserver" not in html
        assert "function renderSettingsView(generation=state.viewGeneration)" in html
    finally:
        service.stop()


def test_primary_view_controller_has_generation_ownership_and_functional_settings() -> None:
    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18093, bearer_token="view-race-test"), lambda model, request: None)
    service.start()
    try:
        cookie = _session(18093)
        with urlopen(Request("http://127.0.0.1:18093/", headers={"Cookie": cookie})) as response:
            html = response.read().decode()
        assert "state.primaryView===view&&state.viewGeneration===generation" in html
        assert "requestedView:view" in html
        assert "state.primaryView!==view||state.viewGeneration!==generation" in html
        assert "settings-clean-list" in html
        assert "/api/conversations/bulk" in html
        assert "Reset Operator preferences" in html
        assert "data-voice-test" in html
        assert "addVoicePreviewControls" not in html
        assert "function startActivityRefresh(" in html
        assert "function scheduleActivityRefresh(" in html
        assert "activityRequestInFlight" in html
        assert "document.addEventListener('visibilitychange'" in html
        assert "state.activityDirty=true" in html
        assert 'id="activity-list"' in html
    finally:
        service.stop()


def test_neutral_conversation_assigns_resident_without_changing_id_and_activity_is_durable() -> None:
    service = RiverviewOpenWebUIService(OpenWebUIConfig(port=18092, bearer_token="activity-test"), lambda model, request: None)
    service.start()
    try:
        cookie = _session(18092)
        headers = {"Cookie": cookie, "Content-Type": "application/json"}
        create = Request("http://127.0.0.1:18092/api/conversations", data=json.dumps({"resident_id": "", "title": "New Conversation"}).encode(), method="POST", headers=headers)
        with urlopen(create) as response:
            neutral = json.load(response)
        assign = Request(f"http://127.0.0.1:18092/api/conversations/{neutral['id']}", data=json.dumps({"resident_id": "RES-000001", "title": "Alfred Conversation"}).encode(), method="PUT", headers=headers)
        with urlopen(assign) as response:
            assigned = json.load(response)
        assert assigned["id"] == neutral["id"]
        assert assigned["resident_id"] == "RES-000001"
        assert assigned["title"] == "Alfred Conversation"

        service.emit_event("resident.response.completed", "resident", "RES-000001", uuid4(), {"summary": "Bounded activity test"})
        activity_request = Request("http://127.0.0.1:18092/api/activity?after=0&limit=100&category=all", headers={"Cookie": cookie})
        with urlopen(activity_request) as response:
            activity = json.load(response)
        match = [item for item in activity["items"] if item["event_type"] == "resident.response.completed"]
        assert match
        assert match[-1]["category"] == "river"
        assert activity["next_cursor"] >= match[-1]["river_sequence"]
    finally:
        service.stop()
