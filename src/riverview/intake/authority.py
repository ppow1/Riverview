"""Durable, immutable Steward authority for bounded Grace formation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.intake.engineering import EngineeringIntent
from riverview.intake.policy import (
    ENGINEERING_ACTION,
    ENGINEERING_CAPABILITY,
    ENGINEERING_POLICIES,
)
from riverview.river.events import Classification, RiverEvent
from riverview.river.store import EventStore


class StewardAuthorityError(RuntimeError):
    """Fail-closed authority or scope validation failure."""


class StewardAuthorityStore:
    """Create and consume the one durable Steward approval representation."""

    @staticmethod
    def validate_formation_contract(value: Any) -> dict[str, Any]:
        """Validate the non-executable typed contract before durable storage."""
        if not isinstance(value, dict):
            raise StewardAuthorityError("RIV-INT-0004: formation_contract must be an object.")
        required = {"repository_identity", "repository_root", "expected_base_sha", "bounded_instruction", "allowed_paths", "acceptance_criteria", "evidence_requirements", "capability_name", "action_type", "timeout_seconds", "write_policy"}
        if set(value) != required:
            raise StewardAuthorityError("RIV-INT-0004: formation_contract fields are incomplete or unrecognized.")
        if value["write_policy"] not in ENGINEERING_POLICIES or value["capability_name"] != ENGINEERING_CAPABILITY or value["action_type"] != ENGINEERING_ACTION:
            raise StewardAuthorityError("RIV-CAP-0004: only the registered bounded Codex engineering action is accepted.")
        for key in ("allowed_paths", "acceptance_criteria", "evidence_requirements"):
            if not isinstance(value[key], list) or not value[key] or any(not isinstance(item, str) for item in value[key]):
                raise StewardAuthorityError("RIV-INT-0004: formation contract lists are bounded string lists.")
        if not isinstance(value["timeout_seconds"], int) or not 1 <= value["timeout_seconds"] <= 86_400:
            raise StewardAuthorityError("RIV-INT-0004: formation timeout is outside its safe limit.")
        encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode()
        if len(encoded) > 64_000:
            raise StewardAuthorityError("RIV-INT-0004: formation contract exceeds its bounded limit.")
        return value

    @staticmethod
    def _contract(row: Any) -> dict[str, Any] | None:
        if row is None:
            return None
        return row if isinstance(row, dict) else json.loads(row)

    def grant_for_promoted_seed(
        self,
        seed_id: UUID,
        objective_id: UUID,
        *,
        correlation_id: UUID,
        approval_operation_id: UUID | None = None,
        idempotency_key: str,
    ) -> dict[str, Any] | None:
        """Materialize approval only for the exact stored specification.

        A seed without a specification is intentionally left fail-closed.  A
        prose specification may receive an auditable grant, but it is not
        formation-ready until it contains the validated typed contract.
        """
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT sd.specification_id,sd.specification_version,sd.classification,
                          s.version,s.content_sha256,s.formation_contract,o.objective_id,st.stage_id
                   FROM steward_seed_drafts sd
                   LEFT JOIN comms5_specifications s ON s.specification_id=sd.specification_id
                   JOIN objectives o ON o.objective_id=%s
                   JOIN objective_stages st ON st.objective_id=o.objective_id AND st.stage_key='validate'
                   WHERE sd.seed_id=%s AND sd.objective_id=%s FOR UPDATE""",
                (objective_id, seed_id, objective_id),
            )
            row = cursor.fetchone()
            if row is None or row[0] is None or row[3] is None:
                return None
            if row[1] != row[3] or row[2] not in {"river", "internal"}:
                raise StewardAuthorityError("RIV-GRC-0010: seed specification version or classification does not reconcile.")
            cursor.execute("SELECT authority_id,specification_id,specification_sha256,status FROM steward_authority_grants WHERE idempotency_key=%s", (idempotency_key,))
            existing = cursor.fetchone()
            if existing:
                if existing[1] != row[0] or existing[2] != row[4]:
                    raise StewardAuthorityError("RIV-GRC-0010: authority idempotency key conflicts with approved scope.")
                return self.load(existing[0])
            authority_id = uuid4()
            contract = self._contract(row[5])
            capabilities = [] if not contract else [str(contract.get("capability_name", ""))]
            scope = {"formation_contract_present": contract is not None, "contract": contract or {}}
            cursor.execute(
                """INSERT INTO steward_authority_grants
                   (authority_id,specification_id,specification_version,specification_sha256,seed_id,objective_id,stage_id,
                    approving_principal,classification,correlation_id,causation_id,approval_operation_id,idempotency_key,
                    scope,permitted_capabilities,status)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,'steward',%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,'active')""",
                (authority_id, row[0], row[1], row[4], seed_id, objective_id, row[7], row[2], correlation_id,
                 seed_id, approval_operation_id, idempotency_key, json.dumps(scope), json.dumps(capabilities)),
            )
            result = self.load(authority_id, cursor=cursor)
        EventStore().append(RiverEvent(
            event_type="steward.authority.granted", aggregate_type="objective", aggregate_id=objective_id,
            correlation_id=correlation_id, causation_id=seed_id,
            idempotency_key=f"steward.authority.granted:{result['authority_id']}", classification=Classification(result["classification"]),
            payload={"authority_id": result["authority_id"], "specification_id": result["specification_id"], "specification_version": result["specification_version"], "specification_sha256": result["specification_sha256"], "objective_id": result["objective_id"], "seed_id": result["seed_id"]},
        ))
        return result

    def grant_for_existing_specification(
        self, specification_id: UUID, *, seed_id: UUID, objective_id: UUID, stage_id: UUID,
        correlation_id: UUID, idempotency_key: str, approving_principal: str,
        approval_operation_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Direct Grace-origin ingress using the same Steward artifact.

        The caller must already have a governed seed/objective and an explicit
        authenticated Steward approval; this method is not a prose parser or
        a public arbitrary state setter.
        """
        if approving_principal != "steward":
            raise StewardAuthorityError("RIV-GRC-0010: only the authenticated Steward may grant authority.")
        if approval_operation_id is None:
            raise StewardAuthorityError("RIV-GRC-0010: direct authority requires an approval operation identity.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT version,content_sha256,classification,formation_contract FROM comms5_specifications WHERE specification_id=%s AND lifecycle_state IN ('stored','referenced') FOR UPDATE", (specification_id,))
            spec = cursor.fetchone()
            if spec is None:
                raise StewardAuthorityError("RIV-GRC-0010: approved specification is unavailable.")
            cursor.execute("SELECT status,objective_id,specification_id,specification_version,correlation_id FROM steward_seed_drafts WHERE seed_id=%s FOR UPDATE", (seed_id,))
            seed = cursor.fetchone()
            if seed is None or seed[0] != "promoted" or seed[1] != objective_id or seed[2] != specification_id or seed[3] != spec[0]:
                raise StewardAuthorityError("RIV-GRC-0010: direct Grace authority lineage does not reconcile.")
            cursor.execute("SELECT authority_id FROM steward_authority_grants WHERE idempotency_key=%s", (idempotency_key,))
            existing = cursor.fetchone()
            if existing:
                result = self.load(existing[0], cursor=cursor)
            else:
                authority_id = uuid4()
                contract = self._contract(spec[3])
                cursor.execute("""INSERT INTO steward_authority_grants
                    (authority_id,specification_id,specification_version,specification_sha256,seed_id,objective_id,stage_id,
                     approving_principal,classification,correlation_id,causation_id,approval_operation_id,idempotency_key,scope,permitted_capabilities,status)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,'steward',%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,'active')""",
                    (authority_id, specification_id, spec[0], spec[1], seed_id, objective_id, stage_id, spec[2], correlation_id,
                     seed_id, approval_operation_id, idempotency_key, json.dumps({"formation_contract_present": contract is not None, "contract": contract or {}}), json.dumps([] if not contract else [contract.get("capability_name", "")])))
                result = self.load(authority_id, cursor=cursor)
        EventStore().append(RiverEvent(event_type="steward.authority.granted", aggregate_type="objective", aggregate_id=objective_id, correlation_id=correlation_id, causation_id=seed_id, idempotency_key=f"steward.authority.granted:{result['authority_id']}", classification=Classification(result["classification"]), payload={"authority_id": result["authority_id"], "specification_id": result["specification_id"], "objective_id": result["objective_id"]}))
        return result

    def load(self, authority_id: UUID, *, cursor: Any | None = None) -> dict[str, Any] | None:
        if cursor is not None:
            cursor.execute("SELECT authority_id,specification_id,specification_version,specification_sha256,seed_id,objective_id,stage_id,approving_principal,approved_at,classification,correlation_id,causation_id,approval_operation_id,idempotency_key,scope,permitted_capabilities,status,consumed_at,superseded_by,created_at,updated_at FROM steward_authority_grants WHERE authority_id=%s", (authority_id,))
            row = cursor.fetchone()
            if row is None: return None
            return dict(zip([d.name for d in cursor.description], row, strict=True))
        with connect() as connection, connection.cursor() as db_cursor:
            return self.load(authority_id, cursor=db_cursor)

    def for_stage(self, objective_id: UUID, stage_id: UUID, *, cursor: Any | None = None) -> dict[str, Any] | None:
        own = cursor is None
        if own:
            connection = connect(); cursor = connection.cursor()
        cursor.execute("SELECT authority_id FROM steward_authority_grants WHERE objective_id=%s AND stage_id=%s AND status='active' ORDER BY approved_at DESC LIMIT 1", (objective_id, stage_id))
        row = cursor.fetchone()
        result = self.load(row[0], cursor=cursor) if row else None
        if own:
            cursor.close(); connection.close()
        return result

    @staticmethod
    def intent_from_contract(authority: dict[str, Any]) -> EngineeringIntent:
        contract = authority["scope"].get("contract") if isinstance(authority.get("scope"), dict) else None
        if not isinstance(contract, dict):
            raise StewardAuthorityError("RIV-GRC-0010: approved specification has no typed engineering formation contract.")
        try:
            return EngineeringIntent(
                seed_id=UUID(str(authority["seed_id"])), objective_id=UUID(str(authority["objective_id"])), stage_id=UUID(str(authority["stage_id"])),
                repository_identity=str(contract["repository_identity"]), repository_root=Path(str(contract["repository_root"])),
                expected_base_sha=str(contract["expected_base_sha"]), bounded_instruction=str(contract["bounded_instruction"]),
                allowed_paths=tuple(contract["allowed_paths"]), acceptance_criteria=tuple(contract["acceptance_criteria"]),
                evidence_requirements=tuple(contract["evidence_requirements"]), capability_name=str(contract["capability_name"]),
                action_type=str(contract["action_type"]), timeout_seconds=int(contract["timeout_seconds"]),
                classification=str(authority["classification"]), correlation_id=UUID(str(authority["correlation_id"])),
                causation_id=UUID(str(authority["causation_id"])) if authority.get("causation_id") else None,
                idempotency_key=f"engineering-intent:authority:{authority['authority_id']}",
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise StewardAuthorityError("RIV-GRC-0010: typed engineering formation contract is malformed.") from exc
