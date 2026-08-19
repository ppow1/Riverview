from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from riverview.residents.direct_grace import DirectGraceApproval, DirectGraceApprovalError


def contract() -> dict[str, object]:
    return {
        "repository_identity": "ppow1/Riverview",
        "repository_root": str(Path.cwd()),
        "expected_base_sha": "a" * 40,
        "bounded_instruction": "Inspect the repository read-only and return structured evidence.",
        "allowed_paths": ["AI_HINTS.md", "docs/governance/RIVERVIEW_CHARTER.md"],
        "acceptance_criteria": ["return exact Git HEAD", "change zero files"],
        "evidence_requirements": ["AI_HINTS readable", "Charter readable"],
        "capability_name": "codex.engineering.v1",
        "action_type": "codex.engineering.v1",
        "timeout_seconds": 300,
        "write_policy": "read_only",
    }


def payload() -> dict[str, object]:
    return {
        "content": "Exact bounded read-only engineering specification.",
        "summary": "Bounded read-only repository inspection",
        "formation_contract": contract(),
        "seed_text": "Create one bounded read-only engineering objective from the approved specification.",
        "idempotency_key": "direct-grace-test-1",
        "approval_operation_id": str(uuid4()),
        "authenticated_principal": "steward",
        "explicit_steward_confirmation": True,
    }


def test_direct_grace_approval_requires_typed_exact_contract() -> None:
    result = DirectGraceApproval.from_payload(payload(), correlation_id=uuid4())
    assert result.authenticated_principal == "steward"
    assert result.formation_contract["action_type"] == "codex.engineering.v1"


def test_direct_grace_prose_cannot_become_approval() -> None:
    value = payload()
    value.pop("formation_contract")
    with pytest.raises(DirectGraceApprovalError, match="formation_contract"):
        DirectGraceApproval.from_payload(value, correlation_id=uuid4())


def test_direct_grace_non_steward_approval_fails_closed() -> None:
    value = payload()
    value["authenticated_principal"] = "resident-grace"
    with pytest.raises(DirectGraceApprovalError, match="authenticated Steward"):
        DirectGraceApproval.from_payload(value, correlation_id=uuid4())
