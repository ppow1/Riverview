"""Durable, bounded control-plane primitives for Grace and local Codex.

Version: 0.1.0

This module deliberately keeps provider selection and execution separate from MCP.
The database stores typed envelopes and results; it never stores executable shell
text or provider credentials.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect


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
    classification: str = "river"
    causation_id: UUID | None = None
    objective_id: UUID | None = None
    stage_id: UUID | None = None
    work_order_id: UUID | None = None

    def __post_init__(self) -> None:
        if not self.capability_name or not self.repository_identity:
            raise ValueError("RIV-EXE-0001: capability and repository identity are required.")
        if not self.repository_root.is_absolute():
            raise ValueError("RIV-EXE-0001: execution root must be absolute.")
        if not self.expected_base_sha or len(self.expected_base_sha) != 40:
            raise ValueError("RIV-EXE-0001: expected base SHA is invalid.")
        if not 1 <= len(self.bounded_instruction) <= 16_000:
            raise ValueError("RIV-EXE-0001: bounded instruction is outside its safe limit.")
        if not self.allowed_paths or any(not path or Path(path).is_absolute() for path in self.allowed_paths):
            raise ValueError("RIV-EXE-0001: allowed paths must be non-empty relative paths.")
        if not 1 <= self.timeout_seconds <= 86_400:
            raise ValueError("RIV-EXE-0001: timeout is outside its safe limit.")
        if self.classification not in {"river", "internal"}:
            raise ValueError("RIV-EXE-0001: unsupported classification.")


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
                """SELECT stage_id,stage_key,status,readiness,steward_checkpoint FROM objective_stages
                   WHERE objective_id=%s ORDER BY sort_order""", (objective[0],)
            )
            rows = cursor.fetchall()
            decisions: list[dict[str, Any]] = []
            for stage_id, stage_key, status, readiness, steward_checkpoint in rows:
                decision = "completed" if status == "completed" else ("ready" if readiness == "ready" else "blocked")
                reason = "stage is completed" if decision == "completed" else ("declared dependencies are complete" if decision == "ready" else "declared dependencies or evidence are incomplete")
                key = f"grace.evaluation:{objective_key}:{stage_key}:{decision}"
                cursor.execute(
                    """INSERT INTO grace_transition_evaluations(evaluation_id,objective_id,stage_id,correlation_id,decision,reason,next_action,evidence_refs,idempotency_key)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s) ON CONFLICT(idempotency_key) DO NOTHING""",
                    (uuid4(), objective[0], stage_id, correlation_id, "checkpoint" if steward_checkpoint and decision == "ready" else decision, reason, None if decision != "ready" else "declared-stage-action", _json([]), key),
                )
                decisions.append({"stage_key": stage_key, "decision": decision, "steward_checkpoint": steward_checkpoint})
            return decisions

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
                """INSERT INTO execution_envelopes(execution_id,work_order_id,objective_id,stage_id,correlation_id,causation_id,capability_name,repository_identity,repository_root,expected_base_sha,bounded_instruction,allowed_paths,acceptance_criteria,evidence_requirements,timeout_seconds,retry_key,classification,status)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,'queued')
                   ON CONFLICT(retry_key) DO NOTHING
                   RETURNING execution_id""",
                (envelope.execution_id, envelope.work_order_id, envelope.objective_id, envelope.stage_id, envelope.correlation_id, envelope.causation_id, envelope.capability_name, envelope.repository_identity, str(envelope.repository_root), envelope.expected_base_sha, envelope.bounded_instruction, _json(envelope.allowed_paths), _json(envelope.acceptance_criteria), _json(envelope.evidence_requirements), envelope.timeout_seconds, envelope.retry_key, envelope.classification),
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
        command = [executable, "exec", "--json", "--ephemeral", "--sandbox", "workspace-write", "-C", str(repository), envelope.bounded_instruction]
        started = datetime.now(UTC)
        try:
            process = subprocess.Popen(command, cwd=repository, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
            _stdout, stderr = process.communicate(timeout=envelope.timeout_seconds)
            category = "succeeded" if process.returncode == 0 else "failed"
            exit_state = f"exit:{process.returncode}"
            summary = "Codex CLI completed the bounded package." if process.returncode == 0 else "Codex CLI returned a nonzero exit state."
            checkpoint = () if process.returncode == 0 else ("RIV-EXE-0004",)
        except subprocess.TimeoutExpired:
            process.kill()
            _stdout, stderr = process.communicate()
            category, exit_state, summary, checkpoint = "timed_out", "timeout", "Codex CLI exceeded the bounded execution deadline.", ("RIV-EXE-0003",)
        finished = datetime.now(UTC)
        del stderr
        result = ExecutionResult(uuid4(), envelope.execution_id, envelope.correlation_id, self.provider_id, category, exit_state, (), (), None, None, checkpoint, (), summary, started, finished)
        return result


class ResultReconciler:
    """Persist typed results and refuse unsupported publication claims."""

    def persist(self, result: ExecutionResult) -> None:
        if result.remote_verified_sha and not result.commit_sha:
            raise ValueError("RIV-EXE-0005: remote verification cannot exist without a commit SHA.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO execution_results(result_id,execution_id,correlation_id,provider_id,result_category,exit_state,changed_paths,validation_evidence,commit_sha,remote_verified_sha,checkpoint_refs,artifact_refs,bounded_summary,started_at,finished_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s)
                   ON CONFLICT(execution_id) DO NOTHING""",
                (result.result_id, result.execution_id, result.correlation_id, result.provider_id, result.result_category, result.exit_state, _json(result.changed_paths), _json(result.validation_evidence), result.commit_sha, result.remote_verified_sha, _json(result.checkpoint_refs), _json(result.artifact_refs), result.bounded_summary, result.started_at, result.finished_at),
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

    def reconcile_repository(self, execution_id: UUID, repository_root: Path, allowed_paths: tuple[str, ...], baseline_paths: tuple[str, ...] = ()) -> dict[str, Any]:
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
        allowed = tuple(Path(path).as_posix().rstrip("/") for path in allowed_paths)
        outside = tuple(path for path in changed if not any(path == item or path.startswith(f"{item}/") for item in allowed))
        if outside:
            raise RuntimeError(f"RIV-EXE-0007: changed path escaped envelope: {outside!r}")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE execution_results SET changed_paths=%s::jsonb,validation_evidence=%s::jsonb
                   WHERE execution_id=%s""",
                (_json(changed), _json(["git status path-boundary check passed"]), execution_id),
            )
            cursor.execute("UPDATE execution_envelopes SET status='reconciled',updated_at=now() WHERE execution_id=%s", (execution_id,))
        return {"execution_id": str(execution_id), "changed_paths": changed, "outside_scope": outside, "reconciled": True}

    def record_publication(self, execution_id: UUID, commit_sha: str, remote_verified_sha: str) -> None:
        if len(commit_sha) != 40 or len(remote_verified_sha) != 40 or commit_sha != remote_verified_sha:
            raise ValueError("RIV-EXE-0005: publication SHA must be independently exact.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE execution_results SET commit_sha=%s,remote_verified_sha=%s WHERE execution_id=%s", (commit_sha, remote_verified_sha, execution_id))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-EXE-0005: execution result is missing.")
