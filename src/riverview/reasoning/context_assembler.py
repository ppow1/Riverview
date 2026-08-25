"""F2 projection from an accepted resident context bundle to F1.

Version: 1.0.0 | Package: GRC-005/F2

This module projects authoritative, already-assembled resident context into a
bounded :class:`ResidentReasoningPacket`. It does not retrieve memory, invoke
a provider, choose a resource, perform reasoning, or execute a result.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from riverview.residents.context import ContextAssemblyError, ContextBundle

from .cognition_contracts import (
    COGNITION_CONTRACT_VERSION,
    MAX_CONTEXT_CHARS,
    MAX_CONTEXT_REFS,
    MAX_PACKET_TEXT,
    CognitionTier,
    ResidentReasoningPacket,
)

ASSEMBLER_VERSION = "resident-reasoning-context-assembler-v1.0.0"
ASSEMBLY_CHECKPOINT = "RIV-COG-ASM-0001"
_ANCHOR_LAYERS = frozenset({"identity_anchor", "office_anchor", "authority_anchor"})
_STATE_LAYERS = frozenset({
    "current_assignment",
    "implementation_constraints",
    "professional_doctrine",
    "professional_methods",
    "relationship_context",
    "episodic_history",
    "uncertainty_conflict",
    "artifact_material",
})
_EVIDENCE_LAYERS = _STATE_LAYERS - {"current_assignment", "implementation_constraints"}
_FORBIDDEN_LAYERS = frozenset({"unbounded_transcript", "conversation_history"})


class ReasoningContextAssemblyError(ContextAssemblyError):
    """Fail-closed F2 packet projection error."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(reason, f"{ASSEMBLY_CHECKPOINT}: {message}")
        self.checkpoint = ASSEMBLY_CHECKPOINT


@dataclass(frozen=True, slots=True)
class ReasoningAssemblyRequest:
    """Explicit task and lineage inputs; identity is never inferred from text."""

    packet_id: UUID
    resident_id: UUID
    occupant_id: UUID
    implementation_id: UUID
    source_cognition_event_id: UUID
    objective_id: UUID
    correlation_id: UUID
    cognition_tier: CognitionTier
    request_class: str
    objective: str
    exact_question: str
    home_assessment: str
    requested_output_schema: str
    egress_policy: str
    classification: str
    max_budget: int
    expires_at: datetime
    constraints: tuple[str, ...] = ()
    unresolved_ambiguity: tuple[str, ...] = ()
    relevant_prior_decisions: tuple[str, ...] = ()
    known_deterministic_results: tuple[str, ...] = ()
    causation_id: UUID | None = None


def _unique(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _context_total(packet: dict[str, Any]) -> int:
    fields = (
        packet["objective"],
        packet["question"],
        packet["operational_state_refs"],
        packet["constraints"],
        packet["authoritative_current_state_refs"],
        packet["evidence_refs"],
        packet["unresolved_ambiguity"],
        packet["relevant_prior_decisions"],
        packet["known_deterministic_results"],
        packet["home_assessment"],
        packet["requested_output_schema"],
        packet["egress_policy"],
    )
    return sum(sum(map(len, value)) if isinstance(value, tuple) else len(value) for value in fields)


def _bounded_packet_preflight(packet: dict[str, Any]) -> None:
    """Reject over-budget context before constructing the F1 contract."""

    text_fields = (
        "objective", "question", "home_assessment", "requested_output_schema", "egress_policy",
    )
    for name in text_fields:
        value = packet[name]
        if not isinstance(value, str) or not value.strip() or len(value) > MAX_PACKET_TEXT:
            raise ReasoningContextAssemblyError("packet-field-invalid", f"{name} is not bounded.")
    collection_limits = {
        "operational_state_refs": MAX_CONTEXT_REFS,
        "authoritative_current_state_refs": MAX_CONTEXT_REFS,
        "evidence_refs": MAX_CONTEXT_REFS,
        "relevant_prior_decisions": MAX_CONTEXT_REFS,
        "unresolved_ambiguity": MAX_CONTEXT_REFS,
        "known_deterministic_results": MAX_CONTEXT_REFS,
        "constraints": 32,
    }
    for name, limit in collection_limits.items():
        values = packet[name]
        if not isinstance(values, tuple) or len(values) > limit:
            raise ReasoningContextAssemblyError("packet-bound-exceeded", f"{name} exceeds its collection bound.")
        value_limit = 4_000 if name in {"constraints", "unresolved_ambiguity", "known_deterministic_results"} else 500
        if not all(isinstance(value, str) and value.strip() and len(value) <= value_limit for value in values):
            raise ReasoningContextAssemblyError("packet-field-invalid", f"{name} contains an invalid value.")
    if _context_total(packet) > MAX_CONTEXT_CHARS:
        raise ReasoningContextAssemblyError("packet-bound-exceeded", "assembled packet exceeds the F1 aggregate context bound.")


def _item_refs(bundle: ContextBundle, layers: frozenset[str]) -> tuple[str, ...]:
    values = []
    for item in sorted(bundle.items, key=lambda item: (item.layer, item.item_id, item.source_ref)):
        if item.layer not in layers:
            continue
        if not isinstance(item.source_ref, str) or not item.source_ref.strip() or len(item.source_ref) > 500:
            raise ReasoningContextAssemblyError("reference-invalid", f"context item {item.item_id} has an invalid source reference.")
        values.append(item.source_ref)
    return _unique(values)


def _anchor(bundle: ContextBundle, layer: str) -> dict[str, Any]:
    matches = [item for item in bundle.items if item.layer == layer and item.mandatory and isinstance(item.value, Mapping)]
    if layer == "identity_anchor":
        matches = [item for item in matches if item.value.get("resident_id") == str(bundle.resident_id)]
    if len(matches) != 1 or not isinstance(matches[0].value, dict):
        raise ReasoningContextAssemblyError("identity-anchor-incomplete", f"exactly one mandatory {layer} is required.")
    return dict(matches[0].value)


class ResidentReasoningPacketAssembler:
    """Project one authoritative ContextBundle into one F1 packet."""

    version = ASSEMBLER_VERSION

    def assemble(self, bundle: ContextBundle, request: ReasoningAssemblyRequest) -> ResidentReasoningPacket:
        if bundle.stale:
            raise ReasoningContextAssemblyError("stale-bundle", "stale context cannot become a reasoning packet.")
        if bundle.resident_id != request.occupant_id:
            raise ReasoningContextAssemblyError("identity-mismatch", "packet occupant does not match the authoritative context bundle.")
        if bundle.resident_id != request.resident_id:
            raise ReasoningContextAssemblyError("identity-mismatch", "packet resident does not match the authoritative context bundle.")
        if bundle.office_id is None:
            raise ReasoningContextAssemblyError("office-binding-invalid", "authoritative office identity is required.")
        if not isinstance(request.max_budget, int) or not 0 < request.max_budget <= MAX_CONTEXT_CHARS:
            raise ReasoningContextAssemblyError("packet-field-invalid", "max_budget is outside the accepted F1 bound.")
        identity = _anchor(bundle, "identity_anchor")
        office = _anchor(bundle, "office_anchor")
        authority = _anchor(bundle, "authority_anchor")
        if str(identity.get("resident_id")) != str(bundle.resident_id):
            raise ReasoningContextAssemblyError("identity-mismatch", "identity anchor does not match the context bundle.")
        if str(office.get("office_id")) != str(bundle.office_id):
            raise ReasoningContextAssemblyError("identity-mismatch", "office anchor does not match the context bundle.")
        authority_ref = authority.get("authority_envelope_ref")
        if not isinstance(authority_ref, str) or not authority_ref.strip():
            raise ReasoningContextAssemblyError("authority-anchor-incomplete", "authority envelope reference is required.")
        if any(item.layer in _FORBIDDEN_LAYERS for item in bundle.items):
            raise ReasoningContextAssemblyError("unbounded-context", "transcript-like context cannot cross the packet boundary.")
        current_state_items = [
            item for item in bundle.items
            if item.layer == "current_assignment" and item.mandatory and isinstance(item.value, Mapping)
        ]
        if len(current_state_items) != 1 or not current_state_items[0].source_ref.strip():
            raise ReasoningContextAssemblyError("current-state-missing", "authoritative current operational state is required.")

        state_refs = _item_refs(bundle, _STATE_LAYERS)
        evidence_refs = _item_refs(bundle, _EVIDENCE_LAYERS)
        authoritative_state_refs = _item_refs(bundle, _ANCHOR_LAYERS | {"current_assignment", "implementation_constraints"})
        ambiguity = list(request.unresolved_ambiguity)
        ambiguity.extend(f"{item.item_id}:unresolved" for item in bundle.items if item.layer == "uncertainty_conflict")
        prior_decisions = list(request.relevant_prior_decisions)
        prior_decisions.extend(item.source_ref for item in bundle.items if item.authority_class == "ACCEPTED_INSTITUTIONAL_DECISION")
        constraints = list(request.constraints)
        assignment_items = [item for item in bundle.items if item.layer == "current_assignment"]
        for item in assignment_items:
            accepted = item.value.get("accepted_constraints", ())
            if isinstance(accepted, list):
                constraints.extend(value for value in accepted if isinstance(value, str))
        packet = {
            "objective": request.objective,
            "question": request.exact_question,
            "operational_state_refs": state_refs,
            "constraints": _unique(constraints),
            "authoritative_current_state_refs": authoritative_state_refs,
            "evidence_refs": evidence_refs,
            "unresolved_ambiguity": _unique(ambiguity),
            "relevant_prior_decisions": _unique(prior_decisions),
            "known_deterministic_results": _unique(list(request.known_deterministic_results)),
            "home_assessment": request.home_assessment,
            "requested_output_schema": request.requested_output_schema,
            "egress_policy": request.egress_policy,
        }
        _bounded_packet_preflight(packet)
        digest_payload = {
            "assembler_version": self.version,
            "bundle_id": str(bundle.bundle_id),
            "request": {
                "packet_id": str(request.packet_id),
                "resident_id": str(request.resident_id),
                "occupant_id": str(request.occupant_id),
                "implementation_id": str(request.implementation_id),
                "source_cognition_event_id": str(request.source_cognition_event_id),
                "objective_id": str(request.objective_id),
                "correlation_id": str(request.correlation_id),
                "cognition_tier": request.cognition_tier.value if isinstance(request.cognition_tier, CognitionTier) else str(request.cognition_tier),
                "request_class": request.request_class,
                "objective": request.objective,
                "question": request.exact_question,
                "home_assessment": request.home_assessment,
                "requested_output_schema": request.requested_output_schema,
                "egress_policy": request.egress_policy,
                "classification": request.classification,
                "max_budget": request.max_budget,
                "expires_at": request.expires_at.isoformat(),
            },
            "packet": packet,
        }
        digest = hashlib.sha256(json.dumps(digest_payload, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
        try:
            return ResidentReasoningPacket(
                packet_id=request.packet_id,
                resident_id=request.resident_id,
                occupant_id=request.occupant_id,
                office_id=bundle.office_id,
                implementation_id=request.implementation_id,
                source_cognition_event_id=request.source_cognition_event_id,
                objective_id=request.objective_id,
                authority_ref=authority_ref,
                cognition_tier=request.cognition_tier,
                request_class=request.request_class,
                objective=request.objective,
                question=request.exact_question,
                operational_state_refs=state_refs,
                evidence_refs=evidence_refs,
                constraints=packet["constraints"],
                authoritative_current_state_refs=authoritative_state_refs,
                unresolved_ambiguity=packet["unresolved_ambiguity"],
                relevant_prior_decisions=packet["relevant_prior_decisions"],
                known_deterministic_results=packet["known_deterministic_results"],
                home_assessment=request.home_assessment,
                requested_output_schema=request.requested_output_schema,
                egress_policy=request.egress_policy,
                max_budget=request.max_budget,
                classification=request.classification,
                correlation_id=request.correlation_id,
                packet_digest=digest,
                expires_at=request.expires_at,
                source_context_id=bundle.bundle_id,
                causation_id=request.causation_id,
                contract_version=COGNITION_CONTRACT_VERSION,
            )
        except (TypeError, ValueError) as exc:
            raise ReasoningContextAssemblyError("packet-invalid", str(exc)) from exc
