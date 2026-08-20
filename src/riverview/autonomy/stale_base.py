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
        if material:
            decision, reason = "material_drift", "the repository diff touches the approved scope or execution dependencies."
        elif review:
            decision, reason = "narrow_steward_confirmation", "scope is unchanged, but governance/ingress changes require Pat's narrow confirmation of the new base."
        else:
            decision, reason = "safe_revalidation", "the repository diff is outside the approved scope and execution dependencies."
        return DriftAssessment(approved_base_sha, proposed, changed, material, review, True, decision, reason)

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
    ) -> dict[str, Any]:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT w.status,w.error_checkpoint,w.parameters,w.action_type,w.action_version,
                          w.requested_by,w.correlation_id,w.expected_duration_seconds,w.hard_timeout_seconds,
                          i.intent_id,i.authority_id,i.objective_id,i.repository_root,i.expected_base_sha,
                          i.allowed_paths,a.status
                   FROM work_orders w JOIN engineering_intents i ON (w.parameters->>'engineering_intent_id')=i.intent_id::text
                   JOIN steward_authority_grants a ON a.authority_id=i.authority_id
                   WHERE w.work_order_id=%s FOR UPDATE""",
                (failed_work_order_id,),
            )
            row = cursor.fetchone()
            if row is None or row[0] != "failed" or row[1] != "RIV-EXE-0008":
                raise RuntimeError("RIV-EXE-0008: only the preserved stale-base failure is revalidatable.")
            if row[15] not in {"active", "consumed"}:
                raise RuntimeError("RIV-GRC-0010: authority lineage is not available for revalidation.")
            root = Path(row[12])
            repository = (repository or root).resolve()
            if repository != root.resolve():
                raise PermissionError("RIV-GRC-0010: repository root does not match the bound engineering intent.")
            assessment = RepositoryDriftAnalyzer().assess(repository, row[13], tuple(row[14]))
            evidence = {**assessment.as_dict(), "allowed_paths": list(row[14]), "correlation_id": str(row[6]), "repository_root": str(root)}
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
            return result

    def approve_and_queue(
        self,
        revalidation_id: UUID,
        *,
        explicit_steward_confirmation: bool,
        transport_principal: str | None,
        repository: Path | None = None,
    ) -> dict[str, Any]:
        if transport_principal != "steward" or not explicit_steward_confirmation:
            raise PermissionError("RIV-GRC-0010: narrow Steward base confirmation is required.")
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
            repository = (repository or Path(evidence["repository_root"])).resolve()
            assessment = RepositoryDriftAnalyzer().assess(repository, record["approved_base_sha"], tuple(evidence.get("allowed_paths", [])))
            if assessment.proposed_base_sha != record["proposed_base_sha"]:
                raise RuntimeError("RIV-EXE-0008: repository moved after revalidation; prepare a new evidence record.")
            if record["decision"] not in {"safe_revalidation", "narrow_steward_confirmation"}:
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
