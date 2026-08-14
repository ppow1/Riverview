"""Live PostgreSQL acceptance for RV-005.1.

Version: 0.1.0
"""

from __future__ import annotations

import json

from riverview.grace.authority import GraceAuthority


def acceptance() -> dict[str, object]:
    authority = GraceAuthority()
    identity = authority.identity()

    allowed = authority.evaluate(
        "evaluate_progression",
        "declared_dependencies_and_evidence",
        persist=True,
        evidence_refs=["acceptance:rv0051"],
    )
    denied = authority.evaluate(
        "arbitrary_sql",
        "all",
        persist=True,
        evidence_refs=["acceptance:rv0051"],
    )
    unknown = authority.evaluate(
        "invented_capability",
        "all",
        persist=True,
        evidence_refs=["acceptance:rv0051"],
    )
    conversation = authority.evaluate(
        "infer_authority_from_conversation",
        "all",
        persist=True,
        evidence_refs=["acceptance:rv0051"],
    )

    if not identity["enabled"]:
        raise RuntimeError("RIV-GRC-0001: Grace identity is disabled.")
    if allowed.decision != "allow":
        raise RuntimeError("RIV-GRC-0001: allowed progression evaluation was rejected.")
    if denied.decision != "deny":
        raise RuntimeError("RIV-GRC-0001: arbitrary SQL was not denied.")
    if unknown.decision != "escalate":
        raise RuntimeError("RIV-GRC-0001: unknown capability did not escalate.")
    if conversation.decision != "deny":
        raise RuntimeError("RIV-GRC-0001: conversation-derived authority was not denied.")

    return {
        "status": "healthy",
        "grace_id": identity["grace_id"],
        "role": identity["role"],
        "authority_version": identity["authority_version"],
        "allowed_progression_evaluation": allowed.decision,
        "arbitrary_sql": denied.decision,
        "unknown_capability": unknown.decision,
        "conversation_authority": conversation.decision,
    }


if __name__ == "__main__":
    print(json.dumps(acceptance(), indent=2, sort_keys=True))