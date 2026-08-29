"""Hermes project-plugin bridge for Riverview Steward attention.

Version: 0.1.0
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
_SOURCE_ROOT = _PLUGIN_ROOT / "src"
if _SOURCE_ROOT.is_dir() and str(_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SOURCE_ROOT))



_SCHEMA = {
    "name": "riverview_steward_attention",
    "description": (
        "Record and deliver exactly one Riverview Steward attention notification "
        "for a genuine bounded engineering terminal boundary. Do not use for "
        "ordinary progress, intermediate tests, retries, or successful steps."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "lane": {"type": "string", "description": "Short engineering lane attribution."},
            "boundary": {
                "type": "string",
                "enum": [
                    "READY_FOR_STEWARD_REVIEW",
                    "BLOCKED_REQUIRES_STEWARD",
                    "STEWARD_DECISION_REQUIRED",
                ],
                "description": "The genuine terminal attention boundary.",
            },
            "checkpoint_id": {"type": "string", "description": "Riverview RIV-* checkpoint."},
            "evidence_ref": {"type": "string", "description": "Durable evidence reference."},
            "session_id": {"type": "string", "description": "Hermes session identity."},
            "transition_id": {
                "type": "string",
                "description": "Stable identity of this terminal transition; reuse on retry.",
            },
            "objective_id": {"type": "string", "description": "Optional Riverview objective identity."},
            "work_order_id": {"type": "string", "description": "Optional Riverview work-order identity."},
            "summary": {"type": "string", "description": "Optional short spoken summary."},
        },
        "required": [
            "lane",
            "boundary",
            "checkpoint_id",
            "evidence_ref",
            "session_id",
            "transition_id",
        ],
        "additionalProperties": False,
    },
}


def _handle_attention(args: dict[str, Any], **_: Any) -> str:
    # Keep plugin discovery usable in a Hermes environment that does not carry
    # Riverview's PostgreSQL dependency; import only when the boundary is used.
    from riverview.hermes_attention import submit_hermes_attention

    result = submit_hermes_attention(
        lane=args.get("lane"),
        boundary=args.get("boundary"),
        checkpoint_id=args.get("checkpoint_id"),
        evidence_ref=args.get("evidence_ref"),
        session_id=args.get("session_id"),
        transition_id=args.get("transition_id"),
        objective_id=args.get("objective_id"),
        work_order_id=args.get("work_order_id"),
        summary=args.get("summary"),
    )
    return json.dumps(result, ensure_ascii=False, sort_keys=True)


def _transform_riverview_outcome(response_text: str, *, session_id: str, **kwargs: Any) -> str:
    """Process one final Riverview terminal envelope, when project opt-in is active."""
    if os.environ.get("RIVERVIEW_HERMES_ENGINEERING") != "1":
        return response_text
    from riverview.hermes_terminal_outcome import process_terminal_outcome

    return process_terminal_outcome(
        response_text,
        session_id=session_id,
        window_description=kwargs.get("window_description") or kwargs.get("task_title"),
        notify=False,
    )


def _post_response_rendered(response_text: str, *, session_id: str, **kwargs: Any) -> None:
    """Render the waiting banner, flush it, then notify at the idle boundary."""
    if os.environ.get("RIVERVIEW_HERMES_ENGINEERING") != "1":
        return
    from riverview.hermes_terminal_outcome import _parse_marker, _text
    from riverview.hermes_attention import submit_hermes_run_boundary

    _, envelope = _parse_marker(response_text)
    if envelope is None:
        return
    outcome = _text(envelope.get("disposition", envelope.get("outcome")), "disposition").upper()
    if outcome not in {"CONTINUE", "OBJECTIVE_COMPLETE", "COMPLETED_NO_ATTENTION", "READY_FOR_STEWARD_REVIEW", "BLOCKED_REQUIRES_STEWARD", "STEWARD_DECISION_REQUIRED"}:
        return
    title = envelope.get("task_title") or kwargs.get("task_title") or envelope.get("lane") or "Riverview Hermes"
    labels = {
        "CONTINUE": ("HERMES ITERATION COMPLETE", "CONTINUATION REMAINS · WAITING"),
        "COMPLETED_NO_ATTENTION": ("TASK COMPLETE", "NO STEWARD ACTION REQUIRED"),
        "OBJECTIVE_COMPLETE": ("OBJECTIVE COMPLETE", "NO STEWARD ACTION REQUIRED"),
        "READY_FOR_STEWARD_REVIEW": ("HERMES WAITING", "READY FOR STEWARD REVIEW"),
        "BLOCKED_REQUIRES_STEWARD": ("HERMES WAITING", "BLOCKED · STEWARD INPUT REQUIRED"),
        "STEWARD_DECISION_REQUIRED": ("HERMES WAITING", "STEWARD DECISION REQUIRED"),
    }
    heading, state = labels[outcome]
    print(f"\n\n{'═' * 72}\n  {heading}\n  {title}\n  {state}\n{'═' * 72}")
    sys.stdout.flush()
    submit_hermes_run_boundary(
        lane=_text(envelope.get("lane"), "lane"), outcome=outcome,
        checkpoint_id=_text(envelope.get("checkpoint_id"), "checkpoint_id"),
        evidence_ref=_text(envelope.get("evidence_ref"), "evidence_ref", limit=2000),
        session_id=session_id, transition_id=_text(envelope.get("terminal_transition_id"), "terminal_transition_id"),
        task_title=envelope.get("task_title") or kwargs.get("task_title"),
        roadmap_title=envelope.get("roadmap_title"), window_description=kwargs.get("window_description"),
        correlation_id=envelope.get("correlation_id"), resulting_sha=envelope.get("resulting_sha"),
    )


def register(ctx) -> None:
    # Opt the Hermes core into the same structured envelope that this bridge
    # consumes.  The core remains Riverview-import-free; the plugin is the
    # project-owned activation boundary.
    os.environ.setdefault("HERMES_OBJECTIVE_CONTINUITY", "1")
    os.environ.setdefault("RIVERVIEW_HERMES_ENGINEERING", "1")
    ctx.register_hook("transform_llm_output", _transform_riverview_outcome)
    ctx.register_hook("post_response_rendered", _post_response_rendered)
    ctx.register_tool(
        name="riverview_steward_attention",
        toolset="riverview",
        schema=_SCHEMA,
        handler=_handle_attention,
        description="Riverview terminal-boundary Steward attention bridge.",
    )
