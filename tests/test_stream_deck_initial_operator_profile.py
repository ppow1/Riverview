import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "config/stream_deck/Riverview-Initial-Operator-Profile.json"
ACTION = ROOT / "tools/powershell/stream_deck/Invoke-RiverviewStreamDeckControl.ps1"
NATIVE_PROFILE = ROOT / "config/stream_deck/native_profile/manifest.json"
NATIVE_PAGE = ROOT / "config/stream_deck/native_profile/Profiles/7C0C9D36-8B7F-4D71-9D45-2B6B1C05D0A1/manifest.json"
NATIVE_PLUGIN = ROOT / "tools/powershell/stream_deck/riverview-native-plugin"


def test_profile_has_exactly_three_bounded_controls():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert [key["control"] for key in data["keys"]] == ["runtime", "quest-dev", "quest-cast"]
    assert len(data["keys"]) == 3
    assert data["version"] == "1.0.0"


def test_each_control_maps_all_gestures_to_same_bounded_action():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    for key in data["keys"]:
        for gesture in ("single_tap", "double_tap", "long_press"):
            args = key[gesture]
            assert args[0:2] == ["-Control", key["control"]]
            expected = gesture.removesuffix("_tap").removesuffix("_press")
            assert args[2:4] == ["-Gesture", expected]


def test_action_layer_contains_required_boundaries_without_transient_endpoint():
    text = ACTION.read_text(encoding="utf-8")
    assert "Start-RiverviewRuntimeSupervisor.ps1" in text
    assert "Start-ScheduledTask" in text
    assert "QuestMirror" in text
    assert "mdns services" in text
    assert "tcpip 5555" in text
    assert "Meta Quest Developer Hub" in text
    assert "adb-1WMHHB67ZF1473" not in text
    assert "192.168.1.159" not in text
    assert "C:\\Program Files\\PowerShell\\7\\pwsh.exe" in text


def test_cast_and_dev_paths_are_independent():
    text = ACTION.read_text(encoding="utf-8")
    cast = text[text.index("function Invoke-QuestCast"):]
    dev = text[text.index("function Invoke-QuestDev"):text.index("function Invoke-QuestCast")]
    assert "adb" not in cast.lower()
    assert "QuestMirror" in dev
    assert "Invoke-QuestCast" not in dev


def test_native_profile_is_exactly_three_controls():
    root = json.loads(NATIVE_PROFILE.read_text(encoding="utf-8"))
    page = json.loads(NATIVE_PAGE.read_text(encoding="utf-8"))
    actions = page["Controllers"][0]["Actions"]
    assert root["Name"] == "Riverview"
    assert root["Pages"]["Current"] == root["Pages"]["Default"]
    assert len([action for action in actions.values() if action.get("Plugin", {}).get("UUID") == "com.riverview.operator"]) == 3
    assert [actions[key]["UUID"] for key in ("0,0", "1,0", "2,0")] == [
        "com.riverview.operator.runtime",
        "com.riverview.operator.quest-dev",
        "com.riverview.operator.quest-cast",
    ]
    assert actions["5,3"]["UUID"] == "com.elgato.streamdeck.page.previous"
    assert actions["7,3"]["UUID"] == "com.elgato.streamdeck.page.next"
    assert actions["7,1"]["UUID"] == "com.elgato.streamdeck.profile.rotate"
    assert actions["7,2"]["UUID"] == "com.elgato.streamdeck.profile.rotate"
    assert actions["7,1"]["Settings"]["ProfileUUID"] == "d4abffcd-7bde-4db7-856b-b26823e1780b"
    assert actions["7,2"]["Settings"]["ProfileUUID"] == "9c576814-c3e0-4d5b-9b5d-dda437f9a89a"


def test_native_plugin_preserves_gesture_and_estate_separation():
    manifest = json.loads((NATIVE_PLUGIN / "manifest.json").read_text(encoding="utf-8"))
    plugin = (NATIVE_PLUGIN / "plugin.js").read_text(encoding="utf-8")
    assert manifest["StreamdeckID"] == "com.riverview.operator"
    assert manifest["CategoryIcon"] == "images/riverview"
    assert (NATIVE_PLUGIN / "images/riverview.svg").exists()
    assert "LONG_PRESS_MS = 1250" in plugin
    assert "DOUBLE_TAP_MS = 400" in plugin
    assert "com.estate" not in plugin
    assert manifest["CodePathWin"] == "RiverviewOperator.cmd"


def test_native_plugin_uses_verified_execution_and_live_status_sources():
    plugin = (NATIVE_PLUGIN / "plugin.js").read_text(encoding="utf-8")
    assert 'const POWERSHELL = "C:\\\\Program Files\\\\PowerShell\\\\7\\\\pwsh.exe"' in plugin
    assert 'const ADB = "C:\\\\Users\\\\wille\\\\Downloads\\\\platform-tools-latest-windows\\\\platform-tools\\\\adb.exe"' in plugin
    assert 'http://127.0.0.1:18082/health' in plugin
    assert 'status control=' in plugin
    assert 'setInterval(() => refreshVisibleContexts' in plugin
    assert 'detached: true' not in plugin
    assert 'async function questMirrorRunning()' in plugin
    assert 'value: "LIVE"' in plugin
    assert 'value: "RUNNING"' in plugin
