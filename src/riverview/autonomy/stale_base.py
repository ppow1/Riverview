"""Bounded stale-base assessment and retry lineage for approved work."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.river.events import Classification, RiverEvent
from riverview.river.store import EventStore

_SHA = re.compile(r"^[0-9a-f]{40}$")
_MATERIAL_PREFIXES = (
    "src/riverview/autonomy/stale_base.py",
    "src/riverview/runner.py",
    "src/riverview/autonomy/control.py",
    "src/riverview/relay/",
    "src/riverview/intake/engineering.py",
    "src/riverview/intake/policy.py",
    "database/",
    "pyproject.toml",
    "uv.lock",
    "requirements",
)
_REVIEW_PREFIXES = (
    "src/riverview/intake/authority.py",
    "src/riverview/mcp/",
    "config/",
)

# Recovery is an explicit allow-list.  A failed execution is not itself proof
# that retrying is safe, and a checkpoint must never be inferred from a
# provider narrative.
RECOVERABLE_FAILURE_CHECKPOINTS = frozenset({
    "RIV-EXE-0003",  # bounded execution timeout
    "RIV-EXE-0008",  # stale approved base
    "RIV-EXE-0010",  # authoritative execution/reconciliation defect
})
RECOVERABLE_FAILURE_PREFIXES = ("RIV-REC-",)


def is_recoverable_failure(checkpoint: str, failure_evidence: object | None = None) -> bool:
    """Return whether a durable failure checkpoint is explicitly retryable."""

    if checkpoint in RECOVERABLE_FAILURE_CHECKPOINTS or any(checkpoint.startswith(prefix) for prefix in RECOVERABLE_FAILURE_PREFIXES):
        return True
    evidence = failure_evidence if isinstance(failure_evidence, dict) else {}
    reason = str(evidence.get("reason", ""))
    # These two historical records are retryable only with their exact,
    # already-audited defect evidence.  The broad checkpoints remain closed.
    return (checkpoint == "RIV-DB-0004" and "execution_results_bounded_summary_check" in reason) or (
        checkpoint == "RIV-RUN-0001" and "expected string or bytes-like object" in reason
    ) or (
        checkpoint == "RIV-WRK-0004" and evidence.get("status") == "timed_out"
    ) or (
        checkpoint == "RIV-EXE-0007" and "changed path escaped envelope" in reason
    )


def immutable_contract_matches(authority_scope: dict[str, Any], intent_contract: dict[str, Any], permitted_capabilities: list[str], capability_name: str) -> bool:
    """Verify that recovery cannot silently change the authorized job."""

    contract = authority_scope.get("contract", {}) if isinstance(authority_scope, dict) else {}
    if not isinstance(contract, dict):
        return False
    required = (
        "repository_identity", "repository_root", "expected_base_sha", "bounded_instruction",
        "allowed_paths", "acceptance_criteria", "evidence_requirements", "capability_name",
        "action_type", "write_policy",
    )
    if any(contract.get(key) != intent_contract.get(key) for key in required):
        return False
    return permitted_capabilities == [capability_name]


def _under(path: str, roots: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return any(normalized == root or normalized.startswith(f"{root.rstrip('/')}/") for root in roots)


@dataclass(frozen=True, slots=True)
class DriftAssessment:
    approved_base_sha: str
    proposed_base_sha: str
    changed_paths: tuple[str, ...]
    material_paths: tuple[str, ...]
    review_paths: tuple[str, ...]
    repository_is_descendant: bool
    decision: str
    reason: str
    infrastructure_repair_evidence: dict[str, Any] | None = None

    @property
    def safe_to_revalidate(self) -> bool:
        return self.decision in {"safe_revalidation", "narrow_steward_confirmation"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "approved_base_sha": self.approved_base_sha,
            "proposed_base_sha": self.proposed_base_sha,
            "changed_paths": list(self.changed_paths),
            "material_paths": list(self.material_paths),
            "review_paths": list(self.review_paths),
            "repository_is_descendant": self.repository_is_descendant,
            "decision": self.decision,
            "reason": self.reason,
            "infrastructure_repair_evidence": self.infrastructure_repair_evidence or {},
        }


class RepositoryDriftAnalyzer:
    """Compare Git history without treating every SHA change as material."""

    def assess(
        self,
        repository: Path,
        approved_base_sha: str,
        allowed_paths: tuple[str, ...],
        dependency_paths: tuple[str, ...] = (),
        proposed_base_sha: str | None = None,
        infrastructure_repair_evidence: dict[str, Any] | None = None,
    ) -> DriftAssessment:
        if not _SHA.fullmatch(approved_base_sha):
            raise ValueError("RIV-EXE-0008: approved base SHA is invalid.")
        proposed = proposed_base_sha or self._git(repository, "rev-parse", "HEAD")
        if not _SHA.fullmatch(proposed):
            raise ValueError("RIV-EXE-0008: proposed base SHA is invalid.")
        descendant = self._is_ancestor(repository, approved_base_sha, proposed)
        if not descendant:
            return DriftAssessment(approved_base_sha, proposed, (), (), (), False, "invalid_repository", "current HEAD is not a descendant of the approved base.")
        changed = tuple(self._git(repository, "diff", "--name-only", f"{approved_base_sha}..{proposed}").splitlines())
        material = tuple(path for path in changed if _under(path, allowed_paths + dependency_paths) or _under(path, _MATERIAL_PREFIXES))
        review = tuple(path for path in changed if path not in material and _under(path, _REVIEW_PREFIXES))
        infra = tuple(path for path in material if _under(path, _MATERIAL_PREFIXES))
        approved_material = tuple(path for path in material if _under(path, allowed_paths))
        if material and set(material) == set(infra).union(approved_material) and infrastructure_repair_evidence:
            required = {
                "repository_identity_unchanged",
                "allowed_paths_unchanged",
                "capability_unchanged",
                "action_unchanged",
                "write_policy_unchanged",
                "instruction_unchanged",
                "reconciliation_not_weakened",
                "authority_not_weakened",
                "target_requirements_unchanged",
                "descendant_of_approved_base",
                "tests_passed",
            }
            missing = sorted(key for key in required if infrastructure_repair_evidence.get(key) is not True)
            if not missing:
                decision = "infrastructure_repair_revalidation"
                reason = "execution/reconciliation infrastructure and the approved bounded feature paths changed; repair evidence proves the authorized contract is unchanged."
            else:
                decision = "material_drift"
                reason = f"infrastructure repair evidence is incomplete: {', '.join(missing)}."
        elif material:
            decision, reason = "material_drift", "the repository diff touches the approved scope or execution dependencies."
        elif review:
            decision, reason = "narrow_steward_confirmation", "scope is unchanged, but governance/ingress changes require Pat's narrow confirmation of the new base."
        else:
            decision, reason = "safe_revalidation", "the repository diff is outside the approved scope and execution dependencies."
        return DriftAssessment(approved_base_sha, proposed, changed, material, review, True, decision, reason, infrastructure_repair_evidence)

    @staticmethod
    def _git(repository: Path, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=repository, text=True, stderr=subprocess.STDOUT).strip()

    @staticmethod
    def _is_ancestor(repository: Path, base: str, head: str) -> bool:
        return subprocess.run(["git", "merge-base", "--is-ancestor", base, head], cwd=repository, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


class StaleBaseRecoveryStore:
    """Prepare and approve a successor attempt without mutating history."""

    def prepare(
        self,
        failed_work_order_id: UUID,
        *,
        repository: Path | None = None,
        idempotency_key: str,
        infrastructure_repair_evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT w.status,w.error_checkpoint,w.parameters,w.action_type,w.action_version,
                          w.requested_by,w.correlation_id,w.expected_duration_seconds,w.hard_timeout_seconds,
                          i.intent_id,i.authority_id,i.objective_id,i.repository_root,i.expected_base_sha,
                          i.allowed_paths,i.acceptance_criteria,i.evidence_requirements,i.bounded_instruction,
                          i.capability_name,i.action_type,i.write_policy,i.repository_identity,
                          a.status,a.scope,a.permitted_capabilities,o.status,w.result_report
                   FROM work_orders w JOIN engineering_intents i ON (w.parameters->>'engineering_intent_id')=i.intent_id::text
                   JOIN steward_authority_grants a ON a.authority_id=i.authority_id
                   JOIN objectives o ON o.objective_id=i.objective_id
                   WHERE w.work_order_id=%s FOR UPDATE""",
                (failed_work_order_id,),
            )
            row = cursor.fetchone()
            failure_evidence = row[26] if row is not None and isinstance(row[26], dict) else {"status": row[0]} if row is not None else {}
            if row is None or row[0] not in {"failed", "timed_out"} or not is_recoverable_failure(row[1], failure_evidence):
                raise RuntimeError("RIV-GRC-0007: failure checkpoint is not explicitly recoverable.")
            if row[25] in {"completed", "cancelled"}:
                raise RuntimeError("RIV-GRC-0007: completed objective cannot create a successor.")
            if row[22] not in {"active", "consumed"}:
                raise RuntimeError("RIV-GRC-0010: authority lineage is not available for revalidation.")
            expected_contract = {
                "repository_identity": row[21], "repository_root": str(row[12]).replace("\\", "/"),
                "expected_base_sha": row[13], "bounded_instruction": row[17],
                "allowed_paths": list(row[14]), "acceptance_criteria": list(row[15]),
                "evidence_requirements": list(row[16]), "capability_name": row[18],
                "action_type": row[19], "write_policy": row[20],
            }
            if not immutable_contract_matches(row[23], expected_contract, row[24], row[18]):
                raise RuntimeError("RIV-GRC-0010: authority capability scope no longer matches the intent.")
            root = Path(row[12])
            repository = (repository or root).resolve()
            if repository != root.resolve():
                raise PermissionError("RIV-GRC-0010: repository root does not match the bound engineering intent.")
            assessment = RepositoryDriftAnalyzer().assess(repository, row[13], tuple(row[14]), infrastructure_repair_evidence=infrastructure_repair_evidence)
            evidence = {**assessment.as_dict(), "allowed_paths": list(row[14]), "correlation_id": str(row[6]), "repository_root": str(root)}
            cursor.execute("SELECT revalidation_id,status,successor_work_order_id FROM execution_base_revalidations WHERE failed_work_order_id=%s FOR UPDATE", (failed_work_order_id,))
            existing_revalidation = cursor.fetchone()
            if existing_revalidation and existing_revalidation[1] == "approved":
                return {"revalidation_id": existing_revalidation[0], "failed_work_order_id": failed_work_order_id, "successor_work_order_id": existing_revalidation[2], "status": "approved"}
            if existing_revalidation:
                cursor.execute(
                    """UPDATE execution_base_revalidations
                       SET approved_base_sha=%s,proposed_base_sha=%s,changed_paths=%s::jsonb,material_paths=%s::jsonb,
                           review_paths=%s::jsonb,evidence=%s::jsonb,decision=%s,status='pending',idempotency_key=%s,updated_at=now()
                       WHERE revalidation_id=%s""",
                    (assessment.approved_base_sha, assessment.proposed_base_sha, json.dumps(assessment.changed_paths),
                     json.dumps(assessment.material_paths), json.dumps(assessment.review_paths), json.dumps(evidence),
                     assessment.decision, idempotency_key, existing_revalidation[0]),
                )
            else:
                cursor.execute(
                    """INSERT INTO execution_base_revalidations(
                    revalidation_id,failed_work_order_id,intent_id,objective_id,authority_id,
                    approved_base_sha,proposed_base_sha,changed_paths,material_paths,review_paths,evidence,
                    decision,status,idempotency_key)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s,'pending',%s)
                   ON CONFLICT(idempotency_key) DO NOTHING""",
                    (uuid4(), failed_work_order_id, row[9], row[11], row[10], assessment.approved_base_sha,
                     assessment.proposed_base_sha, json.dumps(assessment.changed_paths), json.dumps(assessment.material_paths),
                     json.dumps(assessment.review_paths), json.dumps(evidence), assessment.decision, idempotency_key),
                )
            cursor.execute("SELECT * FROM execution_base_revalidations WHERE idempotency_key=%s", (idempotency_key,))
            names = [column.name for column in cursor.description]
            result = dict(zip(names, cursor.fetchone(), strict=True))
            if result["failed_work_order_id"] != failed_work_order_id:
                raise ValueError("RIV-COMMS5-0015: revalidation idempotency key conflicts with another work order.")
            cursor.execute(
                """SELECT 1 FROM work_order_successor_lineage
                   WHERE failed_work_order_id=%s
                   UNION ALL
                   SELECT 1 FROM work_order_retry_lineage WHERE failed_work_order_id=%s LIMIT 1""",
                (failed_work_order_id, failed_work_order_id),
            )
            if cursor.fetchone():
                raise RuntimeError("RIV-GRC-0007: a successful or active successor already exists for this failed work order.")
            return result

    def approve_and_queue(
        self,
        revalidation_id: UUID,
        *,
        explicit_steward_confirmation: bool,
        transport_principal: str | None,
        repository: Path | None = None,
    ) -> dict[str, Any]:
        if transport_principal != "steward":
            raise PermissionError("RIV-GRC-0010: recovery approval must be performed by the Steward principal.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM execution_base_revalidations WHERE revalidation_id=%s FOR UPDATE", (revalidation_id,))
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-EXE-0008: stale-base revalidation was not found.")
            names = [column.name for column in cursor.description]
            record = dict(zip(names, row, strict=True))
            if record["status"] == "approved":
                return {"revalidation_id": str(revalidation_id), "successor_work_order_id": str(record["successor_work_order_id"]), "idempotent_replay": True}
            evidence = record["evidence"] if isinstance(record["evidence"], dict) else json.loads(record["evidence"])
            # A qualified infrastructure repair is governed by the explicit
            # evidence contract below; it is not a second approval.  Only
            # governance/ingress drift asks Pat for a narrow base confirmation.
            confirmation_required = record["decision"] == "narrow_steward_confirmation"
            if confirmation_required and not explicit_steward_confirmation:
                raise PermissionError("RIV-GRC-0010: narrow Steward base confirmation is required for this drift class.")
            repository = (repository or Path(evidence["repository_root"])).resolve()
            assessment = RepositoryDriftAnalyzer().assess(repository, record["approved_base_sha"], tuple(evidence.get("allowed_paths", [])))
            if assessment.proposed_base_sha != record["proposed_base_sha"]:
                raise RuntimeError("RIV-EXE-0008: repository moved after revalidation; prepare a new evidence record.")
            if record["decision"] not in {"safe_revalidation", "narrow_steward_confirmation", "infrastructure_repair_revalidation"}:
                raise RuntimeError("RIV-GRC-0010: material repository drift requires renewed specification approval.")
            cursor.execute("SELECT action_type,action_version,parameters,requested_by,correlation_id,expected_duration_seconds,hard_timeout_seconds FROM work_orders WHERE work_order_id=%s FOR UPDATE", (record["failed_work_order_id"],))
            original = cursor.fetchone()
            cursor.execute("SELECT count(*) FROM work_order_retry_lineage WHERE failed_work_order_id=%s", (record["failed_work_order_id"],))
            if cursor.fetchone()[0]:
                raise RuntimeError("RIV-GRC-0007: a successor attempt already exists for this failed work order.")
            successor = uuid4()
            parameters = dict(original[2])
            parameters["stale_base_revalidation_id"] = str(revalidation_id)
            retry_key = f"stale-base-retry:{revalidation_id}"
            cursor.execute(
                """INSERT INTO work_orders(work_order_id,action_type,action_version,status,parameters,requested_by,idempotency_key,correlation_id,causation_id,expected_duration_seconds,hard_timeout_seconds)
                   VALUES(%s,%s,%s,'queued',%s::jsonb,%s,%s,%s,%s,%s,%s)""",
                (successor, original[0], original[1], json.dumps(parameters), original[3], retry_key, original[4], record["failed_work_order_id"], original[5], original[6]),
            )
            cursor.execute("INSERT INTO work_order_retry_lineage(retry_id,failed_work_order_id,successor_work_order_id,revalidation_id,attempt,idempotency_key) VALUES(%s,%s,%s,%s,2,%s)", (uuid4(), record["failed_work_order_id"], successor, revalidation_id, retry_key))
            cursor.execute("UPDATE execution_base_revalidations SET status='approved',successor_work_order_id=%s,explicit_steward_confirmation=true,approved_at=now(),updated_at=now() WHERE revalidation_id=%s", (successor, revalidation_id))
            cursor.execute(
                """INSERT INTO river_events(event_id,event_type,aggregate_type,aggregate_id,correlation_id,causation_id,idempotency_key,classification,payload,occurred_at)
                   VALUES(%s,'work.order.queued','work_order',%s,%s,%s,%s,'river',%s::jsonb,now())
                   ON CONFLICT(idempotency_key) DO NOTHING""",
                (uuid4(), successor, original[4], record["failed_work_order_id"], f"work.order.queued:{successor}", json.dumps({"action_type": original[0], "status": "queued", "revalidation_id": str(revalidation_id)})),
            )
        evidence = record["evidence"] if isinstance(record["evidence"], dict) else json.loads(record["evidence"])
        EventStore().append(RiverEvent(event_type="execution.base.revalidated", aggregate_type="work_order", aggregate_id=successor, correlation_id=UUID(str(evidence["correlation_id"])), idempotency_key=f"execution.base.revalidated:{revalidation_id}", classification=Classification.RIVER, payload={"revalidation_id": str(revalidation_id), "successor_work_order_id": str(successor), "decision": record["decision"]}))
        return {"revalidation_id": str(revalidation_id), "successor_work_order_id": str(successor), "status": "queued", "idempotent_replay": False}

    def execution_base_for(self, work_order_id: UUID, revalidation_id: UUID, intent_id: UUID) -> str:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT r.proposed_base_sha FROM execution_base_revalidations r JOIN work_orders w ON w.work_order_id=r.successor_work_order_id JOIN engineering_intents i ON i.intent_id=r.intent_id WHERE r.revalidation_id=%s AND r.successor_work_order_id=%s AND r.intent_id=%s AND i.authority_id=r.authority_id AND r.status='approved'""", (revalidation_id, work_order_id, intent_id))
            row = cursor.fetchone()
        if row is None:
            raise PermissionError("RIV-GRC-0010: refreshed base binding is not approved for this exact work lineage.")
        return str(row[0])

    def refresh_approved_successor_base(self, revalidation_id: UUID, repository: Path) -> str:
        """Refresh a queued successor's verified descendant base before start."""

        current = RepositoryDriftAnalyzer._git(repository.resolve(), "rev-parse", "HEAD")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE execution_base_revalidations
                   SET proposed_base_sha=%s,updated_at=now()
                   WHERE revalidation_id=%s AND status='approved'
                     AND successor_work_order_id IN (SELECT work_order_id FROM work_orders WHERE status IN ('queued','claimed'))""",
                (current, revalidation_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-EXE-0008: approved successor is not queued or claimable.")
        return current
