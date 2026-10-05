import json
import os
import time
import zipfile
from pathlib import PureWindowsPath
import pytest

from riverview.snail.runtime import SnailRuntime
from riverview.snail.validator import validate_reasoning


@pytest.fixture
def snail(tmp_path):
    runtime = SnailRuntime(tmp_path / "runtime")
    runtime.start()
    state = runtime.state
    state["evidence_refs"].append("EVD-1")
    runtime.store.save_state(state)
    return runtime


def action(operation_id="op-1", command="Write-Output ok", **extra):
    return {"operation_id": operation_id, "operation_type": "write_harmless_marker", "target": "OCTO1", "command": command, "language": "powershell", "evidence_ids": ["EVD-1"], "state_changing": True, **extra}


def response(**extra):
    value = {"interpretation": "bounded qualification", "evidence_used": ["EVD-1"], "hypothesis": "marker can be safely written", "proposed_action": action(), "expected_result": "marker exists", "pass_condition": "marker observed", "fail_condition": "marker absent", "timeout": 5, "confidence": 0.9, "escalation_required": False}
    value.update(extra)
    return value


def test_persistence_and_append_integrity(snail):
    first = snail.state["current_event_id"]
    recovered = SnailRuntime(snail.store.root)
    assert recovered.state["current_event_id"] == first
    assert recovered.store.verify_events()


def test_reasoning_contract_and_malformed_rejection(snail):
    packet = snail.build_reasoning_packet()
    assert packet["response_contract"]
    assert snail.accept_reasoning(response())
    assert not snail.accept_reasoning({"interpretation": "incomplete"})
    assert not validate_reasoning({**response(), "confidence": 2}).accepted


@pytest.mark.parametrize("script", ["if ($x) { 1 } else { 2 }", "ELSE\n{bad}", "# else is still rejected before any execution"])
def test_absolute_powershell_else_rejection(snail, script):
    called = False
    def executor(_):
        nonlocal called
        called = True
    assert not snail.execute(action(command=script), executor, lambda *_: True)
    assert not called
    assert snail.store.events()[-1]["type"] == "VALIDATION_REJECTED_NO_ELSE_POLICY"


def test_validator_scope_authority_evidence_and_syntax(snail):
    assert not snail.validate(action(target="OCTO2")).accepted
    assert not snail.validate(action(operation_type="bios_flash")).accepted
    assert not snail.validate(action(evidence_ids=[])).accepted
    assert not snail.validate(action(destructive=True)).accepted


def test_execute_verify_checkpoint_and_duplicate_prevention(snail):
    calls = []
    operation = action()
    assert snail.execute(operation, lambda _: calls.append("write") or "ok", lambda _, output: output == "ok")
    assert not snail.execute(operation, lambda _: calls.append("duplicate"), lambda *_: True)
    assert calls == ["write"]
    assert list(snail.store.checkpoints.glob("*.json"))


def test_controls_are_durable_append_only(snail):
    snail.command("UPDATE_TASK", "new bounded task")
    snail.command("UPDATE_DIRECTION", "new constraint")
    snail.command("INQUIRY", "why?")
    snail.command("PAUSE")
    assert snail.state["snail_state"] == "PAUSED"
    SnailRuntime(snail.store.root).command("RESUME")
    assert snail.state["snail_state"] == "RECOVERING"
    snail.command("PHYSICAL_WORK_COMPLETE", "cable reseated")
    assert snail.state["snail_state"] == "RECOVERING"
    assert any(e["status"] == "VERIFICATION_REQUIRED" for e in snail.store.events())


def test_stop_is_checkpointed_and_resumable(snail):
    snail.command("STOP")
    assert snail.state["snail_state"] == "STOPPED"
    recovered = SnailRuntime(snail.store.root)
    recovered.command("RESUME")
    assert recovered.state["snail_state"] == "RECOVERING"
    assert recovered.state["reconciliation_required"]


def test_control_queue_names_are_windows_safe_and_preserve_timestamp(snail):
    pause = snail.store.enqueue_control("PAUSE")
    stop = snail.store.enqueue_control("STOP")
    queued = snail.store.pending_controls()

    assert [request["command"] for request in queued] == ["PAUSE", "STOP"]
    assert queued[0]["timestamp"] == pause["timestamp"]
    assert queued[1]["timestamp"] == stop["timestamp"]
    assert ":" in pause["timestamp"] and ":" in stop["timestamp"]
    for request in queued:
        name = PureWindowsPath(request["_path"]).name
        assert not set('<>:"/\\|?*').intersection(name)
        assert name.endswith(f"-{request['request_id']}.json")
    assert not list(snail.store.controls.glob(".*"))


def test_worker_loss_boot_change_pid_replacement_and_packet_rebuild(snail):
    snail.worker_observation({"state": "80B_READY", "boot_id": "boot-a", "pid": "1"})
    transaction = snail.build_reasoning_packet()["transaction_id"]
    snail.worker_observation({"state": "OCTO2_UNREACHABLE", "boot_id": "boot-a", "pid": None})
    assert snail.state["snail_state"] == "WAITING_FOR_WORKER"
    snail.worker_observation({"state": "80B_READY", "boot_id": "boot-b", "pid": "2"})
    assert snail.state["snail_state"] == "READY"
    assert snail.state["pending_reasoning"]["transaction_id"] == transaction
    kinds = [event["type"] for event in snail.store.events()]
    assert "OCTO2_REBOOT_CONFIRMED" in kinds
    snail.worker_observation({"state": "80B_READY", "boot_id": "boot-b", "pid": "3"})
    assert "WORKER_PID_REPLACED" in [event["type"] for event in snail.store.events()]


def test_unreachable_without_boot_change_is_not_reboot(snail):
    snail.worker_observation({"state": "80B_READY", "boot_id": "same", "pid": "1"})
    snail.worker_observation({"state": "OCTO2_UNREACHABLE", "boot_id": "same", "pid": None})
    snail.worker_observation({"state": "80B_READY", "boot_id": "same", "pid": "1"})
    assert "OCTO2_REBOOT_CONFIRMED" not in [event["type"] for event in snail.store.events()]


def test_frame_staleness_and_immutable_preservation(snail, tmp_path):
    latest = tmp_path / "latest.jpg"
    latest.write_bytes(b"first-frame")
    os.utime(latest, (time.time() - 20, time.time() - 20))
    assert snail.frame_status(latest)["stale"]
    record = snail.preserve_frame(latest, "console", 0.8)
    immutable = snail.store.evidence / record["file"]
    latest.write_bytes(b"second-frame")
    assert immutable.read_bytes() == b"first-frame"
    assert json.loads((snail.store.evidence / f"{record['evidence_id']}.json").read_text())["class"] == "OBSERVED"


def test_snapshot_contains_review_packet_and_evidence(snail, tmp_path):
    frame = tmp_path / "latest.jpg"
    frame.write_bytes(b"frame")
    snail.preserve_frame(frame)
    archive = snail.snapshot("path review")
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        review = package.read("REVIEW_PACKET.md").decode()
    assert "Is SNAIL still on the correct engineering path?" in review
    assert any(name.startswith("evidence/EVD-") for name in names)


def test_harmless_recovery_qualification_without_conversation_memory(tmp_path):
    runtime = SnailRuntime(tmp_path / "qualification")
    runtime.start()
    source = tmp_path / "observed.txt"
    source.write_text("precondition", encoding="utf-8")
    evidence = runtime.store.preserve(source, {"kind": "qualification_precondition"})
    state = runtime.state
    state["evidence_refs"].append(evidence["evidence_id"])
    runtime.store.save_state(state)
    packet = runtime.build_reasoning_packet()
    operation = action(operation_id="qualification-marker", evidence_ids=[evidence["evidence_id"]])
    result = response(proposed_action=operation, evidence_used=[evidence["evidence_id"]])
    assert runtime.accept_reasoning(result)
    marker = tmp_path / "marker"
    assert runtime.execute(operation, lambda _: marker.write_text("once", encoding="utf-8"), lambda *_: marker.read_text() == "once")
    runtime.worker_observation({"state": "OCTO2_UNREACHABLE", "boot_id": "a", "pid": None})
    del runtime
    fresh = SnailRuntime(tmp_path / "qualification")
    assert fresh.state["snail_state"] == "WAITING_FOR_WORKER"
    fresh.worker_observation({"state": "80B_READY", "boot_id": "b", "pid": "10"})
    rebuilt = fresh.build_reasoning_packet()
    assert rebuilt["campaign"] == packet["campaign"]
    assert not fresh.execute(operation, lambda _: marker.write_text("twice"), lambda *_: True)
    assert marker.read_text() == "once"
    assert fresh.snapshot("qualification").exists()
