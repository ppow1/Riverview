from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Protocol

from .adapters import EnvironmentObserver, OperationAdapter
from .runtime import SnailRuntime
from .store import utcnow
from .worker import WorkerResponseError


class Worker(Protocol):
    def reason(self, packet: dict[str, Any]) -> dict[str, Any]: ...


BLOCKED_STATES = {"PAUSED", "STOPPED", "ABORTING", "ERROR", "WAITING_FOR_STEWARD"}


class SnailCoordinator:
    """The single production state-machine owner for autonomous campaign progression."""

    def __init__(
        self,
        runtime: SnailRuntime,
        worker: Worker,
        observer: EnvironmentObserver,
        adapter: OperationAdapter,
        *,
        poll_seconds: float = 2.0,
    ):
        self.runtime = runtime
        self.worker = worker
        self.observer = observer
        self.adapter = adapter
        self.poll_seconds = poll_seconds
        self._wake = threading.Event()
        self._shutdown = threading.Event()

    def wake(self) -> None:
        self._wake.set()

    def run(self, max_cycles: int | None = None) -> None:
        self.runtime.prepare_for_coordinator()
        cycles = 0
        while not self._shutdown.is_set():
            progressed = self.step()
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                return
            if self.runtime.state["snail_state"] == "STOPPED":
                return
            if not progressed:
                self._wake.wait(self.poll_seconds)
                self._wake.clear()

    def step(self) -> bool:
        self._process_controls()
        state = self.runtime.state
        if state["snail_state"] in BLOCKED_STATES:
            return False
        if state["snail_state"] == "WAITING_FOR_WORKER":
            return self._observe_worker_recovery()
        if state.get("reconciliation_required"):
            return self._reconcile()
        stage = state.get("coordinator_stage", "OBSERVE")
        if stage == "OBSERVE":
            return self._observe()
        if stage == "REASON":
            return self._reason()
        if stage == "VALIDATE":
            return self._validate()
        if stage == "EXECUTE":
            return self._execute()
        if stage == "VERIFY":
            return self._verify()
        if stage == "CONTINUE":
            return self._continue()
        self._intervene("IMPOSSIBLE_STATE", f"Unknown coordinator stage: {stage}", [], "Inspect durable state before resuming.")
        return True

    def _save_stage(self, stage: str) -> None:
        state = self.runtime.state
        state["coordinator_stage"] = stage
        self.runtime.store.save_state(state)

    def _process_controls(self) -> None:
        for request in self.runtime.store.pending_controls():
            command = request["command"]
            try:
                self.runtime.apply_control(
                    command,
                    request.get("value"),
                    request_id=request["request_id"],
                )
            except ValueError as exc:
                self.runtime._event(
                    "STEWARD_CONTROL_REJECTED",
                    actor="STEWARD",
                    status="REJECTED",
                    details={"request_id": request["request_id"], "command": command, "reason": str(exc)},
                )
            finally:
                self.runtime.store.complete_control(request)
            if command in {"STOP", "ABORT"}:
                self._shutdown.set()

    def _observe_environment(
        self,
        *,
        record_unchanged: bool = True,
        observation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        observation = observation or self.observer.observe()
        previous_observation = self.runtime.state.get("last_observation")
        if not record_unchanged and observation == previous_observation:
            return observation
        encoded = json.dumps(observation, indent=2, sort_keys=True).encode()
        source = self.runtime.store.root / "observations" / "latest-environment.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(encoded)
        evidence = self.runtime.store.preserve(source, {"kind": "environment_observation"})
        state = self.runtime.state
        state["last_observation"] = observation
        if observation["worker"].get("boot_id"):
            state["last_known_worker_boot_id"] = observation["worker"]["boot_id"]
        if observation["worker"].get("pid"):
            state["last_known_worker_pid"] = observation["worker"]["pid"]
        state["worker"] = observation["worker"]
        state["latest_evidence_id"] = evidence["evidence_id"]
        if evidence["evidence_id"] not in state["evidence_refs"]:
            state["evidence_refs"].append(evidence["evidence_id"])
        self.runtime.store.save_state(state)
        self.runtime._event("ENVIRONMENT_OBSERVED", evidence=[evidence["evidence_id"]])
        return observation

    def _observe(self) -> bool:
        self.runtime.transition("OBSERVING", "AUTONOMOUS_OBSERVATION_STARTED")
        observation = self._observe_environment()
        worker = observation["worker"]
        if worker.get("state") != "80B_READY":
            self.runtime.transition("WAITING_FOR_WORKER", "WORKER_UNAVAILABLE", details={"worker": worker})
            self.runtime.checkpoint()
            return True
        self.runtime.transition("READY", "OBSERVATION_COMPLETE")
        self._save_stage("REASON")
        self.runtime.checkpoint()
        return True

    def _reason(self) -> bool:
        self.runtime.transition("REASONING", "REASONING_STARTED")
        packet = self.runtime.build_reasoning_packet(fresh_transaction=True)
        try:
            response = self.worker.reason(packet)
        except WorkerResponseError as exc:
            self._failure("MALFORMED_REASONING", str(exc), "worker returned malformed structured output")
            return True
        except Exception as exc:
            self.runtime._event("REASONING_WORKER_FAILED", status="FAILED", details={"error": str(exc)})
            state = self.runtime.state
            state["worker"] = {**state["worker"], "state": "80B_CALL_FAILED"}
            self.runtime.store.save_state(state)
            self.runtime.transition("WAITING_FOR_WORKER", "WORKER_UNAVAILABLE")
            self.runtime.checkpoint()
            return True
        self.runtime.record_reasoning_response(packet["transaction_id"], response)
        confidence = response.get("confidence") if isinstance(response, dict) else None
        if isinstance(confidence, (int, float)) and confidence < self.runtime.config["minimum_confidence"]:
            self._failure("LOW_CONFIDENCE", response, f"confidence {confidence} is below {self.runtime.config['minimum_confidence']}")
            return True
        if not self.runtime.accept_reasoning(response):
            self._failure("MALFORMED_REASONING", response, "worker response failed the structured contract")
            return True
        if response.get("escalation_required"):
            self._intervene("WORKER_ESCALATION", response.get("interpretation", "Worker requested escalation"), response.get("evidence_used", []), "Review the reasoning transaction and provide direction.")
            return True
        self._save_stage("VALIDATE")
        return True

    def _validate(self) -> bool:
        action = self.runtime.state.get("pending_operation")
        if not isinstance(action, dict):
            self._failure("MALFORMED_ACTION", action, "reasoning did not provide an operation object")
            return True
        result = self.runtime.validate(action)
        if not result.accepted:
            if result.code in {"DESTRUCTIVE_OPERATION_REJECTED", "STEWARD_GATE_REQUIRED", "OPERATION_REJECTED"}:
                self._intervene(result.code, result.reason, action.get("evidence_ids", []), "Review or replace the proposed operation; no action executed.")
            else:
                self._failure(result.code, action, result.reason)
            return True
        state = self.runtime.state
        state["pending_execution"] = {"status": "AUTHORIZED_NOT_EXECUTED", "action": action, "updated_at": utcnow()}
        state["coordinator_stage"] = "EXECUTE"
        self.runtime.store.save_state(state)
        self.runtime.checkpoint()
        return True

    def _execute(self) -> bool:
        pending = self.runtime.state["pending_execution"]
        action = pending["action"]
        state = self.runtime.state
        pending["status"] = "EXECUTION_UNCERTAIN"
        pending["updated_at"] = utcnow()
        state["pending_execution"] = pending
        self.runtime.store.save_state(state)
        self.runtime.checkpoint()
        self.runtime.transition("EXECUTING", "EXECUTION_STARTED", details={"operation_id": action["operation_id"]})
        try:
            result = self.adapter.execute(action)
        except Exception as exc:
            self._intervene("EXECUTION_FAILED", str(exc), action.get("evidence_ids", []), "Inspect the target; SNAIL will verify before any retry.")
            return True
        state = self.runtime.state
        pending = state["pending_execution"]
        pending.update({"status": "EXECUTED_UNVERIFIED", "result": result, "updated_at": utcnow()})
        state["pending_execution"] = pending
        state["coordinator_stage"] = "VERIFY"
        self.runtime.store.save_state(state)
        self.runtime.checkpoint()
        return True

    def _verify(self) -> bool:
        pending = self.runtime.state["pending_execution"]
        action = pending["action"]
        self.runtime.transition("VERIFYING", "INDEPENDENT_VERIFICATION_STARTED", details={"operation_id": action["operation_id"]})
        verification = self.adapter.verify(action)
        self.runtime._event("EFFECT_OBSERVED", status="VERIFIED" if verification["verified"] else "UNVERIFIED", evidence=verification.get("evidence_ids", []), details=verification)
        if not verification["verified"]:
            self._intervene("EFFECT_UNVERIFIED", verification["reason"], verification.get("evidence_ids", []), "Determine actual effect state before authorizing a retry.")
            return True
        state = self.runtime.state
        operation_id = action["operation_id"]
        if operation_id not in state["verified_operation_ids"]:
            state["verified_operation_ids"].append(operation_id)
        state["last_verified_machine_state"] = {"operation_id": operation_id, "effect": verification, "verified_at": utcnow()}
        state["pending_execution"] = None
        state["pending_operation"] = None
        state["pending_reasoning"] = None
        state["coordinator_stage"] = "CONTINUE"
        self.runtime.store.save_state(state)
        self._clear_failures()
        self.runtime.transition(
            "READY",
            "OPERATION_VERIFIED",
            evidence=verification.get("evidence_ids", []),
            details={"operation_id": operation_id, "operation_type": action["operation_type"]},
        )
        self.runtime.checkpoint()
        return True

    def _continue(self) -> bool:
        state = self.runtime.state
        last_type = next(
            (
                event.get("details", {}).get("operation_type")
                for event in reversed(self.runtime.store.events())
                if event["type"] == "OPERATION_VERIFIED"
            ),
            None,
        )
        if last_type == "request_physical_work":
            self._intervene(
                "PHYSICAL_WORK_REQUIRED",
                "The approved campaign has reached a physical configuration change that automation cannot perform.",
                state["evidence_refs"],
                "Perform the requested physical work and report PHYSICAL WORK COMPLETE; SNAIL will independently reconcile before continuing.",
            )
            return True
        if last_type == "stock_recovery":
            self._intervene(
                "STOCK_RECOVERY_DECISION_REQUIRED",
                "Stock recovery is the campaign's explicit Steward-gated contingency operation.",
                state["evidence_refs"],
                "Authorize or reject stock recovery based on the preserved failure evidence.",
            )
            return True
        self._save_stage("OBSERVE")
        return True

    def _reconcile(self) -> bool:
        self.runtime.transition("RECOVERING", "RECOVERY_RECONCILIATION_STARTED")
        before = self.runtime.state
        previous_boot = before.get("last_known_worker_boot_id")
        previous_pid = before.get("last_known_worker_pid")
        observation = self._observe_environment()
        current_worker = observation["worker"]
        if previous_boot and current_worker.get("boot_id") and current_worker["boot_id"] != previous_boot:
            self.runtime._event(
                "OCTO2_REBOOT_CONFIRMED",
                details={"old_boot_id": previous_boot, "new_boot_id": current_worker.get("boot_id")},
            )
        elif previous_pid and current_worker.get("pid") and current_worker.get("pid") != previous_pid:
            self.runtime._event(
                "WORKER_PID_REPLACED",
                details={"old_pid": previous_pid, "new_pid": current_worker["pid"]},
            )
        state = self.runtime.state
        pending = state.get("pending_execution")
        if pending:
            verification = self.adapter.verify(pending["action"])
            if verification["verified"]:
                state["coordinator_stage"] = "VERIFY"
                self.runtime.store.save_state(state)
                return self._verify()
            if pending["status"] != "AUTHORIZED_NOT_EXECUTED":
                self._intervene("UNCERTAIN_OPERATION_EFFECT", "A prior execution may have occurred but its effect is not verified.", pending["action"].get("evidence_ids", []), "Inspect the target and provide evidence; SNAIL will not replay the operation.")
                return True
        state = self.runtime.state
        state["reconciliation_required"] = False
        state["last_reconciled_at"] = utcnow()
        state["coordinator_stage"] = "EXECUTE" if pending else "OBSERVE"
        self.runtime.store.save_state(state)
        if observation["worker"].get("state") != "80B_READY":
            self.runtime.transition("WAITING_FOR_WORKER", "RECOVERY_WAITING_FOR_WORKER")
        else:
            self.runtime.transition("READY", "RECOVERY_RECONCILED")
        self.runtime.checkpoint()
        return True

    def _observe_worker_recovery(self) -> bool:
        stored = self.runtime.state
        last_sample = stored["worker"]
        previous = {
            **last_sample,
            "boot_id": stored.get("last_known_worker_boot_id"),
            "pid": stored.get("last_known_worker_pid"),
        }
        sampled = self.observer.observe()
        if sampled["worker"] == last_sample:
            return False
        observation = self._observe_environment(observation=sampled)
        if observation["worker"].get("state") != "80B_READY":
            return False
        current = observation["worker"]
        if previous.get("boot_id") and current.get("boot_id") != previous.get("boot_id"):
            self.runtime._event("OCTO2_REBOOT_CONFIRMED", details={"old_boot_id": previous["boot_id"], "new_boot_id": current["boot_id"]})
        elif previous.get("pid") and current.get("pid") != previous.get("pid"):
            self.runtime._event("WORKER_PID_REPLACED", details={"old_pid": previous["pid"], "new_pid": current["pid"]})
        state = self.runtime.state
        state["reconciliation_required"] = True
        self.runtime.store.save_state(state)
        return self._reconcile()

    def _failure(self, code: str, payload: Any, reason: str) -> None:
        signature = hashlib.sha256(json.dumps({"code": code, "payload": payload}, sort_keys=True, default=str).encode()).hexdigest()
        state = self.runtime.state
        failures = state.setdefault("failure_counts", {})
        failures[signature] = failures.get(signature, 0) + 1
        state["failure_counts"] = failures
        state["coordinator_stage"] = "OBSERVE"
        self.runtime.store.save_state(state)
        self.runtime._event(code, status="REJECTED", details={"reason": reason, "identical_count": failures[signature]})
        if failures[signature] >= self.runtime.config["max_identical_failures"]:
            self._intervene("REPEATED_IDENTICAL_FAILURE", reason, [], "Review repeated failure and update task or direction.")
        else:
            self.runtime.transition("READY", "RETRY_WITH_FRESH_OBSERVATION")

    def _clear_failures(self) -> None:
        state = self.runtime.state
        state["failure_counts"] = {}
        self.runtime.store.save_state(state)

    def _intervene(self, code: str, known: str, evidence: list[str], human_action: str) -> None:
        state = self.runtime.state
        state["steward_intervention_required"] = True
        state["intervention"] = {"code": code, "what_happened": known, "known": known, "unknown": "No assumption is made beyond cited evidence.", "evidence": evidence, "human_action_required": human_action, "verification_after_action": "SNAIL will re-observe and independently reconcile before continuing."}
        self.runtime.store.save_state(state)
        self.runtime.transition("WAITING_FOR_STEWARD", "STEWARD_INTERVENTION_REQUIRED", status=code, evidence=evidence, details=state["intervention"])
        self.runtime.checkpoint()
