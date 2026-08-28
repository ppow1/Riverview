"""Bounded RUN-004B Campaign Runner orchestration.

The one-go runner coordinates accepted persistence/fencing and lifecycle gates.
Execution remains behind the injected role executor boundary; this module does
not select a model/provider or create a weaker completion path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Protocol
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.relay import AttemptIdentity, ClaimedWork, FenceNotCurrentError, RelayStore
from riverview.relay.store import FencedClaimedWork
from riverview.resources.control import DurableResourcePlanner, ResourceControlError, SeatClaim, SeatClaimStore
from riverview.river.events import Classification, RiverEvent

from .lifecycle import CampaignLifecycleStore, DefectInput, LifecycleGateError

ONE_GO_CHECKPOINT = "RIV-CAM-004B"
ROLE_ORDER = ("writer", "validator", "repair_writer", "revalidator")


@dataclass(frozen=True, slots=True)
class WorkerSlot:
    """Configured worker capability; seat labels are operational configuration."""

    worker_id: str
    seat_id: str
    roles: tuple[str, ...]
    worker_instance_id: UUID

    def __post_init__(self) -> None:
        if not self.worker_id.strip() or not self.seat_id.strip() or not self.roles:
            raise ValueError(f"{ONE_GO_CHECKPOINT}: worker slot is incomplete.")
        if not isinstance(self.worker_instance_id, UUID) or not set(self.roles) <= set(ROLE_ORDER):
            raise ValueError(f"{ONE_GO_CHECKPOINT}: worker slot roles are invalid.")


class RoleExecutor(Protocol):
    def __call__(self, work: ClaimedWork) -> dict[str, Any]: ...


class OneGoError(RuntimeError):
    """A bounded runner coordination failure."""


def _prepare_execution(execution: dict[str, Any]) -> dict[str, Any]:
    """Normalize structured defects before any fenced JSON persistence."""
    prepared = dict(execution)
    raw_defects = prepared.get("defects", ())
    if not isinstance(raw_defects, (list, tuple)):
        raise OneGoError(f"{ONE_GO_CHECKPOINT}-0004: structured defects must be a bounded collection.")
    defects = tuple(
        item if isinstance(item, DefectInput) else DefectInput.from_payload(item)
        for item in raw_defects
    )
    prepared["defects"] = [defect.as_payload() for defect in defects]
    return prepared


def _structured_defects(execution: dict[str, Any]) -> tuple[DefectInput, ...]:
    raw_defects = execution.get("defects", ())
    if not isinstance(raw_defects, (list, tuple)):
        raise OneGoError(f"{ONE_GO_CHECKPOINT}-0005: persisted structured defects are malformed.")
    return tuple(item if isinstance(item, DefectInput) else DefectInput.from_payload(item) for item in raw_defects)


def _identity(work: ClaimedWork) -> AttemptIdentity:
    values = (work.work_order_id, work.attempt_id, work.lease_generation, work.fencing_token, work.worker_instance_id)
    if any(value is None for value in values[1:]):
        raise OneGoError(f"{ONE_GO_CHECKPOINT}-0001: claimed work lacks exact fence identity.")
    return AttemptIdentity(work.work_order_id, work.attempt_id, work.lease_generation, work.fencing_token, work.worker_instance_id)


def _claimed(work: FencedClaimedWork) -> ClaimedWork:
    return ClaimedWork(
        work.identity.work_order_id, work.action_type, work.action_version, work.parameters,
        work.hard_timeout_seconds, 0, work.identity.attempt_id, work.identity.lease_generation,
        work.identity.fencing_token, work.identity.worker_instance_id, work.seat_id, work.role,
        work.correlation_id, work.run_id,
    )


class CampaignOneGoRunner:
    """Advance persisted campaign work through one bounded role at a time."""

    def __init__(
        self,
        workers: tuple[WorkerSlot, ...],
        executors: dict[str, RoleExecutor],
        *,
        relay: RelayStore | None = None,
        lifecycle: CampaignLifecycleStore | None = None,
        objective_id: UUID | None = None,
        max_steps: int = 100,
        attention_delivery: Callable[[str], dict[str, Any]] | None = None,
        resource_planner: DurableResourcePlanner | None = None,
        resource_claim_store: SeatClaimStore | None = None,
    ) -> None:
        if not workers or max_steps < 1:
            raise ValueError(f"{ONE_GO_CHECKPOINT}: workers and positive max_steps are required.")
        if any(role not in executors for worker in workers for role in worker.roles):
            raise ValueError(f"{ONE_GO_CHECKPOINT}: every configured role requires an executor.")
        self.workers = workers
        self.executors = executors
        self.relay = relay or RelayStore()
        self.lifecycle = lifecycle or CampaignLifecycleStore()
        if objective_id is not None and not isinstance(objective_id, UUID):
            raise ValueError(f"{ONE_GO_CHECKPOINT}: objective_id is invalid.")
        self.objective_id = objective_id
        self.max_steps = max_steps
        self.attention_delivery = attention_delivery
        if (resource_planner is None) != (resource_claim_store is None):
            raise ValueError(f"{ONE_GO_CHECKPOINT}: resource planner and claim store must be supplied together.")
        self.resource_planner = resource_planner
        self.resource_claim_store = resource_claim_store

    def run(self, *, max_steps: int | None = None) -> tuple[dict[str, Any], ...]:
        """Run a bounded number of persisted role transitions, then return history."""
        limit = max_steps if max_steps is not None else self.max_steps
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError(f"{ONE_GO_CHECKPOINT}: max_steps is invalid.")
        outcomes: list[dict[str, Any]] = []
        for _ in range(limit):
            self.admit_eligible_stages()
            outcome = self.tick()
            if outcome is None:
                break
            outcomes.append(outcome)
        return tuple(outcomes)

    def run_package(self, *, stage_id: UUID, worktree_ref: str, package_executor: Any,
                    independent_acceptance: Any, max_repairs_per_root: int = 3) -> Any:
        """Run package-engineer self-repair before the final validator boundary.

        Existing ``run`` remains the compatible role-by-role RUN-004 path.  New
        package launches use this explicit seam so a package engineer owns
        diagnosis, bounded repair, and full verification in one worktree while
        the lifecycle store still owns durable identity/fencing evidence.
        """
        if self.objective_id is None:
            raise OneGoError(f"{ONE_GO_CHECKPOINT}: package execution requires an objective scope.")
        from .package_runner import PackageEngineerLoop

        return PackageEngineerLoop(
            self.lifecycle, objective_id=self.objective_id, stage_id=stage_id,
            worktree_ref=worktree_ref, executor=package_executor,
            independent_acceptance=independent_acceptance,
            max_repairs_per_root=max_repairs_per_root,
        ).run()

    def tick(self) -> dict[str, Any] | None:
        """Claim and advance at most one exact fenced role attempt."""
        for worker in self.workers:
            for role in worker.roles:
                resource_claim: SeatClaim | None = None
                selected_seat = worker.seat_id
                reservation_id = f"campaign-reservation:{uuid4()}"
                if self.resource_planner is not None and self.resource_claim_store is not None:
                    try:
                        if selected_seat.strip().upper() == "AUTO":
                            resource_claim, _ = self.resource_planner.claim_automatic(
                                reservation_id, worker.worker_id, role=role,
                            )
                            selected_seat = resource_claim.seat_id
                        else:
                            resource_claim = self.resource_claim_store.claim(
                                selected_seat, reservation_id, worker.worker_id,
                            )
                    except ResourceControlError as exc:
                        if selected_seat.strip().upper() != "AUTO":
                            raise OneGoError(f"{ONE_GO_CHECKPOINT}-0007: explicit seat {selected_seat} is unavailable.") from exc
                        continue
                try:
                    if self.objective_id is not None:
                        claimed = self.relay.claim_fenced(worker.worker_id, worker.worker_instance_id, seat_id=selected_seat, role=role, allow_internal=True, objective_id=self.objective_id)
                    else:
                        claimed = self.relay.claim_fenced(worker.worker_id, worker.worker_instance_id, seat_id=selected_seat, role=role)
                except Exception:
                    if resource_claim is not None:
                        self.resource_claim_store.release(resource_claim.claim_id, reason="work admission failed", failed=True)
                    raise
                if claimed is None:
                    if resource_claim is not None:
                        self.resource_claim_store.release(resource_claim.claim_id, reason="no work admitted")
                    continue
                work = _claimed(claimed)
                resource_failed = False
                try:
                    if resource_claim is not None:
                        if work.seat_id != selected_seat:
                            raise OneGoError(f"{ONE_GO_CHECKPOINT}-0006: claimed seat differs from admitted work seat.")
                        self.resource_claim_store.attach_work(resource_claim.claim_id, str(work.work_order_id))
                    if resource_claim is not None:
                        self.resource_claim_store.transition(resource_claim.claim_id, "starting")
                    self.lifecycle.mark_running(work)
                    if resource_claim is not None:
                        self.resource_claim_store.transition(resource_claim.claim_id, "running")
                    execution = self.executors[role](work)
                    if not isinstance(execution, dict) or execution.get("status") != "succeeded":
                        raise OneGoError(f"{ONE_GO_CHECKPOINT}-0002: role executor did not return a successful result.")
                    execution = _prepare_execution(execution)
                    self.relay.complete_fenced(_identity(work), execution)
                    transition = self._advance_completed(role, work, execution)
                    return {"status": "succeeded", "role": role, "work_order_id": str(work.work_order_id), "transition": transition}
                except FenceNotCurrentError as exc:
                    resource_failed = True
                    return {"status": "stale", "role": role, "work_order_id": str(work.work_order_id), "checkpoint_id": "RIV-WRK-0003", "reason": str(exc)}
                except RuntimeError as exc:
                    if "RIV-WRK-0003" in str(exc):
                        resource_failed = True
                        return {"status": "stale", "role": role, "work_order_id": str(work.work_order_id), "checkpoint_id": "RIV-WRK-0003", "reason": str(exc)}
                    resource_failed = True
                    self._deliver_attention(self._fail_if_current(work, str(exc)))
                    return {"status": "failed", "role": role, "work_order_id": str(work.work_order_id), "checkpoint_id": self._checkpoint(exc), "reason": str(exc)}
                except (LifecycleGateError, OneGoError, RuntimeError, TypeError, ValueError) as exc:
                    resource_failed = True
                    self._deliver_attention(self._fail_if_current(work, str(exc)))
                    return {"status": "failed", "role": role, "work_order_id": str(work.work_order_id), "checkpoint_id": self._checkpoint(exc), "reason": str(exc)}
                finally:
                    if resource_claim is not None:
                        self.resource_claim_store.release(
                            resource_claim.claim_id,
                            reason="execution failed" if resource_failed else "execution completed",
                            failed=resource_failed,
                        )
        return None

    def _scoped_work_order_id(self, worker: WorkerSlot, role: str) -> UUID | None:
        """Select one queued order inside the configured campaign scope.

        RelayStore remains the authority for the actual fenced claim.  This
        lookup only prevents a campaign-scoped one-go invocation from
        accidentally claiming another objective's queued work.
        """
        if self.objective_id is None:
            return None
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT w.work_order_id
                     FROM work_orders w
                     JOIN objective_stages s ON s.stage_id=w.stage_id
                    WHERE s.objective_id=%s AND w.status='queued'
                      AND (w.role IS NULL OR w.role=%s)
                      AND (w.seat_id IS NULL OR w.seat_id=%s)
                    ORDER BY w.created_at
                    LIMIT 1""",
                (self.objective_id, role, worker.seat_id),
            )
            row = cursor.fetchone()
        return row[0] if row else None

    def _advance_completed(self, role: str, work: ClaimedWork, execution: dict[str, Any]) -> str:
        if role == "writer":
            validator_action = str(execution.get("validator_action_type", "relay.noop"))
            validator_id = self.lifecycle.handoff_writer_to_validation(work, validator_action_type=validator_action, requested_by="campaign-runner", parameters=execution.get("validator_parameters"))
            return f"validator_queued:{validator_id}"
        if role == "repair_writer":
            revalidation_id = self.lifecycle.record_repair_completion(
                work,
                revalidation_action_type=str(execution.get("revalidation_action_type", "relay.noop")),
                revalidation_parameters=execution.get("revalidation_parameters"),
                requested_by="campaign-runner",
            )
            return f"revalidator_queued:{revalidation_id}"
        validation = {key: execution[key] for key in (
            "verdict", "basis_hash", "result_version_hash", "evidence_refs", "findings_summary",
            "defects", "implementation_ref",
        ) if key in execution}
        validation["defects"] = _structured_defects(execution)
        result_id = self.lifecycle.record_validation(
            work,
            requested_by="campaign-runner",
            repair_parameters=execution.get("repair_parameters"),
            **validation,
        )
        if execution.get("verdict") == "PASS":
            self._deliver_attention(f"runner.steward_attention:ready:{result_id}")
        return f"validation_recorded:{result_id}"

    @staticmethod
    def _checkpoint(error: object) -> str:
        text = str(error)
        marker = text.split(":", 1)[0]
        return marker if marker.startswith("RIV-") else f"{ONE_GO_CHECKPOINT}-0003"

    def _deliver_attention(self, idempotency_key: str | None) -> None:
        if not idempotency_key:
            return
        if self.attention_delivery is not None:
            self.attention_delivery(idempotency_key)
            return
        from riverview.notifications_audio import deliver_steward_notification
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT notification_id FROM steward_notifications WHERE idempotency_key=%s", (idempotency_key,))
            row = cursor.fetchone()
        if row is not None:
            deliver_steward_notification(row[0])

    def _fail_if_current(self, work: ClaimedWork, reason: str) -> str | None:
        """Record a truthful fenced terminal failure before any next dispatch."""
        identity = _identity(work)
        attention_key = None
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT stage_id FROM work_orders WHERE work_order_id=%s AND status IN ('claimed','running') "
                "AND active_attempt_id=%s AND lease_generation=%s AND fencing_token=%s AND worker_instance_id=%s FOR UPDATE",
                (identity.work_order_id, identity.attempt_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            stage_row = cursor.fetchone()
            cursor.execute(
                """UPDATE work_orders SET status='failed',error_checkpoint=%s,result_report=%s::jsonb,
                          finished_at=now(),lease_expires_at=NULL,active_attempt_id=NULL,
                          lease_generation=NULL,fencing_token=NULL,worker_instance_id=NULL,
                          seat_id=NULL,role=NULL,updated_at=now()
                   WHERE work_order_id=%s AND status IN ('claimed','running')
                     AND active_attempt_id=%s AND lease_generation=%s AND fencing_token=%s
                     AND worker_instance_id=%s""",
                (self._checkpoint(reason), json.dumps({"status": "failed", "reason": reason}),
                 identity.work_order_id, identity.attempt_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            if cursor.rowcount == 1:
                cursor.execute("UPDATE work_order_attempts SET finished_at=now(),terminal_state='failed',exit_code=1 WHERE attempt_id=%s AND work_order_id=%s", (identity.attempt_id, identity.work_order_id))
                if stage_row is not None:
                    cursor.execute("UPDATE objective_stages SET runner_state='failed',blocked_reason=%s,last_state_transition_at=now(),updated_at=now() WHERE stage_id=%s AND runner_state NOT IN ('accepted','blocked')", (reason[:1000], stage_row[0]))
                cursor.execute(
                    """INSERT INTO river_events(event_id,event_type,aggregate_type,aggregate_id,correlation_id,
                              causation_id,idempotency_key,classification,payload,occurred_at)
                           SELECT %s,'runner.state_transition','work_order',work_order_id,correlation_id,
                                  %s,%s,%s,%s::jsonb,now() FROM work_orders WHERE work_order_id=%s""",
                    (uuid4(), identity.attempt_id, f"runner.one-go.failure:{identity.attempt_id}", Classification.RIVER.value,
                     json.dumps({"from": "running", "to": "failed", "attempt_id": str(identity.attempt_id), "reason": reason}), identity.work_order_id),
                )
                if self._checkpoint(reason) in {"RIV-CAM-HERMES-0008", "RIV-CAM-HERMES-0010"} and stage_row is not None:
                    attention_key = f"runner.steward_attention:blocked:{identity.attempt_id}"
                    CampaignLifecycleStore._queue_steward_attention(
                        cursor, notification_type="blocked_requires_steward",
                        checkpoint_id="RIV-HERMES-TRANCHE2-BLOCKED",
                        summary="Riverview Hermes needs your assistance.",
                        idempotency_key=attention_key,
                        evidence_refs=(f"stage:{stage_row[0]}", f"attempt:{identity.attempt_id}", f"failure:{self._checkpoint(reason)}"),
                    )
        return attention_key

    def admit_eligible_stages(self) -> tuple[UUID, ...]:
        """Queue writer work for ready stages using ordered dependency state."""
        queued: list[UUID] = []
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT objective_id FROM objective_stages WHERE runner_state='accepted'")
            objective_ids = [row[0] for row in cursor.fetchall()]
            if self.objective_id is not None:
                objective_ids = [self.objective_id]
            for objective_id in objective_ids:
                self._refresh_readiness(cursor, objective_id)
            candidate_sql = """SELECT s.objective_id,s.stage_id,s.validation_basis_id,s.declared_action
                     FROM objective_stages s
                    WHERE s.runner_state='queued' AND s.status='ready'
                      AND s.validation_basis_id IS NOT NULL
                      {objective_filter}
                      AND NOT EXISTS (
                          SELECT 1 FROM work_orders w WHERE w.stage_id=s.stage_id
                            AND w.role='writer' AND w.status IN ('queued','claimed','running','succeeded')
                      )
                      AND NOT EXISTS (
                          SELECT 1 FROM objective_stage_dependencies d
                          JOIN objective_stages dependency ON dependency.stage_id=d.depends_on_stage_id
                          WHERE d.stage_id=s.stage_id AND dependency.status <> 'completed'
                      )
                    ORDER BY s.objective_id,s.sort_order""".format(
                        objective_filter="AND s.objective_id=%s" if self.objective_id is not None else ""
                    )
            cursor.execute(candidate_sql, (self.objective_id,) if self.objective_id is not None else ())
            candidates = cursor.fetchall()
        for objective_id, stage_id, basis_id, declared_action in candidates:
            action = declared_action if isinstance(declared_action, dict) else {}
            action_type = str(action.get("action_type", "relay.noop"))
            parameters = action.get("parameters") if isinstance(action.get("parameters"), dict) else {}
            queued.append(self.lifecycle.queue_writer(
                objective_id=objective_id, stage_id=stage_id, basis_id=basis_id,
                action_type=action_type, requested_by="campaign-runner",
                idempotency_key=f"runner.writer:{stage_id}:{basis_id}", parameters=parameters,
            ))
        return tuple(queued)

    @staticmethod
    def _refresh_readiness(cursor: Any, objective_id: UUID) -> None:
        cursor.execute(
            """SELECT s.stage_id,s.status,
                      bool_and(d.status='completed') FILTER (WHERE d.stage_id IS NOT NULL) AS deps_done,
                      count(d.stage_id) AS dep_count
                 FROM objective_stages s
                 LEFT JOIN objective_stage_dependencies x ON x.stage_id=s.stage_id
                 LEFT JOIN objective_stages d ON d.stage_id=x.depends_on_stage_id
                WHERE s.objective_id=%s GROUP BY s.stage_id,s.status""", (objective_id,)
        )
        for stage_id, status, deps_done, dep_count in cursor.fetchall():
            if status == "completed":
                continue
            ready = dep_count == 0 or bool(deps_done)
            cursor.execute("UPDATE objective_stages SET readiness=%s,status=%s,updated_at=now() WHERE stage_id=%s", ("ready" if ready else "waiting", "ready" if ready else "pending", stage_id))
