"""Bounded Steward seed draft and promotion contract for RV-008.5."""

from __future__ import annotations

from uuid import UUID, uuid4

from riverview.database import connect
from riverview.grace.objectives import ObjectiveStore, StageSpec
from riverview.river.events import Classification, RiverEvent
from riverview.river.store import EventStore

DESIGNATED_CONSUMER = "chatgpt:riverview_001"
MAX_SEED_BYTES = 8_000


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
            cursor.execute("SELECT seed_id FROM steward_seed_drafts WHERE idempotency_key=%s", (idempotency_key,))
            return cursor.fetchone()[0]

    def confirm_and_promote(self, seed_id: UUID, *, confirmer: str) -> UUID:
        if confirmer != "steward":
            raise PermissionError("RIV-0085-0002: only the Steward may promote a seed draft.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT correlation_id,seed_text,status,objective_id FROM steward_seed_drafts WHERE seed_id=%s FOR UPDATE",
                (seed_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-0085-0002: seed draft is not promotable.")
            if row[2] == "promoted" and row[3] is not None:
                return row[3]
            if row[2] != "draft":
                raise RuntimeError("RIV-0085-0002: seed draft is not promotable.")
            cursor.execute(
                "UPDATE steward_seed_drafts SET status='confirmed',confirmed_at=now() WHERE seed_id=%s",
                (seed_id,),
            )
        objective_id = ObjectiveStore().create(
            f"seed:{seed_id}",
            "Steward seed draft",
            row[1],
            [StageSpec("validate", "Validate steward seed", "Grace validates the bounded seed before work formation.", ("seed:confirmed",))],
            owner_id="grace", requested_by="steward", correlation_id=row[0],
        )
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE steward_seed_drafts SET status='promoted',objective_id=%s,promoted_at=now() WHERE seed_id=%s", (objective_id, seed_id))
        EventStore().append(RiverEvent(
            event_type="steward.seed.promoted", aggregate_type="objective", aggregate_id=objective_id,
            correlation_id=row[0], causation_id=seed_id,
            idempotency_key=f"steward.seed.promoted:{seed_id}", classification=Classification.RIVER,
            payload={"seed_id": str(seed_id), "objective_id": str(objective_id), "status": "promoted"},
        ))
        return objective_id
