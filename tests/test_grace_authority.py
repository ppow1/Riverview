"""Contract tests for RV-005.1 Grace authority.

Version: 0.1.0
"""

from __future__ import annotations

from riverview.grace.authority import GraceAuthority


def test_grace_identity_is_operational_coordinator() -> None:
    identity = GraceAuthority().identity()
    assert identity["grace_id"] == "grace"
    assert identity["role"] == "operational_coordinator"
    assert identity["enabled"] is True


def test_allowed_progression_evaluation_is_bounded() -> None:
    decision = GraceAuthority().evaluate(
        "evaluate_progression",
        "declared_dependencies_and_evidence",
    )
    assert decision.decision == "allow"
    assert decision.requires_steward is False


def test_scope_mismatch_escalates() -> None:
    decision = GraceAuthority().evaluate(
        "evaluate_progression",
        "undeclared_scope",
    )
    assert decision.decision == "escalate"
    assert decision.requires_steward is True


def test_prohibited_authority_is_rejected() -> None:
    authority = GraceAuthority()
    for capability in (
        "change_mission",
        "change_authority_model",
        "bypass_steward_checkpoint",
        "arbitrary_sql",
        "arbitrary_shell",
        "access_undercurrent",
        "infer_authority_from_conversation",
    ):
        decision = authority.evaluate(capability, "all")
        assert decision.decision == "deny"
        assert decision.requires_steward is True


def test_unknown_capability_escalates() -> None:
    decision = GraceAuthority().evaluate("unregistered_capability", "all")
    assert decision.decision == "escalate"
    assert decision.requires_steward is True