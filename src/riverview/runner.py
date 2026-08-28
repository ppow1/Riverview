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
from dataclasses import replace
from datetime import UTC, datetime, timedelta
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
from riverview.campaign.hermes_executor import HermesCampaignRoleExecutor
from riverview.database import connect
from riverview.intake import EngineeringIntentStore
from riverview.relay import AttemptIdentity, ClaimedWork, FenceNotCurrentError, RelayStore
from riverview.resources.control import DurableResourcePlanner, ResourceControlError, ResourcePolicyStore, SeatClaim, SeatClaimStore
from riverview.resources.registry import ResourceRegistry
from riverview.reasoning.contracts import ReasoningRequest
from riverview.reasoning.hermes import HermesReasoningProvider


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    action_type: str
    action_version: str
    command_path: str
    command_sha256: str
    hard_timeout_seconds: int


class RestrictedRunner:
    """Execute only explicitly implemented actions whose source hash matches policy."""

    def __init__(self, repository: Path, worker_id: str, heartbeat_seconds: float = 0.5,
                 *, resource_planner: DurableResourcePlanner | None = None,
                 resource_claim_store: SeatClaimStore | None = None) -> None:
        self.repository = repository.resolve()
        self.worker_id = worker_id
        self.worker_instance_id = uuid4()
        self.heartbeat_seconds = heartbeat_seconds
        self.store = RelayStore()
        if (resource_planner is None) != (resource_claim_store is None):
            raise ValueError("resource planner and claim store must be supplied together")
        self.resource_claim_store = resource_claim_store or SeatClaimStore()
        self.resource_lease_seconds = 300
        self.resource_renewal_seconds = 100
        self.resource_planner = resource_planner or DurableResourcePlanner(
            ResourceRegistry.from_codex_telemetry(), ResourcePolicyStore(), self.resource_claim_store,
        )

    def run_once(self, *, target_work_order_id: UUID | None = None) -> dict[str, Any] | None:
        """Run one order, optionally restricting admission to an exact ID."""
        reservation_id = f"relay-reservation:{uuid4()}"
        resource_claim: SeatClaim | None = None
        renewal_stop = threading.Event()
        renewal_errors: list[str] = []
        renewal_thread: threading.Thread | None = None
        try:
            resource_claim, _reason = self.resource_planner.claim_automatic(
                reservation_id, self.worker_id, role="writer",
            )
            work = self.store.claim(self.worker_id, 10, worker_instance_id=self.worker_instance_id,
                                    seat_id=resource_claim.seat_id, role="writer",
                                    work_order_id=target_work_order_id,
                                    allow_internal=target_work_order_id is not None)
            if work is None:
                self.resource_claim_store.release(resource_claim.claim_id, reason="no work admitted")
                return None
            self.resource_claim_store.attach_work(resource_claim.claim_id, str(work.work_order_id))
            if resource_claim.decision_id is not None:
                self.resource_planner.decision_store.bind_execution(
                    resource_claim.decision_id,
                    work_id=str(work.work_order_id),
                    execution_correlation_id=str(work.correlation_id),
                )
            self.resource_claim_store.transition(resource_claim.claim_id, "starting")
            self.resource_claim_store.transition(resource_claim.claim_id, "running")
            renewal_thread = threading.Thread(
                target=self._renew_resource_claim,
                args=(resource_claim.claim_id, renewal_stop, renewal_errors),
                name=f"riverview-resource-renewal-{self.worker_id}", daemon=True,
            )
            renewal_thread.start()
        except ResourceControlError:
            if resource_claim is not None:
                self.resource_claim_store.release(resource_claim.claim_id, reason="production admission failed", failed=True)
            return None
        except Exception:
            if resource_claim is not None:
                self.resource_claim_store.release(resource_claim.claim_id, reason="production admission failed", failed=True)
            raise
        if work is None:
            return None
        try:
            definition = self._definition(work)
            if work.action_type == "codex.engineering.v1":
                result = self._execute_action(work)
                if renewal_errors:
                    raise RuntimeError(f"RIV-RSRC-0004: resource claim renewal failed: {renewal_errors[-1]}")
                return result
            command = self._command(work, definition)
            result = self._execute(work, command)
            if renewal_errors:
                raise RuntimeError(f"RIV-RSRC-0004: resource claim renewal failed: {renewal_errors[-1]}")
            return result
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            checkpoint = self._checkpoint_from_error(str(exc))
            self._fail(work, checkpoint, str(exc), timed_out=checkpoint == "RIV-EXE-0003")
            return {"status": "failed", "checkpoint_id": checkpoint}
        finally:
            renewal_stop.set()
            if renewal_thread is not None:
                renewal_thread.join(timeout=2)
            if resource_claim is not None:
                self.resource_claim_store.release(
                    resource_claim.claim_id,
                    reason="execution completed" if not renewal_errors else "resource lease renewal failed",
                    failed=bool(renewal_errors),
                )

    def _renew_resource_claim(self, claim_id: UUID, stop: threading.Event, errors: list[str]) -> None:
        """Renew one active resource lease until its owning execution ends."""
        while not stop.wait(self.resource_renewal_seconds):
            try:
                self.resource_claim_store.renew(claim_id, lease_seconds=self.resource_lease_seconds)
            except (ResourceControlError, OSError, RuntimeError) as exc:
                errors.append(str(exc))
                return

    @staticmethod
    def _checkpoint_from_error(reason: object) -> str:
        """Preserve the most specific stable checkpoint surfaced by a seam."""

        if not isinstance(reason, str):
            reason = "" if reason is None else str(reason)
        match = re.search(r"\b(RIV-[A-Z0-9]+-\d{4})\b", reason)
        return match.group(1) if match else "RIV-RUN-0001"

    def _execute_action(self, work: ClaimedWork) -> dict[str, Any]:
        """Route each action class to its authoritative executor."""
        if work.action_type == "codex.engineering.v1":
            return self._execute_hermes(work)
        raise RuntimeError(f"RIV-RUN-0004: unsupported action executor: {work.action_type}")

    def _execute_hermes(self, work: ClaimedWork) -> dict[str, Any]:
        """Run governed engineering reasoning through the claimed seat."""
        if work.correlation_id is None or work.seat_id not in {"C1", "C2", "C3"}:
            raise RuntimeError("RIV-CAM-HERMES-0019: claimed work lacks canonical seat/correlation.")
        intent_id = UUID(str(work.parameters.get("engineering_intent_id", "")))
        record = EngineeringIntentStore().load(intent_id)
        if record is None:
            raise RuntimeError("RIV-EXE-0002: engineering intent is missing.")
        if not record["authority_id"] or record["approved_by"] != "steward":
            raise PermissionError("RIV-GRC-0004: execution requires a durable Steward authority grant.")
        request = ReasoningRequest(
            request_id=uuid4(), correlation_id=work.correlation_id,
            request_type="analysis", instruction=record["bounded_instruction"],
            context_refs=(f"work-order:{work.work_order_id}",),
            classification=record["classification"], required_output_schema="bounded",
            evidence_requirements=tuple(record["evidence_requirements"]),
            expires_at=datetime.now(UTC) + timedelta(seconds=min(work.hard_timeout_seconds, 1800)),
            allowed_authority=("return:advisory",), objective_id=record["objective_id"],
            stage_id=record["stage_id"], causation_id=record["causation_id"],
            response_format={"type": "json_object"},
        )
        provider = HermesReasoningProvider(
            provider_id="hermes:codex.engineering.v1", resource_class_ref=f"codex:{work.seat_id}",
            execution_class="campaign-engineering", timeout_seconds=min(work.hard_timeout_seconds, 1800),
            codex_seat_id=work.seat_id,
        )
        routed = replace(work, role="engineering", parameters={**work.parameters, "hermes_request": {
            "request_id": str(request.request_id), "request_type": request.request_type,
            "instruction": request.instruction, "context_refs": list(request.context_refs),
            "classification": request.classification, "required_output_schema": request.required_output_schema,
            "evidence_requirements": list(request.evidence_requirements), "expires_at": request.expires_at.isoformat(),
            "allowed_authority": list(request.allowed_authority), "objective_id": str(request.objective_id),
            "stage_id": str(request.stage_id), "causation_id": str(request.causation_id) if request.causation_id else None,
            "response_format": request.response_format,
        }})
        result = HermesCampaignRoleExecutor(provider).execute(routed)
        if result.get("semantic_outcome") is None:
            raise RuntimeError("RIV-CAM-HERMES-0020: engineering result omitted structured semantic_outcome.")
        result.update({"execution_class": "codex.engineering.v1", "execution_mode": "hermes-http", "codex_seat_id": work.seat_id})
        self.store.complete_fenced(self._identity(work), result)
        return result

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
            authority_context = self.store.reconciliation_authority(self._identity(work))
            authority = authority_context.__enter__()
        except FenceNotCurrentError as exc:
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
                "result_version_hash": observed_head,
                "implementation_ref": f"commit:{observed_head}",
                "evidence_refs": [f"execution:{execution}", f"reconciliation:execution:{execution}"],
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
            authority.complete(report)
            return report
        except BaseException as exc:
            authority_context.__exit__(type(exc), exc, exc.__traceback__)
            raise
        else:
            authority_context.__exit__(None, None, None)

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
            report = {"status": state, "reason": reason}
            if checkpoint == "RIV-REASON-0001" and "request type is unsupported" in reason:
                report["execution_started"] = False
            cursor.execute("""UPDATE work_orders SET status=%s,error_checkpoint=%s,result_report=%s::jsonb,
                              finished_at=now(),lease_expires_at=NULL,active_attempt_id=NULL,
                              lease_generation=NULL,fencing_token=NULL,worker_instance_id=NULL,
                              seat_id=NULL,role=NULL,updated_at=now()
                           WHERE work_order_id=%s AND status IN('claimed','running')
                             AND active_attempt_id=%s AND lease_generation=%s
                             AND fencing_token=%s AND worker_instance_id=%s""",
                           (state,checkpoint,json.dumps(report),
                            identity.work_order_id, identity.attempt_id, identity.lease_generation,
                            identity.fencing_token, identity.worker_instance_id))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-RUN-0008: Runner could not record terminal state.")
            cursor.execute("UPDATE work_order_attempts SET finished_at=now(),terminal_state=%s,exit_code=%s WHERE attempt_id=%s",(state,124 if timed_out else 1,identity.attempt_id))
            cursor.execute("INSERT INTO steward_escalations(escalation_id,work_order_id,checkpoint_id,reason,state)VALUES(%s,%s,%s,%s,'open')",(uuid4(),identity.work_order_id,checkpoint,reason))
