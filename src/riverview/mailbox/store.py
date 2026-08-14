"""Bounded mailbox persistence for RV-008.2.

Version: 0.10.0

Mailbox rows are metadata and bounded payloads only. Protected material must be
represented by a safe local reference and never copied into ordinary River,
PostgreSQL, GitHub, or MCP paths.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from riverview.database import DatabaseConfig, connect
from riverview.river import Classification, RiverEvent

MAX_PAYLOAD_BYTES = 16_384
MAX_REFERENCE_LENGTH = 512
ALLOWED_CLASSIFICATIONS = frozenset(item.value for item in Classification)


@dataclass(frozen=True, slots=True)
class MailboxMessage:
    request_id: UUID
    sender_id: str
    requester_id: str
    correlation_id: UUID
    causation_id: UUID | None
    message_type: str
    payload: Any | None
    payload_ref: str | None
    classification: str
    acknowledgement_state: str
    claim_state: str
    claim_owner: str | None
    claim_expires_at: datetime | None
    claimed_at: datetime | None
    response_id: UUID | None
    completion_state: str
    idempotency_key: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class MailboxResponse:
    response_id: UUID
    request_id: UUID
    correlation_id: UUID
    causation_id: UUID
    responder_id: str
    response_type: str
    payload: Any | None
    payload_ref: str | None
    classification: str


def _bounded(value: Any | None, reference: str | None, label: str) -> tuple[Any | None, str | None]:
    if (value is None) == (reference is None):
        raise ValueError(f"RIV-MCP-0007: exactly one {label} or {label}_ref is required.")
    if reference is not None:
        if not reference.strip() or len(reference) > MAX_REFERENCE_LENGTH:
            raise ValueError(f"RIV-MCP-0007: {label}_ref is empty or exceeds the safe bound.")
        return None, reference
    encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError(f"RIV-MCP-0007: {label} exceeds {MAX_PAYLOAD_BYTES} bytes.")
    return value, None


def _classification(value: str) -> str:
    if value not in ALLOWED_CLASSIFICATIONS:
        raise ValueError("RIV-SEC-0001: protected or unsupported classification is not allowed.")
    return value


def _event(cursor: Any, event: RiverEvent) -> None:
    cursor.execute(
        """
        INSERT INTO river_events(
            event_id,event_type,aggregate_type,aggregate_id,correlation_id,
            causation_id,idempotency_key,classification,payload,occurred_at
        ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
        ON CONFLICT(idempotency_key) DO NOTHING
        """,
        (
            event.event_id,
            event.event_type,
            event.aggregate_type,
            event.aggregate_id,
            event.correlation_id,
            event.causation_id,
            event.idempotency_key,
            event.classification.value,
            json.dumps(dict(event.payload)),
            event.occurred_at,
        ),
    )


class MailboxStore:
    """Create and advance one correlated mailbox lineage at a time."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    @staticmethod
    def _message(row: tuple[Any, ...]) -> MailboxMessage:
        return MailboxMessage(*row)

    def submit(
        self,
        *,
        sender_id: str,
        requester_id: str,
        message_type: str,
        idempotency_key: str,
        payload: Any | None = None,
        payload_ref: str | None = None,
        classification: str = Classification.RIVER.value,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        ttl_seconds: int = 300,
    ) -> MailboxMessage:
        if (
            not sender_id.strip()
            or not requester_id.strip()
            or not message_type.strip()
            or not idempotency_key.strip()
        ):
            raise ValueError(
                "RIV-MCP-0007: sender, requester, type, and idempotency key are required."
            )
        if not 1 <= ttl_seconds <= 86_400:
            raise ValueError("RIV-MCP-0007: expiry must be between 1 second and 24 hours.")
        payload, payload_ref = _bounded(payload, payload_ref, "payload")
        classification = _classification(classification)
        request_id = uuid4()
        correlation_id = correlation_id or uuid4()
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO mailbox_messages(
                    request_id,sender_id,requester_id,correlation_id,causation_id,message_type,
                    payload,payload_ref,classification,idempotency_key,expires_at
                ) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,now()+make_interval(secs=>%s))
                ON CONFLICT(idempotency_key) DO NOTHING
                """,
                (
                    request_id,
                    sender_id,
                    requester_id,
                    correlation_id,
                    causation_id,
                    message_type,
                    json.dumps(payload) if payload is not None else None,
                    payload_ref,
                    classification,
                    idempotency_key,
                    ttl_seconds,
                ),
            )
            cursor.execute(self._select_sql() + " WHERE idempotency_key=%s", (idempotency_key,))
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError(
                    "RIV-MCP-0008: idempotent mailbox insert could not be reconciled."
                )
            message = self._message(row)
            _event(
                cursor,
                RiverEvent(
                    event_type="mailbox.request.accepted",
                    aggregate_type="mailbox_request",
                    aggregate_id=message.request_id,
                    correlation_id=message.correlation_id,
                    causation_id=message.causation_id,
                    idempotency_key=f"mailbox.request.accepted:{message.request_id}",
                    classification=Classification(classification),
                    payload={
                        "message_type": message.message_type,
                        "requester_id": message.requester_id,
                    },
                ),
            )
            return message

    @staticmethod
    def _select_sql() -> str:
        return """SELECT request_id,sender_id,requester_id,correlation_id,causation_id,message_type,
            payload,payload_ref,classification,acknowledgement_state,claim_state,claim_owner,
            claim_expires_at,claimed_at,response_id,completion_state,idempotency_key,created_at,expires_at
            FROM mailbox_messages"""

    def get(self, request_id: UUID) -> MailboxMessage | None:
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(self._select_sql() + " WHERE request_id=%s", (request_id,))
            row = cursor.fetchone()
            return self._message(row) if row else None

    def acknowledge(self, request_id: UUID, actor_id: str) -> MailboxMessage:
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE mailbox_messages SET acknowledgement_state='acknowledged',acknowledged_at=COALESCE(acknowledged_at,now())
                   WHERE request_id=%s AND completion_state='pending' RETURNING request_id""",
                (request_id,),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-MCP-0008: acknowledgement target is missing or complete.")
            message = self._locked(cursor, request_id)
            _event(
                cursor,
                RiverEvent(
                    event_type="mailbox.request.acknowledged",
                    aggregate_type="mailbox_request",
                    aggregate_id=request_id,
                    correlation_id=message.correlation_id,
                    idempotency_key=f"mailbox.request.acknowledged:{request_id}",
                    causation_id=message.causation_id or request_id,
                    payload={"actor_id": actor_id},
                ),
            )
            return message

    def claim(self, request_id: UUID, owner_id: str, lease_seconds: int = 30) -> MailboxMessage:
        if not owner_id.strip() or not 1 <= lease_seconds <= 3_600:
            raise ValueError("RIV-MCP-0008: claim owner and lease are invalid.")
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE mailbox_messages SET claim_state='claimed',claim_owner=%s,claim_expires_at=now()+make_interval(secs=>%s),claimed_at=COALESCE(claimed_at,now())
                   WHERE request_id=%s AND completion_state='pending' AND (claim_state IN ('unclaimed','released','expired') OR claim_expires_at<now())""",
                (owner_id, lease_seconds, request_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(
                    "RIV-MCP-0008: request is already claimed, complete, expired, or missing."
                )
            message = self._locked(cursor, request_id)
            _event(
                cursor,
                RiverEvent(
                    event_type="mailbox.request.claimed",
                    aggregate_type="mailbox_request",
                    aggregate_id=request_id,
                    correlation_id=message.correlation_id,
                    causation_id=message.causation_id or request_id,
                    idempotency_key=f"mailbox.request.claimed:{request_id}:{owner_id}:{message.claimed_at}",
                    payload={"owner_id": owner_id},
                ),
            )
            return message

    def respond(
        self,
        request_id: UUID,
        *,
        responder_id: str,
        response_type: str,
        payload: Any | None = None,
        payload_ref: str | None = None,
        classification: str = Classification.RIVER.value,
    ) -> MailboxResponse:
        payload, payload_ref = _bounded(payload, payload_ref, "response")
        classification = _classification(classification)
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(self._select_sql() + " WHERE request_id=%s FOR UPDATE", (request_id,))
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-MCP-0008: response target is missing.")
            request = self._message(row)
            if request.completion_state == "completed":
                cursor.execute(
                    "SELECT response_id,request_id,correlation_id,causation_id,responder_id,response_type,payload,payload_ref,classification FROM mailbox_responses WHERE request_id=%s",
                    (request_id,),
                )
                return MailboxResponse(*cursor.fetchone())
            if request.claim_state != "claimed":
                raise RuntimeError("RIV-MCP-0008: only a claimed request may be completed.")
            response_id = uuid4()
            cursor.execute(
                """INSERT INTO mailbox_responses(response_id,request_id,correlation_id,causation_id,responder_id,response_type,payload,payload_ref,classification)
                   VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)""",
                (
                    response_id,
                    request_id,
                    request.correlation_id,
                    request_id,
                    responder_id,
                    response_type,
                    json.dumps(payload) if payload is not None else None,
                    payload_ref,
                    classification,
                ),
            )
            cursor.execute(
                """UPDATE mailbox_messages SET response_id=%s,response_payload=%s::jsonb,response_payload_ref=%s,
                   completion_state='completed',claim_state='released',completed_at=now(),claim_expires_at=NULL
                   WHERE request_id=%s""",
                (response_id, json.dumps(payload) if payload is not None else None, payload_ref, request_id),
            )
            _event(
                cursor,
                RiverEvent(
                    event_type="mailbox.response.completed",
                    aggregate_type="mailbox_request",
                    aggregate_id=request_id,
                    correlation_id=request.correlation_id,
                    causation_id=request_id,
                    idempotency_key=f"mailbox.response.completed:{request_id}",
                    classification=Classification(classification),
                    payload={"response_id": str(response_id), "response_type": response_type},
                ),
            )
            return MailboxResponse(
                response_id,
                request_id,
                request.correlation_id,
                request_id,
                responder_id,
                response_type,
                payload,
                payload_ref,
                classification,
            )

    def expire(self) -> list[UUID]:
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE mailbox_messages SET completion_state='expired',claim_state='expired',completed_at=now() WHERE completion_state='pending' AND expires_at<=now() RETURNING request_id,correlation_id,causation_id"
            )
            rows = cursor.fetchall()
            for request_id, correlation_id, causation_id in rows:
                _event(
                    cursor,
                    RiverEvent(
                        event_type="mailbox.request.expired",
                        aggregate_type="mailbox_request",
                        aggregate_id=request_id,
                        correlation_id=correlation_id,
                        causation_id=causation_id or request_id,
                        idempotency_key=f"mailbox.request.expired:{request_id}",
                        payload={},
                    ),
                )
            return [row[0] for row in rows]

    @staticmethod
    def _locked(cursor: Any, request_id: UUID) -> MailboxMessage:
        cursor.execute(
            MailboxStore._select_sql() + " WHERE request_id=%s FOR UPDATE", (request_id,)
        )
        return MailboxStore._message(cursor.fetchone())
