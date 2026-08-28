"""Durable, bounded control-plane primitives for Grace and local Codex.

Version: 0.1.0

This module deliberately keeps provider selection and execution separate from MCP.
The database stores typed envelopes and results; it never stores executable shell
text or provider credentials.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.grace.objectives import ObjectiveStore
from riverview.intake.policy import (
    ENGINEERING_ACTION,
    ENGINEERING_CAPABILITY,
    READ_ONLY_POLICY,
    validate_allowed_paths,
    validate_engineering_policy,
)
from riverview.river.events import Classification, RiverEvent
from riverview.river.store import EventStore


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class ExecutionEnvelope:
    execution_id: UUID
    correlation_id: UUID
    capability_name: str
    repository_identity: str
    repository_root: Path
    expected_base_sha: str
    bounded_instruction: str
    allowed_paths: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    timeout_seconds: int
    retry_key: str
    action_type: str = ENGINEERING_ACTION
    classification: str = "river"
    causation_id: UUID | None = None
    objective_id: UUID | None = None
    stage_id: UUID | None = None
    work_order_id: UUID | None = None
    write_policy: str = READ_ONLY_POLICY

    def __post_init__(self) -> None:
        if not self.capability_name or not self.repository_identity:
            raise ValueError("RIV-EXE-0001: capability and repository identity are required.")
        if not self.repository_root.is_absolute():
            raise ValueError("RIV-EXE-0001: execution root must be absolute.")
        if not self.expected_base_sha or len(self.expected_base_sha) != 40:
            raise ValueError("RIV-EXE-0001: expected base SHA is invalid.")
        if not 1 <= len(self.bounded_instruction) <= 16_000:
            raise ValueError("RIV-EXE-0001: bounded instruction is outside its safe limit.")
        validate_allowed_paths(self.allowed_paths)
        if not 1 <= self.timeout_seconds <= 86_400:
            raise ValueError("RIV-EXE-0001: timeout is outside its safe limit.")
        if self.classification not in {"river", "internal"}:
            raise ValueError("RIV-EXE-0001: unsupported classification.")
        if self.capability_name != ENGINEERING_CAPABILITY or self.action_type != ENGINEERING_ACTION:
            raise ValueError("RIV-CAP-0004: the execution envelope is not the registered engineering action.")
        validate_engineering_policy(self.write_policy)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    result_id: UUID
    execution_id: UUID
    correlation_id: UUID
    provider_id: str
    result_category: str
    exit_state: str
    changed_paths: tuple[str, ...]
    validation_evidence: tuple[str, ...]
    commit_sha: str | None
    remote_verified_sha: str | None
    checkpoint_refs: tuple[str, ...]
    artifact_refs: tuple[str, ...]
    bounded_summary: str
    started_at: datetime
    finished_at: datetime


class CapabilityRegistry:
    """Register measured named capabilities and select only healthy capacity."""

    def register(
        self,
        *,
        capability_name: str,
        provider_id: str,
        version: str,
        supported_tasks: list[str],
        restrictions: list[str],
        evidence_refs: list[str],
        health_status: str = "unknown",
        capability_id: UUID | None = None,
    ) -> UUID:
        if not capability_name or not provider_id or "openai" in provider_id.lower() or health_status not in {"unknown", "healthy", "unhealthy", "disabled"}:
            raise ValueError("RIV-CAP-0001: capability registration is invalid.")
        capability_id = capability_id or uuid4()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO capabilities(capability_id,capability_name,provider_id,version,supported_tasks,restrictions,evidence_refs,health_status,measured_at)
                   VALUES(%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,now())
                   ON CONFLICT(capability_name) DO UPDATE SET provider_id=EXCLUDED.provider_id,version=EXCLUDED.version,
                   supported_tasks=EXCLUDED.supported_tasks,restrictions=EXCLUDED.restrictions,evidence_refs=EXCLUDED.evidence_refs,
                   health_status=EXCLUDED.health_status,measured_at=EXCLUDED.measured_at,updated_at=now()
                   RETURNING capability_id""",
                (capability_id, capability_name, provider_id, version, _json(supported_tasks), _json(restrictions), _json(evidence_refs), health_status),
            )
            return cursor.fetchone()[0]

    def record_capacity(self, capability_name: str, *, available: bool, concurrency_limit: int, current_load: int, fuel: dict[str, Any] | None = None, backoff_until: datetime | None = None) -> None:
        if concurrency_limit < 1 or current_load < 0 or current_load > concurrency_limit:
            raise ValueError("RIV-CAP-0002: capacity values are invalid.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT capability_id FROM capabilities WHERE capability_name=%s AND enabled=true", (capability_name,))
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-CAP-0002: capability is not registered.")
            cursor.execute(
                """INSERT INTO capability_capacity(capability_id,available,concurrency_limit,current_load,fuel,backoff_until)
                   VALUES(%s,%s,%s,%s,%s::jsonb,%s)
                   ON CONFLICT(capability_id) DO UPDATE SET available=EXCLUDED.available,concurrency_limit=EXCLUDED.concurrency_limit,
                   current_load=EXCLUDED.current_load,fuel=EXCLUDED.fuel,backoff_until=EXCLUDED.backoff_until,observed_at=now()""",
                (row[0], available, concurrency_limit, current_load, _json(fuel or {}), backoff_until),
            )

    def select(self, task: str, *, max_age_seconds: int = 300) -> dict[str, Any] | None:
        if not 1 <= max_age_seconds <= 86_400:
            raise ValueError("RIV-CAP-0002: freshness bound is invalid.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT c.capability_name,c.provider_id,c.version,cc.concurrency_limit,cc.current_load,cc.observed_at
                   FROM capabilities c JOIN capability_capacity cc ON cc.capability_id=c.capability_id
                   WHERE c.enabled=true AND c.health_status='healthy' AND cc.available=true
                   AND cc.current_load < cc.concurrency_limit AND %s = ANY(SELECT jsonb_array_elements_text(c.supported_tasks))
                   AND cc.observed_at >= now()-make_interval(secs=>%s)
                   AND (cc.backoff_until IS NULL OR cc.backoff_until <= now())
                   ORDER BY cc.current_load ASC,c.capability_name ASC LIMIT 1""",
                (task, max_age_seconds),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(zip(("capability_name", "provider_id", "version", "concurrency_limit", "current_load", "observed_at"), row, strict=True))

    def dispatch(self, task: str, *, classification: str = "river", max_age_seconds: int = 300) -> dict[str, Any]:
        """Return deterministic provider selection and the reason for it."""
        if classification not in {"river", "internal"}:
            raise ValueError("RIV-CAP-0001: protected classification cannot enter this dispatch path.")
        selected = self.select(task, max_age_seconds=max_age_seconds)
        if selected is None:
            return {"selected": None, "reason": "no enabled healthy capability has fresh compatible capacity", "classification": classification}
        return {"selected": selected, "reason": "lowest current load among enabled healthy measured capabilities with fresh compatible capacity", "classification": classification}


class GraceMomentum:
    """Evaluate objective readiness without inventing transitions or authority."""

    def evaluate(self, objective_key: str, correlation_id: UUID | None = None) -> list[dict[str, Any]]:
        correlation_id = correlation_id or uuid4()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT objective_id FROM objectives WHERE objective_key=%s", (objective_key,))
            objective = cursor.fetchone()
            if objective is None:
                raise RuntimeError("RIV-GRC-0004: objective is not present in PostgreSQL.")
            cursor.execute(
                """SELECT stage_id,stage_key,status,readiness,steward_checkpoint,declared_action FROM objective_stages
                   WHERE objective_id=%s ORDER BY sort_order""", (objective[0],)
            )
            rows = cursor.fetchall()
            decisions: list[dict[str, Any]] = []
            for stage_id, stage_key, status, readiness, steward_checkpoint, declared_action in rows:
                decision = "completed" if status == "completed" else ("ready" if readiness == "ready" else "blocked")
                reason = "stage is completed" if decision == "completed" else ("declared dependencies are complete" if decision == "ready" else "declared dependencies or evidence are incomplete")
                key = f"grace.evaluation:{objective_key}:{stage_key}:{decision}"
                cursor.execute(
                    """INSERT INTO grace_transition_evaluations(evaluation_id,objective_id,stage_id,correlation_id,decision,reason,next_action,evidence_refs,idempotency_key)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s) ON CONFLICT(idempotency_key) DO NOTHING""",
                    (uuid4(), objective[0], stage_id, correlation_id, "checkpoint" if steward_checkpoint and decision == "ready" else decision, reason, None if decision != "ready" else "declared-stage-action", _json([]), key),
                )
                decisions.append({"stage_key": stage_key, "decision": decision, "steward_checkpoint": steward_checkpoint, "declared_action": declared_action})
            return decisions

    def enqueue_declared_action(self, objective_key: str, stage_key: str, *, requested_by: str = "grace", root_task_id: UUID | None = None) -> dict[str, Any]:
        from riverview.relay import RelayStore

        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT s.stage_id,s.status,s.readiness,s.steward_checkpoint,s.declared_action,o.correlation_id,o.objective_id
                   FROM objective_stages s JOIN objectives o ON o.objective_id=s.objective_id
                   WHERE o.objective_key=%s AND s.stage_key=%s""", (objective_key, stage_key)
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("RIV-GRC-0004: declared objective stage is missing.")
        stage_id, status, readiness, steward_checkpoint, action, correlation_id, objective_id = row
        if status == "completed" or readiness != "ready" or steward_checkpoint:
            raise RuntimeError("RIV-GRC-0004: stage is not eligible for automatic action.")
        if not isinstance(action, dict) or not isinstance(action.get("action_type"), str) or not isinstance(action.get("parameters"), dict):
            raise TypeError("RIV-GRC-0004: no declared approved action is present.")
        intent_id = action["parameters"].get("engineering_intent_id")
        if intent_id:
            with connect() as connection, connection.cursor() as cursor:
                cursor.execute("""SELECT work_order_id,status,action_type FROM work_orders
                                  WHERE engineering_intent_id=%s AND work_order_kind='initial'
                                    AND source_work_order_id IS NULL
                                  ORDER BY created_at LIMIT 1""", (intent_id,))
                existing = cursor.fetchone()
            if existing is not None:
                return {"stage_id": str(stage_id), "work_order_id": str(existing[0]), "correlation_id": str(correlation_id), "action_type": existing[2], "already_enqueued": True}
        parameters = {**action["parameters"], **({"root_task_id": str(root_task_id)} if root_task_id is not None else {})}
        order = RelayStore().enqueue(action["action_type"], parameters, requested_by, f"grace:{objective_key}:{stage_key}", correlation_id, objective_id=objective_id, stage_id=stage_id)
        return {"stage_id": str(stage_id), "work_order_id": str(order.work_order_id), "correlation_id": str(correlation_id), "action_type": order.action_type}

    def form_authorized_intent(self, objective_id: UUID, stage_id: UUID) -> dict[str, Any]:
        """Consume a valid durable grant; never infer authority from prose."""
        from riverview.intake.authority import StewardAuthorityError, StewardAuthorityStore
        from riverview.intake.engineering import EngineeringIntentStore

        authority = StewardAuthorityStore().for_stage(objective_id, stage_id)
        if authority is None:
            return {"formed": False, "reason": "no_active_steward_authority"}
        try:
            result = EngineeringIntentStore().bind_from_authority(UUID(str(authority["authority_id"])))
        except (StewardAuthorityError, PermissionError, RuntimeError, ValueError) as exc:
            return {"formed": False, "authority_id": str(authority["authority_id"]), "reason": str(exc)}
        return {"formed": True, "authority_id": str(authority["authority_id"]), **result}

    def reconcile_execution(self, execution_id: UUID) -> dict[str, Any]:
        """Accept only a durable, successful, reconciled execution as stage evidence."""
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT e.status,r.result_category,rr.decision,o.objective_key,s.stage_key
                FROM execution_envelopes e JOIN execution_results r ON r.execution_id=e.execution_id
                LEFT JOIN reconciliation_records rr ON rr.execution_id=e.execution_id
                JOIN objectives o ON o.objective_id=e.objective_id
                JOIN objective_stages s ON s.stage_id=e.stage_id
                WHERE e.execution_id=%s ORDER BY rr.created_at DESC LIMIT 1""", (execution_id,))
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("RIV-REC-0001: execution reconciliation record is missing.")
        status, result_category, decision, objective_key, stage_key = row
        if status != "reconciled" or result_category != "succeeded" or decision != "accepted":
            return {"execution_id": str(execution_id), "progressed": False, "reason": "execution is not an accepted reconciled success"}
        store = ObjectiveStore()
        store.add_evidence(objective_key, stage_key, f"execution:reconciled:{execution_id}")
        store.complete_stage(objective_key, stage_key, {"execution_id": str(execution_id), "result": "accepted"})
        store.finalize(objective_key, {"execution_id": str(execution_id), "result": "accepted"})
        return {"execution_id": str(execution_id), "progressed": True, "objective_key": objective_key, "stage_key": stage_key}

    def detect_stale_work(self, correlation_id: UUID | None = None) -> list[dict[str, Any]]:
        """Record stale leases/checkpoints without changing user intent."""
        correlation_id = correlation_id or uuid4()
        stale: list[dict[str, Any]] = []
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT work_order_id,lease_owner,lease_expires_at FROM work_orders
                   WHERE status IN ('claimed','running') AND lease_expires_at < now()
                   ORDER BY lease_expires_at"""
            )
            for work_order_id, owner, expires_at in cursor.fetchall():
                key = f"grace.stale:{work_order_id}:{expires_at.isoformat()}"
                cursor.execute(
                    """INSERT INTO grace_checkpoints(checkpoint_id,checkpoint_code,subject_type,subject_id,correlation_id,reason,required_action,state,idempotency_key)
                       VALUES(%s,'RIV-GRC-0005','work_order',%s,%s,%s,%s,'open',%s)
                       ON CONFLICT(idempotency_key) DO NOTHING""",
                    (uuid4(), work_order_id, correlation_id, f"Lease owned by {owner!r} expired at {expires_at.isoformat()}.", "Inspect evidence, then apply only a declared retry-safe policy.", key),
                )
                stale.append({"work_order_id": work_order_id, "owner": owner, "expires_at": expires_at})
        return stale

    def route_checkpoint(self, *, checkpoint_code: str, subject_id: UUID | None, correlation_id: UUID, reason: str, required_action: str, idempotency_key: str) -> UUID:
        if not checkpoint_code or not reason or not required_action:
            raise ValueError("RIV-GRC-0006: checkpoint fields are required.")
        cookbook = CookbookAdvisor().lookup(checkpoint_code)
        if cookbook is not None:
            required_action = f"{required_action} Cookbook: {cookbook['repair_procedure'][0]}"
        checkpoint_id = uuid4()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO grace_checkpoints(checkpoint_id,checkpoint_code,subject_type,subject_id,correlation_id,reason,required_action,state,idempotency_key)
                   VALUES(%s,%s,'control_plane',%s,%s,%s,%s,'open',%s)
                   ON CONFLICT(idempotency_key) DO UPDATE SET checkpoint_id=grace_checkpoints.checkpoint_id
                   RETURNING checkpoint_id""",
                (checkpoint_id, checkpoint_code, subject_id, correlation_id, reason, required_action, idempotency_key),
            )
            return cursor.fetchone()[0]


class ContinuousMomentumEngine:
    """Run one bounded, event-driven Grace cycle across independent objectives."""

    def enqueue_declared_action(self, objective_key: str, stage_key: str, *, requested_by: str = "grace", root_task_id: UUID | None = None) -> dict[str, Any]:
        """Delegate approved work formation to Grace's authority boundary."""
        return GraceMomentum().enqueue_declared_action(objective_key, stage_key, requested_by=requested_by, root_task_id=root_task_id)

    def frontier(
        self,
        *,
        limit: int = 16,
        priority_objective_id: UUID | None = None,
        declared_only: bool = False,
    ) -> list[dict[str, Any]]:
        if not 1 <= limit <= 64:
            raise ValueError("RIV-GRC-0004: frontier limit is outside the bounded range.")
        with connect() as connection, connection.cursor() as cursor:
            order_clause = "CASE WHEN o.objective_id=%s THEN 0 ELSE 1 END, o.created_at,s.sort_order" if priority_objective_id else "o.created_at,s.sort_order"
            declared_clause = " AND s.declared_action IS NOT NULL" if declared_only else ""
            query = f"""SELECT o.objective_id,o.objective_key,o.correlation_id,s.stage_id,s.stage_key,
                          s.readiness,s.status,s.declared_action,s.steward_checkpoint
                   FROM objectives o JOIN objective_stages s ON s.objective_id=o.objective_id
                   WHERE o.status IN ('ready','active') AND s.status<>'completed'
                     AND s.readiness='ready' AND s.steward_checkpoint=false{declared_clause}
                   ORDER BY {order_clause} LIMIT %s"""
            cursor.execute(query, (priority_objective_id, limit) if priority_objective_id else (limit,))
            names = [item.name for item in cursor.description]
            return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]

    def cycle(self, *, limit: int = 16, correlation_id: UUID | None = None, priority_objective_id: UUID | None = None) -> dict[str, Any]:
        """Evaluate all currently eligible stages once; callers trigger the next cycle from an event."""
        correlation_id = correlation_id or uuid4()
        frontier = self.frontier(limit=limit, priority_objective_id=priority_objective_id)
        return self._evaluate_frontier(frontier, correlation_id=correlation_id)

    def _evaluate_frontier(self, frontier: list[dict[str, Any]], *, correlation_id: UUID) -> dict[str, Any]:
        """Evaluate one captured frontier without weakening its checkpoint boundary."""
        evaluated: list[dict[str, Any]] = []
        for item in frontier:
            # The database query enforces this boundary. Keep the check here too so
            # alternate/test frontier providers cannot turn a checkpoint into work.
            if item.get("steward_checkpoint", False):
                continue
            formation = GraceMomentum().form_authorized_intent(item["objective_id"], item["stage_id"])
            decisions = GraceMomentum().evaluate(item["objective_key"], correlation_id=correlation_id)
            stage = next(entry for entry in decisions if entry["stage_key"] == item["stage_key"])
            declared_action = item["declared_action"] if item["declared_action"] is not None else formation.get("action")
            evaluated.append({"objective_key": item["objective_key"], "stage_key": item["stage_key"], "decision": stage["decision"], "declared_action": declared_action, "formation": formation})
        return {"correlation_id": str(correlation_id), "frontier_count": len(frontier), "evaluated": evaluated, "bounded": True}

    def cycle_until_quiescent(
        self,
        *,
        limit: int = 16,
        max_cycles: int = 8,
        correlation_id: UUID | None = None,
        redispatch: Callable[[dict[str, Any]], None] | None = None,
        priority_objective_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Continue bounded Grace cycles after a provider result.

        A provider result is only one observation.  This method re-queries the
        authoritative frontier after each cycle and optionally redispatches
        each still-ready stage through an injected, already-authorized action.
        The cycle bound and the no-progress return prevent recursion and busy
        looping when a stage needs evidence or an external decision.
        """
        if not 1 <= max_cycles <= 64:
            raise ValueError("RIV-GRC-0004: cycle bound is outside the bounded range.")
        correlation = correlation_id or uuid4()
        cycles: list[dict[str, Any]] = []
        redispatched = 0
        stop_reason = "frontier_empty"
        for _ in range(max_cycles):
            current = self.frontier(limit=limit, priority_objective_id=priority_objective_id)
            if not current:
                break
            result = self.cycle(limit=limit, correlation_id=correlation, priority_objective_id=priority_objective_id)
            cycles.append(result)
            eligible = {
                (item["objective_key"], item["stage_key"])
                for item in current
                if not item.get("steward_checkpoint", False)
            }
            ready = [
                item
                for item in result["evaluated"]
                if item["decision"] == "ready"
                and (item["objective_key"], item["stage_key"]) in eligible
            ]
            if redispatch is not None:
                for item in ready:
                    redispatch(item)
                    redispatched += 1
            else:
                for item in ready:
                    if isinstance(item.get("declared_action"), dict):
                        self.enqueue_declared_action(item["objective_key"], item["stage_key"])
                        redispatched += 1
            next_frontier = self.frontier(limit=limit, priority_objective_id=priority_objective_id)
            if not next_frontier:
                stop_reason = "frontier_empty"
                break
            if not ready or next_frontier == current:
                stop_reason = "no_progress_or_external_boundary"
                break
        else:
            stop_reason = "cycle_bound_reached"
        return {
            "correlation_id": str(correlation),
            "cycles": cycles,
            "cycle_count": len(cycles),
            "redispatched": redispatched,
            "remaining_frontier": self.frontier(limit=limit, priority_objective_id=priority_objective_id),
            "stop_reason": stop_reason,
            "bounded": True,
        }


class CookbookAdvisor:
    """Read only the validated bounded repair guidance for a stable checkpoint."""

    def lookup(self, checkpoint_code: str) -> dict[str, Any] | None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT checkpoint_id,component,diagnostic_procedure,repair_procedure,verification_procedure,validation_state
                   FROM cookbook_entries WHERE checkpoint_id=%s AND validation_state='validated'""",
                (checkpoint_code,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(zip(("checkpoint_id", "component", "diagnostic_procedure", "repair_procedure", "verification_procedure", "validation_state"), row, strict=True))


class ExecutionStore:
    """Persist an envelope once and load it for a named adapter."""

    def persist(self, envelope: ExecutionEnvelope) -> UUID:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO execution_envelopes(execution_id,work_order_id,objective_id,stage_id,correlation_id,causation_id,capability_name,action_type,repository_identity,repository_root,expected_base_sha,bounded_instruction,allowed_paths,acceptance_criteria,evidence_requirements,timeout_seconds,retry_key,classification,write_policy,status)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s,'queued')
                   ON CONFLICT(retry_key) DO NOTHING
                   RETURNING execution_id""",
                (envelope.execution_id, envelope.work_order_id, envelope.objective_id, envelope.stage_id, envelope.correlation_id, envelope.causation_id, envelope.capability_name, envelope.action_type, envelope.repository_identity, str(envelope.repository_root), envelope.expected_base_sha, envelope.bounded_instruction, _json(envelope.allowed_paths), _json(envelope.acceptance_criteria), _json(envelope.evidence_requirements), envelope.timeout_seconds, envelope.retry_key, envelope.classification, envelope.write_policy),
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            cursor.execute("SELECT execution_id FROM execution_envelopes WHERE retry_key=%s", (envelope.retry_key,))
            return cursor.fetchone()[0]

    def start(self, execution_id: UUID) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE execution_envelopes SET status='running',started_at=COALESCE(started_at,now()),updated_at=now() WHERE execution_id=%s AND status='queued'", (execution_id,))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-EXE-0006: execution is not queued or does not exist.")

    def fail(self, execution_id: UUID, checkpoint: str, reason: str) -> None:
        """Close an adapter-start failure without rewriting its evidence."""
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE execution_envelopes SET status='failed',finished_at=now(),updated_at=now() WHERE execution_id=%s AND status='running'",
                (execution_id,),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-EXE-0006: failed execution envelope is not running.")
            cursor.execute("SELECT correlation_id FROM execution_envelopes WHERE execution_id=%s", (execution_id,))
            correlation_id = cursor.fetchone()[0]
            cursor.execute(
                """INSERT INTO grace_checkpoints(checkpoint_id,checkpoint_code,subject_type,subject_id,correlation_id,reason,required_action,state,idempotency_key)
                   SELECT %s,%s,'execution',execution_id,correlation_id,%s,%s,'open',%s
                   FROM execution_envelopes WHERE execution_id=%s
                   ON CONFLICT(idempotency_key) DO NOTHING""",
                (uuid4(), checkpoint, reason, "Prepare governed stale-base revalidation or route the execution checkpoint.", f"execution.failure:{execution_id}:{checkpoint}", execution_id),
            )
        EventStore().append(RiverEvent(
            event_type="execution.failure.recorded", aggregate_type="execution", aggregate_id=execution_id,
            correlation_id=correlation_id, causation_id=execution_id,
            idempotency_key=f"execution.failure.recorded:{execution_id}:{checkpoint}", classification=Classification.RIVER,
            payload={"execution_id": str(execution_id), "checkpoint": checkpoint, "status": "failed", "reason": reason[:500]},
        ))


class RetryPolicy:
    """Bounded retry decision based on the registered action, never recursion."""

    def decide(self, action_type: str, attempt: int, *, failure_class: str) -> dict[str, Any]:
        if attempt < 1:
            raise ValueError("RIV-GRC-0007: attempt must be positive.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT retry_safe FROM approved_actions WHERE action_type=%s AND enabled=true", (action_type,))
            row = cursor.fetchone()
        retry_safe = bool(row and row[0])
        allowed = retry_safe and attempt < 2 and failure_class in {"transport", "timeout", "provider_unavailable"}
        return {"retry": allowed, "attempt": attempt, "failure_class": failure_class, "reason": "registered action is retry-safe and below the one-retry bound" if allowed else "retry requires an explicit checkpoint"}


class CodexCliAdapter:
    """Run one bounded local Codex CLI package; no shell text comes from PostgreSQL."""

    provider_id = "codex-cli-local"

    def __init__(self, executable: str = "codex") -> None:
        self.executable = executable

    def run(self, envelope: ExecutionEnvelope) -> ExecutionResult:
        repository = envelope.repository_root.resolve()
        if not repository.is_dir() or not (repository / ".git").exists():
            raise RuntimeError("RIV-EXE-0002: repository root is unavailable or is not a Git repository.")
        executable = self.executable
        if os.name == "nt":
            executable = shutil.which(f"{self.executable}.cmd") or shutil.which(f"{self.executable}.exe") or self.executable
        else:
            executable = shutil.which(self.executable) or self.executable
        observed_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
        if observed_head != envelope.expected_base_sha:
            raise RuntimeError(
                f"RIV-EXE-0008: repository HEAD {observed_head} does not match the approved base revision."
            )
        execution_root = repository
        worktree: Path | None = None
        if envelope.write_policy == "bounded_write":
            worktree = Path(tempfile.mkdtemp(prefix="riverview-codex-worktree-"))
            worktree.rmdir()
            subprocess.run(["git", "worktree", "add", "--detach", "--quiet", str(worktree), observed_head], cwd=repository, check=True, capture_output=True, text=True)
            execution_root = worktree
        output_path = Path(tempfile.gettempdir()) / f"riverview-codex-result-{uuid4()}.txt"
        sandbox = "workspace-write" if envelope.write_policy == "bounded_write" else "read-only"
        command = [
            executable, "exec", "--json", "--ephemeral", "--sandbox", sandbox,
            "--output-last-message", str(output_path), "-C", str(execution_root), envelope.bounded_instruction,
        ]
        started = datetime.now(UTC)
        changed: tuple[str, ...] = ()
        commit_sha: str | None = None
        remote_verified_sha: str | None = None
        stdout = ""
        stderr = ""
        provider_output = ""
        try:
            process = subprocess.Popen(
                command,
                cwd=execution_root,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
            stdout, stderr = process.communicate(timeout=envelope.timeout_seconds)
            category = "succeeded" if process.returncode == 0 else "failed"
            exit_state = f"exit:{process.returncode}"
            provider_output = output_path.read_text(encoding="utf-8") if output_path.exists() else stdout
            if process.returncode == 0 and worktree is not None:
                changed = self._worktree_paths(worktree)
                rename_pairs = self._worktree_rename_pairs(worktree)
                allowed = tuple(Path(path).as_posix().rstrip("/") for path in envelope.allowed_paths)
                outside = ResultReconciler._outside_scope(changed, allowed, rename_pairs)
                if outside:
                    raise RuntimeError(f"RIV-EXE-0007: changed path escaped envelope: {outside!r}")
                if not changed:
                    raise RuntimeError("RIV-EXE-0010: bounded_write completed without an observable repository change.")
                self._copy_allowed_changes(worktree, repository, changed)
                if self._requires_commit(envelope.evidence_requirements):
                    commit_sha = self._commit_allowed_changes(repository, changed, envelope.execution_id)
                if self._requires_publication(envelope.evidence_requirements):
                    remote_verified_sha = self._publish_commit(repository, commit_sha)
            summary = self._bounded_success_summary(repository, provider_output, observed_head, envelope.write_policy) if process.returncode == 0 else "Codex CLI returned a nonzero exit state."
            checkpoint = () if process.returncode == 0 else ("RIV-EXE-0004",)
        except subprocess.TimeoutExpired:
            process_id = process.pid
            self._terminate_process_tree(process)
            try:
                _stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    _stdout, stderr = process.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    _stdout, stderr = "", ""
            timeout_paths: tuple[str, ...] = ()
            if worktree is not None:
                try:
                    timeout_paths = self._worktree_paths(worktree)
                except (OSError, subprocess.SubprocessError):
                    timeout_paths = ()
            target_state = {
                path: (worktree / path).is_file() if worktree is not None else False
                for path in envelope.allowed_paths
            }
            summary = self._timeout_diagnostic_summary(
                process_id=process_id,
                elapsed_seconds=(datetime.now(UTC) - started).total_seconds(),
                stdout=_stdout,
                stderr=stderr,
                changed_paths=timeout_paths,
                target_state=target_state,
            )
            changed = timeout_paths
            category, exit_state, checkpoint = "timed_out", "timeout", ("RIV-EXE-0003",)
        except RuntimeError as exc:
            message = str(exc)
            category, exit_state = "failed", "adapter_error"
            summary = self._adapter_error_summary(
                error=message,
                execution_root=execution_root,
                worktree=worktree,
                allowed_paths=envelope.allowed_paths,
                changed_paths=changed,
                provider_output=provider_output,
                stdout=stdout,
                stderr=stderr,
            )
            checkpoint = (self._checkpoint_for_error(message),)
        finally:
            output_path.unlink(missing_ok=True)
            if worktree is not None:
                subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repository, check=False, capture_output=True, text=True)
        finished = datetime.now(UTC)
        del stderr
        result = ExecutionResult(uuid4(), envelope.execution_id, envelope.correlation_id, self.provider_id, category, exit_state, changed, (summary,), commit_sha, remote_verified_sha, checkpoint, (), summary, started, finished)
        return result

    @staticmethod
    def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
        """Terminate the provider and descendants at the bounded timeout boundary."""

        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
            )
        else:
            process.kill()

    @staticmethod
    def _safe_diagnostic_tail(value: object, limit: int = 2000) -> str:
        """Keep timeout diagnostics bounded and redact common credential-shaped values."""

        if not isinstance(value, str):
            value = "" if value is None else str(value)
        redacted = re.sub(
            r"(?i)(authorization|password|secret|token|api[_-]?key)(?:[\"']?\s*[:=]\s*[\"']?)[^\"'\s,}]+",
            r"\1=[REDACTED]",
            value,
        )
        return redacted[-limit:]

    @classmethod
    def _timeout_diagnostic_summary(
        cls,
        *,
        process_id: int,
        elapsed_seconds: float,
        stdout: str,
        stderr: str,
        changed_paths: tuple[str, ...],
        target_state: dict[str, bool],
    ) -> str:
        """Persist phase metadata without persisting full provider prompts or events."""

        event_types: list[str] = []
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                event_type = event.get("type") or event.get("event")
                if isinstance(event_type, str) and event_type not in event_types:
                    event_types.append(event_type)
        payload = {
            "checkpoint": "RIV-EXE-0003",
            "message": "Codex CLI exceeded the bounded execution deadline.",
            "process_id": process_id,
            "elapsed_seconds": round(elapsed_seconds, 3),
            "last_event_type": event_types[-1] if event_types else None,
            "event_types": event_types[-20:],
            "changed_paths_at_timeout": list(changed_paths),
            "target_state_at_timeout": target_state,
            "stdout_tail": cls._safe_diagnostic_tail(stdout),
            "stderr_tail": cls._safe_diagnostic_tail(stderr),
        }
        return _json(payload)

    @classmethod
    def _adapter_error_summary(
        cls,
        *,
        error: str,
        execution_root: Path,
        worktree: Path | None,
        allowed_paths: tuple[str, ...],
        changed_paths: tuple[str, ...],
        provider_output: str,
        stdout: str,
        stderr: str,
    ) -> str:
        """Retain bounded evidence for post-provider adapter failures."""

        git_status = ""
        try:
            git_status = subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=execution_root,
                text=True,
                stderr=subprocess.STDOUT,
            )
        except (OSError, subprocess.SubprocessError):
            git_status = "<unavailable>"
        target_state = {
            path: (execution_root / path).is_file()
            for path in allowed_paths
        }
        payload = {
            "checkpoint": "adapter_error",
            "error": error[:500],
            "execution_root": str(execution_root),
            "temporary_worktree": str(worktree) if worktree is not None else None,
            "changed_paths": list(changed_paths),
            "allowed_path_state": target_state,
            "git_status": cls._safe_diagnostic_tail(git_status),
            "provider_output_tail": cls._safe_diagnostic_tail(provider_output),
            "stdout_tail": cls._safe_diagnostic_tail(stdout),
            "stderr_tail": cls._safe_diagnostic_tail(stderr),
        }
        return _json(payload)

    @staticmethod
    def _checkpoint_for_error(message: str) -> str:
        """Keep recovery routing aligned with the demonstrated failure class."""

        for prefix in ("RIV-EXE-0007", "RIV-EXE-0010", "RIV-REC-"):
            if message.startswith(prefix):
                return message.split(":", 1)[0]
        return "RIV-EXE-0010"

    @staticmethod
    def _requires_commit(evidence_requirements: tuple[str, ...]) -> bool:
        return any("commit" in item.lower() for item in evidence_requirements)

    @staticmethod
    def _requires_publication(evidence_requirements: tuple[str, ...]) -> bool:
        return any("publication" in item.lower() or "origin/main" in item.lower() for item in evidence_requirements)

    @staticmethod
    def _commit_allowed_changes(repository: Path, changed: tuple[str, ...], execution_id: UUID) -> str:
        if not changed:
            raise RuntimeError("RIV-REC-0004: cannot commit an empty bounded write.")
        subprocess.run(["git", "add", "--", *changed], cwd=repository, check=True, capture_output=True, text=True)
        staged = tuple(line.strip() for line in subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=repository, text=True).splitlines() if line.strip())
        if set(staged) != set(changed):
            raise RuntimeError(f"RIV-REC-0004: staged paths do not exactly match bounded changes: {staged!r}")
        subprocess.run(["git", "commit", "-m", f"Apply governed bounded engineering write {execution_id}"], cwd=repository, check=True, capture_output=True, text=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()

    @staticmethod
    def _publish_commit(repository: Path, commit_sha: str | None) -> str:
        if not commit_sha:
            raise RuntimeError("RIV-REC-0004: publication requires a verified commit.")
        subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=repository, check=True, capture_output=True, text=True)
        subprocess.run(["git", "fetch", "origin", "main"], cwd=repository, check=True, capture_output=True, text=True)
        remote = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=repository, text=True).strip()
        if remote != commit_sha:
            raise RuntimeError("RIV-REC-0004: published commit does not match origin/main.")
        return remote

    @staticmethod
    def _worktree_paths(worktree: Path) -> tuple[str, ...]:
        output = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=worktree, text=True)
        paths: list[str] = []
        for line in output.splitlines():
            if len(line) < 4:
                continue
            value = line[3:].strip()
            if " -> " in value:
                old, new = value.split(" -> ", 1)
                paths.extend((old, new))
            else:
                paths.append(value)
        return tuple(dict.fromkeys(paths))

    @staticmethod
    def _worktree_rename_pairs(worktree: Path) -> tuple[tuple[str, str], ...]:
        """Read Git's authoritative old/new correspondence for worktree renames."""

        output = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--find-renames=20%", "--untracked-files=all"],
            cwd=worktree,
            text=True,
        )
        pairs: list[tuple[str, str]] = []
        for line in output.splitlines():
            if len(line) < 4:
                continue
            value = line[3:].strip()
            if " -> " in value and line[0] == "R":
                old, new = value.split(" -> ", 1)
                pairs.append((old, new))
        return tuple(dict.fromkeys(pairs))

    @staticmethod
    def _copy_allowed_changes(worktree: Path, repository: Path, changed: tuple[str, ...]) -> None:
        for relative in changed:
            relative_path = Path(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise RuntimeError("RIV-EXE-0007: relative change path is invalid.")
            source = (worktree / relative_path).resolve()
            target = (repository / relative_path).resolve()
            if (source != worktree and worktree not in source.parents) or (target != repository and repository not in target.parents):
                raise RuntimeError("RIV-EXE-0007: resolved change escaped repository root.")
            if source.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            elif target.exists():
                target.unlink()

    @staticmethod
    def _bounded_success_summary(repository: Path, provider_output: str, observed_head: str, write_policy: str) -> str:
        """Keep provider output plus independently bounded repository evidence."""
        evidence = {
            "provider_output": provider_output[-2600:] if provider_output else "",
            "repository_identity": "ppow1/Riverview",
            "observed_git_head": observed_head,
            "ai_hints_readable": (repository / "AI_HINTS.md").is_file(),
            "charter_readable": (repository / "docs" / "governance" / "RIVERVIEW_CHARTER.md").is_file(),
            "write_policy": write_policy,
        }
        return json.dumps(evidence, ensure_ascii=False, separators=(",", ":"))[-3800:]


class ResultReconciler:
    """Persist typed results and refuse unsupported publication claims."""

    @staticmethod
    def validate_observed_state(
        *, result_category: str, observed_head: str, expected_base_sha: str,
        changed_paths: tuple[str, ...], allowed_paths: tuple[str, ...],
        repository_root: Path, acceptance_criteria: tuple[str, ...] = (),
        evidence_requirements: tuple[str, ...] = (),
        write_policy: str = READ_ONLY_POLICY, commit_sha: str | None = None,
        remote_verified_sha: str | None = None, claimed_changed_paths: tuple[str, ...] | None = None,
        rename_pairs: tuple[tuple[str, str], ...] = (),
    ) -> dict[str, Any]:
        if result_category != "succeeded":
            raise RuntimeError("RIV-REC-0002: provider result is not successful.")
        if commit_sha:
            if observed_head != commit_sha:
                raise RuntimeError("RIV-REC-0002: authoritative HEAD does not equal the verified commit.")
            try:
                subprocess.run(["git", "merge-base", "--is-ancestor", expected_base_sha, commit_sha], cwd=repository_root, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as exc:
                raise RuntimeError("RIV-REC-0002: resulting commit is not based on the approved base SHA.") from exc
        elif observed_head != expected_base_sha:
            raise RuntimeError("RIV-REC-0002: authoritative repository HEAD changed during execution.")
        allowed = tuple(Path(path).as_posix().rstrip("/") for path in allowed_paths)
        outside = ResultReconciler._outside_scope(changed_paths, allowed, rename_pairs)
        if outside:
            raise RuntimeError(f"RIV-EXE-0007: authoritative changed path escaped envelope: {outside!r}")
        if claimed_changed_paths is not None and set(claimed_changed_paths) != set(changed_paths):
            raise RuntimeError("RIV-REC-0003: provider changed-path claim differs from authoritative paths.")
        if write_policy == "bounded_write" and not changed_paths:
            raise RuntimeError("RIV-REC-0003: bounded write produced no authoritative changed path.")
        missing: list[str] = []
        content_failures: list[str] = []
        for criterion in acceptance_criteria:
            exists = re.search(r"(?:file|path)?\s*([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+)\s+exists\b", criterion, re.IGNORECASE)
            if exists and not (repository_root / exists.group(1)).is_file():
                missing.append(exists.group(1))
            contains = re.search(r"(?:file|path)?\s*([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+)\s+contains\s+(.+)", criterion, re.IGNORECASE)
            if contains:
                relative, expected = contains.groups()
                expected = expected.strip().strip("\"'")
                path = repository_root / relative
                if not path.is_file() or expected not in path.read_text(encoding="utf-8"):
                    content_failures.append(relative)
        if missing:
            raise RuntimeError(f"RIV-REC-0003: required artifact is missing: {tuple(missing)!r}")
        if content_failures:
            raise RuntimeError(f"RIV-REC-0003: required artifact content is not verified: {tuple(content_failures)!r}")
        commit_required = any("resulting commit" in item.lower() for item in evidence_requirements)
        publication_required = any("publication" in item.lower() or "origin/main" in item.lower() for item in evidence_requirements)
        if write_policy == "bounded_write" and commit_required and not commit_sha:
            raise RuntimeError("RIV-REC-0004: required resulting commit was not independently supplied.")
        if publication_required and not remote_verified_sha:
            raise RuntimeError("RIV-REC-0004: required publication was not independently verified.")
        if commit_sha:
            try:
                subprocess.run(["git", "cat-file", "-e", f"{commit_sha}^{{commit}}"], cwd=repository_root, check=True, capture_output=True, text=True)
                tree = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", commit_sha], cwd=repository_root, text=True).splitlines()
            except subprocess.CalledProcessError as exc:
                raise RuntimeError("RIV-REC-0004: provider-claimed commit is not present authoritatively.") from exc
            if not any(path in tree for path in changed_paths):
                raise RuntimeError("RIV-REC-0004: provider-claimed commit does not contain verified changes.")
        if remote_verified_sha:
            if remote_verified_sha != commit_sha:
                raise RuntimeError("RIV-REC-0004: remote publication SHA does not match commit SHA.")
            try:
                subprocess.run(["git", "merge-base", "--is-ancestor", remote_verified_sha, "origin/main"], cwd=repository_root, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as exc:
                raise RuntimeError("RIV-REC-0004: published commit is not reachable from origin/main.") from exc
        return {"observed_head": observed_head, "changed_paths": changed_paths, "rename_pairs": rename_pairs, "outside_scope": outside, "missing_artifacts": missing, "content_verified": not content_failures}

    @staticmethod
    def _outside_scope(
        changed_paths: tuple[str, ...], allowed_paths: tuple[str, ...],
        rename_pairs: tuple[tuple[str, str], ...] = (),
    ) -> tuple[str, ...]:
        """Authorize exact paths and bounded same-scope Git rename replacements."""

        allowed = tuple(Path(path).as_posix().rstrip("/") for path in allowed_paths)
        paired: set[str] = set()
        outside: list[str] = []
        seen_old: set[str] = set()
        seen_new: set[str] = set()
        changed = set(changed_paths)
        for old, new in rename_pairs:
            old_path = Path(old)
            new_path = Path(new)
            valid = (
                old in changed
                and new in changed
                and old not in seen_old
                and new not in seen_new
                and not old_path.is_absolute()
                and not new_path.is_absolute()
                and ".." not in old_path.parts
                and ".." not in new_path.parts
                and any(old == item or old.startswith(f"{item}/") for item in allowed)
                and old_path.parent == new_path.parent
            )
            if valid:
                paired.update((old, new))
                seen_old.add(old)
                seen_new.add(new)
            else:
                outside.extend((old, new))
        for path in changed_paths:
            if path in paired or any(path == item or path.startswith(f"{item}/") for item in allowed):
                continue
            outside.append(path)
        return tuple(dict.fromkeys(outside))

    @staticmethod
    def _git_rename_pairs(repository_root: Path, base_sha: str, commit_sha: str) -> tuple[tuple[str, str], ...]:
        """Extract deterministic Git rename correspondence from an authoritative commit."""

        output = subprocess.check_output(
            ["git", "diff", "--name-status", "--find-renames=20%", base_sha, commit_sha],
            cwd=repository_root,
            text=True,
        )
        pairs: list[tuple[str, str]] = []
        for line in output.splitlines():
            fields = line.split("\t")
            if len(fields) == 3 and fields[0].startswith("R"):
                pairs.append((fields[1], fields[2]))
        return tuple(dict.fromkeys(pairs))

    def persist(self, result: ExecutionResult) -> None:
        if result.remote_verified_sha and not result.commit_sha:
            raise ValueError("RIV-EXE-0005: remote verification cannot exist without a commit SHA.")
        bounded_summary = self._bounded_persisted_summary(result.bounded_summary)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO execution_results(result_id,execution_id,correlation_id,provider_id,result_category,exit_state,changed_paths,validation_evidence,commit_sha,remote_verified_sha,checkpoint_refs,artifact_refs,bounded_summary,started_at,finished_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s)
                   ON CONFLICT(execution_id) DO NOTHING""",
                (result.result_id, result.execution_id, result.correlation_id, result.provider_id, result.result_category, result.exit_state, _json(result.changed_paths), _json(result.validation_evidence), result.commit_sha, result.remote_verified_sha, _json(result.checkpoint_refs), _json(result.artifact_refs), bounded_summary, result.started_at, result.finished_at),
            )
            cursor.execute("UPDATE execution_envelopes SET status=%s,finished_at=%s,updated_at=now() WHERE execution_id=%s", (result.result_category, result.finished_at, result.execution_id))
            if result.result_category != "succeeded":
                checkpoint = result.checkpoint_refs[0] if result.checkpoint_refs else "RIV-EXE-0001"
                guidance = CookbookAdvisor().lookup(checkpoint)
                repair = guidance["repair_procedure"][0] if guidance else "Inspect the bounded execution evidence and route a checkpoint."
                cursor.execute(
                    """INSERT INTO grace_checkpoints(checkpoint_id,checkpoint_code,subject_type,subject_id,correlation_id,reason,required_action,state,idempotency_key)
                       SELECT %s,%s,'execution',execution_id,correlation_id,%s,%s,'open',%s
                       FROM execution_envelopes WHERE execution_id=%s
                       ON CONFLICT(idempotency_key) DO NOTHING""",
                    (uuid4(), checkpoint, "Bounded adapter result was not successful.", repair, f"execution.failure:{result.execution_id}:{checkpoint}", result.execution_id),
                )
        EventStore().append(RiverEvent(
            event_type="execution.result.recorded", aggregate_type="execution", aggregate_id=result.execution_id,
            correlation_id=result.correlation_id, causation_id=result.execution_id,
            idempotency_key=f"execution.result.recorded:{result.execution_id}", classification=Classification.RIVER,
            payload={"execution_id": str(result.execution_id), "result_category": result.result_category},
        ))

    @staticmethod
    def _bounded_persisted_summary(value: Any) -> str:
        """Guarantee the database invariant without weakening its safety bound."""

        text = value if isinstance(value, str) else str(value or "No bounded execution summary was supplied.")
        text = text.strip()
        if not text:
            text = "No bounded execution summary was supplied."
        suffix = "… [bounded summary truncated]"
        return text if len(text) <= 4000 else f"{text[:4000 - len(suffix)]}{suffix}"

    def reconcile_repository(self, execution_id: UUID, repository_root: Path, allowed_paths: tuple[str, ...], baseline_paths: tuple[str, ...] = (), *, expected_base_sha: str | None = None, acceptance_criteria: tuple[str, ...] = (), evidence_requirements: tuple[str, ...] = (), write_policy: str = READ_ONLY_POLICY) -> dict[str, Any]:
        """Independently verify changed paths and close only a bounded result."""
        if not repository_root.is_dir() or not (repository_root / ".git").exists():
            raise RuntimeError("RIV-EXE-0002: repository root is unavailable during reconciliation.")
        output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=repository_root,
            text=True,
            stderr=subprocess.STDOUT,
        )
        baseline = set(baseline_paths)
        changed = tuple(path for path in (line[3:].strip() for line in output.splitlines() if len(line) >= 4) if path not in baseline)
        observed_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository_root, text=True).strip()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT result_category,commit_sha,remote_verified_sha,changed_paths FROM execution_results WHERE execution_id=%s", (execution_id,))
            result_row = cursor.fetchone()
        if result_row is None:
            raise RuntimeError("RIV-REC-0001: execution result is missing during authoritative verification.")
        commit_sha = result_row[1]
        rename_pairs = self._git_rename_pairs(repository_root, expected_base_sha, commit_sha) if commit_sha and expected_base_sha else ()
        if commit_sha and expected_base_sha:
            changed = tuple(path for path in subprocess.check_output(["git", "diff", "--name-only", f"{expected_base_sha}..{commit_sha}"], cwd=repository_root, text=True).splitlines() if path)
        claimed = tuple(result_row[3] or ())
        verified = self.validate_observed_state(
            result_category=result_row[0], observed_head=observed_head, expected_base_sha=expected_base_sha or observed_head,
            changed_paths=changed, allowed_paths=allowed_paths, repository_root=repository_root,
            acceptance_criteria=acceptance_criteria, evidence_requirements=evidence_requirements, write_policy=write_policy,
            commit_sha=commit_sha, remote_verified_sha=result_row[2], claimed_changed_paths=claimed,
            rename_pairs=rename_pairs,
        )
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE execution_results SET changed_paths=%s::jsonb,validation_evidence=%s::jsonb
                   WHERE execution_id=%s""",
                (_json(changed), _json([{"provider_claimed_result": result_row[0], "provider_claimed_commit": result_row[1], "riverview_verified": verified}]), execution_id),
            )
            cursor.execute("UPDATE execution_envelopes SET status='reconciled',updated_at=now() WHERE execution_id=%s", (execution_id,))
        EventStore().append(RiverEvent(
            event_type="execution.reconciled", aggregate_type="execution", aggregate_id=execution_id,
            correlation_id=UUID(str(self._execution_correlation(execution_id))), causation_id=execution_id,
            idempotency_key=f"execution.reconciled:{execution_id}", classification=Classification.RIVER,
            payload={"execution_id": str(execution_id), "changed_paths": list(changed), "rename_pairs": [list(pair) for pair in rename_pairs], "outside_scope": list(verified["outside_scope"])},
        ))
        return {"execution_id": str(execution_id), "changed_paths": changed, "outside_scope": verified["outside_scope"], "reconciled": True}

    @staticmethod
    def _execution_correlation(execution_id: UUID) -> UUID:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT correlation_id FROM execution_envelopes WHERE execution_id=%s", (execution_id,))
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("RIV-REC-0001: execution correlation is missing.")
        return row[0]

    def record_publication(self, execution_id: UUID, commit_sha: str, remote_verified_sha: str) -> None:
        if len(commit_sha) != 40 or len(remote_verified_sha) != 40 or commit_sha != remote_verified_sha:
            raise ValueError("RIV-EXE-0005: publication SHA must be independently exact.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE execution_results SET commit_sha=%s,remote_verified_sha=%s WHERE execution_id=%s", (commit_sha, remote_verified_sha, execution_id))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-EXE-0005: execution result is missing.")

    def record_decision(self, execution_id: UUID, correlation_id: UUID, decision: str, reason: str, evidence_refs: tuple[str, ...], idempotency_key: str) -> UUID:
        if decision not in {"accepted", "rejected", "conflict", "checkpoint"} or not reason:
            raise ValueError("RIV-REC-0001: reconciliation decision is invalid.")
        reconciliation_id = uuid4()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""INSERT INTO reconciliation_records(reconciliation_id,execution_id,correlation_id,decision,reason,evidence_refs,idempotency_key)
                VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s) ON CONFLICT(idempotency_key) DO NOTHING""", (reconciliation_id, execution_id, correlation_id, decision, reason, _json(evidence_refs), idempotency_key))
            cursor.execute("SELECT reconciliation_id FROM reconciliation_records WHERE idempotency_key=%s", (idempotency_key,))
            result = cursor.fetchone()[0]
            if decision in {"rejected", "conflict", "checkpoint"}:
                cursor.execute("UPDATE execution_envelopes SET status='escalated',finished_at=COALESCE(finished_at,now()),updated_at=now() WHERE execution_id=%s", (execution_id,))
        EventStore().append(RiverEvent(
            event_type="execution.reconciliation.recorded", aggregate_type="execution", aggregate_id=execution_id,
            correlation_id=correlation_id, causation_id=execution_id,
            idempotency_key=f"execution.reconciliation.recorded:{idempotency_key}", classification=Classification.RIVER,
            payload={"execution_id": str(execution_id), "decision": decision},
        ))
        return result

    def record_correction(self, execution_id: UUID, correlation_id: UUID, reason: str, evidence: dict[str, Any], idempotency_key: str) -> UUID:
        """Append a correction without changing the original reconciliation record."""
        correction_id = uuid4()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO execution_reconciliation_corrections(correction_id,execution_id,correlation_id,prior_decision,corrected_decision,reason,evidence,idempotency_key)
                   VALUES(%s,%s,%s,'accepted','checkpoint',%s,%s::jsonb,%s)
                   ON CONFLICT(idempotency_key) DO NOTHING""",
                (correction_id, execution_id, correlation_id, reason, _json(evidence), idempotency_key),
            )
            cursor.execute("SELECT correction_id FROM execution_reconciliation_corrections WHERE idempotency_key=%s", (idempotency_key,))
            return cursor.fetchone()[0]


class LaneRegistry:
    """Exclusive relative-path ownership for separable execution lanes."""

    def acquire(self, lane_key: str, owner_id: str, correlation_id: UUID, allowed_paths: tuple[str, ...]) -> UUID:
        if not lane_key or not owner_id or not allowed_paths or any(Path(path).is_absolute() for path in allowed_paths):
            raise ValueError("RIV-CAP-0003: lane ownership input is invalid.")
        lane_id = uuid4()
        with connect() as connection, connection.cursor() as cursor:
            for path in sorted(set(allowed_paths)):
                cursor.execute("SELECT lane_id FROM lane_path_owners WHERE relative_path=%s FOR UPDATE", (path,))
                if cursor.fetchone() is not None:
                    raise RuntimeError("RIV-CAP-0003: path is already owned by another active lane.")
            cursor.execute("INSERT INTO execution_lanes(lane_id,lane_key,correlation_id,owner_id,allowed_paths,state) VALUES(%s,%s,%s,%s,%s::jsonb,'active')", (lane_id, lane_key, correlation_id, owner_id, _json(allowed_paths)))
            for path in sorted(set(allowed_paths)):
                cursor.execute("INSERT INTO lane_path_owners(relative_path,lane_id,owner_id) VALUES(%s,%s,%s)", (path, lane_id, owner_id))
        return lane_id

    def release(self, lane_id: UUID, owner_id: str) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE execution_lanes SET state='released',released_at=now() WHERE lane_id=%s AND owner_id=%s AND state='active'", (lane_id, owner_id))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-CAP-0003: lane is not active or owner does not match.")
            cursor.execute("DELETE FROM lane_path_owners WHERE lane_id=%s", (lane_id,))
