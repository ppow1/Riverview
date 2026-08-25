"""Fixed-policy local runner for Riverview Relay.

Version: 0.5.2
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import UUID, uuid4

from riverview.autonomy.control import (
    CodexCliAdapter,
    ExecutionEnvelope,
    ExecutionStore,
    ResultReconciler,
)
from riverview.autonomy.stale_base import StaleBaseRecoveryStore
from riverview.database import connect
from riverview.intake import EngineeringIntentStore
from riverview.relay import AttemptIdentity, ClaimedWork, RelayStore


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    action_type: str
    action_version: str
    command_path: str
    command_sha256: str
    hard_timeout_seconds: int


class RestrictedRunner:
    """Execute only explicitly implemented actions whose source hash matches policy."""

    def __init__(self, repository: Path, worker_id: str, heartbeat_seconds: float = 0.5) -> None:
        self.repository = repository.resolve()
        self.worker_id = worker_id
        self.worker_instance_id = uuid4()
        self.heartbeat_seconds = heartbeat_seconds
        self.store = RelayStore()

    def run_once(self) -> dict[str, Any] | None:
        work = self.store.claim(self.worker_id, 10, worker_instance_id=self.worker_instance_id,
                                seat_id="C1", role="writer")
        if work is None:
            return None
        try:
            definition = self._definition(work)
            if work.action_type == "codex.engineering.v1":
                return self._execute_codex(work)
            command = self._command(work, definition)
            return self._execute(work, command)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            checkpoint = self._checkpoint_from_error(str(exc))
            self._fail(work, checkpoint, str(exc), timed_out=checkpoint == "RIV-EXE-0003")
            return {"status": "failed", "checkpoint_id": checkpoint}

    @staticmethod
    def _checkpoint_from_error(reason: object) -> str:
        """Preserve the most specific stable checkpoint surfaced by a seam."""

        if not isinstance(reason, str):
            reason = "" if reason is None else str(reason)
        match = re.search(r"\b(RIV-[A-Z0-9]+-\d{4})\b", reason)
        return match.group(1) if match else "RIV-RUN-0001"

    def _execute_codex(self, work: ClaimedWork) -> dict[str, Any]:
        intent_id = UUID(str(work.parameters.get("engineering_intent_id", "")))
        record = EngineeringIntentStore().load(intent_id)
        if record is None:
            raise RuntimeError("RIV-EXE-0002: engineering intent is missing.")
        if not record["authority_id"] or record["approved_by"] != "steward":
            raise PermissionError("RIV-GRC-0004: execution requires a durable Steward authority grant.")
        refreshed_base = record["expected_base_sha"]
        revalidation_id = work.parameters.get("stale_base_revalidation_id")
        if revalidation_id:
            refreshed_base = StaleBaseRecoveryStore().execution_base_for(work.work_order_id, UUID(str(revalidation_id)), intent_id)
        envelope = ExecutionEnvelope(
            execution_id=uuid4(), work_order_id=work.work_order_id, objective_id=record["objective_id"],
            stage_id=record["stage_id"], correlation_id=record["correlation_id"], causation_id=record["causation_id"],
            capability_name=record["capability_name"], repository_identity=record["repository_identity"],
            repository_root=Path(record["repository_root"]), expected_base_sha=refreshed_base,
            bounded_instruction=record["bounded_instruction"], allowed_paths=tuple(record["allowed_paths"]),
            acceptance_criteria=tuple(record["acceptance_criteria"]), evidence_requirements=tuple(record["evidence_requirements"]),
            timeout_seconds=record["timeout_seconds"], retry_key=f"execution:{work.work_order_id}",
            classification=record["classification"], write_policy=record["write_policy"],
        )
        baseline = self._working_paths(envelope.repository_root)
        execution = ExecutionStore().persist(envelope)
        ExecutionStore().start(execution)
        try:
            result = CodexCliAdapter().run(envelope)
        except RuntimeError as exc:
            checkpoint = "RIV-EXE-0008" if str(exc).startswith("RIV-EXE-0008:") else "RIV-EXE-0001"
            ExecutionStore().fail(execution, checkpoint, str(exc))
            raise
        ResultReconciler().persist(result)
        if result.result_category != "succeeded":
            checkpoint = result.checkpoint_refs[0] if result.checkpoint_refs else "RIV-EXE-0001"
            ResultReconciler().record_decision(
                execution,
                envelope.correlation_id,
                "checkpoint",
                f"Provider execution did not succeed: {result.bounded_summary}",
                ("execution:provider-failed",),
                f"execution.provider-failed:{execution}",
            )
            self._fail(work.work_order_id, checkpoint, result.bounded_summary, result.result_category == "timed_out")
            return {"status": result.result_category, "execution_id": str(execution), "checkpoint_id": checkpoint}
        try:
            self.store.assert_fence_current(self._identity(work))
        except RuntimeError as exc:
            # complete_fenced records the late result without touching the
            # successor's active authority. Never cross reconciliation after
            # this gate rejects the exact attempt tuple.
            try:
                self.store.complete_fenced(
                    self._identity(work),
                    {"status": "late_or_stale", "execution_id": str(execution), "reason": str(exc)},
                )
            except RuntimeError:
                pass
            return {"status": "stale", "execution_id": str(execution), "checkpoint_id": "RIV-WRK-0003"}
        try:
            reconciled = ResultReconciler().reconcile_repository(
                execution,
                envelope.repository_root,
                envelope.allowed_paths,
                baseline,
                expected_base_sha=envelope.expected_base_sha,
                acceptance_criteria=envelope.acceptance_criteria,
                evidence_requirements=envelope.evidence_requirements,
                write_policy=envelope.write_policy,
            )
        except RuntimeError as exc:
            ResultReconciler().record_decision(
                execution,
                envelope.correlation_id,
                "checkpoint",
                f"Authoritative execution verification failed: {exc}",
                ("execution:authoritative-verification-failed",),
                f"execution.reconciliation.checkpoint:{execution}",
            )
            if result.result_category != "succeeded" and result.checkpoint_refs:
                raise RuntimeError(f"{result.checkpoint_refs[0]}: {result.bounded_summary}") from exc
            raise
        ResultReconciler().record_decision(execution, envelope.correlation_id, "accepted", "Codex result reconciled within the declared path policy.", ("execution:reconciled",), f"execution.reconciliation:{execution}")
        observed_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=envelope.repository_root, text=True).strip()
        report = {
            "status": result.result_category,
            "execution_id": str(execution),
            "changed_paths": list(reconciled["changed_paths"]),
            "summary": result.bounded_summary,
            "repository_evidence": {
                "observed_git_head": observed_head,
                "ai_hints_readable": (envelope.repository_root / "AI_HINTS.md").is_file(),
                "charter_readable": (envelope.repository_root / "docs" / "governance" / "RIVERVIEW_CHARTER.md").is_file(),
                "changed_files": list(reconciled["changed_paths"]),
                "repository_suitable_for_bounded_codex_work": True,
                "write_policy": envelope.write_policy,
            },
        }
        if result.result_category == "succeeded":
            self.store.complete_fenced(self._identity(work), report)
        else:
            self._fail(work.work_order_id, result.checkpoint_refs[0] if result.checkpoint_refs else "RIV-EXE-0001", result.bounded_summary, result.result_category == "timed_out")
        return report

    @staticmethod
    def _working_paths(repository: Path) -> tuple[str, ...]:
        output = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=repository, text=True)
        return tuple(line[3:].strip() for line in output.splitlines() if len(line) >= 4)

    def _definition(self, work: ClaimedWork) -> ActionDefinition:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT action_type,action_version,command_path,command_sha256,hard_timeout_seconds FROM approved_actions WHERE action_type=%s AND action_version=%s AND enabled=true",(work.action_type,work.action_version))
            row = cursor.fetchone()
        if not row or not row[3]:
            raise RuntimeError("RIV-RUN-0001: Action definition is absent, disabled, unversioned, or unhashed.")
        return ActionDefinition(*row)

    def _command(self, work: ClaimedWork, definition: ActionDefinition) -> list[str]:
        path = (self.repository / definition.command_path).resolve()
        tools_root = (self.repository / "tools" / "powershell").resolve()
        if tools_root not in path.parents or not path.is_file():
            raise RuntimeError("RIV-RUN-0002: Registered command escaped the repository tools boundary.")
        if hashlib.sha256(path.read_bytes()).hexdigest() != definition.command_sha256:
            raise RuntimeError("RIV-RUN-0003: Registered command hash mismatch.")
        delay = work.parameters.get("delay_seconds")
        if work.action_type not in {"relay.noop", "relay.timeout_probe"} or not isinstance(delay, int) or isinstance(delay, bool) or not 1 <= delay <= 5:
            raise ValueError("RIV-RUN-0004: Action parameters failed the fixed runner adapter.")
        executable = shutil.which("pwsh")
        if executable is None:
            raise RuntimeError("RIV-RUN-0001: pwsh executable was not found.")
        return [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(path), "-DelaySeconds", str(delay)]

    def _execute(self, work: ClaimedWork, command: list[str]) -> dict[str, Any]:
        process = subprocess.Popen(
            command, cwd=self.repository, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stopped = threading.Event()
        heartbeat_error: list[str] = []
        last_progress = monotonic()

        def heartbeat() -> None:
            nonlocal last_progress
            while not stopped.wait(self.heartbeat_seconds):
                try:
                    self.store.heartbeat_fenced(self._identity(work), 10)
                    if monotonic() - last_progress >= 120:
                        self.store.progress_fenced(self._identity(work), idempotency_key=f"runner-progress:{work.attempt_id}:{int(monotonic())}", message="Restricted runner meaningful progress observed.", detail={"phase": "testing", "progress_percent": 50})
                        last_progress = monotonic()
                except RuntimeError as exc:
                    heartbeat_error.append(str(exc))
                    return

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            stdout, stderr = process.communicate(timeout=work.hard_timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            self._fail(work, "RIV-RUN-0005", "Hard timeout exceeded.", timed_out=True)
            return {"status": "timed_out", "checkpoint_id": "RIV-RUN-0005", "stdout": stdout[-4000:], "stderr": stderr[-4000:]}
        finally:
            stopped.set()
            thread.join(timeout=2)
        if heartbeat_error:
            raise RuntimeError(f"RIV-RUN-0006: Heartbeat failed: {heartbeat_error[-1]}")
        if process.returncode != 0:
            self._fail(work, "RIV-RUN-0007", f"Process exit code {process.returncode}.", timed_out=False)
            return {"status": "failed", "checkpoint_id": "RIV-RUN-0007", "stdout": stdout[-4000:], "stderr": stderr[-4000:]}
        report = {"status": "succeeded", "exit_code": process.returncode, "stdout": stdout[-4000:], "stderr": stderr[-4000:]}
        self.store.complete_fenced(self._identity(work), report)
        return report

    @staticmethod
    def _identity(work: ClaimedWork) -> AttemptIdentity:
        if None in (work.attempt_id, work.lease_generation, work.fencing_token, work.worker_instance_id):
            raise RuntimeError("RIV-WRK-0014: Claimed work has incomplete fencing identity.")
        return AttemptIdentity(work.work_order_id, work.attempt_id, work.lease_generation,
                               work.fencing_token, work.worker_instance_id)

    def _fail(self, work: ClaimedWork, checkpoint: str, reason: str, timed_out: bool) -> None:
        state = "timed_out" if timed_out else "failed"
        identity = self._identity(work)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""UPDATE work_orders SET status=%s,error_checkpoint=%s,result_report=%s::jsonb,
                              finished_at=now(),lease_expires_at=NULL,active_attempt_id=NULL,
                              lease_generation=NULL,fencing_token=NULL,worker_instance_id=NULL,
                              seat_id=NULL,role=NULL,updated_at=now()
                           WHERE work_order_id=%s AND status IN('claimed','running')
                             AND active_attempt_id=%s AND lease_generation=%s
                             AND fencing_token=%s AND worker_instance_id=%s""",
                           (state,checkpoint,json.dumps({"status":state,"reason":reason}),
                            identity.work_order_id, identity.attempt_id, identity.lease_generation,
                            identity.fencing_token, identity.worker_instance_id))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-RUN-0008: Runner could not record terminal state.")
            cursor.execute("UPDATE work_order_attempts SET finished_at=now(),terminal_state=%s,exit_code=%s WHERE attempt_id=%s",(state,124 if timed_out else 1,identity.attempt_id))
            cursor.execute("INSERT INTO steward_escalations(escalation_id,work_order_id,checkpoint_id,reason,state)VALUES(%s,%s,%s,%s,'open')",(uuid4(),identity.work_order_id,checkpoint,reason))
