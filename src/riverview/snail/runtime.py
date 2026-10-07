from __future__ import annotations

import json
import uuid
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .config import load_config
from .store import DurableStore, utcnow
from .validator import validate_action, validate_reasoning

STATES = {"STARTING", "PREFLIGHT", "READY", "OBSERVING", "REASONING", "VALIDATING", "EXECUTING", "VERIFYING", "WAITING_FOR_WORKER", "WAITING_FOR_STEWARD", "PAUSING", "PAUSED", "RECOVERING", "STOPPING", "STOPPED", "ABORTING", "ERROR"}


class SnailRuntime:
    def __init__(self, root: Path, config_path: Path | None = None):
        self.store = DurableStore(root)
        self.config = load_config(config_path)
        if not self.store.load_state():
            self.store.save_state(self._initial_state())
        else:
            self._migrate_state()

    def _initial_state(self) -> dict[str, Any]:
        return {
            "version": "1.0", "campaign_id": self.config["campaign_id"], "campaign_name": self.config["name"],
            "phase": "C1 PHYSICAL QUALIFICATION PREP", "objective": self.config["objective"], "task": self.config["initial_task"],
            "direction": self.config.get("authority_model", "Execute the approved campaign toward the objective using qualified paths and durable verification."),
            "snail_state": "STOPPED", "event_sequence": 0, "current_event_id": None, "last_event_id": None,
            "hypothesis": None, "evidence_refs": [], "pending_reasoning": None, "pending_operation": None,
            "next_proposed_action": "Stage and verify the validated C1 candidate, then continue the approved physical qualification sequence", "verified_operation_ids": [],
            "worker": {"state": "UNKNOWN", "boot_id": None, "pid": None}, "last_verified_machine_state": {"baseline": "C0", "bios_mutations": 0},
            "pause_requested": False, "checkpoint_time": None, "steward_intervention_required": False,
            "qualification": "C1 OFFLINE VALIDATED; PHYSICAL QUALIFICATION PENDING",
            "coordinator_stage": "OBSERVE", "pending_execution": None,
            "reconciliation_required": True, "last_reconciled_at": None,
            "failure_counts": {}, "intervention": None, "latest_evidence_id": None,
            "campaign_status": "ACTIVE",
            "last_known_worker_boot_id": None, "last_known_worker_pid": None,
        }

    def _migrate_state(self) -> None:
        state = self.store.load_state()
        defaults = self._initial_state()
        changed = False
        for key, value in defaults.items():
            if key not in state:
                state[key] = value
                changed = True
        legacy_planning = (
            state.get("phase") == "C1 PLANNING"
            and state.get("task") == "Generate the C1 BIOS planning proposal for Steward/external review"
            and "no C1 mutation without later Steward/external-review authorization" in str(state.get("direction", ""))
        )
        if legacy_planning and self.config.get("campaign_go_authorized"):
            state["phase"] = "C1 PHYSICAL QUALIFICATION PREP"
            state["objective"] = self.config["objective"]
            state["task"] = self.config["initial_task"]
            state["direction"] = self.config["authority_model"]
            state["qualification"] = "C1 OFFLINE VALIDATED; PHYSICAL QUALIFICATION PENDING"
            state["next_proposed_action"] = "Stage and verify the validated C1 candidate, then continue the approved physical qualification sequence"
            state["steward_intervention_required"] = False
            state["intervention"] = None
            if state.get("snail_state") == "WAITING_FOR_STEWARD":
                state["snail_state"] = "RECOVERING"
                state["reconciliation_required"] = True
            changed = True
        if changed:
            self.store.save_state(state)

    @property
    def state(self) -> dict[str, Any]:
        return self.store.load_state()

    def _event(self, kind: str, *, actor: str = "SNAIL", status: str = "OK", evidence: list[str] | None = None, details: dict | None = None, before: str | None = None) -> dict:
        state = self.state
        event = self.store.append_event({"actor": actor, "type": kind, "state_before": before or state["snail_state"], "state_after": state["snail_state"], "evidence": evidence or [], "details": details or {}, "status": status})
        state["last_event_id"] = state.get("current_event_id")
        state["current_event_id"] = event["event_id"]
        state["event_sequence"] = int(event["event_id"].split("-")[-1])
        self.store.save_state(state)
        return event

    def transition(self, new: str, kind: str, **kwargs: Any) -> dict:
        if new not in STATES:
            raise ValueError(f"unknown state {new}")
        state = self.state
        before = state["snail_state"]
        state["snail_state"] = new
        self.store.save_state(state)
        return self._event(kind, before=before, **kwargs)

    def start(self) -> dict:
        state = self.state
        if state["snail_state"] == "READY":
            return state
        self.transition("STARTING", "RUNTIME_STARTING")
        self.transition("PREFLIGHT", "PREFLIGHT_STARTED")
        if not self.store.verify_events():
            self.transition("ERROR", "EVENT_CHAIN_CORRUPT", status="ERROR")
            raise RuntimeError("event chain corrupt")
        self.transition("READY", "RUNTIME_READY")
        self.checkpoint()
        return self.state

    def prepare_for_coordinator(self) -> dict:
        state = self.state
        if state["campaign_status"] == "ABORTED" or state["snail_state"] in {
            "PAUSED",
            "WAITING_FOR_STEWARD",
            "ERROR",
        }:
            return state
        self.transition("STARTING", "COORDINATOR_STARTING")
        self.transition("PREFLIGHT", "COORDINATOR_PREFLIGHT")
        if not self.store.verify_events():
            self.transition("ERROR", "EVENT_CHAIN_CORRUPT", status="ERROR")
            raise RuntimeError("event chain corrupt")
        state = self.state
        state["reconciliation_required"] = True
        state["steward_intervention_required"] = False
        self.store.save_state(state)
        self.checkpoint()
        return self.state

    def checkpoint(self) -> Path:
        state = self.state
        path = self.store.checkpoint(state)
        self._event("CHECKPOINT_WRITTEN", details={"path": str(path)})
        return path

    def command(self, command: str, value: str | None = None) -> dict:
        """Apply a control synchronously; production surfaces should enqueue controls."""
        return self.apply_control(command, value)

    def apply_control(
        self,
        command: str,
        value: str | None = None,
        *,
        request_id: str | None = None,
    ) -> dict:
        command = command.upper().replace(" ", "_")
        state = self.state
        if command == "START":
            if state["campaign_status"] == "ABORTED":
                raise ValueError("aborted campaign cannot be restarted")
            if state["snail_state"] == "WAITING_FOR_STEWARD":
                raise ValueError("resolve intervention with RESUME or PHYSICAL WORK COMPLETE")
            state["reconciliation_required"] = True
            state["steward_intervention_required"] = False
            state["intervention"] = None
            self.store.save_state(state)
            self.transition("RECOVERING", "STEWARD_START_REQUESTED", actor="STEWARD")
        elif command == "PAUSE":
            state["pause_requested"] = True
            self.store.save_state(state)
            self.transition("PAUSING", "STEWARD_PAUSE_REQUESTED", actor="STEWARD")
            self.transition("PAUSED", "SAFE_BOUNDARY_PAUSED")
        elif command == "STOP":
            self.transition("STOPPING", "STEWARD_STOP_REQUESTED", actor="STEWARD")
            self.checkpoint()
            self.transition("STOPPED", "RUNTIME_STOPPED")
        elif command == "RESUME":
            self.transition("RECOVERING", "STEWARD_RESUME_REQUESTED", actor="STEWARD")
            state = self.state
            state["pause_requested"] = False
            state["reconciliation_required"] = True
            state["steward_intervention_required"] = False
            state["intervention"] = None
            self.store.save_state(state)
            self._event("MACHINE_STATE_REVERIFY_REQUIRED")
        elif command == "ABORT":
            self.transition("ABORTING", "STEWARD_ABORT_REQUESTED", actor="STEWARD")
            state = self.state
            state["campaign_status"] = "ABORTED"
            self.store.save_state(state)
            self.transition("STOPPED", "CAMPAIGN_ABORTED", status="ABORTED")
        elif command in {"UPDATE_TASK", "UPDATE_DIRECTION"}:
            if not value:
                raise ValueError("value required")
            field = "task" if command == "UPDATE_TASK" else "direction"
            old = state[field]
            state[field] = value
            self.store.save_state(state)
            self._event(f"STEWARD_{command}", actor="STEWARD", details={"old": old, "new": value})
        elif command == "INQUIRY":
            self._event("STEWARD_INQUIRY", actor="STEWARD", details={"question": value or ""})
        elif command == "PHYSICAL_WORK_COMPLETE":
            self._event("PHYSICAL_WORK_REPORTED", actor="STEWARD", status="VERIFICATION_REQUIRED", details={"report": value or ""})
            state = self.state
            state["reconciliation_required"] = True
            state["steward_intervention_required"] = False
            state["intervention"] = None
            self.store.save_state(state)
            self.transition("RECOVERING", "INDEPENDENT_PHYSICAL_VERIFICATION_REQUIRED")
        elif command == "SNAPSHOT":
            self.snapshot(value or "Steward requested external review")
        else:
            raise ValueError(f"unknown command {command}")
        if request_id:
            self._event("STEWARD_CONTROL_APPLIED", actor="STEWARD", details={"request_id": request_id, "command": command})
        self.checkpoint()
        return self.state

    def build_reasoning_packet(self, *, fresh_transaction: bool = False) -> dict[str, Any]:
        state = self.state
        events = self.store.events()[-20:]
        packet = {
            "transaction_id": (
                str(uuid.uuid4())
                if fresh_transaction
                else (state.get("pending_reasoning") or {}).get("transaction_id")
                or str(uuid.uuid4())
            ),
            "campaign": state["campaign_name"], "objective": state["objective"], "phase": state["phase"],
            "task": state["task"], "state": state["snail_state"], "hard_constraints": [state["direction"], "PowerShell must contain no else token", "Descriptor and ME writes are outside campaign scope", "Stock recovery requires Steward authorization"],
            "steward_direction": state["direction"], "proven_facts": ["C0 is the booting baseline", "PiKVM HID and independent video1 observation are proven", "BIOS-grade vision is unqualified"],
            "known_failures": ["KVMD API acceptance alone does not prove physical delivery", "Reachability loss alone does not prove reboot"],
            "evidence": state["evidence_refs"], "hypothesis": state["hypothesis"], "recent_events": [{k: e.get(k) for k in ("event_id", "type", "status", "evidence")} for e in events],
            "pending_decision": state.get("pending_operation") or state["next_proposed_action"],
            "response_contract": sorted(__import__("riverview.snail.validator", fromlist=["REASONING_FIELDS"]).REASONING_FIELDS),
        }
        state["pending_reasoning"] = {"transaction_id": packet["transaction_id"], "packet": packet, "created_at": utcnow()}
        self.store.save_state(state)
        self._event("REASONING_PACKET_BUILT", details={"transaction_id": packet["transaction_id"]})
        return packet

    def record_reasoning_response(self, transaction_id: str, response: Any) -> Path:
        path = self.store.root / "reasoning" / f"{transaction_id}.response.json"
        self.store._write_json(path, response)
        state = self.state
        pending = state.get("pending_reasoning") or {}
        pending.update({"transaction_id": transaction_id, "response_path": str(path), "responded_at": utcnow()})
        state["pending_reasoning"] = pending
        self.store.save_state(state)
        self._event("REASONING_RESPONSE_PERSISTED", details={"transaction_id": transaction_id, "path": str(path)})
        return path

    def accept_reasoning(self, response: Any) -> bool:
        result = validate_reasoning(response)
        self._event("REASONING_ACCEPTED" if result.accepted else "REASONING_REJECTED", status=result.code, evidence=response.get("evidence_used", []) if isinstance(response, dict) else [], details={"reason": result.reason})
        if not result.accepted:
            return False
        state = self.state
        state["hypothesis"] = {"class": "HYPOTHESIS", "text": response["hypothesis"], "evidence_ids": response["evidence_used"]}
        state["pending_operation"] = response["proposed_action"]
        self.store.save_state(state)
        return True

    def validate(self, action: dict[str, Any]):
        state = self.state
        before = state["snail_state"]
        state["snail_state"] = "VALIDATING"
        self.store.save_state(state)
        result = validate_action(action, self.state, self.config)
        state = self.state
        state["snail_state"] = "READY"
        self.store.save_state(state)
        self._event("ACTION_VALIDATED" if result.accepted else result.code, status=result.code, evidence=action.get("evidence_ids", []), details={"operation_id": action.get("operation_id"), "reason": result.reason}, before=before)
        return result

    def execute(self, action: dict[str, Any], executor: Callable[[dict], Any], verifier: Callable[[dict, Any], bool]) -> bool:
        result = self.validate(action)
        if not result.accepted:
            return False
        self.transition("EXECUTING", "EXECUTION_STARTED", details={"operation_id": action["operation_id"]})
        output = executor(action)
        self.transition("VERIFYING", "EFFECT_OBSERVATION_STARTED")
        verified = verifier(action, output)
        state = self.state
        if verified:
            state["verified_operation_ids"].append(action["operation_id"])
            state["pending_operation"] = None
            self.store.save_state(state)
            self.transition("READY", "OPERATION_VERIFIED", evidence=action["evidence_ids"], details={"operation_id": action["operation_id"]})
            self.checkpoint()
            return True
        self.transition("WAITING_FOR_STEWARD", "OPERATION_VERIFICATION_FAILED", status="FAILED")
        return False

    def worker_observation(self, worker: dict[str, Any]) -> None:
        state = self.state
        previous = deepcopy(state["worker"])
        state["worker"] = worker
        self.store.save_state(state)
        if worker["state"] != "80B_READY":
            self.transition("WAITING_FOR_WORKER", "WORKER_UNAVAILABLE", details={"previous": previous, "current": worker})
            self.checkpoint()
            return
        if previous.get("boot_id") and worker.get("boot_id") != previous.get("boot_id"):
            self._event("OCTO2_REBOOT_CONFIRMED", details={"old_boot_id": previous["boot_id"], "new_boot_id": worker["boot_id"]})
        elif previous.get("pid") and worker.get("pid") != previous.get("pid"):
            self._event("WORKER_PID_REPLACED", details={"old_pid": previous["pid"], "new_pid": worker["pid"]})
        self.transition("RECOVERING", "WORKER_READY_RECOVERY")
        if self.state.get("pending_reasoning"):
            self.build_reasoning_packet()
        self.transition("READY", "WORKER_TRANSACTION_RESUMABLE")

    def ingest_octo2_monitor(self, monitor_state: Path) -> None:
        """Consume the existing DEV monitor V2 projection without replacing its witness."""
        observed = json.loads(monitor_state.read_text(encoding="utf-8-sig"))
        self.worker_observation({
            "state": observed.get("state", "UNKNOWN"),
            "boot_id": observed.get("boot_id") or self.state["worker"].get("boot_id"),
            "pid": observed.get("llama_pid") or None,
            "observed_at": observed.get("timestamp"),
        })

    def frame_status(self, latest: Path) -> dict[str, Any]:
        if not latest.exists():
            return {"available": False, "stale": True, "age_seconds": None, "source": str(latest)}
        age = max(0.0, datetime.now(timezone.utc).timestamp() - latest.stat().st_mtime)
        return {"available": True, "stale": age > self.config["frame_freshness_seconds"], "age_seconds": round(age, 1), "source": str(latest), "resolution": None}

    def preserve_frame(self, latest: Path, interpretation: str | None = None, confidence: float | None = None) -> dict:
        record = self.store.preserve(latest, {"kind": "video1_frame", "interpretation": interpretation, "confidence": confidence})
        state = self.state
        if record["evidence_id"] not in state["evidence_refs"]:
            state["evidence_refs"].append(record["evidence_id"])
            self.store.save_state(state)
        self._event("EVIDENCE_CAPTURED", evidence=[record["evidence_id"]], details={"source": str(latest)})
        return record

    def snapshot(self, reason: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        target = self.store.snapshots / f"snail-review-{stamp}-{uuid.uuid4().hex[:6]}.zip"
        state, events = self.state, self.store.events()
        review = self._review_packet(state, events, reason)
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("REVIEW_PACKET.md", review)
            archive.writestr("state.json", json.dumps(state, indent=2))
            archive.writestr("events.jsonl", "".join(json.dumps(e, sort_keys=True) + "\n" for e in events))
            for evidence_id in state["evidence_refs"]:
                for path in self.store.evidence.glob(f"{evidence_id}*"):
                    archive.write(path, f"evidence/{path.name}")
        self._event("SNAPSHOT_CREATED", actor="STEWARD", details={"path": str(target), "reason": reason})
        return target

    def _review_packet(self, state: dict, events: list[dict], reason: str) -> str:
        recent = "\n".join(f"- {e['event_id']} {e['type']} [{e['status']}] evidence={e['evidence']}" for e in events[-20:]) or "- None"
        return f"""# SNAIL External Review Packet\n\nGenerated: {utcnow()}\nReason for review: {reason}\n\n## Authority\nCampaign: {state['campaign_name']}\nPhase: {state['phase']}\nObjective: {state['objective']}\nTask: {state['task']}\nSNAIL state: {state['snail_state']}\nCurrent event: {state['current_event_id']}\nLast event: {state['last_event_id']}\n\n## Worker\nState: {state['worker']['state']}\nBoot ID: {state['worker']['boot_id']}\nPID: {state['worker']['pid']}\n\n## Engineering position\nVerified facts: C0 is the booting baseline; infrastructure/HID/video observation are qualified.\nHypothesis: {json.dumps(state['hypothesis'])}\nContradictions: None recorded in authoritative state.\nPending operation: {json.dumps(state['pending_operation'])}\nNext proposed action: {state['next_proposed_action']}\nEvidence references: {', '.join(state['evidence_refs']) or 'None'}\nChanges since previous snapshot: see append-only events below.\n\n## Recent significant events\n{recent}\n\n## Review question\nIs SNAIL still on the correct engineering path?\n"""
