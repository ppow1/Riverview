"""Automatic semantic terminal-outcome bridge for Riverview Hermes lanes.

Version: 1.0.0

The Hermes project plugin calls this module from ``transform_llm_output``.
A model declares the outcome as part of its normal bounded-lane report; the
plugin owns parsing, validation, notification dispatch, and diagnostics. The
model never needs a second notification-tool call.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from typing import Any

from riverview.hermes_attention import submit_hermes_attention, submit_hermes_run_boundary

VERSION = "riverview-hermes-terminal-outcome-v1"
MARKER_RE = re.compile(
    r"(?P<whole><!--\s*RIVERVIEW_TERMINAL_OUTCOME\s*"
    r"(?P<payload>\{.*?\})\s*-->)",
    re.DOTALL,
)
ATTENTION_OUTCOMES = frozenset(
    {
        "READY_FOR_STEWARD_REVIEW",
        "BLOCKED_REQUIRES_STEWARD",
        "STEWARD_DECISION_REQUIRED",
    }
)
FAILURE_OUTCOMES = frozenset({"RETRYABLE_FAILURE", "TERMINAL_FAILURE"})
NON_ATTENTION_OUTCOMES = frozenset({"CONTINUE", "OBJECTIVE_COMPLETE", "COMPLETED_NO_ATTENTION"})
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE)
_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$", re.IGNORECASE)
_CHECKPOINT_RE = re.compile(r"^RIV-[A-Z0-9-]+$", re.IGNORECASE)
_LEADING_ARTICLES = frozenset({"a", "an", "the"})


def first_window_word(description: Any, fallback: Any = "Hermes") -> str:
    """Return the first safe human-facing word from a visible window title."""
    for candidate in (description, fallback, "Hermes"):
        if not isinstance(candidate, str):
            continue
        text = candidate.strip()
        while text:
            parts = text.split(None, 1)
            token = re.sub(r"^[^\w]+|[^\w]+$", "", parts[0], flags=re.UNICODE)
            remainder = parts[1] if len(parts) == 2 else ""
            if token and token.lower() not in _LEADING_ARTICLES:
                if _UUID_RE.fullmatch(token) or _SHA_RE.fullmatch(token) or _CHECKPOINT_RE.fullmatch(token):
                    break
                return token
            text = remainder.lstrip()
        # An unsafe or empty title must not cause us to speak its identifier.
    return "Hermes"


def attention_speech(outcome: str, *, window_description: Any = None, lane: Any = None) -> str:
    """Build the short spoken projection for an attention boundary."""
    word = first_window_word(window_description, lane)
    suffix = {
        "READY_FOR_STEWARD_REVIEW": "needs your review.",
        "BLOCKED_REQUIRES_STEWARD": "needs your assistance.",
        "STEWARD_DECISION_REQUIRED": "needs your decision.",
    }[outcome]
    return f"{word} {suffix}"


def _text(value: Any, field: str, *, limit: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError(f"RIV-HERMES-OUTCOME-0001: {field} is missing or unbounded.")
    return value.strip()


def _parse_marker(response_text: str) -> tuple[str, dict[str, Any] | None]:
    matches = list(MARKER_RE.finditer(response_text))
    if not matches:
        return response_text, None
    if len(matches) != 1:
        raise ValueError("RIV-HERMES-OUTCOME-0002: exactly one terminal outcome marker is required.")
    match = matches[0]
    try:
        envelope = json.loads(match.group("payload"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"RIV-HERMES-OUTCOME-0003: malformed terminal outcome JSON: {exc.msg}.") from exc
    if not isinstance(envelope, dict):
        raise TypeError("RIV-HERMES-OUTCOME-0004: terminal outcome must be a JSON object.")
    clean = (response_text[: match.start()] + response_text[match.end() :]).strip()
    return clean, envelope


def _diagnostic(response: str, message: str) -> str:
    suffix = f"\n\n[Hermes/Riverview terminal-attention diagnostic: {message}]"
    return f"{response.rstrip()}{suffix}" if response.strip() else suffix.lstrip()


def process_terminal_outcome(
    response_text: str,
    *,
    session_id: str,
    window_description: str | None = None,
    submit: Callable[..., Mapping[str, Any]] = submit_hermes_attention,
    run_boundary_submit: Callable[..., Mapping[str, Any]] = submit_hermes_run_boundary,
    notify: bool = True,
) -> str:
    """Process one normal Hermes final response and return report text.

    No marker means ordinary Hermes output and is left unchanged. A marker with
    CONTINUE or an objective-complete compatibility state is removed without
    attention; the Hermes core consumes CONTINUE before this post-response hook.
    Attention markers are submitted exactly once by the existing Riverview
    idempotency machinery. Failure dispositions remain visible diagnostics and
    never masquerade as successful completion.
    """
    if not isinstance(response_text, str):
        return response_text
    try:
        clean, envelope = _parse_marker(response_text)
    except ValueError as exc:
        return _diagnostic(response_text, str(exc))
    if envelope is None:
        return response_text

    try:
        outcome = _text(
            envelope.get("disposition", envelope.get("outcome")), "disposition"
        ).upper()
        if outcome in FAILURE_OUTCOMES:
            return _diagnostic(
                clean,
                f"structured objective disposition is {outcome}; no successful completion was recorded",
            )
        if outcome in NON_ATTENTION_OUTCOMES and not notify:
            return clean
        if outcome in NON_ATTENTION_OUTCOMES:
            boundary = run_boundary_submit(
                lane=_text(envelope.get("lane"), "lane"), outcome=outcome,
                checkpoint_id=_text(envelope.get("checkpoint_id"), "checkpoint_id"),
                evidence_ref=_text(envelope.get("evidence_ref"), "evidence_ref", limit=2000),
                session_id=session_id,
                transition_id=_text(envelope.get("terminal_transition_id"), "terminal_transition_id"),
                task_title=envelope.get("task_title"), roadmap_title=envelope.get("roadmap_title"),
                window_description=window_description, correlation_id=envelope.get("correlation_id"),
                resulting_sha=envelope.get("resulting_sha"),
            )
            delivery = boundary.get("delivery") if isinstance(boundary, Mapping) else None
            if not isinstance(delivery, Mapping):
                raise TypeError("RIV-HERMES-OUTCOME-0007: run-boundary notification returned no delivery result.")
            return clean
        if outcome not in ATTENTION_OUTCOMES:
            raise ValueError(
                "RIV-HERMES-OUTCOME-0005: unknown outcome; notification suppressed."
            )
        marker_session_id = envelope.get("hermes_session_id")
        if marker_session_id is not None and _text(marker_session_id, "hermes_session_id") != session_id:
            raise ValueError("RIV-HERMES-OUTCOME-0006: envelope session does not match Hermes session.")
        result = submit(
            lane=_text(envelope.get("lane"), "lane"),
            boundary=outcome,
            checkpoint_id=_text(envelope.get("checkpoint_id"), "checkpoint_id"),
            evidence_ref=_text(envelope.get("evidence_ref"), "evidence_ref", limit=2000),
            session_id=session_id,
            transition_id=_text(envelope.get("terminal_transition_id"), "terminal_transition_id"),
            objective_id=envelope.get("objective_id"),
            work_order_id=envelope.get("work_order_id"),
            summary=envelope.get("summary"),
            window_description=window_description,
        )
        delivery = result.get("delivery") if isinstance(result, Mapping) else None
        if not isinstance(delivery, Mapping):
            raise TypeError("RIV-HERMES-OUTCOME-0007: notification returned no delivery result.")
        if delivery.get("state") in {"failed", "error"} or delivery.get("success") is False:
            raise RuntimeError(
                f"RIV-HERMES-OUTCOME-0008: notification delivery failed: {dict(delivery)!r}."
            )
        return clean
    except Exception as exc:  # noqa: BLE001 - diagnostics must cover adapter failures
        return _diagnostic(clean, str(exc))


__all__ = ["VERSION", "attention_speech", "first_window_word", "process_terminal_outcome"]
