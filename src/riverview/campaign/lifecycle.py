"""Durable writer/validator/repair/revalidation lifecycle gates.

RUN-004A deliberately owns persistence and gates only. Automatic role dispatch
and one-GO orchestration remain RUN-004B responsibilities.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, ClassVar
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.relay import AttemptIdentity, ClaimedWork, RelayStore
from riverview.river.events import Classification, RiverEvent


class LifecycleGateError(RuntimeError):
    """A requested lifecycle transition failed closed."""


@dataclass(frozen=True, slots=True)
class DefectInput:
    acceptance_criterion_ref: str
    severity: str
    expected_behavior: str
    observed_behavior: str
    evidence_ref: str
    required_repair: str

    _FIELDS = (
        "acceptance_criterion_ref",
        "severity",
        "expected_behavior",
        "observed_behavior",
        "evidence_ref",
        "required_repair",
    )

    def as_payload(self) -> dict[str, str]:
        """Return the canonical bounded JSON representation used at persistence boundaries."""
        values = {field: getattr(self, field) for field in self._FIELDS}
        if any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise LifecycleGateError("RIV-CAM-0020A: structured defect fields must be non-empty strings.")
        if self.severity not in {"blocking", "non_blocking"}:
            raise LifecycleGateError("RIV-CAM-0020B: structured defect severity is invalid.")
        if any(len(value) > 8_000 for value in values.values()):
            raise LifecycleGateError("RIV-CAM-0020C: structured defect field exceeds its bound.")
        return values

    @classmethod
    def from_payload(cls, payload: Any) -> "DefectInput":
        if not isinstance(payload, dict) or set(payload) != set(cls._FIELDS):
            raise LifecycleGateError("RIV-CAM-0020D: persisted structured defect is malformed.")
        values = {field: payload[field] for field in cls._FIELDS}
        defect = cls(**values)
        defect.as_payload()
        return defect


class CampaignLifecycleStore:
    """Transactional package lifecycle persistence on objective stages."""

    _role_states: ClassVar[dict[str, tuple[str, str]]] = {
        "writer": ("queued", "running"),
        "validator": ("validation_pending", "validation_running"),
        "repair_writer": ("repair_pending", "repair_running"),
        "revalidator": ("revalidation_pending", "revalidation_running"),
    }

    @staticmethod
    def _event(cursor: Any, *, stage_id: UUID, correlation_id: UUID, event_type: str,
               payload: dict[str, Any], idempotency_key: str) -> None:
        event = RiverEvent(
            event_type=event_type,
            aggregate_type="objective_stage",
            aggregate_id=stage_id,
            correlation_id=correlation_id,
            causation_id=stage_id,
            idempotency_key=idempotency_key,
            classification=Classification.RIVER,
            payload=payload,
        )
        cursor.execute(
            """INSERT INTO river_events(
                event_id,event_type,aggregate_type,aggregate_id,correlation_id,
                causation_id,idempotency_key,classification,payload,occurred_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
                ON CONFLICT(idempotency_key) DO NOTHING""",
            (event.event_id, event.event_type, event.aggregate_type, event.aggregate_id,
             event.correlation_id, event.causation_id, event.idempotency_key,
             event.classification.value, json.dumps(dict(event.payload)), event.occurred_at),
        )

    @staticmethod
    def _basis_hash(specification_content: str | None, specification_ref: str | None) -> str:
        value = specification_content if specification_content is not None else specification_ref
        if not value or not value.strip():
            raise ValueError("RIV-CAM-0001: specification content or reference is required.")
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def create_basis(
        self, *, objective_id: UUID, stage_id: UUID, specification_content: str | None,
        specification_ref: str | None, acceptance_criteria: tuple[str, ...],
        evidence_requirements: tuple[str, ...], original_base_sha: str,
        allowed_paths: tuple[str, ...], validation_commands: tuple[str, ...],
        expected_outputs: tuple[str, ...], created_by: str, basis_revision: int = 1,
        supersedes_basis_id: UUID | None = None,
    ) -> UUID:
        basis_id = uuid4()
        basis_hash = self._basis_hash(specification_content, specification_ref)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO campaign_validation_bases(
                    basis_id,objective_id,stage_id,specification_ref,specification_content,
                    specification_hash,acceptance_criteria,evidence_requirements,original_base_sha,
                    allowed_paths,validation_commands,expected_outputs,basis_revision,
                    supersedes_basis_id,created_by)
                   VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s)""",
                (basis_id, objective_id, stage_id, specification_ref, specification_content,
                 basis_hash, json.dumps(acceptance_criteria), json.dumps(evidence_requirements),
                 original_base_sha, json.dumps(allowed_paths), json.dumps(validation_commands),
                 json.dumps(expected_outputs), basis_revision, supersedes_basis_id, created_by),
            )
            cursor.execute(
                """UPDATE objective_stages
                      SET validation_basis_id=%s,runner_state='queued',last_state_transition_at=now(),updated_at=now()
                    WHERE stage_id=%s AND objective_id=%s""",
                (basis_id, stage_id, objective_id),
            )
            if cursor.rowcount != 1:
                raise LifecycleGateError("RIV-CAM-0002: objective stage is missing for validation basis.")
        return basis_id

    def _queue_work(
        self, cursor: Any, *, objective_id: UUID, stage_id: UUID, basis_id: UUID,
        role: str, action_type: str, requested_by: str, idempotency_key: str,
        source_work_order_id: UUID | None = None, source_attempt_id: UUID | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> UUID:
        if role not in {"writer", "validator", "repair_writer", "revalidator"}:
            raise LifecycleGateError("RIV-CAM-0003: unsupported campaign role.")
        cursor.execute(
            """SELECT action_version,expected_duration_seconds,hard_timeout_seconds,enabled
                 FROM approved_actions WHERE action_type=%s""", (action_type,)
        )
        action = cursor.fetchone()
        if not action or not action[3]:
            raise LifecycleGateError("RIV-CAM-0004: lifecycle action is unavailable.")
        work_order_id = uuid4()
        cursor.execute(
            """INSERT INTO work_orders(
                work_order_id,action_type,action_version,status,parameters,requested_by,
                idempotency_key,correlation_id,causation_id,expected_duration_seconds,
                hard_timeout_seconds,objective_id,stage_id,role,validation_basis_id,
                source_work_order_id,source_attempt_id)
               SELECT %s,%s,%s,'queued',%s::jsonb,%s,%s,o.correlation_id,%s,%s,%s,
                      %s,%s,%s,%s,%s,%s
                 FROM objectives o WHERE o.objective_id=%s
               ON CONFLICT(idempotency_key) DO NOTHING""",
            (work_order_id, action_type, action[0], json.dumps(parameters or {}), requested_by,
             idempotency_key, source_work_order_id, action[1], action[2], objective_id, stage_id,
             role, basis_id, source_work_order_id, source_attempt_id, objective_id),
        )
        cursor.execute("SELECT work_order_id FROM work_orders WHERE idempotency_key=%s", (idempotency_key,))
        row = cursor.fetchone()
        if row is None:
            raise LifecycleGateError("RIV-CAM-0005: lifecycle work-order idempotency reconciliation failed.")
        return row[0]

    def queue_writer(
        self, *, objective_id: UUID, stage_id: UUID, basis_id: UUID, action_type: str,
        requested_by: str, idempotency_key: str, parameters: dict[str, Any] | None = None,
    ) -> UUID:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT validation_basis_id,runner_state FROM objective_stages WHERE stage_id=%s AND objective_id=%s FOR UPDATE", (stage_id, objective_id))
            row = cursor.fetchone()
            if row is None or row[0] != basis_id or row[1] not in {"queued", "failed", "timed_out"}:
                raise LifecycleGateError("RIV-CAM-0006: stage is not eligible for writer admission.")
            work_order_id = self._queue_work(
                cursor, objective_id=objective_id, stage_id=stage_id, basis_id=basis_id,
                role="writer", action_type=action_type, requested_by=requested_by,
                idempotency_key=idempotency_key, parameters=parameters,
            )
            self._event(cursor, stage_id=stage_id, correlation_id=self._stage_correlation(cursor, stage_id),
                        event_type="runner.package.writer_queued", payload={"work_order_id": str(work_order_id)},
                        idempotency_key=f"runner.package.writer_queued:{work_order_id}")
            return work_order_id

    @staticmethod
    def _stage_correlation(cursor: Any, stage_id: UUID) -> UUID:
        cursor.execute("SELECT o.correlation_id FROM objective_stages s JOIN objectives o ON o.objective_id=s.objective_id WHERE s.stage_id=%s", (stage_id,))
        row = cursor.fetchone()
        if row is None:
            raise LifecycleGateError("RIV-CAM-0007: stage correlation is missing.")
        return row[0]

    def mark_running(self, work: ClaimedWork) -> None:
        if work.role not in self._role_states:
            raise LifecycleGateError("RIV-CAM-0008: work role is not a lifecycle role.")
        expected, running = self._role_states[work.role]
        identity = self._identity(work)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT w.stage_id,s.runner_state,w.objective_id FROM work_orders w
                   JOIN objective_stages s ON s.stage_id=w.stage_id
                   WHERE w.work_order_id=%s AND w.status='claimed' AND w.role=%s
                     AND active_attempt_id=%s AND lease_generation=%s
                     AND fencing_token=%s AND worker_instance_id=%s FOR UPDATE OF w,s""",
                (identity.work_order_id, work.role, identity.attempt_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise LifecycleGateError("RIV-CAM-0009: claimed lifecycle attempt is stale.")
            cursor.execute("SELECT runner_state FROM objective_stages WHERE stage_id=%s FOR UPDATE", (row[0],))
            stage = cursor.fetchone()
            if stage is None or stage[0] != expected:
                raise LifecycleGateError("RIV-CAM-0010: lifecycle transition to running is illegal.")
            cursor.execute("UPDATE work_orders SET status='running',updated_at=now() WHERE work_order_id=%s AND status='claimed'", (identity.work_order_id,))
            stage_column = {"writer": "writer_attempt_id", "validator": "validator_attempt_id", "repair_writer": "repair_attempt_id", "revalidator": "revalidation_attempt_id"}[work.role]
            cursor.execute(f"UPDATE objective_stages SET runner_state=%s,{stage_column}=%s,last_state_transition_at=now(),updated_at=now() WHERE stage_id=%s", (running, identity.attempt_id, row[0]))
            self._event(cursor, stage_id=row[0], correlation_id=self._stage_correlation(cursor, row[0]),
                        event_type="runner.state_transition", payload={"from": expected, "to": running, "role": work.role, "attempt_id": str(identity.attempt_id)},
                        idempotency_key=f"runner.lifecycle.running:{identity.attempt_id}")

    def record_progress(self, work: ClaimedWork, *, idempotency_key: str,
                        message: str, detail: dict[str, Any] | None = None) -> None:
        """Preserve RUN-003 progress semantics and update the stage projection."""
        identity = self._identity(work)
        inserted = self._relay().progress_fenced(identity, idempotency_key=idempotency_key, message=message, detail=detail)
        if not inserted:
            return
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE objective_stages SET last_progress_at=now(),progress_count=progress_count+1,updated_at=now()
                     WHERE stage_id=(SELECT stage_id FROM work_orders WHERE work_order_id=%s)
                       AND runner_state IN ('claimed','running','validation_running','repair_running','revalidation_running')""",
                (identity.work_order_id,),
            )
            if cursor.rowcount != 1:
                raise LifecycleGateError("RIV-CAM-0029: stage progress projection was not current.")

    @staticmethod
    def _relay() -> RelayStore:
        return RelayStore()

    @staticmethod
    def _identity(work: ClaimedWork) -> AttemptIdentity:
        if None in (work.attempt_id, work.lease_generation, work.fencing_token, work.worker_instance_id):
            raise LifecycleGateError("RIV-CAM-0011: lifecycle work is missing exact fence identity.")
        return AttemptIdentity(work.work_order_id, work.attempt_id, work.lease_generation, work.fencing_token, work.worker_instance_id)

    @staticmethod
    def _result_binding(report: Any) -> tuple[str, str, tuple[str, ...]]:
        """Extract the canonical, durable implementation-result identity."""
        if not isinstance(report, dict):
            raise LifecycleGateError("RIV-CAM-0031: completed result report is malformed.")
        version = report.get("result_version_hash")
        implementation = report.get("implementation_ref")
        evidence = report.get("evidence_refs")
        if not isinstance(version, str) or not version.strip():
            raise LifecycleGateError("RIV-CAM-0032: result version is absent from the completed result.")
        if not isinstance(implementation, str) or not implementation.strip():
            raise LifecycleGateError("RIV-CAM-0033: implementation/tree reference is absent from the completed result.")
        if implementation.startswith("commit:"):
            digest = implementation[7:]
            valid_ref = bool(re.fullmatch(r"[0-9a-fA-F]{40}", digest))
        elif implementation.startswith("tree:"):
            digest = implementation[5:]
            valid_ref = bool(re.fullmatch(r"[0-9a-fA-F]{40,64}", digest))
        else:
            digest = ""
            valid_ref = False
        if not valid_ref or version != digest:
            raise LifecycleGateError("RIV-CAM-0034: result version is not bound to an actual tree/commit reference.")
        if not isinstance(evidence, (list, tuple)) or not evidence:
            raise LifecycleGateError("RIV-CAM-0035: durable validation evidence is required.")
        refs = tuple(evidence)
        if any(not isinstance(ref, str) or not ref.strip() or len(ref) > 512 for ref in refs):
            raise LifecycleGateError("RIV-CAM-0036: durable validation evidence is malformed.")
        if any(":" not in ref for ref in refs):
            raise LifecycleGateError("RIV-CAM-0037: validation evidence must be a durable reference.")
        return version, implementation, refs

    @classmethod
    def _assert_result_binding(
        cls, cursor: Any, *, source_work_order_id: UUID | None, source_attempt_id: UUID | None,
        basis_id: UUID, result_version_hash: str, implementation_ref: str | None,
        evidence_refs: tuple[str, ...],
    ) -> None:
        if source_work_order_id is None or source_attempt_id is None:
            raise LifecycleGateError("RIV-CAM-0038: validation source result is missing.")
        cursor.execute(
            """SELECT w.status,w.result_report,w.validation_basis_id,a.terminal_state,a.work_order_id
                 FROM work_orders w JOIN work_order_attempts a ON a.work_order_id=w.work_order_id
                WHERE w.work_order_id=%s AND a.attempt_id=%s FOR UPDATE""",
            (source_work_order_id, source_attempt_id),
        )
        source = cursor.fetchone()
        if source is None or source[0] != "succeeded" or source[3] != "succeeded" or source[2] != basis_id:
            raise LifecycleGateError("RIV-CAM-0039: source result is not an authoritative completed attempt.")
        stored_version, stored_ref, stored_evidence = cls._result_binding(source[1])
        if (stored_version, stored_ref, stored_evidence) != (result_version_hash, implementation_ref, tuple(evidence_refs)):
            raise LifecycleGateError("RIV-CAM-0040: validation evidence does not correspond to the exact source result.")

    def handoff_writer_to_validation(self, work: ClaimedWork, *, validator_action_type: str,
                                     requested_by: str, parameters: dict[str, Any] | None = None) -> UUID:
        identity = self._identity(work)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT objective_id,stage_id,validation_basis_id,status,result_report
                     FROM work_orders WHERE work_order_id=%s FOR UPDATE""", (identity.work_order_id,)
            )
            order = cursor.fetchone()
            cursor.execute("SELECT role FROM work_order_attempts WHERE attempt_id=%s AND work_order_id=%s", (identity.attempt_id, identity.work_order_id))
            attempt_role = cursor.fetchone()
            if order is None or order[3] != "succeeded" or attempt_role is None or attempt_role[0] != "writer" or not order[4]:
                raise LifecycleGateError("RIV-CAM-0012: writer evidence is not technically complete.")
            cursor.execute(
                """SELECT terminal_state,worker_instance_id FROM work_order_attempts
                   WHERE attempt_id=%s AND work_order_id=%s AND lease_generation=%s
                     AND fencing_token=%s AND worker_instance_id=%s FOR UPDATE""",
                (identity.attempt_id, identity.work_order_id, identity.lease_generation,
                 identity.fencing_token, identity.worker_instance_id),
            )
            attempt = cursor.fetchone()
            if attempt is None or attempt[0] != "succeeded":
                raise LifecycleGateError("RIV-CAM-0013: writer attempt is not a valid completed source.")
            cursor.execute("SELECT runner_state,validation_basis_id FROM objective_stages WHERE stage_id=%s AND objective_id=%s FOR UPDATE", (order[1], order[0]))
            stage = cursor.fetchone()
            if stage is None or stage[0] not in {"running", "claimed"} or stage[1] != order[2]:
                raise LifecycleGateError("RIV-CAM-0014: writer handoff is not a legal lifecycle transition.")
            self._result_binding(order[4])
            validator_id = self._queue_work(
                cursor, objective_id=order[0], stage_id=order[1], basis_id=order[2],
                role="validator", action_type=validator_action_type, requested_by=requested_by,
                idempotency_key=f"runner.validator:{identity.attempt_id}",
                source_work_order_id=identity.work_order_id, source_attempt_id=identity.attempt_id,
                parameters=parameters,
            )
            cursor.execute("UPDATE objective_stages SET runner_state='validation_pending',last_state_transition_at=now(),updated_at=now() WHERE stage_id=%s", (order[1],))
            self._event(cursor, stage_id=order[1], correlation_id=self._stage_correlation(cursor, order[1]),
                        event_type="runner.state_transition", payload={"from": stage[0], "to": "validation_pending", "writer_attempt_id": str(identity.attempt_id), "validator_work_order_id": str(validator_id)},
                idempotency_key=f"runner.validation.pending:{identity.attempt_id}")
            return validator_id

    def record_validation(
        self, work: ClaimedWork, *, verdict: str, basis_hash: str, result_version_hash: str,
        evidence_refs: tuple[str, ...], findings_summary: tuple[str, ...], defects: tuple[DefectInput, ...] = (),
        implementation_ref: str | None = None, repair_action_type: str = "relay.noop",
        revalidation_action_type: str = "relay.noop", requested_by: str = "campaign-runner",
    ) -> UUID:
        identity = self._identity(work)
        if verdict not in {"PASS", "FAIL", "BLOCKED"} or not result_version_hash:
            raise LifecycleGateError("RIV-CAM-0015: validation verdict or result version is invalid.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT objective_id,stage_id,validation_basis_id,source_work_order_id,source_attempt_id,status FROM work_orders WHERE work_order_id=%s FOR UPDATE", (identity.work_order_id,))
            order = cursor.fetchone()
            cursor.execute("SELECT role FROM work_order_attempts WHERE attempt_id=%s AND work_order_id=%s", (identity.attempt_id, identity.work_order_id))
            attempt_role = cursor.fetchone()
            role = attempt_role[0] if attempt_role else None
            if order is None or order[5] != "succeeded" or role not in {"validator", "revalidator"}:
                raise LifecycleGateError("RIV-CAM-0016: validation attempt is not a completed lifecycle attempt.")
            cursor.execute("SELECT terminal_state,worker_instance_id FROM work_order_attempts WHERE attempt_id=%s AND work_order_id=%s AND lease_generation=%s AND fencing_token=%s AND worker_instance_id=%s", (identity.attempt_id, identity.work_order_id, identity.lease_generation, identity.fencing_token, identity.worker_instance_id))
            attempt = cursor.fetchone()
            cursor.execute("SELECT runner_state,validation_basis_id,writer_attempt_id,repair_attempt_id FROM objective_stages WHERE stage_id=%s AND objective_id=%s FOR UPDATE", (order[1], order[0]))
            stage = cursor.fetchone()
            if attempt is None or attempt[0] != "succeeded" or stage is None or stage[1] != order[2]:
                raise LifecycleGateError("RIV-CAM-0017: validation evidence is stale or basis-mismatched.")
            expected_state = "validation_running" if role == "validator" else "revalidation_running"
            if stage[0] != expected_state or order[4] is None:
                raise LifecycleGateError("RIV-CAM-0018: validation transition is not current.")
            cursor.execute("SELECT specification_hash FROM campaign_validation_bases WHERE basis_id=%s", (order[2],))
            basis = cursor.fetchone()
            if basis is None or basis[0] != basis_hash:
                raise LifecycleGateError("RIV-CAM-0019: validation basis hash does not match the immutable basis.")
            writer_attempt_id = stage[2]
            repair_attempt_id = stage[3] if role == "revalidator" else None
            source_attempt_id = repair_attempt_id if role == "revalidator" else writer_attempt_id
            if order[4] != source_attempt_id:
                raise LifecycleGateError("RIV-CAM-0041: validation source attempt is not the authoritative result.")
            self._assert_result_binding(
                cursor, source_work_order_id=order[3], source_attempt_id=source_attempt_id,
                basis_id=order[2], result_version_hash=result_version_hash,
                implementation_ref=implementation_ref, evidence_refs=evidence_refs,
            )
            cursor.execute("SELECT worker_instance_id FROM work_order_attempts WHERE attempt_id=%s", (writer_attempt_id,))
            writer_instance = cursor.fetchone()
            if writer_instance is None or writer_instance[0] == attempt[1]:
                raise LifecycleGateError("RIV-CAM-0020: validator is not independent from the writer.")
            result_id = uuid4()
            cursor.execute(
                """INSERT INTO campaign_validation_results(
                    validation_result_id,work_order_id,validation_attempt_id,writer_attempt_id,
                    repair_attempt_id,basis_id,basis_hash,verdict,result_version_hash,
                    implementation_ref,evidence_refs,findings_summary,idempotency_key)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)""",
                (result_id, identity.work_order_id, identity.attempt_id, writer_attempt_id,
                 repair_attempt_id, order[2], basis_hash, verdict, result_version_hash,
                 implementation_ref, json.dumps(evidence_refs), json.dumps(findings_summary),
                 f"runner.validation.result:{identity.attempt_id}"),
            )
            for defect in defects:
                if defect.severity not in {"blocking", "non_blocking"}:
                    raise LifecycleGateError("RIV-CAM-0021: defect severity is invalid.")
                cursor.execute(
                    """INSERT INTO campaign_validation_defects(
                        defect_id,objective_id,stage_id,validation_result_id,validation_attempt_id,
                        writer_attempt_id,acceptance_criterion_ref,severity,expected_behavior,
                        observed_behavior,evidence_ref,required_repair)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (uuid4(), order[0], order[1], result_id, identity.attempt_id, writer_attempt_id,
                     defect.acceptance_criterion_ref, defect.severity, defect.expected_behavior,
                     defect.observed_behavior, defect.evidence_ref, defect.required_repair),
                )
            if verdict == "PASS":
                if defects:
                    raise LifecycleGateError("RIV-CAM-0022: PASS cannot carry defects.")
                if role == "revalidator":
                    cursor.execute("""UPDATE campaign_validation_defects SET state='resolved',resolution_attempt_id=%s,resolved_at=now() WHERE stage_id=%s AND state='unresolved' AND repair_attempt_id=%s""", (identity.attempt_id, order[1], repair_attempt_id))
                self._accept_locked(cursor, stage_id=order[1], validation_result_id=result_id, validation_attempt_id=identity.attempt_id, expected_state=expected_state)
            elif verdict == "FAIL":
                if not defects:
                    raise LifecycleGateError("RIV-CAM-0023: FAIL requires structured defects.")
                cursor.execute("UPDATE objective_stages SET runner_state='defects_found',last_state_transition_at=now(),updated_at=now() WHERE stage_id=%s", (order[1],))
                repair_id = self._queue_work(cursor, objective_id=order[0], stage_id=order[1], basis_id=order[2], role="repair_writer", action_type=repair_action_type, requested_by=requested_by, idempotency_key=f"runner.repair:{identity.attempt_id}", source_work_order_id=identity.work_order_id, source_attempt_id=identity.attempt_id)
                cursor.execute("UPDATE objective_stages SET runner_state='repair_pending',last_state_transition_at=now(),updated_at=now() WHERE stage_id=%s", (order[1],))
                self._event(cursor, stage_id=order[1], correlation_id=self._stage_correlation(cursor, order[1]), event_type="runner.validation.defects", payload={"validation_result_id": str(result_id), "repair_work_order_id": str(repair_id)}, idempotency_key=f"runner.validation.defects:{result_id}")
            else:
                cursor.execute("UPDATE objective_stages SET runner_state='blocked',blocked_reason='validation evidence unavailable or denied',last_state_transition_at=now(),updated_at=now() WHERE stage_id=%s", (order[1],))
                cursor.execute("UPDATE objectives SET attention_required=true,acceptance_state='rejected',updated_at=now() WHERE objective_id=%s", (order[0],))
            return result_id

    def acceptance_gate(self, *, stage_id: UUID, validation_result_id: UUID,
                        validation_attempt_id: UUID) -> None:
        """Re-evaluate the persisted acceptance invariant under row locks."""
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT runner_state FROM objective_stages WHERE stage_id=%s FOR UPDATE", (stage_id,))
            state = cursor.fetchone()
            if state is None:
                raise LifecycleGateError("RIV-CAM-0030: acceptance stage is missing.")
            self._accept_locked(
                cursor, stage_id=stage_id, validation_result_id=validation_result_id,
                validation_attempt_id=validation_attempt_id, expected_state=state[0],
            )

    def _accept_locked(self, cursor: Any, *, stage_id: UUID, validation_result_id: UUID,
                       validation_attempt_id: UUID, expected_state: str) -> None:
        cursor.execute("SELECT objective_id,runner_state,writer_attempt_id,repair_attempt_id,validation_basis_id FROM objective_stages WHERE stage_id=%s FOR UPDATE", (stage_id,))
        stage = cursor.fetchone()
        if stage is None or stage[1] != expected_state or expected_state not in {"validation_running", "revalidation_running"}:
            raise LifecycleGateError("RIV-CAM-0024: acceptance gate state is invalid.")
        cursor.execute("SELECT verdict,basis_id,writer_attempt_id,repair_attempt_id,result_version_hash,implementation_ref,evidence_refs FROM campaign_validation_results WHERE validation_result_id=%s AND validation_attempt_id=%s FOR UPDATE", (validation_result_id, validation_attempt_id))
        result = cursor.fetchone()
        if result is None or result[0] != "PASS" or result[1] != stage[4] or result[2] != stage[2]:
            raise LifecycleGateError("RIV-CAM-0025: acceptance gate lacks exact independent PASS evidence.")
        expected_source_attempt = stage[3] if expected_state == "revalidation_running" else stage[2]
        expected_repair_attempt = stage[3] if expected_state == "revalidation_running" else None
        if result[3] != expected_repair_attempt:
            raise LifecycleGateError("RIV-CAM-0042: acceptance result is not bound to the current repair attempt.")
        cursor.execute("SELECT work_order_id FROM work_order_attempts WHERE attempt_id=%s", (expected_source_attempt,))
        source_order = cursor.fetchone()
        if source_order is None:
            raise LifecycleGateError("RIV-CAM-0043: acceptance source attempt is missing.")
        self._assert_result_binding(
            cursor, source_work_order_id=source_order[0], source_attempt_id=expected_source_attempt,
            basis_id=stage[4], result_version_hash=result[4], implementation_ref=result[5],
            evidence_refs=tuple(result[6] or ()),
        )
        cursor.execute("SELECT 1 FROM campaign_validation_defects WHERE stage_id=%s AND severity='blocking' AND state='unresolved'", (stage_id,))
        if cursor.fetchone() is not None:
            raise LifecycleGateError("RIV-CAM-0026: unresolved blocking defect prevents acceptance.")
        cursor.execute("UPDATE objective_stages SET runner_state='accepted',status='completed',readiness='satisfied',completed_at=now(),last_state_transition_at=now(),updated_at=now() WHERE stage_id=%s", (stage_id,))
        cursor.execute("SELECT objective_id FROM objective_stages WHERE stage_id=%s", (stage_id,))
        objective_id = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM objective_stages WHERE objective_id=%s AND status NOT IN ('completed','cancelled')", (objective_id,))
        remaining = cursor.fetchone()[0]
        if remaining == 0:
            cursor.execute("UPDATE objectives SET acceptance_state='accepted',status='completed',completed_at=now(),updated_at=now() WHERE objective_id=%s", (objective_id,))
        else:
            cursor.execute("UPDATE objectives SET acceptance_state='awaiting_validation',updated_at=now() WHERE objective_id=%s", (objective_id,))
        self._event(cursor, stage_id=stage_id, correlation_id=self._stage_correlation(cursor, stage_id), event_type="runner.validation.pass", payload={"validation_result_id": str(validation_result_id), "validation_attempt_id": str(validation_attempt_id)}, idempotency_key=f"runner.validation.pass:{validation_result_id}")

    def record_repair_completion(self, work: ClaimedWork, *, revalidation_action_type: str = "relay.noop", requested_by: str = "campaign-runner") -> UUID:
        identity = self._identity(work)
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT objective_id,stage_id,validation_basis_id,source_attempt_id,status FROM work_orders WHERE work_order_id=%s FOR UPDATE", (identity.work_order_id,))
            order = cursor.fetchone()
            cursor.execute("SELECT role FROM work_order_attempts WHERE attempt_id=%s AND work_order_id=%s", (identity.attempt_id, identity.work_order_id))
            attempt_role = cursor.fetchone()
            if order is None or order[4] != "succeeded" or attempt_role is None or attempt_role[0] != "repair_writer":
                raise LifecycleGateError("RIV-CAM-0027: repair attempt is not complete.")
            cursor.execute("SELECT runner_state,validation_basis_id,writer_attempt_id FROM objective_stages WHERE stage_id=%s AND objective_id=%s FOR UPDATE", (order[1], order[0]))
            stage = cursor.fetchone()
            cursor.execute("SELECT terminal_state FROM work_order_attempts WHERE attempt_id=%s AND work_order_id=%s AND lease_generation=%s AND fencing_token=%s AND worker_instance_id=%s", (identity.attempt_id, identity.work_order_id, identity.lease_generation, identity.fencing_token, identity.worker_instance_id))
            attempt = cursor.fetchone()
            if stage is None or stage[0] != "repair_running" or stage[1] != order[2] or attempt is None or attempt[0] != "succeeded":
                raise LifecycleGateError("RIV-CAM-0028: repair transition is stale or illegal.")
            cursor.execute("SELECT result_report FROM work_orders WHERE work_order_id=%s", (identity.work_order_id,))
            repair_report = cursor.fetchone()
            repair_version, repair_ref, repair_evidence = self._result_binding(repair_report[0] if repair_report else None)
            self._assert_result_binding(
                cursor, source_work_order_id=identity.work_order_id, source_attempt_id=identity.attempt_id,
                basis_id=order[2], result_version_hash=repair_version, implementation_ref=repair_ref,
                evidence_refs=repair_evidence,
            )
            cursor.execute("UPDATE campaign_validation_defects SET repair_attempt_id=%s WHERE stage_id=%s AND state='unresolved'", (identity.attempt_id, order[1]))
            revalidation_id = self._queue_work(cursor, objective_id=order[0], stage_id=order[1], basis_id=order[2], role="revalidator", action_type=revalidation_action_type, requested_by=requested_by, idempotency_key=f"runner.revalidation:{identity.attempt_id}", source_work_order_id=identity.work_order_id, source_attempt_id=identity.attempt_id)
            cursor.execute("UPDATE objective_stages SET runner_state='revalidation_pending',last_state_transition_at=now(),updated_at=now() WHERE stage_id=%s", (order[1],))
            self._event(cursor, stage_id=order[1], correlation_id=self._stage_correlation(cursor, order[1]), event_type="runner.state_transition", payload={"from": "repair_running", "to": "revalidation_pending", "repair_attempt_id": str(identity.attempt_id), "revalidation_work_order_id": str(revalidation_id)}, idempotency_key=f"runner.revalidation.pending:{identity.attempt_id}")
            return revalidation_id

    def retry_failed_repair(
        self, *, failed_repair_work_order_id: UUID, requested_by: str,
        action_type: str = "relay.noop", reason: str = "recoverable repair execution failure",
        idempotency_key: str | None = None,
    ) -> UUID:
        """Queue one bounded replacement repair attempt without replaying upstream work."""

        if not isinstance(failed_repair_work_order_id, UUID) or not requested_by.strip() or not reason.strip():
            raise LifecycleGateError("RIV-CAM-0044: repair retry request is incomplete.")
        retry_key = idempotency_key or f"runner.repair.retry:{failed_repair_work_order_id}:1"
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT objective_id,stage_id,validation_basis_id,source_work_order_id,
                              source_attempt_id,status,error_checkpoint,result_report
                     FROM work_orders WHERE work_order_id=%s FOR UPDATE""",
                (failed_repair_work_order_id,),
            )
            failed = cursor.fetchone()
            if failed is None:
                raise LifecycleGateError("RIV-CAM-0045: failed repair work order is missing.")
            objective_id, stage_id, basis_id, validator_order_id, validator_attempt_id, status, checkpoint, report = failed
            if status != "failed" or checkpoint != "RIV-REC-0004":
                raise LifecycleGateError("RIV-CAM-0046: repair failure is not an explicitly recoverable reconciliation failure.")
            if not isinstance(report, dict) or report.get("status") != "failed":
                raise LifecycleGateError("RIV-CAM-0047: failed repair result is not durably recorded.")
            failed_attempt_id = self._failed_attempt_id(cursor, failed_repair_work_order_id)
            cursor.execute(
                "SELECT role FROM work_order_attempts WHERE attempt_id=%s AND work_order_id=%s",
                (failed_attempt_id, failed_repair_work_order_id),
            )
            failed_attempt_role = cursor.fetchone()
            if failed_attempt_role is None or failed_attempt_role[0] != "repair_writer":
                raise LifecycleGateError("RIV-CAM-0056: failed work order is not a repair-writer attempt.")

            cursor.execute(
                """SELECT work_order_id FROM work_orders
                    WHERE stage_id=%s
                      AND parameters->>'retry_of_work_order_id'=%s
                    ORDER BY created_at
                    LIMIT 1""",
                (stage_id, str(failed_repair_work_order_id)),
            )
            existing = cursor.fetchone()
            if existing is not None:
                return existing[0]

            cursor.execute(
                """SELECT runner_state,validation_basis_id,writer_attempt_id,repair_attempt_id
                     FROM objective_stages WHERE stage_id=%s AND objective_id=%s FOR UPDATE""",
                (stage_id, objective_id),
            )
            stage = cursor.fetchone()
            if stage is None or stage[0] != "failed" or stage[1] != basis_id or stage[3] != failed_attempt_id:
                raise LifecycleGateError("RIV-CAM-0048: stage is not eligible for failed-repair recovery.")

            cursor.execute(
                """SELECT w.status,w.validation_basis_id,a.terminal_state,a.role
                     FROM work_orders w
                     JOIN work_order_attempts a ON a.work_order_id=w.work_order_id
                    WHERE w.work_order_id=%s AND a.attempt_id=%s AND a.role='validator'""",
                (validator_order_id, validator_attempt_id),
            )
            validator_order = cursor.fetchone()
            if validator_order is None or validator_order[0] != "succeeded" or validator_order[1] != basis_id or validator_order[2] != "succeeded":
                raise LifecycleGateError("RIV-CAM-0049: repair retry validator lineage is invalid.")
            cursor.execute(
                """SELECT validation_result_id,verdict,writer_attempt_id
                     FROM campaign_validation_results
                    WHERE validation_attempt_id=%s AND basis_id=%s
                    ORDER BY created_at DESC LIMIT 1""",
                (validator_attempt_id, basis_id),
            )
            validation = cursor.fetchone()
            if validation is None or validation[1] != "FAIL" or validation[2] != stage[2]:
                raise LifecycleGateError("RIV-CAM-0050: original validator FAIL is not authoritative.")

            cursor.execute(
                """SELECT defect_id,acceptance_criterion_ref,severity,expected_behavior,
                              observed_behavior,evidence_ref,required_repair
                     FROM campaign_validation_defects
                    WHERE stage_id=%s AND validation_result_id=%s AND state='unresolved'
                    ORDER BY created_at,defect_id""",
                (stage_id, validation[0]),
            )
            defects = cursor.fetchall()
            if not defects:
                raise LifecycleGateError("RIV-CAM-0051: unresolved structured defects are required for repair recovery.")

            cursor.execute(
                """SELECT w.status,w.result_report,a.terminal_state
                     FROM work_orders w JOIN work_order_attempts a ON a.attempt_id=%s
                    WHERE a.role='writer' AND a.work_order_id=w.work_order_id""",
                (stage[2],),
            )
            writer = cursor.fetchone()
            if writer is None or writer[0] != "succeeded" or writer[2] != "succeeded":
                raise LifecycleGateError("RIV-CAM-0052: accepted writer implementation basis is unavailable.")
            self._result_binding(writer[1])

            cursor.execute(
                """SELECT 1 FROM work_orders
                    WHERE stage_id=%s AND role='repair_writer'
                      AND status IN ('queued','claimed','running')""",
                (stage_id,),
            )
            if cursor.fetchone() is not None:
                raise LifecycleGateError("RIV-CAM-0053: an active repair attempt already owns this stage.")

            defect_payload = [
                DefectInput(row[1], row[2], row[3], row[4], row[5], row[6]).as_payload()
                for row in defects
            ]
            parameters = {
                "retry_of_work_order_id": str(failed_repair_work_order_id),
                "retry_of_attempt_id": str(failed_attempt_id),
                "retry_generation": 1,
                "source_validation_result_id": str(validation[0]),
                "source_validator_work_order_id": str(validator_order_id),
                "source_validator_attempt_id": str(validator_attempt_id),
                "defects": defect_payload,
                "retry_reason": reason[:1000],
            }
            replacement_id = self._queue_work(
                cursor, objective_id=objective_id, stage_id=stage_id, basis_id=basis_id,
                role="repair_writer", action_type=action_type, requested_by=requested_by,
                idempotency_key=retry_key, source_work_order_id=validator_order_id,
                source_attempt_id=validator_attempt_id, parameters=parameters,
            )
            cursor.execute(
                """UPDATE objective_stages
                      SET runner_state='repair_pending',blocked_reason=NULL,
                          repair_attempt_id=NULL,last_state_transition_at=now(),updated_at=now()
                    WHERE stage_id=%s AND runner_state='failed'""",
                (stage_id,),
            )
            if cursor.rowcount != 1:
                raise LifecycleGateError("RIV-CAM-0054: failed-repair recovery transition was not applied.")
            self._event(
                cursor, stage_id=stage_id, correlation_id=self._stage_correlation(cursor, stage_id),
                event_type="runner.repair.retry_queued",
                payload={
                    "from": "failed", "to": "repair_pending",
                    "failed_repair_work_order_id": str(failed_repair_work_order_id),
                    "failed_repair_attempt_id": parameters["retry_of_attempt_id"],
                    "replacement_repair_work_order_id": str(replacement_id),
                    "retry_generation": 1,
                    "validation_result_id": str(validation[0]),
                    "validator_work_order_id": str(validator_order_id),
                    "validator_attempt_id": str(validator_attempt_id),
                    "defect_ids": [str(row[0]) for row in defects],
                },
                idempotency_key=retry_key,
            )
            return replacement_id

    @staticmethod
    def _failed_attempt_id(cursor: Any, work_order_id: UUID) -> UUID:
        cursor.execute(
            """SELECT attempt_id FROM work_order_attempts
                WHERE work_order_id=%s AND terminal_state='failed'
                ORDER BY finished_at DESC LIMIT 1""",
            (work_order_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise LifecycleGateError("RIV-CAM-0055: failed repair attempt history is missing.")
        return row[0]
