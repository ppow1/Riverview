"""Bounded mailbox persistence for RV-008.2.

Version: 0.10.0

Mailbox rows are metadata and bounded payloads only. Protected material must be
represented by a safe local reference and never copied into ordinary River,
PostgreSQL, GitHub, or MCP paths.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from riverview.database import DatabaseConfig, connect
from riverview.river import Classification, RiverEvent

MAX_PAYLOAD_BYTES = 16_384
MAX_REFERENCE_LENGTH = 512
ALLOWED_CLASSIFICATIONS = frozenset(item.value for item in Classification)
REASONING_CONSUMER_ID = "chatgpt:riverview_001"


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
        if not actor_id.strip():
            raise ValueError("RIV-MCP-0008: acknowledgement actor is required.")
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                self._select_sql() + " WHERE request_id=%s FOR UPDATE",
                (request_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-MCP-0008: acknowledgement target is missing.")
            message = self._message(row)
            if (
                message.acknowledgement_state == "acknowledged"
                or message.completion_state != "pending"
            ):
                return message
            cursor.execute(
                """UPDATE mailbox_messages SET acknowledgement_state='acknowledged',acknowledged_at=COALESCE(acknowledged_at,now())
                   WHERE request_id=%s""",
                (request_id,),
            )
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

    def acknowledge_reasoning(self, request_id: UUID, correlation_id: UUID) -> MailboxMessage:
        message = self.get(request_id)
        _require_reasoning_message(message, correlation_id)
        return self.acknowledge(request_id, REASONING_CONSUMER_ID)

    def claim(self, request_id: UUID, owner_id: str, lease_seconds: int = 30) -> MailboxMessage:
        if not owner_id.strip() or not 1 <= lease_seconds <= 3_600:
            raise ValueError("RIV-MCP-0008: claim owner and lease are invalid.")
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(self._select_sql() + " WHERE request_id=%s FOR UPDATE", (request_id,))
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-MCP-0008: claim target is missing.")
            current = self._message(row)
            if current.completion_state != "pending":
                raise RuntimeError("RIV-MCP-0008: request is complete, expired, or missing.")
            if (
                current.claim_state == "claimed"
                and current.claim_owner == owner_id
                and current.claim_expires_at is not None
                and current.claim_expires_at > datetime.now(UTC)
            ):
                return current
            if current.claim_state == "claimed":
                raise RuntimeError("RIV-MCP-0008: request is already claimed by another owner.")
            cursor.execute(
                """UPDATE mailbox_messages SET claim_state='claimed',claim_owner=%s,claim_expires_at=now()+make_interval(secs=>%s),claimed_at=now()
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

    def claim_reasoning(self, request_id: UUID, correlation_id: UUID, lease_seconds: int = 120) -> MailboxMessage:
        message = self.get(request_id)
        _require_reasoning_message(message, correlation_id)
        if message.acknowledgement_state != "acknowledged":
            raise RuntimeError("RIV-MCP-0008: reasoning claim requires acknowledgement.")
        return self.claim(request_id, REASONING_CONSUMER_ID, lease_seconds)

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
            if not responder_id.strip() or not response_type.strip():
                raise ValueError("RIV-MCP-0008: responder and response type are required.")
            payload, payload_ref = _bounded(payload, payload_ref, "response")
            classification = _classification(classification)
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
                (
                    response_id,
                    json.dumps(payload) if payload is not None else None,
                    payload_ref,
                    request_id,
                ),
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

    def respond_reasoning(
        self,
        request_id: UUID,
        correlation_id: UUID,
        *,
        response_type: str,
        summary: str,
        evidence_refs: list[str],
        escalation_required: bool,
    ) -> MailboxResponse:
        message = self.get(request_id)
        if message is None:
            raise RuntimeError("RIV-MCP-0008: mailbox request is missing.")
        if message.correlation_id != correlation_id:
            raise ValueError("RIV-MCP-0008: mailbox correlation identity does not match the request.")
        if response_type not in {"advice", "escalation", "seed_result"}:
            raise ValueError("RIV-MCP-0007: response_type is outside the bounded reasoning envelope.")
        if not summary.strip() or len(summary) > 2_048:
            raise ValueError("RIV-MCP-0007: reasoning summary is empty or exceeds 2048 characters.")
        if len(evidence_refs) > 8 or any(not ref.strip() or len(ref) > MAX_REFERENCE_LENGTH for ref in evidence_refs):
            raise ValueError("RIV-MCP-0007: evidence_refs exceed the bounded reasoning envelope.")
        if message.completion_state == "completed":
            return self.respond(
                request_id,
                responder_id=REASONING_CONSUMER_ID,
                response_type=response_type,
                payload={
                    "schema_version": "rv-008.4-response-v1",
                    "summary": summary,
                    "evidence_refs": evidence_refs,
                    "escalation_required": escalation_required,
                },
                classification=Classification.RIVER.value,
            )
        _require_reasoning_message(message, correlation_id)
        if message.claim_state != "claimed" or message.claim_owner != REASONING_CONSUMER_ID:
            raise RuntimeError("RIV-MCP-0008: reasoning response requires the active reasoning claim.")
        return self.respond(
            request_id,
            responder_id=REASONING_CONSUMER_ID,
            response_type=response_type,
            payload={
                "schema_version": "rv-008.4-response-v1",
                "summary": summary,
                "evidence_refs": evidence_refs,
                "escalation_required": escalation_required,
            },
            classification=Classification.RIVER.value,
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

    def expire_and_escalate(self) -> list[UUID]:
        """Expire due requests and open one Steward escalation per request."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT request_id,correlation_id,causation_id FROM mailbox_messages
                   WHERE completion_state='pending' AND expires_at<=now() FOR UPDATE SKIP LOCKED"""
            )
            rows = cursor.fetchall()
            for request_id, correlation_id, causation_id in rows:
                cursor.execute(
                    """UPDATE mailbox_messages SET completion_state='expired',claim_state='expired',completed_at=now()
                       WHERE request_id=%s AND completion_state='pending'""",
                    (request_id,),
                )
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
                evidence = [f"mailbox:request:{request_id}", f"correlation:{correlation_id}"]
                cursor.execute(
                    """INSERT INTO steward_escalations(
                           escalation_id,mailbox_request_id,checkpoint_id,reason,state,evidence_refs)
                       VALUES(%s,%s,'RIV-MCP-0008','Mailbox request expired before bounded reasoning response.','open',%s::jsonb)
                       ON CONFLICT DO NOTHING""",
                    (uuid4(), request_id, json.dumps(evidence)),
                )
                _event(
                    cursor,
                    RiverEvent(
                        event_type="mailbox.timeout.escalated",
                        aggregate_type="mailbox_request",
                        aggregate_id=request_id,
                        correlation_id=correlation_id,
                        causation_id=request_id,
                        idempotency_key=f"mailbox.timeout.escalated:{request_id}",
                        payload={"checkpoint_id": "RIV-MCP-0008"},
                    ),
                )
            return [row[0] for row in rows]

    @staticmethod
    def _locked(cursor: Any, request_id: UUID) -> MailboxMessage:
        cursor.execute(
            MailboxStore._select_sql() + " WHERE request_id=%s FOR UPDATE", (request_id,)
        )
        return MailboxStore._message(cursor.fetchone())


def _require_reasoning_message(message: MailboxMessage | None, correlation_id: UUID) -> MailboxMessage:
    if message is None:
        raise RuntimeError("RIV-MCP-0008: mailbox request is missing.")
    if message.classification != Classification.RIVER.value:
        raise ValueError("RIV-SEC-0001: protected mailbox classification is not available to reasoning.")
    if message.correlation_id != correlation_id:
        raise ValueError("RIV-MCP-0008: mailbox correlation identity does not match the request.")
    if message.completion_state != "pending":
        raise RuntimeError("RIV-MCP-0008: mailbox request is not pending.")
    return message
