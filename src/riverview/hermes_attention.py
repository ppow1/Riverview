"""Shared Hermes-to-Riverview Steward-attention boundary.

Version: 0.1.0

This module is the small adapter used by the project Hermes plugin. Hermes does
not own Riverview lifecycle state; it submits one explicit semantic terminal
boundary to Riverview, which owns persistence, idempotency, and delivery.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from riverview.notifications import NotificationStore
from riverview.notifications_audio import deliver_steward_notification
from riverview.river.events import Classification, RiverEvent
from riverview.river.store import EventStore

VERSION = "riverview-hermes-attention-v1"
_ALLOWED_BOUNDARIES = {
    "READY_FOR_STEWARD_REVIEW": "ready_for_steward_review",
    "BLOCKED_REQUIRES_STEWARD": "blocked_requires_steward",
    "STEWARD_DECISION_REQUIRED": "blocked_requires_steward",
}
_MAX_FIELD = 240


def _display_name(*values: Any) -> str:
    for value in values:
        if not isinstance(value, str):
            continue
        for token in value.strip().split():
            token = token.strip(".,:;!?()[]{}")
            if token and token.casefold() not in {"a", "an", "the"} and not token.startswith("RIV-"):
                return token[:_MAX_FIELD]
    return "Riverview Hermes"


def _display_title(task_title: Any, roadmap_title: Any, window_description: Any, lane: str) -> str:
    for value in (task_title, roadmap_title):
        if isinstance(value, str) and value.strip():
            return value.strip()[:_MAX_FIELD]
    return _display_name(window_description, lane)


def _required_text(value: Any, field: str, *, max_length: int = _MAX_FIELD) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > max_length:
        raise ValueError(f"RIV-HERMES-ATTN-0001: {field} is missing or unbounded.")
    return value.strip()


def _optional_text(value: Any, field: str) -> str | None:
    if value is None or value == "":
        return None
    return _required_text(value, field)


def submit_hermes_attention(
    *,
    lane: str,
    boundary: str,
    checkpoint_id: str,
    evidence_ref: str,
    session_id: str,
    transition_id: str,
    objective_id: str | None = None,
    work_order_id: str | None = None,
    summary: str | None = None,
    window_description: str | None = None,
    store: NotificationStore | None = None,
    deliver=deliver_steward_notification,
) -> dict[str, Any]:
    """Persist and deliver one explicit Hermes terminal attention boundary.

    ``transition_id`` is the caller's durable terminal-transition identity. It
    is required in the idempotency key so rendering, retrying the tool call, or
    restarting a UI cannot ring twice for one transition. This function does
    not acknowledge or accept the resulting notification.
    """
    lane_value = _required_text(lane, "lane")
    boundary_value = _required_text(boundary, "boundary").upper()
    notification_type = _ALLOWED_BOUNDARIES.get(boundary_value)
    if notification_type is None:
        raise ValueError("RIV-HERMES-ATTN-0002: boundary is not a Steward attention boundary.")
    checkpoint_value = _required_text(checkpoint_id, "checkpoint_id")
    if not checkpoint_value.startswith("RIV-"):
        raise ValueError("RIV-HERMES-ATTN-0003: checkpoint_id must begin with 'RIV-'.")
    evidence_value = _required_text(evidence_ref, "evidence_ref", max_length=512)
    session_value = _required_text(session_id, "session_id")
    transition_value = _required_text(transition_id, "transition_id")
    objective_value = _optional_text(objective_id, "objective_id")
    work_order_value = _optional_text(work_order_id, "work_order_id")

    if window_description:
        title = _display_name(window_description, lane_value)
        suffix = {"ready_for_steward_review": "needs your review.", "blocked_requires_steward": "needs your assistance."}[notification_type]
        summary_value = f"{title} {suffix}"
    elif summary is None:
        summary_value = (
            f"{lane_value} work is ready for your review."
            if notification_type == "ready_for_steward_review"
            else f"{lane_value} work is blocked and needs your decision."
        )
    else:
        summary_value = _required_text(summary, "summary", max_length=1000)

    idempotency_key = f"hermes.steward_attention:{lane_value}:{boundary_value}:{transition_value}"
    evidence_refs = [
        f"lane:{lane_value}",
        f"session:{session_value}",
        f"transition:{transition_value}",
        evidence_value,
    ]
    if objective_value:
        evidence_refs.append(f"objective:{objective_value}")
    if work_order_value:
        evidence_refs.append(f"work_order:{work_order_value}")

    notification_id = (store or NotificationStore()).emit(
        idempotency_key=idempotency_key,
        notification_type=notification_type,
        checkpoint_id=checkpoint_value,
        summary=summary_value,
        evidence_refs=tuple(evidence_refs),
    )
    delivery = deliver(notification_id)
    return {
        "schema_version": VERSION,
        "notification_id": str(notification_id),
        "idempotency_key": idempotency_key,
        "notification_type": notification_type,
        "checkpoint_id": checkpoint_value,
        "lane": lane_value,
        "delivery": delivery,
        "acknowledged": bool(delivery.get("acknowledged", False)),
        "institutionally_accepted": False,
    }


def submit_hermes_run_boundary(
    *,
    lane: str,
    outcome: str,
    checkpoint_id: str,
    evidence_ref: str,
    session_id: str,
    transition_id: str,
    task_title: str | None = None,
    roadmap_title: str | None = None,
    window_description: str | None = None,
    correlation_id: str | None = None,
    run_started_at: str | None = None,
    run_completed_at: str | None = None,
    resulting_sha: str | None = None,
    store: NotificationStore | None = None,
    event_store: EventStore | None = None,
    deliver=deliver_steward_notification,
) -> dict[str, Any]:
    """Record one completed Hermes invocation independently of task outcome."""
    lane_value = _required_text(lane, "lane")
    outcome_value = _required_text(outcome, "outcome").upper()
    if outcome_value not in {"CONTINUE", "OBJECTIVE_COMPLETE", "COMPLETED_NO_ATTENTION", "READY_FOR_STEWARD_REVIEW", "BLOCKED_REQUIRES_STEWARD", "STEWARD_DECISION_REQUIRED"}:
        raise ValueError("RIV-HERMES-ATTN-0004: run outcome is not a valid terminal envelope outcome.")
    checkpoint_value = _required_text(checkpoint_id, "checkpoint_id")
    evidence_value = _required_text(evidence_ref, "evidence_ref", max_length=512)
    session_value = _required_text(session_id, "session_id")
    transition_value = _required_text(transition_id, "transition_id")
    title = _display_title(task_title, roadmap_title, window_description, lane_value)
    suffix = "continuation remains." if outcome_value == "CONTINUE" else "completed."
    summary = f"{title} iteration complete; {suffix}"
    key = f"hermes.run_boundary:{session_value}:{transition_value}"
    refs = [f"lane:{lane_value}", f"session:{session_value}", f"transition:{transition_value}", evidence_value]
    if correlation_id:
        refs.append(f"correlation:{_required_text(correlation_id, 'correlation_id')}")
    notification_id = (store or NotificationStore()).emit(
        idempotency_key=key, notification_type="important_completion", checkpoint_id=checkpoint_value,
        summary=summary, evidence_refs=tuple(refs),
    )
    event_id = UUID(notification_id.hex[:8] + "-" + notification_id.hex[8:12] + "-4" + notification_id.hex[13:16] + "-8" + notification_id.hex[17:20] + "-" + notification_id.hex[20:32])
    delivery = deliver(notification_id)
    delivery_status = "delivered" if delivery.get("delivered") is True or delivery.get("state") == "delivered" else str(delivery.get("state") or "unknown")
    event = (event_store or EventStore()).append(RiverEvent(
        event_type="hermes.run_boundary.completed", aggregate_type="hermes_run", aggregate_id=notification_id,
        correlation_id=UUID(correlation_id) if correlation_id else UUID(int=0),
        idempotency_key=key, classification=Classification.INTERNAL,
        payload={"task_title": title, "outcome": outcome_value, "notification_id": str(notification_id), "notification_class": "informational", "run_started_at": run_started_at, "run_completed_at": run_completed_at, "resulting_sha": resulting_sha, "delivery_status": delivery_status},
        event_id=event_id,
    ))
    return {"schema_version": VERSION, "notification_id": str(notification_id), "idempotency_key": key, "notification_type": "important_completion", "task_title": title, "summary": summary, "event_id": str(event.event_id), "delivery": delivery, "action_required": False, "acknowledged": bool(delivery.get("acknowledged", False)), "institutionally_accepted": False}


__all__ = ["VERSION", "submit_hermes_attention", "submit_hermes_run_boundary"]
