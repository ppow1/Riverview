"""Bounded engineering intent and decomposition records for RV-012."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.intake.policy import (
    ENGINEERING_ACTION,
    ENGINEERING_CAPABILITY,
    READ_ONLY_POLICY,
    validate_allowed_paths,
    validate_engineering_policy,
)


@dataclass(frozen=True, slots=True)
class RepositoryMap:
    repository_identity: str
    root: str
    entry_points: tuple[str, ...]
    runtime_seams: tuple[str, ...]
    dependency_seams: tuple[str, ...]
    test_seams: tuple[str, ...]
    data_seams: tuple[str, ...]
    deployment_seams: tuple[str, ...]
    authoritative_sources: tuple[str, ...]
    unknowns: tuple[str, ...]
    mutable_ownership: tuple[str, ...]

    def validate(self) -> None:
        if not self.repository_identity.strip() or not self.root.strip():
            raise ValueError("RIV-INT-0002: repository identity and root are required.")
        if not self.authoritative_sources or not self.mutable_ownership:
            raise ValueError("RIV-INT-0002: authoritative sources and ownership are required.")


@dataclass(frozen=True, slots=True)
class EngineeringTask:
    task_id: str
    objective_id: str
    instruction: str
    allowed_paths: tuple[str, ...]
    provider_need: str
    acceptance: tuple[str, ...]
    checkpoint: str
    merge_owner: str

    def validate(self) -> None:
        if not self.task_id.strip() or not self.objective_id.strip() or not self.instruction.strip():
            raise ValueError("RIV-INT-0003: task identity and bounded instruction are required.")
        if not self.allowed_paths or any(path.startswith(("/", "\\")) for path in self.allowed_paths):
            raise ValueError("RIV-CAP-0002: task paths must be non-empty relative paths.")
        if not self.acceptance or not self.checkpoint.strip() or not self.merge_owner.strip():
            raise ValueError("RIV-INT-0003: task acceptance, checkpoint, and merge owner are required.")


@dataclass(frozen=True, slots=True)
class EngineeringIntent:
    """A typed, Steward-approved formation request; never executable shell text."""

    seed_id: UUID
    objective_id: UUID
    stage_id: UUID
    repository_identity: str
    repository_root: Path
    expected_base_sha: str
    bounded_instruction: str
    allowed_paths: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    capability_name: str
    action_type: str
    timeout_seconds: int
    classification: str
    correlation_id: UUID
    causation_id: UUID | None
    idempotency_key: str
    approved_by: str = "steward"
    write_policy: str = READ_ONLY_POLICY
    intent_id: UUID | None = None

    def validate(self) -> None:
        if not self.repository_identity or self.repository_identity not in {"ppow1/Riverview", "Riverview standalone"}:
            raise ValueError("RIV-INT-0004: repository identity is not approved.")
        if not self.repository_root.is_absolute() or not (self.repository_root / ".git").is_dir():
            raise ValueError("RIV-INT-0004: repository root is not an approved Git repository.")
        if len(self.expected_base_sha) != 40 or any(ch not in "0123456789abcdef" for ch in self.expected_base_sha.lower()):
            raise ValueError("RIV-INT-0004: expected base SHA is invalid.")
        if not 1 <= len(self.bounded_instruction) <= 16_000:
            raise ValueError("RIV-INT-0004: bounded instruction is outside its safe limit.")
        validate_allowed_paths(self.allowed_paths)
        if not self.acceptance_criteria or not self.evidence_requirements:
            raise ValueError("RIV-INT-0004: acceptance and evidence requirements are required.")
        if self.capability_name != ENGINEERING_CAPABILITY or self.action_type != ENGINEERING_ACTION:
            raise ValueError("RIV-CAP-0004: only the registered Codex engineering capability is accepted.")
        if not 1 <= self.timeout_seconds <= 86_400 or self.classification not in {"river", "internal"}:
            raise ValueError("RIV-INT-0004: timeout or classification is invalid.")
        if self.approved_by != "steward":
            raise ValueError("RIV-GRC-0004: only Steward-approved formation is accepted.")
        validate_engineering_policy(self.write_policy)
        if not self.idempotency_key.strip():
            raise ValueError("RIV-INT-0004: idempotency key is required.")


class EngineeringIntentStore:
    """Canonical durable seed-to-action formation boundary."""

    @staticmethod
    def _fingerprint(intent: EngineeringIntent) -> str:
        payload = {
            "seed_id": str(intent.seed_id), "objective_id": str(intent.objective_id), "stage_id": str(intent.stage_id),
            "repository_identity": intent.repository_identity, "repository_root": str(intent.repository_root),
            "expected_base_sha": intent.expected_base_sha, "bounded_instruction": intent.bounded_instruction,
            "allowed_paths": intent.allowed_paths, "acceptance_criteria": intent.acceptance_criteria,
            "evidence_requirements": intent.evidence_requirements, "capability_name": intent.capability_name,
            "action_type": intent.action_type, "timeout_seconds": intent.timeout_seconds,
            "classification": intent.classification, "correlation_id": str(intent.correlation_id),
            "causation_id": str(intent.causation_id) if intent.causation_id else None,
            "approved_by": intent.approved_by, "write_policy": intent.write_policy,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def bind(self, intent: EngineeringIntent, *, authority_id: UUID | None = None, explicit_steward_confirmation: bool | None = None, on_bound: Any = None) -> dict[str, Any]:
        """Bind one validated intent to one eligible stage and emit one River fact."""
        # A caller-supplied boolean is deliberately not an authority source.
        # Formation must name the durable grant that covers this exact scope.
        if authority_id is None:
            raise PermissionError("RIV-GRC-0010: a durable Steward authority grant is required for formation.")
        intent.validate()
        intent_id = intent.intent_id or uuid4()
        fingerprint = self._fingerprint(intent)
        action = {"action_type": intent.action_type, "parameters": {"engineering_intent_id": str(intent_id)}}
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT intent_id,request_hash FROM engineering_intents WHERE idempotency_key=%s", (intent.idempotency_key,))
            existing = cursor.fetchone()
            if existing:
                if existing[1] != fingerprint:
                    raise ValueError("RIV-INT-0005: engineering-intent idempotency conflict.")
                return {"intent_id": str(existing[0]), "status": "already_bound", "idempotent": True}
            cursor.execute(
                """SELECT a.status,a.approving_principal,a.specification_version,a.specification_sha256,
                          a.seed_id,a.objective_id,a.stage_id,a.classification,a.correlation_id,a.causation_id,
                          s.version,s.content_sha256,s.formation_contract
                   FROM steward_authority_grants a JOIN comms5_specifications s ON s.specification_id=a.specification_id
                   WHERE a.authority_id=%s FOR UPDATE""", (authority_id,))
            grant = cursor.fetchone()
            if grant is None or grant[0] != "active" or grant[1] != "steward":
                raise PermissionError("RIV-GRC-0010: Steward authority grant is missing, inactive, or exhausted.")
            if (grant[2], grant[3], grant[4], grant[5], grant[6], grant[7], grant[8], grant[9]) != (grant[10], grant[11], intent.seed_id, intent.objective_id, intent.stage_id, intent.classification, intent.correlation_id, intent.causation_id):
                raise ValueError("RIV-GRC-0010: approved specification, lineage, classification, or correlation does not match formation.")
            if grant[12] is None:
                raise ValueError("RIV-GRC-0010: approved specification has no typed engineering formation contract.")
            cursor.execute("""SELECT s.status,s.readiness,s.declared_action,o.status,sd.status,sd.objective_id,sd.classification
                FROM objective_stages s JOIN objectives o ON o.objective_id=s.objective_id
                JOIN steward_seed_drafts sd ON sd.objective_id=o.objective_id
                WHERE s.stage_id=%s AND s.objective_id=%s AND sd.seed_id=%s FOR UPDATE""", (intent.stage_id, intent.objective_id, intent.seed_id))
            state = cursor.fetchone()
            if state is None or state[5] != intent.objective_id:
                raise RuntimeError("RIV-GRC-0004: seed, objective, and stage authority do not reconcile.")
            stage_status, readiness, declared_action, objective_status, seed_status, _, seed_classification = state
            if seed_classification != intent.classification:
                raise ValueError("RIV-GRC-0004: engineering intent classification does not match the Steward seed.")
            if seed_status != "promoted" or objective_status in {"completed", "cancelled"} or stage_status in {"completed", "cancelled"}:
                raise RuntimeError("RIV-GRC-0004: objective or seed is not eligible for formation.")
            if readiness != "ready" or declared_action is not None:
                raise RuntimeError("RIV-GRC-0004: stage is not an unbound ready formation target.")
            cursor.execute("SELECT enabled FROM approved_actions WHERE action_type=%s", (intent.action_type,))
            action_row = cursor.fetchone()
            if not action_row or not action_row[0]:
                raise RuntimeError("RIV-WRK-0001: registered action is missing or disabled.")
            cursor.execute("SELECT enabled,health_status FROM capabilities WHERE capability_name=%s", (intent.capability_name,))
            capability = cursor.fetchone()
            if not capability or not capability[0] or capability[1] != "healthy":
                raise RuntimeError("RIV-CAP-0001: required capability is unavailable.")
            cursor.execute("""INSERT INTO engineering_intents(
                intent_id,authority_id,seed_id,objective_id,stage_id,request_hash,repository_identity,repository_root,
                expected_base_sha,bounded_instruction,allowed_paths,acceptance_criteria,evidence_requirements,
                capability_name,action_type,timeout_seconds,classification,correlation_id,causation_id,
                idempotency_key,approved_by,write_policy,status)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,'bound')""",
                (intent_id, authority_id, intent.seed_id, intent.objective_id, intent.stage_id, fingerprint, intent.repository_identity,
                 str(intent.repository_root), intent.expected_base_sha, intent.bounded_instruction, json.dumps(intent.allowed_paths),
                 json.dumps(intent.acceptance_criteria), json.dumps(intent.evidence_requirements), intent.capability_name,
                 intent.action_type, intent.timeout_seconds, intent.classification, intent.correlation_id, intent.causation_id,
                 intent.idempotency_key, intent.approved_by, intent.write_policy))
            cursor.execute("UPDATE objective_stages SET declared_action=%s::jsonb,updated_at=now() WHERE stage_id=%s AND declared_action IS NULL", (json.dumps(action), intent.stage_id))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-GRC-0004: declared action binding was not applied.")
            cursor.execute("UPDATE steward_authority_grants SET status='consumed',consumed_at=now(),updated_at=now() WHERE authority_id=%s AND status='active'", (authority_id,))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-GRC-0010: Steward authority was consumed concurrently.")
            event_id = uuid4()
            cursor.execute("""INSERT INTO river_events(event_id,event_type,aggregate_type,aggregate_id,correlation_id,causation_id,idempotency_key,classification,payload,occurred_at)
                VALUES(%s,'engineering.intent.bound','objective',%s,%s,%s,%s,%s,%s::jsonb,now())""",
                (event_id, intent.objective_id, intent.correlation_id, intent.causation_id,
                 f"engineering.intent.bound:{intent_id}", intent.classification,
                 json.dumps({"intent_id": str(intent_id), "objective_id": str(intent.objective_id), "stage_id": str(intent.stage_id), "action_type": intent.action_type})))
            follow_up = on_bound(cursor, intent_id) if on_bound is not None else None
        return {"intent_id": str(intent_id), "status": "bound", "idempotent": False, "action": action, **(follow_up or {})}

    def bind_from_authority(self, authority_id: UUID) -> dict[str, Any]:
        """Derive only the typed contract stored under a durable grant."""
        from riverview.intake.authority import StewardAuthorityStore

        authority = StewardAuthorityStore().load(authority_id)
        if authority is None:
            raise PermissionError("RIV-GRC-0010: authority grant was not found.")
        intent = StewardAuthorityStore.intent_from_contract(authority)
        return self.bind(intent, authority_id=authority_id)

    def form_and_enqueue(self, authority_id: UUID, *, root_task_id: UUID | None = None, root_correlation_id: UUID | None = None) -> dict[str, Any]:
        """Form one approved intent and queue its one Relay work order atomically."""
        from riverview.intake.authority import StewardAuthorityStore
        from riverview.relay.store import RelayStore

        authority = StewardAuthorityStore().load(authority_id)
        if authority is None:
            raise PermissionError("RIV-GRC-0010: authority grant was not found.")
        if root_correlation_id is not None and UUID(str(authority["correlation_id"])) != root_correlation_id:
            raise ValueError("RIV-LOOP-BIND-0011: root correlation does not match authorized formation.")
        intent = StewardAuthorityStore.intent_from_contract(authority)
        work_key = f"engineering-work-order:authority:{authority_id}"

        def enqueue(cursor: Any, intent_id: UUID) -> dict[str, Any]:
            work = RelayStore.enqueue_in_transaction(
                cursor,
                intent.action_type,
                {"engineering_intent_id": str(intent_id), **({"root_task_id": str(root_task_id)} if root_task_id is not None else {})},
                "grace",
                work_key,
                intent.correlation_id,
                intent.causation_id,
                intent.objective_id,
                intent.stage_id,
            )
            return {"work_order_id": str(work.work_order_id), "work_order_status": work.status}

        result = self.bind(intent, authority_id=authority_id, on_bound=enqueue)
        if result["status"] == "already_bound":
            with connect() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT work_order_id,status FROM work_orders WHERE idempotency_key=%s", (work_key,))
                work = cursor.fetchone()
            if work is None:
                raise RuntimeError("RIV-WRK-0001: formed intent has no idempotent work order.")
            result.update({"work_order_id": str(work[0]), "work_order_status": work[1]})
        result["authority_id"] = str(authority_id)
        result["authority_status"] = "consumed"
        return result

    def load(self, intent_id: UUID) -> dict[str, Any] | None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT intent_id,authority_id,seed_id,objective_id,stage_id,repository_identity,repository_root,expected_base_sha,bounded_instruction,allowed_paths,acceptance_criteria,evidence_requirements,capability_name,action_type,timeout_seconds,classification,correlation_id,causation_id,idempotency_key,approved_by,write_policy,status FROM engineering_intents WHERE intent_id=%s", (intent_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            names = [column.name for column in cursor.description]
            return dict(zip(names, row, strict=True))


def reject_path_overlap(tasks: tuple[EngineeringTask, ...]) -> None:
    """Fail closed before decomposition can assign overlapping mutable paths."""
    for index, task in enumerate(tasks):
        for sibling in tasks[index + 1 :]:
            if set(task.allowed_paths) & set(sibling.allowed_paths):
                raise ValueError("RIV-CAP-0002: task path ownership overlaps; reschedule one lane.")
