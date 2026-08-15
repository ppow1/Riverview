"""Bounded Grace consumption of durable Riverview reasoning responses.

Version: 0.1.0 | RV-008.4
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.river import Classification, RiverEvent

REASONING_PRODUCER = "chatgpt:riverview_001"
CONSUMER_ID = "grace"
CONSUMER_VERSION = "0.1.0"
RESPONSE_SCHEMA = "rv-008.4-response-v1"
RESPONSE_TYPES = frozenset({"advice", "escalation", "seed_result"})


@dataclass(frozen=True, slots=True)
class GraceResponseConsumption:
    consumption_id: UUID
    response_id: UUID
    request_id: UUID
    correlation_id: UUID
    objective_key: str
    outcome: str
    consumer_id: str
    consumer_version: str


def _append_event(cursor: Any, event: RiverEvent) -> None:
    cursor.execute(
        """
        INSERT INTO river_events(
            event_id,event_type,aggregate_type,aggregate_id,correlation_id,
            causation_id,idempotency_key,classification,payload,occurred_at
        ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
        ON CONFLICT(idempotency_key) DO NOTHING
        """,
        (
            event.event_id, event.event_type, event.aggregate_type,
            event.aggregate_id, event.correlation_id, event.causation_id,
            event.idempotency_key, event.classification.value,
            json.dumps(dict(event.payload)), event.occurred_at,
        ),
    )


def _response_outcome(response_type: str, escalation_required: bool) -> str:
    if response_type not in RESPONSE_TYPES:
        raise ValueError("RIV-GRC-0003: response type is unsupported.")
    if response_type == "advice" and not escalation_required:
        return "advisory_accepted"
    if response_type == "escalation" or escalation_required:
        return "escalation_required"
    return "no_authorized_transition"


def _validate_payload(response_type: str, payload: Any, classification: str) -> tuple[str, list[str], bool, str]:
    if classification != Classification.RIVER.value:
        raise ValueError("RIV-SEC-0001: response classification is not permitted.")
    if not isinstance(payload, dict) or payload.get("schema_version") != RESPONSE_SCHEMA:
        raise ValueError("RIV-GRC-0003: response schema is missing or incompatible.")
    summary = payload.get("summary")
    evidence_refs = payload.get("evidence_refs")
    escalation_required = payload.get("escalation_required")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("RIV-GRC-0003: required response summary is missing.")
    if not isinstance(evidence_refs, list) or not evidence_refs or any(
        not isinstance(ref, str) or not ref.strip() for ref in evidence_refs
    ):
        raise ValueError("RIV-GRC-0003: required response evidence is missing.")
    if not isinstance(escalation_required, bool):
        raise TypeError("RIV-GRC-0003: escalation flag is invalid.")
    outcome = _response_outcome(response_type, escalation_required)
    return summary, evidence_refs, escalation_required, outcome


class GraceResponseConsumer:
    """Consume one response and evaluate only declared bounded outcomes."""

    def consume(
        self,
        response_id: UUID,
        request_id: UUID,
        correlation_id: UUID,
        objective_key: str,
        *,
        consumer_version: str = CONSUMER_VERSION,
    ) -> GraceResponseConsumption:
        if not objective_key.strip() or not consumer_version.strip():
            raise ValueError("RIV-GRC-0003: objective and consumer version are required.")
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT consumption_id,response_id,request_id,correlation_id,
                       objective_key,outcome,consumer_id,consumer_version
                FROM grace_response_consumptions
                WHERE response_id=%s
                FOR UPDATE
                """,
                (response_id,),
            )
            existing = cursor.fetchone()
            if existing:
                result = GraceResponseConsumption(*existing)
                if (
                    result.request_id != request_id
                    or result.correlation_id != correlation_id
                    or result.objective_key != objective_key
                ):
                    raise ValueError("RIV-GRC-0003: response was already consumed for another lineage.")
                return result

            cursor.execute(
                """
                SELECT r.response_id,r.request_id,r.correlation_id,r.responder_id,
                       r.response_type,r.payload,r.classification,
                       m.correlation_id,m.completion_state
                FROM mailbox_responses r
                JOIN mailbox_messages m ON m.request_id=r.request_id
                WHERE r.response_id=%s
                FOR UPDATE OF r,m
                """,
                (response_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-GRC-0003: reasoning response is missing.")
            (
                stored_response_id, stored_request_id, stored_correlation,
                producer, response_type, payload, classification,
                request_correlation, completion_state,
            ) = row
            if stored_request_id != request_id or stored_correlation != correlation_id:
                raise ValueError("RIV-GRC-0003: response/request correlation does not match.")
            if request_correlation != correlation_id:
                raise ValueError("RIV-GRC-0003: mailbox correlation does not match response.")
            if producer != REASONING_PRODUCER:
                raise PermissionError("RIV-GRC-0003: response producer is not authorized.")
            if completion_state != "completed":
                raise RuntimeError("RIV-GRC-0003: response request is not complete.")
            summary, evidence_refs, escalation_required, outcome = _validate_payload(
                response_type, payload, classification
            )

            cursor.execute(
                "SELECT 1 FROM objectives WHERE objective_key=%s FOR UPDATE",
                (objective_key,),
            )
            if cursor.fetchone() is None:
                raise RuntimeError("RIV-GRC-0003: evaluation objective is missing.")
            cursor.execute(
                """
                SELECT o.objective_id,s.stage_id,s.status,s.readiness,
                       s.required_evidence,s.accepted_evidence
                FROM objective_stages s JOIN objectives o ON o.objective_id=s.objective_id
                WHERE o.objective_key=%s AND s.stage_key='response_return'
                FOR UPDATE
                """,
                (objective_key,),
            )
            stage = cursor.fetchone()
            if stage is None:
                raise RuntimeError("RIV-GRC-0003: response-return stage is missing.")
            objective_id, stage_id, stage_status, readiness, _required, accepted = stage
            if stage_status not in {"ready", "active"} or readiness not in {"ready", "satisfied"}:
                raise RuntimeError("RIV-GRC-0003: response-return stage is not eligible.")

            consumption_id = uuid4()
            evaluation = {
                "response_type": response_type,
                "summary": summary,
                "evidence_refs": evidence_refs,
                "escalation_required": escalation_required,
                "outcome": outcome,
                "authorized_transition": outcome == "advisory_accepted",
            }
            cursor.execute(
                """
                INSERT INTO grace_response_consumptions(
                    consumption_id,response_id,request_id,correlation_id,consumer_id,
                    consumer_version,objective_key,outcome,evaluation
                ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    consumption_id, stored_response_id, stored_request_id,
                    correlation_id, CONSUMER_ID, consumer_version, objective_key,
                    outcome, json.dumps(evaluation),
                ),
            )
            _append_event(
                cursor,
                RiverEvent(
                    event_type="grace.response.consumed",
                    aggregate_type="grace_response",
                    aggregate_id=response_id,
                    correlation_id=correlation_id,
                    causation_id=request_id,
                    idempotency_key=f"grace.response.consumed:{response_id}",
                    classification=Classification.RIVER,
                    payload={"objective_key": objective_key, "consumer_id": CONSUMER_ID},
                ),
            )
            _append_event(
                cursor,
                RiverEvent(
                    event_type="grace.response.evaluated",
                    aggregate_type="grace_response",
                    aggregate_id=response_id,
                    correlation_id=correlation_id,
                    causation_id=response_id,
                    idempotency_key=f"grace.response.evaluated:{response_id}",
                    classification=Classification.RIVER,
                    payload={"outcome": outcome, "objective_key": objective_key},
                ),
            )
            if outcome == "advisory_accepted":
                accepted_evidence = list(accepted or [])
                evidence_ref = f"response:{response_id}"
                if evidence_ref not in accepted_evidence:
                    accepted_evidence.append(evidence_ref)
                cursor.execute(
                    """
                    UPDATE objective_stages
                    SET status='completed',readiness='satisfied',accepted_evidence=%s::jsonb,
                        final_output=%s::jsonb,completed_at=now(),updated_at=now()
                    WHERE stage_id=%s
                    """,
                    (json.dumps(accepted_evidence), json.dumps(evaluation), stage_id),
                )
                cursor.execute(
                    """
                    UPDATE objectives SET status='completed',final_output=%s::jsonb,
                        completed_at=now(),updated_at=now()
                    WHERE objective_key=%s
                    """,
                    (json.dumps(evaluation), objective_key),
                )
                _append_event(
                    cursor,
                    RiverEvent(
                        event_type="grace.response.objective_advanced",
                        aggregate_type="objective",
                        aggregate_id=objective_id,
                        correlation_id=correlation_id,
                        causation_id=response_id,
                        idempotency_key=f"grace.response.objective_advanced:{response_id}",
                        classification=Classification.RIVER,
                        payload={"objective_key": objective_key, "evidence_ref": evidence_ref},
                    ),
                )
            return GraceResponseConsumption(
                consumption_id, stored_response_id, stored_request_id,
                correlation_id, objective_key, outcome, CONSUMER_ID, consumer_version,
            )
