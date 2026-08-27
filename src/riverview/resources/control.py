"""Durable, governed resource policy and exclusive seat claims."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Callable
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.resources.registry import ResourcePlanner, ResourcePolicy, ResourceRegistry

POLICY_ID = "codex-fleet"
POLICY_MODES = frozenset(
    {
        "HIGHEST_CAPACITY",
        "BALANCED",
        "ROUND_ROBIN",
        "DRAIN",
        "PRESERVE",
        "SOONEST_ROLLOVER",
        "MAXIMIZE_RUNWAY",
        "PRIORITY",
    }
)
ACTIVE_CLAIM_STATES = ("claimed", "starting", "running")


class ResourceControlError(RuntimeError):
    """Fail-closed resource-policy or claim error."""


@dataclass(frozen=True)
class DurableResourcePolicy:
    policy_id: str
    revision: int
    mode: str
    parameters: dict[str, Any]
    changed_by: str
    authority: str
    rationale: str | None
    steward_lock: bool
    updated_at: Any


@dataclass(frozen=True)
class SeatClaim:
    claim_id: UUID
    seat_id: str
    work_id: str
    owner_id: str
    state: str
    lease_expires_at: Any
    safe_fingerprint: str | None = None
    decision_id: UUID | None = None


class ResourcePolicyStore:
    """PostgreSQL aggregate for one authoritative Codex fleet policy."""

    def __init__(self, connection_factory: Callable[[], Any] = connect) -> None:
        self.connection_factory = connection_factory

    @staticmethod
    def _policy(row: Any) -> DurableResourcePolicy:
        return DurableResourcePolicy(
            policy_id=row[0], revision=row[1], mode=row[2],
            parameters=row[3] if isinstance(row[3], dict) else json.loads(row[3]),
            changed_by=row[4], authority=row[5], rationale=row[6],
            steward_lock=row[7], updated_at=row[8],
        )

    def get(self, *, cursor: Any | None = None) -> DurableResourcePolicy | None:
        if cursor is not None:
            cursor.execute(
                "SELECT policy_id,revision,mode,parameters,changed_by,authority,rationale,steward_lock,updated_at FROM resource_policy WHERE policy_id=%s",
                (POLICY_ID,),
            )
            row = cursor.fetchone()
            return self._policy(row) if row else None
        with self.connection_factory() as connection, connection.cursor() as owned_cursor:
            return self.get(cursor=owned_cursor)

    def ensure_default(self, *, actor: str = "system", authority: str = "system") -> DurableResourcePolicy:
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO resource_policy(policy_id,mode,parameters,changed_by,authority,rationale)
                   VALUES(%s,'HIGHEST_CAPACITY','{}'::jsonb,%s,%s,'initial durable default')
                   ON CONFLICT(policy_id) DO NOTHING""",
                (POLICY_ID, actor, authority),
            )
            cursor.execute(
                "SELECT policy_id,revision,mode,parameters,changed_by,authority,rationale,steward_lock,updated_at FROM resource_policy WHERE policy_id=%s FOR UPDATE",
                (POLICY_ID,),
            )
            return self._policy(cursor.fetchone())

    def set(
        self,
        mode: str,
        parameters: dict[str, Any] | None = None,
        *,
        actor: str,
        authority: str,
        rationale: str | None = None,
        source_request_id: str | None = None,
        expected_revision: int | None = None,
    ) -> DurableResourcePolicy:
        if mode not in POLICY_MODES:
            raise ResourceControlError(f"unsupported resource policy mode: {mode}")
        parameters = dict(parameters or {})
        if actor != "steward" and authority != "steward" and parameters.get("consume_reset"):
            raise ResourceControlError("reset-credit activation is not an ordinary resource-policy operation")
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT policy_id,revision,mode,parameters,changed_by,authority,rationale,steward_lock,updated_at FROM resource_policy WHERE policy_id=%s FOR UPDATE",
                (POLICY_ID,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ResourceControlError("resource policy aggregate is not initialized")
            previous = self._policy(row)
            if expected_revision is not None and expected_revision != previous.revision:
                raise ResourceControlError(f"resource policy revision conflict: expected {expected_revision}, current {previous.revision}")
            if previous.steward_lock and actor != "steward" and authority != "steward":
                raise ResourceControlError("resource policy is Steward-locked")
            revision = previous.revision + 1
            cursor.execute(
                """UPDATE resource_policy SET revision=%s,mode=%s,parameters=%s::jsonb,changed_by=%s,authority=%s,rationale=%s,updated_at=now() WHERE policy_id=%s""",
                (revision, mode, json.dumps(parameters), actor, authority, rationale, POLICY_ID),
            )
            cursor.execute(
                """INSERT INTO resource_policy_audit
                   (audit_id,policy_id,previous_revision,new_revision,previous_mode,new_mode,previous_parameters,new_parameters,actor,authority,rationale,source_request_id)
                   VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s)""",
                (uuid4(), POLICY_ID, previous.revision, revision, previous.mode, mode,
                 json.dumps(previous.parameters), json.dumps(parameters), actor, authority, rationale, source_request_id),
            )
            cursor.execute(
                "SELECT policy_id,revision,mode,parameters,changed_by,authority,rationale,steward_lock,updated_at FROM resource_policy WHERE policy_id=%s",
                (POLICY_ID,),
            )
            return self._policy(cursor.fetchone())

    def set_lock(self, locked: bool, *, actor: str, authority: str, rationale: str | None = None) -> DurableResourcePolicy:
        if actor != "steward" or authority != "steward":
            raise ResourceControlError("only the Steward may change the resource-policy lock")
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT policy_id,revision,mode,parameters,changed_by,authority,rationale,steward_lock,updated_at FROM resource_policy WHERE policy_id=%s FOR UPDATE",
                (POLICY_ID,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ResourceControlError("resource policy aggregate is not initialized")
            previous = self._policy(row)
            revision = previous.revision + 1
            cursor.execute("UPDATE resource_policy SET revision=%s,steward_lock=%s,changed_by=%s,authority=%s,rationale=%s,updated_at=now() WHERE policy_id=%s", (revision, locked, actor, authority, rationale, POLICY_ID))
            cursor.execute("INSERT INTO resource_policy_audit(audit_id,policy_id,previous_revision,new_revision,previous_mode,new_mode,previous_parameters,new_parameters,actor,authority,rationale) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s)", (uuid4(), POLICY_ID, previous.revision, revision, previous.mode, previous.mode, json.dumps(previous.parameters), json.dumps(previous.parameters), actor, authority, rationale))
            cursor.execute("SELECT policy_id,revision,mode,parameters,changed_by,authority,rationale,steward_lock,updated_at FROM resource_policy WHERE policy_id=%s", (POLICY_ID,))
            return self._policy(cursor.fetchone())

    def audit(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT audit_id,previous_revision,new_revision,previous_mode,new_mode,previous_parameters,new_parameters,actor,authority,rationale,source_request_id,created_at FROM resource_policy_audit WHERE policy_id=%s ORDER BY created_at DESC LIMIT %s", (POLICY_ID, max(1, min(limit, 100))))
            names = [column.name for column in cursor.description]
            return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]

    def next_round_robin_cursor(self) -> int:
        """Advance the durable cursor under the policy row lock."""
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT round_robin_cursor FROM resource_policy WHERE policy_id=%s FOR UPDATE", (POLICY_ID,))
            row = cursor.fetchone()
            if row is None:
                raise ResourceControlError("resource policy aggregate is not initialized")
            current = int(row[0])
            cursor.execute("UPDATE resource_policy SET round_robin_cursor=%s,updated_at=now() WHERE policy_id=%s", (current + 1, POLICY_ID))
            return current


class SeatClaimStore:
    """Atomic PostgreSQL seat lease store; uniqueness is enforced by the DB."""

    def __init__(self, connection_factory: Callable[[], Any] = connect) -> None:
        self.connection_factory = connection_factory

    def claim(self, seat_id: str, work_id: str, owner_id: str, *, lease_seconds: int = 300, safe_fingerprint: str | None = None) -> SeatClaim:
        if seat_id not in {"C1", "C2", "C3"} or not work_id or not owner_id:
            raise ResourceControlError("invalid seat claim identity")
        claim_id = uuid4()
        with self.connection_factory() as connection, connection.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO resource_seat_claims(claim_id,seat_id,work_id,owner_id,state,safe_fingerprint,lease_expires_at) VALUES(%s,%s,%s,%s,'claimed',%s,now()+(%s * interval '1 second')) RETURNING claim_id,seat_id,work_id,owner_id,state,lease_expires_at,safe_fingerprint", (claim_id, seat_id, work_id, owner_id, safe_fingerprint, lease_seconds))
            except Exception as exc:
                raise ResourceControlError(f"seat {seat_id} is already claimed") from exc
            row = cursor.fetchone()
            return SeatClaim(row[0], row[1], row[2], row[3], row[4], row[5], row[6] if len(row) > 6 else safe_fingerprint)

    def expire_stale(self) -> list[UUID]:
        """Release only active claims whose durable lease has expired."""
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute("""UPDATE resource_seat_claims
                              SET state='expired', released_at=now(), release_reason='lease expired during worker failure'
                            WHERE state IN ('claimed','starting','running')
                              AND lease_expires_at < now()
                            RETURNING claim_id""")
            return [row[0] for row in cursor.fetchall()]

    def transition(self, claim_id: UUID, state: str) -> None:
        if state not in {"starting", "running"}:
            raise ResourceControlError("invalid active seat transition")
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE resource_seat_claims SET state=%s,started_at=CASE WHEN %s='running' THEN COALESCE(started_at,now()) ELSE started_at END,last_heartbeat_at=now() WHERE claim_id=%s AND state IN ('claimed','starting','running')", (state, state, claim_id))
            if cursor.rowcount != 1:
                raise ResourceControlError("seat claim is missing, released, or expired")

    def release(self, claim_id: UUID, *, reason: str, failed: bool = False) -> None:
        state = "failed" if failed else "released"
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE resource_seat_claims SET state=%s,released_at=now(),release_reason=%s WHERE claim_id=%s AND state IN ('claimed','starting','running')", (state, reason, claim_id))
            if cursor.rowcount != 1:
                raise ResourceControlError("seat claim is already released or expired")

    def renew(self, claim_id: UUID, *, lease_seconds: int = 300) -> None:
        if isinstance(lease_seconds, bool) or not 1 <= int(lease_seconds) <= 3_600:
            raise ResourceControlError("lease duration is invalid")
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE resource_seat_claims SET last_heartbeat_at=now(),lease_expires_at=now()+(%s * interval '1 second') WHERE claim_id=%s AND state IN ('claimed','starting','running')",
                (lease_seconds, claim_id),
            )
            if cursor.rowcount != 1:
                raise ResourceControlError("seat claim is not active")

    def attach_work(self, claim_id: UUID, work_id: str) -> None:
        """Bind a pre-admission reservation to the fenced work-order identity."""
        if not work_id:
            raise ResourceControlError("work identity is required")
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE resource_seat_claims SET work_id=%s WHERE claim_id=%s AND state='claimed'",
                (work_id, claim_id),
            )
            if cursor.rowcount != 1:
                raise ResourceControlError("seat claim is not attachable")

    def recover_expired(self) -> int:
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE resource_seat_claims SET state='expired',released_at=now(),release_reason='lease expired' WHERE state IN ('claimed','starting','running') AND lease_expires_at<=now()")
            return cursor.rowcount


class ResourceDecisionStore:
    """Append-only structured planner-decision provenance."""

    def __init__(self, connection_factory: Callable[[], Any] = connect) -> None:
        self.connection_factory = connection_factory

    def record(self, *, policy: DurableResourcePolicy, work_id: str, owner_id: str,
               candidates: list[dict[str, Any]], ranking: list[str],
               claim_attempts: list[dict[str, Any]], claim: SeatClaim,
               reason: str, execution_correlation_id: str | None = None) -> UUID:
        decision_id = uuid4()
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO resource_planner_decisions
                   (decision_id,policy_id,policy_revision,policy_mode,policy_parameters,work_id,owner_id,candidates,ranking,claim_attempts,selected_seat,selected_fingerprint,claim_id,execution_correlation_id,fallback_used,decision_reason)
                   VALUES(%s,%s,%s,%s,%s::jsonb,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s)""",
                (decision_id, policy.policy_id, policy.revision, policy.mode, json.dumps(policy.parameters),
                 work_id, owner_id, json.dumps(candidates), json.dumps(ranking), json.dumps(claim_attempts),
                 claim.seat_id, claim.safe_fingerprint, claim.claim_id, execution_correlation_id,
                 len(claim_attempts) > 1, reason),
            )
        return decision_id

    def latest(self) -> dict[str, Any] | None:
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM resource_planner_decisions ORDER BY created_at DESC LIMIT 1")
            row = cursor.fetchone()
            if row is None:
                return None
            names = [column.name for column in cursor.description]
            return dict(zip(names, row, strict=True))

    def bind_execution(self, decision_id: UUID, *, work_id: str, execution_correlation_id: str) -> None:
        """Replace the reservation identity with the admitted execution identity."""
        with self.connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE resource_planner_decisions SET work_id=%s,execution_correlation_id=%s WHERE decision_id=%s",
                (work_id, execution_correlation_id, decision_id),
            )
            if cursor.rowcount != 1:
                raise ResourceControlError("planner decision is missing during execution binding")


class DurableResourcePlanner:
    """Re-evaluate policy selection after each atomic seat-claim race."""

    def __init__(self, registry: ResourceRegistry, policy_store: ResourcePolicyStore, claim_store: SeatClaimStore, decision_store: ResourceDecisionStore | None = None) -> None:
        self.registry = registry
        self.policy_store = policy_store
        self.claim_store = claim_store
        self.decision_store = decision_store or (ResourceDecisionStore(policy_store.connection_factory) if hasattr(policy_store, "connection_factory") else None)

    def claim_automatic(self, work_id: str, owner_id: str, *, role: str = "writer", max_attempts: int = 3, now: datetime | None = None) -> tuple[SeatClaim, str]:
        durable = self.policy_store.get()
        if durable is None:
            raise ResourceControlError("resource policy aggregate is not initialized")
        parameters = durable.parameters
        policy = ResourcePolicy(
            mode=durable.mode,
            target_seat=parameters.get("target_seat"),
            priority_order=tuple(parameters.get("priority_order", ())),
            fallback=bool(parameters.get("fallback", True)),
        )
        planner = ResourcePlanner(self.registry)
        if durable.mode == "ROUND_ROBIN":
            planner._round_robin_cursor = self.policy_store.next_round_robin_cursor()
        excluded: set[str] = set()
        race_reasons: list[str] = []
        claim_attempts: list[dict[str, Any]] = []
        candidates: list[dict[str, Any]] = []
        for _ in range(max(1, max_attempts)):
            selection = planner.select(policy, role=role, now=now, excluded_seats=excluded)
            if selection.resource is None:
                raise ResourceControlError("no eligible seat remains after claim re-evaluation")
            if not candidates:
                for resource in self.registry.resources:
                    candidates.append({
                        "seat_id": resource.seat_id,
                        "resource_id": resource.resource_id,
                        "available": resource.available,
                        "health": resource.health,
                        "observed_capacity": resource.observed_capacity,
                        "observed_at": resource.observed_at.isoformat() if resource.observed_at else None,
                        "quota_windows": list(resource.quota_windows),
                        "eligible_in_selection": resource.resource_id in selection.candidates_considered,
                    })
            claim_attempts.append({"seat_id": selection.resource.seat_id, "resource_id": selection.resource.resource_id, "result": "attempt"})
            try:
                claim = self.claim_store.claim(selection.resource.seat_id or "", work_id, owner_id, safe_fingerprint=selection.resource.identity_fingerprint)
            except ResourceControlError as exc:
                excluded.add(selection.resource.seat_id or "")
                race_reasons.append(str(exc))
                claim_attempts[-1]["result"] = "conflict"
                continue
            reason = selection.reason
            if race_reasons:
                reason += f"; re-evaluated after claim race: {race_reasons}"
            decision_id = None
            if self.decision_store is not None:
                try:
                    decision_id = self.decision_store.record(
                        policy=durable, work_id=work_id, owner_id=owner_id,
                        candidates=candidates, ranking=[item["seat_id"] for item in claim_attempts],
                        claim_attempts=claim_attempts, claim=claim, reason=reason,
                    )
                except Exception as exc:
                    self.claim_store.release(claim.claim_id, reason="decision provenance persistence failed", failed=True)
                    raise ResourceControlError("planner decision provenance could not be persisted") from exc
                reason += f"; decision_id={decision_id}"
            if decision_id is not None:
                claim = SeatClaim(
                    claim.claim_id, claim.seat_id, claim.work_id, claim.owner_id,
                    claim.state, claim.lease_expires_at, claim.safe_fingerprint, decision_id,
                )
            return claim, reason
        raise ResourceControlError("no eligible seat could be atomically claimed")


__all__ = ["DurableResourcePlanner", "DurableResourcePolicy", "POLICY_ID", "POLICY_MODES", "ResourceControlError", "ResourcePolicyStore", "SeatClaim", "SeatClaimStore"]
