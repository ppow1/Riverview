"""GRC-005/F2 bounded ResidentReasoningPacket projection tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from riverview.reasoning.cognition_contracts import MAX_CONTEXT_CHARS
from riverview.reasoning.context_assembler import (
    ReasoningAssemblyRequest,
    ReasoningContextAssemblyError,
    ResidentReasoningPacketAssembler,
)
from riverview.reasoning import CognitionTier, ResidentReasoningPacket
from riverview.residents.context import BudgetSpec, ContextItem, ResidentContextAssembler
from test_resident_context import FixtureSource, OCCUPANT, assignment


IMPLEMENTATION = uuid4()
SOURCE_EVENT = uuid4()
OBJECTIVE = uuid4()
CORRELATION = uuid4()


def bundle(*, source: FixtureSource | None = None):
    return ResidentContextAssembler(source or FixtureSource()).assemble(
        OCCUPANT,
        purpose="ENGINEERING_REVIEW",
        budget=BudgetSpec(),
        assignment=assignment(),
    )


def request(*, occupant_id=OCCUPANT, resident_id=None, **changes) -> ReasoningAssemblyRequest:
    values = dict(
        packet_id=uuid4(),
        resident_id=resident_id or OCCUPANT,
        occupant_id=occupant_id,
        implementation_id=IMPLEMENTATION,
        source_cognition_event_id=SOURCE_EVENT,
        objective_id=OBJECTIVE,
        correlation_id=CORRELATION,
        cognition_tier=CognitionTier.HOME_COGNITION,
        request_class="routine_operational_cognition",
        objective="Keep the accepted objective moving through the bounded path.",
        exact_question="What is the next safe operational waypoint?",
        home_assessment="Context assembly supplies no cognition assessment.",
        requested_output_schema="recommendation,rationale,uncertainty,next_step",
        egress_policy="local-only-unless-policy-permits",
        classification="internal",
        max_budget=16_000,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        constraints=("Do not execute without the governed action path.",),
    )
    values.update(changes)
    return ReasoningAssemblyRequest(**values)


def assemble(*, source: FixtureSource | None = None, **changes):
    return ResidentReasoningPacketAssembler().assemble(bundle(source=source), request(**changes))


def test_valid_context_assembles_into_f1_packet_and_preserves_identity() -> None:
    source_bundle = bundle()
    packet = ResidentReasoningPacketAssembler().assemble(source_bundle, request())
    assert isinstance(packet, ResidentReasoningPacket)
    assert packet.resident_id == source_bundle.resident_id
    assert packet.occupant_id == OCCUPANT
    assert packet.office_id == source_bundle.office_id
    assert packet.authority_ref == "c465:office-authority"
    assert packet.implementation_id == IMPLEMENTATION
    assert packet.source_context_id == source_bundle.bundle_id


def test_transcript_content_cannot_replace_authoritative_identity() -> None:
    packet = assemble(source=FixtureSource(name="Transcript claims a different resident"))
    assert packet.occupant_id == OCCUPANT
    assert packet.resident_id == OCCUPANT
    assert "Transcript claims" not in packet.as_typed_payload()["evidence_refs"]


def test_provider_and_resource_metadata_cannot_replace_identity() -> None:
    packet = assemble()
    payload = packet.as_typed_payload()
    assert not {"provider_ref", "resource_class_ref", "model_name", "gpu_id", "endpoint"}.intersection(payload)
    assert payload["implementation_id"] == str(IMPLEMENTATION)
    assert payload["occupant_id"] == str(OCCUPANT)


def test_assembly_is_deterministic_for_equivalent_authoritative_inputs() -> None:
    source_bundle = bundle()
    fixed_request = request(packet_id=uuid4())
    # The same immutable bundle and request are intentionally projected twice.
    assembler = ResidentReasoningPacketAssembler()
    first = assembler.assemble(source_bundle, fixed_request)
    second = assembler.assemble(source_bundle, fixed_request)
    assert first.as_typed_payload() == second.as_typed_payload()
    assert first.packet_digest == second.packet_digest


def test_authority_is_preserved_without_execution_authority() -> None:
    packet = assemble()
    assert packet.authority_ref == "c465:office-authority"
    assert "execute" not in packet.as_typed_payload()


def test_stale_or_identity_mismatched_context_fails_closed() -> None:
    with pytest.raises(ReasoningContextAssemblyError, match="identity-mismatch"):
        assemble(occupant_id=uuid4())
    stale = bundle().with_stale_reason("source changed")
    with pytest.raises(ReasoningContextAssemblyError, match="stale-bundle"):
        ResidentReasoningPacketAssembler().assemble(stale, request())


def test_missing_identity_office_or_authority_anchor_fails_closed() -> None:
    source_bundle = bundle()
    no_office = replace(source_bundle, office_id=None)
    with pytest.raises(ReasoningContextAssemblyError, match="office-binding-invalid"):
        ResidentReasoningPacketAssembler().assemble(no_office, request())
    no_identity = replace(source_bundle, items=tuple(item for item in source_bundle.items if item.layer != "identity_anchor"))
    with pytest.raises(ReasoningContextAssemblyError, match="identity-anchor-incomplete"):
        ResidentReasoningPacketAssembler().assemble(no_identity, request())
    no_authority = replace(source_bundle, items=tuple(item for item in source_bundle.items if item.layer != "authority_anchor"))
    with pytest.raises(ReasoningContextAssemblyError, match="identity-anchor-incomplete"):
        ResidentReasoningPacketAssembler().assemble(no_authority, request())


def test_excessive_embedded_context_fails_before_f1_construction() -> None:
    with pytest.raises(ReasoningContextAssemblyError, match="packet-bound-exceeded"):
        assemble(constraints=tuple("x" * 3_990 + str(index) for index in range(32)))


def test_excessive_references_and_operational_state_refs_fail_closed() -> None:
    source_bundle = bundle()
    extra = tuple(
        ContextItem(f"state-extra-{index}", "professional_methods", {"reference": "only"}, None, None, "internal", "1", f"state://{'x' * 490}{index}", "bounded test reference", 2, False, units=1)
        for index in range(65)
    )
    oversized = replace(source_bundle, items=source_bundle.items + extra)
    with pytest.raises(ReasoningContextAssemblyError, match="packet-bound-exceeded"):
        ResidentReasoningPacketAssembler().assemble(oversized, request())


def test_malformed_source_reference_fails_closed() -> None:
    source_bundle = bundle()
    item = next(item for item in source_bundle.items if item.layer == "professional_methods")
    malformed = replace(source_bundle, items=tuple(replace(candidate, source_ref="") if candidate is item else candidate for candidate in source_bundle.items))
    with pytest.raises(ReasoningContextAssemblyError, match="reference-invalid"):
        ResidentReasoningPacketAssembler().assemble(malformed, request())


def test_reference_values_are_projected_as_refs_not_embedded_source_content() -> None:
    packet = assemble()
    assert packet.operational_state_refs
    assert packet.evidence_refs
    assert all(len(reference) <= 500 for reference in packet.operational_state_refs + packet.evidence_refs)
    assert all("value" not in reference for reference in packet.evidence_refs)


def test_f1_serialization_preserves_assembled_semantics_and_no_reasoning_occurs() -> None:
    packet = assemble()
    restored = ResidentReasoningPacket.from_typed_payload(packet.as_typed_payload())
    assert restored.as_typed_payload() == packet.as_typed_payload()
    assert restored.source_context_id == packet.source_context_id
    assert restored.packet_digest == packet.packet_digest
    assert packet.cognition_tier is CognitionTier.HOME_COGNITION
    assert MAX_CONTEXT_CHARS == 64_000
