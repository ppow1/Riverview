"""GRC-008R targeted F4 resident/current-state regressions."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from riverview.reasoning.context_assembler import (
    ReasoningContextAssemblyError,
    ResidentReasoningPacketAssembler,
)
from test_reasoning_context_assembler import bundle, request
from test_resident_context import OCCUPANT


def _without_current_state(source_bundle):
    return replace(source_bundle, items=tuple(item for item in source_bundle.items if item.layer != "current_assignment"))


def test_matching_authoritative_resident_is_projected_and_serialized() -> None:
    packet = ResidentReasoningPacketAssembler().assemble(bundle(), request(resident_id=OCCUPANT))
    assert packet.resident_id == OCCUPANT
    restored = packet.from_typed_payload(packet.as_typed_payload())
    assert restored.resident_id == OCCUPANT


def test_wrong_resident_is_rejected_before_packet_emission() -> None:
    source_bundle = bundle()
    with pytest.raises(ReasoningContextAssemblyError, match="identity-mismatch"):
        ResidentReasoningPacketAssembler().assemble(source_bundle, request(resident_id=uuid4()))


def test_missing_current_assignment_state_fails_closed_even_with_transcript_like_context() -> None:
    source_bundle = _without_current_state(bundle())
    with pytest.raises(ReasoningContextAssemblyError, match="current-state-missing"):
        ResidentReasoningPacketAssembler().assemble(source_bundle, request())


def test_current_state_requirement_does_not_accept_empty_or_provider_metadata() -> None:
    source_bundle = _without_current_state(bundle())
    items = list(source_bundle.items)
    items.append(replace(items[0], layer="implementation_constraints", value={"provider_ref": "provider://observed"}, mandatory=False))
    with pytest.raises(ReasoningContextAssemblyError, match="current-state-missing"):
        ResidentReasoningPacketAssembler().assemble(replace(source_bundle, items=tuple(items)), request())


def test_empty_current_assignment_value_fails_closed() -> None:
    source_bundle = bundle()
    items = tuple(
        replace(item, value={}) if item.layer == "current_assignment" else item
        for item in source_bundle.items
    )
    with pytest.raises(ReasoningContextAssemblyError, match="current-state-missing"):
        ResidentReasoningPacketAssembler().assemble(replace(source_bundle, items=items), request())


def test_current_assignment_without_required_state_material_fails_closed() -> None:
    source_bundle = bundle()
    items = tuple(
        replace(item, value={"provider_ref": "provider://observed"})
        if item.layer == "current_assignment" else item
        for item in source_bundle.items
    )
    with pytest.raises(ReasoningContextAssemblyError, match="current-state-missing"):
        ResidentReasoningPacketAssembler().assemble(replace(source_bundle, items=items), request())


def test_valid_bounded_current_assignment_and_aggregate_limit_remain_enforced() -> None:
    packet = ResidentReasoningPacketAssembler().assemble(bundle(), request())
    assert packet.operational_state_refs
    with pytest.raises(ReasoningContextAssemblyError, match="packet-bound-exceeded"):
        ResidentReasoningPacketAssembler().assemble(bundle(), request(constraints=tuple("x" * 3990 + str(i) for i in range(32))))
