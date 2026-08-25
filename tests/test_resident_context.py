"""C469 JCA-016/JCA-017 bounded context assembly tests.

Version: 1.0.0 | Date: 2026-08-19 | Scope: no provider invocation
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from riverview.residents.context import (
    AssignmentContext,
    BudgetSpec,
    ContextAssemblyError,
    ContextPolicy,
    ContextRendererContract,
    InMemoryContextEventSink,
    ResidentContextAssembler,
)


OCCUPANT = UUID("f98ff6cc-907a-5ac9-909f-7165358084d2")
OFFICE = UUID("b3bf3855-4dc1-5697-ac90-977d7a8a8d21")


class FixtureSource:
    def __init__(self, *, name: str = "Jessica", occupancy: dict | None = None, private_artifact: bool = False) -> None:
        evidence = {"evidence_id": "evidence-jessica", "source_key": "c467:steward:jessica-identity", "source_location": "C465 current facts", "source_revision": "C465", "content_hash": None, "classification": "internal"}
        self.projection = {
            "occupant": {"occupant_id": str(OCCUPANT), "display_name": name, "status": "active", "classification": "internal", "canonical_anchor_ref": "c465:identity-anchor", "provenance_id": "evidence-jessica", "version": 1},
            "occupancy": occupancy or {"office_id": str(OFFICE), "title": "Office of Character Architecture", "purpose_ref": "c465:office-purpose", "authority_envelope_ref": "c465:office-authority", "policy_profile_ref": "resident-office-policy:single", "occupancy_policy": "single", "classification": "internal", "occupancy_id": "occupancy-jessica", "effective_from": "2026-08-19T00:00:00+00:00", "assignment_reason_ref": "Steward-established current office assignment", "assignment_authority_ref": "Steward", "provenance_id": "evidence-jessica"},
            "bindings": [],
            "claims": [
                {"claim_id": "claim-name", "predicate": "name", "value": name, "authority_class": "STEWARD_AUTHORIZED_FACT", "confidence": "high", "status": "accepted", "provenance": evidence},
                {"claim_id": "claim-title", "predicate": "office_title", "value": "Chief Character Architect", "authority_class": "STEWARD_AUTHORIZED_FACT", "confidence": "high", "status": "accepted", "provenance": evidence},
            ],
            "artifacts": [
                {"artifact_id": "artifact-corpus", "artifact_key": "c464:corpus", "artifact_type": "recovery_corpus", "logical_version": "1.1", "content_hash": "a" * 64, "repository_or_store": "Riverview", "source_location": "docs/architecture/resident_localization/jessica_recovery_corpus_manifest_v1.json", "canonical_revision": "C464", "historical_revision": None, "classification": "internal", "owner_ref": "Office", "availability": "available", "storage_class": "github", "retrieval_eligibility": "eligible", "provenance_id": "evidence-jessica", "superseded_by": None},
                {"artifact_id": "artifact-private", "artifact_key": "private:fixture", "artifact_type": "private_fixture", "logical_version": "1", "content_hash": "b" * 64, "repository_or_store": "protected", "source_location": "protected://fixture", "canonical_revision": None, "historical_revision": None, "classification": "private" if private_artifact else "internal", "owner_ref": "fixture", "availability": "available", "storage_class": "protected_local", "retrieval_eligibility": "eligible", "provenance_id": "evidence-jessica", "superseded_by": None},
            ],
            "relationships": [{"relationship_id": "relationship-1", "subject_a_type": "occupant", "subject_a_id": str(OCCUPANT), "subject_b_type": "occupant", "subject_b_id": str(UUID("11111111-1111-1111-1111-111111111111")), "relationship_type": "task_collaborator", "status": "active", "effective_from": "2026-08-19T00:00:00+00:00", "effective_to": None, "authority_ref": "fixture", "provenance_id": "evidence-jessica", "classification": "internal", "visibility_policy_ref": "explicit"}],
            "state_records": [{"state_id": "state-method", "state_class": "professional_methods", "value_kind": "reference", "value_ref": "artifact:c464:corpus", "bounded_metadata": {"method_family": "visual_canon_method"}, "classification": "internal", "retrieval_policy_ref": "eligible", "status": "active", "effective_from": "2026-08-19T00:00:00+00:00", "provenance_id": "evidence-jessica"}],
            "contradictions": [{"contradiction_group_id": "contradiction-1", "subject_type": "historical_architect_record", "subject_id": str(OCCUPANT), "status": "unresolved", "resolution_ref": None, "provenance_id": "evidence-jessica"}],
        }

    def rehydration_projection(self, occupant_id: UUID) -> dict:
        if occupant_id != OCCUPANT:
            raise LookupError("unknown fixture resident")
        return self.projection

    def health(self) -> dict:
        return {"status": "healthy", "migration_id": "0035"}


def assignment() -> AssignmentContext:
    return AssignmentContext("fixture:character-assignment", "stage:1", "Produce a bounded implementation specification for a small Activity view status indicator.", ("do not execute",), ("c464:corpus",), (str(UUID("11111111-1111-1111-1111-111111111111")),), "C469-test-authority", "bounded specification")


def test_jessica_assignment_bundle_is_bounded_and_traceable() -> None:
    events = InMemoryContextEventSink()
    assembler = ResidentContextAssembler(FixtureSource(), event_sink=events)
    bundle = assembler.assemble(OCCUPANT, purpose="CHARACTER_ARCHITECTURE_WORK", budget=BudgetSpec(), assignment=assignment(), identity_deferred=("surname", "biography", "appearance", "visual_canon"))
    layers = {item.layer for item in bundle.items}
    assert bundle.resident_id == OCCUPANT
    assert bundle.office_id == OFFICE
    assert {"identity_anchor", "office_anchor", "authority_anchor", "current_assignment", "professional_methods"} <= layers
    assert "all Estate history" not in json_text(bundle)
    assert bundle.audit_provenance["accepted_count"] == len(bundle.items)
    assert bundle.dependency_fingerprint
    assert [event["event_type"] for event in events.events] == ["resident.rehydration.requested", "resident.context.assembled"]


def json_text(bundle) -> str:
    import json
    return json.dumps(bundle.to_dict(), sort_keys=True)


def test_replacement_implementation_does_not_change_occupant_or_bundle_semantics() -> None:
    assembler = ResidentContextAssembler(FixtureSource())
    first = assembler.assemble(OCCUPANT, purpose="CONTINUITY_RENEWAL", budget=BudgetSpec(), assignment=assignment(), implementation_ref="implementation:old")
    replacement = assembler.assemble(OCCUPANT, purpose="CONTINUITY_RENEWAL", budget=BudgetSpec(), assignment=assignment(), implementation_ref="implementation:new")
    assert first.resident_id == replacement.resident_id == OCCUPANT
    assert first.office_id == replacement.office_id == OFFICE
    assert all(item.layer != "conversation_history" for item in replacement.items)


def test_mandatory_assignment_and_budget_fail_closed() -> None:
    assembler = ResidentContextAssembler(FixtureSource())
    with pytest.raises(ContextAssemblyError, match="assignment-missing"):
        assembler.assemble(OCCUPANT, purpose="PROFESSIONAL_ASSIGNMENT", budget=BudgetSpec())
    with pytest.raises(ContextAssemblyError, match="mandatory-context-truncated"):
        assembler.assemble(OCCUPANT, purpose="PROFESSIONAL_ASSIGNMENT", budget=BudgetSpec(total_units=20, reserved_task_units=0), assignment=assignment())


def test_policy_denial_and_artifact_revision_mismatch_are_distinguishable() -> None:
    denied = ResidentContextAssembler(FixtureSource(private_artifact=True))
    private_assignment = AssignmentContext("fixture:private-assignment", "stage:1", "bounded task", artifact_refs=("private:fixture",))
    bundle = denied.assemble(OCCUPANT, purpose="CHARACTER_ARCHITECTURE_WORK", budget=BudgetSpec(), assignment=private_assignment)
    assert any("protected" in item["reason"] or "classification" in item["reason"] for item in bundle.excluded_candidates)
    mismatch_assignment = AssignmentContext("fixture:character-assignment", "stage:1", "bounded task", artifact_refs=("c464:corpus",), artifact_expectations=(("c464:corpus", "9.9", None),))
    with pytest.raises(ContextAssemblyError, match="artifact-revision-mismatch"):
        ResidentContextAssembler(FixtureSource()).assemble(OCCUPANT, purpose="CHARACTER_ARCHITECTURE_WORK", budget=BudgetSpec(), assignment=mismatch_assignment)


def test_contradictions_remain_unresolved_and_renderer_rejects_stale_bundle() -> None:
    assembler = ResidentContextAssembler(FixtureSource())
    bundle = assembler.assemble(OCCUPANT, purpose="HISTORICAL_REVIEW", budget=BudgetSpec())
    assert any(item.layer == "uncertainty_conflict" for item in bundle.items)
    stale = bundle.with_stale_reason("artifact superseded")
    with pytest.raises(ContextAssemblyError, match="renderer-contract-mismatch"):
        ContextRendererContract().validate(stale)
    assert ContextRendererContract().validate(bundle)["authority_preserved"] is True


def test_renderer_explicitly_preserves_authority_and_non_authority_rules() -> None:
    bundle = ResidentContextAssembler(FixtureSource()).assemble(OCCUPANT, purpose="ENGINEERING_REVIEW", budget=BudgetSpec(), assignment=assignment())
    rendered = ContextRendererContract().render(bundle)
    assert "inclusion never grants authority" in rendered
    assert "authority_class=" in rendered
    assert "mandatory=true" in rendered
    assert "Implementation, provider, model, host, and session are not occupant identity." in rendered


def test_policy_unavailable_fails_closed_for_mandatory_anchor() -> None:
    assembler = ResidentContextAssembler(FixtureSource(), policy=ContextPolicy(available=False))
    with pytest.raises(ContextAssemblyError, match="policy-decision-missing"):
        assembler.assemble(OCCUPANT, purpose="HISTORICAL_REVIEW", budget=BudgetSpec())


def test_non_jessica_fixture_uses_same_assembler_without_structural_hack() -> None:
    source = FixtureSource(name="Grace")
    bundle = ResidentContextAssembler(source).assemble(OCCUPANT, purpose="ENGINEERING_REVIEW", budget=BudgetSpec(), assignment=assignment())
    identity = next(item for item in bundle.items if item.item_id.startswith("occupant:") and item.layer == "identity_anchor")
    assert identity.value["name"] == "Grace"
