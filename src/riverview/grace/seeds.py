"""Bounded Steward seed draft and promotion contract for RV-008.5."""

from __future__ import annotations

from uuid import UUID, uuid4

from riverview.database import connect
from riverview.grace.objectives import ObjectiveStore, StageSpec
from riverview.intake.authority import StewardAuthorityStore
from riverview.river.events import Classification, RiverEvent
from riverview.river.store import EventStore

DESIGNATED_CONSUMER = "chatgpt:riverview_001"
MAX_SEED_BYTES = 8_000


class SeedLifecycleError(RuntimeError):
    """Bounded domain failure for governed seed lifecycle transitions."""

    def __init__(self, code: str, reason: str, *, seed_id: UUID | None = None, objective_id: UUID | None = None) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.seed_id = seed_id
        self.objective_id = objective_id


class StewardSeedStore:
    """Conversation text creates a draft only; Grace promotes it explicitly."""

    def submit(
        self,
        seed_text: str,
        *,
        correlation_id: UUID,
        idempotency_key: str,
        causation_id: UUID | None = None,
        classification: str = "river",
        client_id: str | None = None,
        client_type: str | None = None,
        client_name: str | None = None,
        client_version: str | None = None,
        protocol_version: str | None = None,
        authenticated_principal: str | None = None,
        specification_id: UUID | None = None,
        specification_version: int | None = None,
    ) -> UUID:
        if not seed_text.strip() or len(seed_text.encode("utf-8")) > MAX_SEED_BYTES:
            raise ValueError("RIV-0085-0001: seed is empty or exceeds its bounded size.")
        if classification not in {"river", "internal"}:
            raise ValueError("RIV-0085-0001: seed classification is unsupported.")
        seed_id = uuid4()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO steward_seed_drafts(
                       seed_id,correlation_id,causation_id,consumer_id,seed_text,classification,status,idempotency_key,
                       client_id,client_type,client_name,client_version,protocol_version,authenticated_principal,
                       specification_id,specification_version)
                   VALUES(%s,%s,%s,%s,%s,%s,'draft',%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(idempotency_key) DO NOTHING""",
                (seed_id, correlation_id, causation_id, DESIGNATED_CONSUMER, seed_text, classification, idempotency_key,
                 client_id, client_type, client_name, client_version, protocol_version, authenticated_principal,
                 specification_id, specification_version),
            )
            cursor.execute(
                """SELECT seed_id,seed_text,classification,specification_id
                   FROM steward_seed_drafts WHERE idempotency_key=%s""",
                (idempotency_key,),
            )
            row = cursor.fetchone()
            if row is None:
                raise SeedLifecycleError("RIV-COMMS5-0015", "seed idempotency reconciliation found no seed")
            if row[1] != seed_text or row[2] != classification or row[3] != specification_id:
                raise SeedLifecycleError("RIV-COMMS5-0015", "idempotency key conflicts with an existing seed")
            return row[0]

    def confirm_and_promote(self, seed_id: UUID, *, confirmer: str, idempotency_key: str | None = None) -> UUID:
        if confirmer != "steward":
            raise PermissionError("RIV-0085-0002: only the Steward may promote a seed draft.")
        with connect() as connection, connection.cursor() as cursor:
            if idempotency_key:
                cursor.execute("SELECT request_id,seed_id,objective_id,actor FROM steward_seed_promotion_requests WHERE idempotency_key=%s FOR UPDATE", (idempotency_key,))
                request = cursor.fetchone()
                if request:
                    if request[1] != seed_id or request[3] != confirmer:
                        raise SeedLifecycleError("RIV-COMMS5-0015", "promotion idempotency key conflicts with an existing promotion", seed_id=seed_id, objective_id=request[2])
                    authority_key = f"steward-authority:{idempotency_key}"
                    cursor.execute("SELECT authority_id FROM steward_authority_grants WHERE idempotency_key=%s", (authority_key,))
                    if cursor.fetchone():
                        return request[2]
            cursor.execute(
                "SELECT correlation_id,seed_text,status,objective_id FROM steward_seed_drafts WHERE seed_id=%s FOR UPDATE",
                (seed_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise SeedLifecycleError("RIV-COMMS5-0006", "seed was not found", seed_id=seed_id)
            if row[2] == "promoted" and row[3] is not None:
                if not request or not idempotency_key:
                    raise SeedLifecycleError("RIV-COMMS5-0015", "promotion is incomplete: authority idempotency record is missing", seed_id=seed_id, objective_id=row[3])
                authority = StewardAuthorityStore().grant_for_promoted_seed_in_transaction(
                    cursor, seed_id, row[3], correlation_id=row[0],
                    approval_operation_id=request[0],
                    idempotency_key=f"steward-authority:{idempotency_key}",
                )
                if authority is None:
                    raise SeedLifecycleError("RIV-GRC-0010", "promoted seed is not bound to an eligible specification", seed_id=seed_id, objective_id=row[3])
                EventStore().append_in_transaction(cursor, RiverEvent(
                    event_type="steward.authority.granted", aggregate_type="objective", aggregate_id=row[3],
                    correlation_id=row[0], causation_id=seed_id,
                    idempotency_key=f"steward.authority.granted:{authority['authority_id']}", classification=Classification.RIVER,
                    payload={"authority_id": str(authority["authority_id"]), "specification_id": str(authority["specification_id"]), "objective_id": str(row[3]), "seed_id": str(seed_id)},
                ))
                return row[3]
            if row[2] == "cancelled":
                raise SeedLifecycleError("RIV-COMMS5-0014", "seed is already cancelled", seed_id=seed_id)
            if row[2] == "superseded":
                raise SeedLifecycleError("RIV-COMMS5-0014", "seed is superseded", seed_id=seed_id)
            if row[2] != "draft":
                raise SeedLifecycleError("RIV-COMMS5-0014", "seed draft is not promotable", seed_id=seed_id)
            objective_id = ObjectiveStore().create_in_transaction(
                cursor, f"seed:{seed_id}", "Steward seed draft", row[1],
                [StageSpec("validate", "Validate steward seed", "Grace validates the bounded seed before work formation.", ("seed:confirmed",))],
                owner_id="grace", requested_by="steward", correlation_id=row[0],
            )
            cursor.execute(
                "UPDATE steward_seed_drafts SET status='confirmed',objective_id=%s,confirmed_at=now() WHERE seed_id=%s",
                (objective_id, seed_id),
            )
            approval_operation_id = None
            if idempotency_key:
                cursor.execute(
                    """INSERT INTO steward_seed_promotion_requests(request_id,seed_id,objective_id,actor,idempotency_key)
                       VALUES(%s,%s,%s,%s,%s) ON CONFLICT(idempotency_key) DO NOTHING""",
                    (uuid4(), seed_id, objective_id, confirmer, idempotency_key),
                )
                cursor.execute("SELECT request_id FROM steward_seed_promotion_requests WHERE idempotency_key=%s FOR UPDATE", (idempotency_key,))
                approval_operation_id = cursor.fetchone()[0]
            cursor.execute("UPDATE steward_seed_drafts SET status='promoted',objective_id=%s,promoted_at=now() WHERE seed_id=%s", (objective_id, seed_id))
            authority = StewardAuthorityStore().grant_for_promoted_seed_in_transaction(
                cursor, seed_id, objective_id, correlation_id=row[0],
                approval_operation_id=approval_operation_id,
                idempotency_key=f"steward-authority:{idempotency_key or seed_id}",
            )
            if authority is None:
                raise SeedLifecycleError("RIV-GRC-0010", "promoted seed is not bound to an eligible specification", seed_id=seed_id, objective_id=objective_id)
            EventStore().append_in_transaction(cursor, RiverEvent(
                event_type="steward.authority.granted", aggregate_type="objective", aggregate_id=objective_id,
                correlation_id=row[0], causation_id=seed_id,
                idempotency_key=f"steward.authority.granted:{authority['authority_id']}", classification=Classification.RIVER,
                payload={"authority_id": str(authority["authority_id"]), "specification_id": str(authority["specification_id"]), "objective_id": str(objective_id), "seed_id": str(seed_id)},
            ))
            EventStore().append_in_transaction(cursor, RiverEvent(
                event_type="steward.seed.promoted", aggregate_type="objective", aggregate_id=objective_id,
                correlation_id=row[0], causation_id=seed_id,
                idempotency_key=f"steward.seed.promoted:{seed_id}", classification=Classification.RIVER,
                payload={"seed_id": str(seed_id), "objective_id": str(objective_id), "status": "promoted"},
            ))
            return objective_id

    @staticmethod
    def _lifecycle_retry(cursor, idempotency_key: str, *, transition: str, seed_id: UUID, replacement_seed_id: UUID | None, actor: str, reason: str, classification: str, correlation_id: UUID) -> dict[str, object] | None:
        cursor.execute(
            """SELECT lifecycle_event_id,seed_id,transition,replacement_seed_id,actor,reason,
                      classification,correlation_id,created_at
               FROM steward_seed_lifecycle_events WHERE idempotency_key=%s""",
            (idempotency_key,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if (row[1], row[2], row[3], row[4], row[5], row[6], row[7]) != (seed_id, transition, replacement_seed_id, actor, reason, classification, correlation_id):
            raise SeedLifecycleError("RIV-COMMS5-0015", "idempotency key conflicts with an existing lifecycle transition", seed_id=seed_id)
        return {
            "lifecycle_event_id": row[0], "seed_id": row[1], "transition": row[2],
            "replacement_seed_id": row[3], "actor": row[4], "reason": row[5],
            "classification": row[6], "correlation_id": row[7], "created_at": row[8],
            "idempotent_replay": True,
        }

    def cancel_draft(self, seed_id: UUID, *, actor: str, explicit_steward_confirmation: bool, reason: str, classification: str, correlation_id: UUID, idempotency_key: str) -> dict[str, object]:
        if actor != "steward" or explicit_steward_confirmation is not True:
            raise SeedLifecycleError("RIV-COMMS5-0009", "explicit Steward authorization is required", seed_id=seed_id)
        if not reason.strip() or len(reason.encode("utf-8")) > 2_000:
            raise SeedLifecycleError("RIV-COMMS5-0014", "cancellation reason is missing or exceeds its bound", seed_id=seed_id)
        with connect() as connection, connection.cursor() as cursor:
            replay = self._lifecycle_retry(cursor, idempotency_key, transition="cancelled", seed_id=seed_id, replacement_seed_id=None, actor=actor, reason=reason, classification=classification, correlation_id=correlation_id)
            if replay:
                return replay
            cursor.execute("SELECT status,objective_id FROM steward_seed_drafts WHERE seed_id=%s FOR UPDATE", (seed_id,))
            row = cursor.fetchone()
            if row is None:
                raise SeedLifecycleError("RIV-COMMS5-0006", "seed was not found", seed_id=seed_id)
            if row[0] == "cancelled":
                raise SeedLifecycleError("RIV-COMMS5-0014", "seed is already cancelled", seed_id=seed_id)
            if row[0] == "superseded":
                raise SeedLifecycleError("RIV-COMMS5-0014", "seed is superseded", seed_id=seed_id)
            if row[0] in {"confirmed", "promoted"} or row[1] is not None:
                raise SeedLifecycleError("RIV-COMMS5-0014", "seed is already promoted and its objective cannot be cancelled", seed_id=seed_id, objective_id=row[1])
            if row[0] != "draft":
                raise SeedLifecycleError("RIV-COMMS5-0014", "seed is not a cancellable draft", seed_id=seed_id)
            lifecycle_id = uuid4()
            cursor.execute(
                """INSERT INTO steward_seed_lifecycle_events
                   (lifecycle_event_id,seed_id,transition,actor,reason,classification,correlation_id,idempotency_key)
                   VALUES(%s,%s,'cancelled',%s,%s,%s,%s,%s)""",
                (lifecycle_id, seed_id, actor, reason, classification, correlation_id, idempotency_key),
            )
            cursor.execute(
                """UPDATE steward_seed_drafts
                   SET status='cancelled',cancelled_at=now(),cancellation_reason=%s,cancelled_by=%s
                   WHERE seed_id=%s""",
                (reason, actor, seed_id),
            )
            return {"lifecycle_event_id": lifecycle_id, "seed_id": seed_id, "transition": "cancelled", "actor": actor, "reason": reason, "classification": classification, "correlation_id": correlation_id, "idempotent_replay": False}

    def supersede_seed(self, seed_id: UUID, replacement_seed_id: UUID, *, actor: str, explicit_steward_confirmation: bool, reason: str, classification: str, correlation_id: UUID, idempotency_key: str) -> dict[str, object]:
        if actor != "steward" or explicit_steward_confirmation is not True:
            raise SeedLifecycleError("RIV-COMMS5-0009", "explicit Steward authorization is required", seed_id=seed_id)
        if seed_id == replacement_seed_id:
            raise SeedLifecycleError("RIV-COMMS5-0014", "a seed cannot supersede itself", seed_id=seed_id)
        if not reason.strip() or len(reason.encode("utf-8")) > 2_000:
            raise SeedLifecycleError("RIV-COMMS5-0014", "supersession reason is missing or exceeds its bound", seed_id=seed_id)
        with connect() as connection, connection.cursor() as cursor:
            replay = self._lifecycle_retry(cursor, idempotency_key, transition="superseded", seed_id=seed_id, replacement_seed_id=replacement_seed_id, actor=actor, reason=reason, classification=classification, correlation_id=correlation_id)
            if replay:
                return replay
            first, second = sorted((seed_id, replacement_seed_id), key=str)
            cursor.execute("SELECT seed_id,status,objective_id FROM steward_seed_drafts WHERE seed_id=%s FOR UPDATE", (first,))
            first_row = cursor.fetchone()
            cursor.execute("SELECT seed_id,status,objective_id FROM steward_seed_drafts WHERE seed_id=%s FOR UPDATE", (second,))
            second_row = cursor.fetchone()
            rows = {row[0]: row for row in (first_row, second_row) if row is not None}
            old = rows.get(seed_id)
            replacement = rows.get(replacement_seed_id)
            if old is None:
                raise SeedLifecycleError("RIV-COMMS5-0006", "seed was not found", seed_id=seed_id)
            if replacement is None:
                raise SeedLifecycleError("RIV-COMMS5-0014", "replacement seed was not found", seed_id=seed_id)
            if old[2] is not None or old[1] in {"confirmed", "promoted"}:
                raise SeedLifecycleError("RIV-COMMS5-0014", "promoted seed cannot be superseded", seed_id=seed_id, objective_id=old[2])
            if old[1] == "cancelled":
                raise SeedLifecycleError("RIV-COMMS5-0014", "cancelled seed cannot be superseded", seed_id=seed_id)
            if old[1] == "superseded":
                raise SeedLifecycleError("RIV-COMMS5-0014", "seed is already superseded", seed_id=seed_id)
            if replacement[1] != "draft" or replacement[2] is not None:
                raise SeedLifecycleError("RIV-COMMS5-0014", "replacement seed is not an eligible draft", seed_id=replacement_seed_id, objective_id=replacement[2])
            lifecycle_id = uuid4()
            cursor.execute(
                """INSERT INTO steward_seed_lifecycle_events
                   (lifecycle_event_id,seed_id,transition,replacement_seed_id,actor,reason,classification,correlation_id,idempotency_key)
                   VALUES(%s,%s,'superseded',%s,%s,%s,%s,%s,%s)""",
                (lifecycle_id, seed_id, replacement_seed_id, actor, reason, classification, correlation_id, idempotency_key),
            )
            cursor.execute("UPDATE steward_seed_drafts SET status='superseded',superseded_at=now(),replacement_seed_id=%s WHERE seed_id=%s", (replacement_seed_id, seed_id))
            cursor.execute("UPDATE steward_seed_drafts SET supersedes_seed_id=%s WHERE seed_id=%s", (seed_id, replacement_seed_id))
            return {"lifecycle_event_id": lifecycle_id, "seed_id": seed_id, "transition": "superseded", "replacement_seed_id": replacement_seed_id, "actor": actor, "reason": reason, "classification": classification, "correlation_id": correlation_id, "idempotent_replay": False}
