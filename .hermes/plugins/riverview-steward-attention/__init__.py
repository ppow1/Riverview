"""Hermes project-plugin bridge for Riverview Steward attention.

Version: 0.1.0
"""

from __future__ import annotations

import json
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


def register(ctx) -> None:
    ctx.register_tool(
        name="riverview_steward_attention",
        toolset="riverview",
        schema=_SCHEMA,
        handler=_handle_attention,
        description="Riverview terminal-boundary Steward attention bridge.",
    )
