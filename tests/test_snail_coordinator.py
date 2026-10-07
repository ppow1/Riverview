from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json

from riverview.snail.adapters import LocalPlanningAdapter
from riverview.snail.coordinator import SnailCoordinator
from riverview.snail.runtime import SnailRuntime
from riverview.snail.worker import ReasoningWorker


def reasoning(action: dict, confidence: float = 0.95) -> dict:
    return {
        "interpretation": "durable evidence supports the bounded operation",
        "evidence_used": action["evidence_ids"],
        "hypothesis": "the bounded artifact can be created and read back",
        "proposed_action": action,
        "expected_result": "the fixed local artifact contains the proposed bytes",
        "pass_condition": "independent read-back matches",
        "fail_condition": "artifact absent or mismatched",
        "timeout": 5,
        "confidence": confidence,
        "escalation_required": False,
    }


class ScriptedWorker:
    def __init__(self, responses):
        self.responses = list(responses)
        self.packets = []

    def reason(self, packet):
        self.packets.append(packet)
        return self.responses.pop(0)


@dataclass
class SequencedObserver:
    states: list[str]
    boot_id: str = "boot-a"
    pid: str = "100"
    calls: int = 0

    def observe(self):
        state = self.states[min(self.calls, len(self.states) - 1)]
        self.calls += 1
        return {
            "observed_at": f"sample-{self.calls}",
            "worker": {
                "state": state,
                "boot_id": self.boot_id if state != "OCTO2_UNREACHABLE" else None,
                "pid": self.pid if state == "80B_READY" else None,
            },
            "target": {"identity": "OCTO1", "state": "UNCHANGED"},
            "frame": {"available": False, "path": "latest.jpg"},
        }


class RecordingAdapter(LocalPlanningAdapter):
    def __init__(self, store, executions):
        super().__init__(store)
        self.executions = executions

    def execute(self, action):
        self.executions.append(action["operation_id"])
        return super().execute(action)


def operation(operation_id: str, operation_type: str, evidence_id: str, content: str) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": operation_type,
        "target": "OCTO1",
        "command": content,
        "language": "text",
        "evidence_ids": [evidence_id],
        "state_changing": True,
        "destructive": False,
    }


def test_autonomous_end_to_end_and_fresh_process_recovery(tmp_path: Path):
    root = tmp_path / "snail"
    runtime = SnailRuntime(root)
    evidence_source = tmp_path / "precondition.txt"
    evidence_source.write_text("qualified harmless path", encoding="utf-8")
    evidence = runtime.store.preserve(evidence_source, {"kind": "qualification_precondition"})
    state = runtime.state
    state["evidence_refs"].append(evidence["evidence_id"])
    runtime.store.save_state(state)

    marker = operation("qualified-marker", "write_harmless_marker", evidence["evidence_id"], "SNAIL-QUALIFIED")
    first_worker = ScriptedWorker([reasoning(marker)])
    executions = []
    first = SnailCoordinator(
        runtime,
        first_worker,
        SequencedObserver(["80B_READY", "80B_READY", "OCTO2_UNREACHABLE"]),
        RecordingAdapter(runtime.store, executions),
        poll_seconds=0,
    )
    first.run(max_cycles=12)

    assert runtime.state["snail_state"] == "WAITING_FOR_WORKER"
    assert runtime.state["verified_operation_ids"] == ["qualified-marker"]
    assert executions == ["qualified-marker"]
    assert first_worker.packets and first_worker.packets[0]["evidence"]

    # Destroy every original runtime/coordinator dependency and reconstruct from disk.
    del first, runtime, first_worker
    recovered = SnailRuntime(root)
    duplicate = operation("qualified-marker", "write_harmless_marker", evidence["evidence_id"], "SNAIL-QUALIFIED")
    proposal = operation(
        "c1-planning-proposal",
        "planning_proposal",
        evidence["evidence_id"],
        "# Candidate C1 Planning Proposal\n\nNo firmware mutation is authorized.\n",
    )
    second_worker = ScriptedWorker([reasoning(duplicate), reasoning(proposal)])
    second = SnailCoordinator(
        recovered,
        second_worker,
        SequencedObserver(["80B_READY"], boot_id="boot-b", pid="200"),
        RecordingAdapter(recovered.store, executions),
        poll_seconds=0,
    )
    second.run(max_cycles=30)

    state = recovered.state
    assert state["snail_state"] != "WAITING_FOR_STEWARD"
    assert not state["steward_intervention_required"]
    assert state["last_known_worker_boot_id"] == "boot-b"
    assert executions == ["qualified-marker", "c1-planning-proposal"]
    assert len(second_worker.packets) == 2
    assert second_worker.packets[0]["campaign"] == second_worker.packets[1]["campaign"]
    assert (root / "artifacts" / "C1_PLANNING_PROPOSAL.md").exists()
    assert list((root / "snapshots").glob("*.zip"))
    assert recovered.store.verify_events()
    assert any(event["type"] == "OCTO2_REBOOT_CONFIRMED" for event in recovered.store.events())


def test_confidence_and_repeated_identical_failure_gates(tmp_path: Path):
    runtime = SnailRuntime(tmp_path / "runtime")
    source = tmp_path / "evidence.txt"
    source.write_text("observed", encoding="utf-8")
    evidence = runtime.store.preserve(source, {"kind": "precondition"})
    action = operation("low-confidence", "write_harmless_marker", evidence["evidence_id"], "safe")
    low = reasoning(action, confidence=0.2)
    worker = ScriptedWorker([low, low, low])
    coordinator = SnailCoordinator(
        runtime,
        worker,
        SequencedObserver(["80B_READY"]),
        RecordingAdapter(runtime.store, []),
        poll_seconds=0,
    )
    coordinator.run(max_cycles=30)
    assert runtime.state["snail_state"] == "WAITING_FOR_STEWARD"
    assert runtime.state["intervention"]["code"] == "REPEATED_IDENTICAL_FAILURE"
    assert not runtime.state["verified_operation_ids"]


def test_uncertain_execution_is_verified_before_replay(tmp_path: Path):
    runtime = SnailRuntime(tmp_path / "runtime")
    source = tmp_path / "evidence.txt"
    source.write_text("observed", encoding="utf-8")
    evidence = runtime.store.preserve(source, {"kind": "precondition"})
    action = operation("crash-window", "write_harmless_marker", evidence["evidence_id"], "already happened")
    adapter = LocalPlanningAdapter(runtime.store)
    adapter.execute(action)
    state = runtime.state
    state["pending_execution"] = {"status": "EXECUTION_UNCERTAIN", "action": action}
    state["reconciliation_required"] = True
    runtime.store.save_state(state)

    fresh = SnailRuntime(runtime.store.root)
    executions = []
    coordinator = SnailCoordinator(
        fresh,
        ScriptedWorker([]),
        SequencedObserver(["80B_READY"]),
        RecordingAdapter(fresh.store, executions),
        poll_seconds=0,
    )
    coordinator.run(max_cycles=4)
    assert "crash-window" in fresh.state["verified_operation_ids"]
    assert executions == []


def test_queued_pause_stop_and_physical_work_controls_drive_coordinator(tmp_path: Path):
    runtime = SnailRuntime(tmp_path / "runtime")
    coordinator = SnailCoordinator(
        runtime,
        ScriptedWorker([]),
        SequencedObserver(["80B_READY"]),
        LocalPlanningAdapter(runtime.store),
        poll_seconds=0,
    )
    runtime.store.enqueue_control("PAUSE")
    coordinator.run(max_cycles=2)
    assert runtime.state["snail_state"] == "PAUSED"
    runtime.store.enqueue_control("PHYSICAL_WORK_COMPLETE", "cable reseated")
    runtime.store.enqueue_control("RESUME")
    coordinator.run(max_cycles=3)
    assert runtime.state["last_reconciled_at"]
    runtime.store.enqueue_control("STOP")
    coordinator.run(max_cycles=2)
    assert runtime.state["snail_state"] == "STOPPED"


def test_production_reasoning_worker_uses_openai_compatible_endpoint(tmp_path: Path):
    evidence_id = "EVD-http"
    action = operation("http-worker", "write_harmless_marker", evidence_id, "safe")
    expected = reasoning(action)
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            requests.append(json.loads(body))
            payload = {"choices": [{"message": {"content": json.dumps(expected)}}]}
            encoded = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        packet = {"transaction_id": "durable", "response_contract": list(expected)}
        result = ReasoningWorker(
            f"http://127.0.0.1:{server.server_address[1]}/v1/chat/completions",
            timeout=2,
        ).reason(packet)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result == expected
    assert requests[0]["messages"][1]["content"] == json.dumps(packet, sort_keys=True)
