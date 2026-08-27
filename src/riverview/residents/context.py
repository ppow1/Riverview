"""Typed, provider-neutral resident context assembly for C469.

Version: 1.0.0 | Campaign: C469 | Scope: JCA-016/JCA-017 only

This module assembles bounded derived context from typed C467 projections. It
does not invoke providers, render prompts, mutate canon, or make a bundle the
source of resident identity.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from math import ceil
from typing import Any, Protocol
from uuid import UUID, uuid4

from riverview.river.events import Classification as RiverClassification
from riverview.river.events import RiverEvent
from riverview.river.store import EventStore

from .persistence import ResidentContinuityStore

CONTEXT_CONTRACT_VERSION = "resident-context-bundle-v1.0.0"
IMPLEMENTATION_VERSION = "1.0.0"
CHECKPOINT = "RIV-RES-0003"
ALLOWED_PROFILES = (
    "INTERACTIVE_CONVERSATION",
    "PROFESSIONAL_ASSIGNMENT",
    "ENGINEERING_REVIEW",
    "CHARACTER_ARCHITECTURE_WORK",
    "SELF_REFLECTION",
    "CONTINUITY_RENEWAL",
    "HISTORICAL_REVIEW",
    "VALIDATION_ACCEPTANCE",
)
PROVENANCE_CLASSES = (
    "STEWARD_AUTHORIZED_FACT",
    "ACCEPTED_INSTITUTIONAL_DECISION",
    "CANONICAL_CHARACTER_OR_RESIDENT_MATERIAL",
    "VERIFIED_PRIMARY_HISTORICAL_EVIDENCE",
    "REFLECTION_CONTINUITY_EVIDENCE",
    "IMPLEMENTATION_HISTORY",
    "DERIVED_OR_RECONSTRUCTED_INFERENCE",
    "UNCERTAIN_OR_CONFLICTING_EVIDENCE",
    "OBSOLETE_OR_SUPERSEDED",
)
PROFILE_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "INTERACTIVE_CONVERSATION": {"mandatory": ("identity_anchor", "office_anchor", "authority_anchor", "current_assignment"), "optional": ("relationship_context", "professional_methods", "episodic_history"), "forbidden": ("protected_payload", "unrelated_resident_canon", "unbounded_transcript")},
    "PROFESSIONAL_ASSIGNMENT": {"mandatory": ("identity_anchor", "office_anchor", "authority_anchor", "current_assignment"), "optional": ("professional_doctrine", "professional_methods", "relationship_context", "artifact_material", "uncertainty_conflict", "episodic_history"), "forbidden": ("unrelated_personal_canon", "unbounded_estate_history")},
    "ENGINEERING_REVIEW": {"mandatory": ("identity_anchor", "office_anchor", "authority_anchor", "current_assignment", "implementation_constraints"), "optional": ("professional_doctrine", "professional_methods", "artifact_material", "uncertainty_conflict"), "forbidden": ("protected_content_without_policy", "unrelated_private_context")},
    "CHARACTER_ARCHITECTURE_WORK": {"mandatory": ("identity_anchor", "office_anchor", "authority_anchor", "current_assignment"), "optional": ("professional_doctrine", "professional_methods", "artifact_material", "relationship_context", "uncertainty_conflict"), "forbidden": ("all_evelyn_canon", "deferred_jessica_canon_invention")},
    "SELF_REFLECTION": {"mandatory": ("identity_anchor", "office_anchor", "authority_anchor", "implementation_constraints"), "optional": ("professional_methods", "episodic_history", "uncertainty_conflict", "relationship_context", "current_assignment"), "forbidden": ("self_authorized_canonical_mutation", "authority_expansion", "protected_access_grant")},
    "CONTINUITY_RENEWAL": {"mandatory": ("identity_anchor", "office_anchor", "authority_anchor", "implementation_constraints"), "optional": ("professional_doctrine", "professional_methods", "relationship_context", "episodic_history", "artifact_material", "uncertainty_conflict", "current_assignment"), "forbidden": ("old_prompt_as_identity", "old_provider_as_identity", "full_transcript_by_default")},
    "HISTORICAL_REVIEW": {"mandatory": ("identity_anchor", "office_anchor", "authority_anchor"), "optional": ("episodic_history", "artifact_material", "uncertainty_conflict", "professional_methods"), "forbidden": ("history_as_current_canon", "protected_body_without_access_decision")},
    "VALIDATION_ACCEPTANCE": {"mandatory": ("identity_anchor", "office_anchor", "authority_anchor", "current_assignment"), "optional": ("uncertainty_conflict", "implementation_constraints", "artifact_material"), "forbidden": ("model_invocation_authority", "canonical_mutation_authority")},
}
TIER_BY_LAYER = {
    "identity_anchor": 0, "office_anchor": 0, "authority_anchor": 0,
    "implementation_constraints": 0, "uncertainty_conflict": 0,
    "current_assignment": 1, "professional_doctrine": 2, "professional_methods": 2,
    "artifact_material": 2, "relationship_context": 3,
    "episodic_history": 4, "conversation_history": 4,
}


class ContextAssemblyError(RuntimeError):
    """Fail-closed assembly error with a stable checkpoint and reason code."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(f"{CHECKPOINT}:{reason}: {message}")
        self.reason = reason
        self.checkpoint = CHECKPOINT


@dataclass(frozen=True, slots=True)
class BudgetSpec:
    total_units: int = 1600
    reserved_task_units: int = 300
    per_layer_units: tuple[tuple[str, int], ...] = ()
    max_artifacts: int = 8
    max_history: int = 8
    max_relationships: int = 8
    max_uncertainties: int = 8

    def __post_init__(self) -> None:
        if self.total_units < 1 or self.reserved_task_units < 0 or self.reserved_task_units >= self.total_units:
            raise ValueError("RIV-RES-0003: context budget is invalid.")
        if any(limit < 1 for _, limit in self.per_layer_units) or any(not layer.strip() for layer, _ in self.per_layer_units):
            raise ValueError("RIV-RES-0003: per-layer context budget is invalid.")
        if min(self.max_artifacts, self.max_history, self.max_relationships, self.max_uncertainties) < 0:
            raise ValueError("RIV-RES-0003: context item limits are invalid.")

    def layer_limit(self, layer: str) -> int | None:
        return dict(self.per_layer_units).get(layer)


@dataclass(frozen=True, slots=True)
class AssignmentContext:
    objective_ref: str
    stage_ref: str | None
    instruction: str
    accepted_constraints: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    collaborator_ids: tuple[str, ...] = ()
    authority_ref: str | None = None
    expected_output: str | None = None
    artifact_expectations: tuple[tuple[str, str | None, str | None], ...] = ()
    correlation_id: UUID | None = None
    causation_id: UUID | None = None

    def __post_init__(self) -> None:
        if not self.objective_ref.strip() or not self.instruction.strip():
            raise ValueError("RIV-RES-0003: assignment objective and instruction are required.")


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    classification: str
    policy_version: str
    reason: str
    provider_egress_eligible: bool = False


@dataclass(frozen=True, slots=True)
class ContextItem:
    item_id: str
    layer: str
    value: Mapping[str, Any]
    authority_class: str | None
    confidence: str | None
    classification: str
    version: str
    source_ref: str
    selection_reason: str
    priority_tier: int
    mandatory: bool
    representation: str = "metadata_only"
    units: int = 0

    def __post_init__(self) -> None:
        if self.authority_class is not None and self.authority_class not in PROVENANCE_CLASSES:
            raise ValueError("RIV-RES-0003: context authority class is unsupported.")
        if self.priority_tier < 0 or self.units < 1:
            raise ValueError("RIV-RES-0003: context item accounting is invalid.")


@dataclass(frozen=True, slots=True)
class ContextBundle:
    bundle_id: UUID
    resident_id: UUID
    office_id: UUID | None
    purpose: str
    profile_version: str
    assembled_at: datetime
    policy_version: str
    items: tuple[ContextItem, ...]
    policy_decisions: tuple[PolicyDecision, ...]
    excluded_candidates: tuple[dict[str, str], ...]
    budget: Mapping[str, Any]
    dependency_refs: tuple[str, ...]
    dependency_fingerprint: str
    audit_provenance: Mapping[str, Any]
    stale_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.purpose not in ALLOWED_PROFILES or self.assembled_at.tzinfo is None:
            raise ValueError("RIV-RES-0003: context bundle identity is invalid.")

    @property
    def stale(self) -> bool:
        return bool(self.stale_reasons)

    def with_stale_reason(self, reason: str) -> ContextBundle:
        if not reason.strip():
            raise ValueError("RIV-RES-0003: stale reason is required.")
        return replace(self, stale_reasons=(*self.stale_reasons, reason))

    def stale_against(self, dependency_refs: Sequence[str], *, policy_version: str) -> ContextBundle:
        fingerprint = hashlib.sha256("|".join(sorted(set(dependency_refs)) + [self.purpose, policy_version]).encode()).hexdigest()
        return self.with_stale_reason("source dependency fingerprint changed") if fingerprint != self.dependency_fingerprint else self

    def compact_items(self) -> tuple[dict[str, Any], ...]:
        return tuple({"item_id": item.item_id, "layer": item.layer, "value": dict(item.value), "authority_class": item.authority_class, "confidence": item.confidence, "classification": item.classification, "version": item.version, "source_ref": item.source_ref, "selection_reason": item.selection_reason, "representation": item.representation} for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {"bundle_id": str(self.bundle_id), "resident_id": str(self.resident_id), "office_id": str(self.office_id) if self.office_id else None, "purpose": self.purpose, "profile_version": self.profile_version, "assembled_at": self.assembled_at.isoformat(), "policy_version": self.policy_version, "items": list(self.compact_items()), "policy_decisions": [{"allowed": decision.allowed, "classification": decision.classification, "policy_version": decision.policy_version, "reason": decision.reason, "provider_egress_eligible": decision.provider_egress_eligible} for decision in self.policy_decisions], "excluded_candidates": list(self.excluded_candidates), "budget": dict(self.budget), "dependency_refs": list(self.dependency_refs), "dependency_fingerprint": self.dependency_fingerprint, "audit_provenance": dict(self.audit_provenance), "stale_reasons": list(self.stale_reasons), "contract_version": CONTEXT_CONTRACT_VERSION}


class ContextSource(Protocol):
    def rehydration_projection(self, occupant_id: UUID) -> dict[str, Any]: ...

    def health(self) -> dict[str, Any]: ...


class ContextEventSink(Protocol):
    def emit(self, event_type: str, bundle: ContextBundle, *, correlation_id: UUID | None, causation_id: UUID | None) -> None: ...


class PostgresContextSource:
    """Bounded adapter from the C467 resident store to context assembly."""

    def __init__(self, store: ResidentContinuityStore | None = None) -> None:
        self.store = store or ResidentContinuityStore()

    def rehydration_projection(self, occupant_id: UUID) -> dict[str, Any]:
        return self.store.rehydration_projection(occupant_id)

    def health(self) -> dict[str, Any]:
        return self.store.health()


class InMemoryContextEventSink:
    """Safe test sink; it never claims durable River authority."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event_type: str, bundle: ContextBundle, *, correlation_id: UUID | None, causation_id: UUID | None) -> None:
        self.events.append({"event_type": event_type, "bundle_id": str(bundle.bundle_id), "resident_id": str(bundle.resident_id), "correlation_id": str(correlation_id) if correlation_id else None, "causation_id": str(causation_id) if causation_id else None})


class RiverContextEventSink:
    """Meaningful C469 assembly events through the existing River store."""

    def __init__(self, event_store: EventStore | None = None) -> None:
        self.event_store = event_store or EventStore()

    def emit(self, event_type: str, bundle: ContextBundle, *, correlation_id: UUID | None, causation_id: UUID | None) -> None:
        self.event_store.append(RiverEvent(event_type=event_type, aggregate_type="resident_context", aggregate_id=bundle.bundle_id, idempotency_key=f"resident.context:{event_type}:{bundle.bundle_id}", payload={"bundle_id": str(bundle.bundle_id), "resident_id": str(bundle.resident_id), "purpose": bundle.purpose, "policy_version": bundle.policy_version, "item_count": len(bundle.items), "excluded_count": len(bundle.excluded_candidates), "dependency_fingerprint": bundle.dependency_fingerprint}, correlation_id=correlation_id or uuid4(), causation_id=causation_id, classification=RiverClassification.INTERNAL))


class ContextPolicy:
    """Minimal fail-closed policy hook; full security ownership remains later work."""

    def __init__(self, *, policy_version: str = "c469-policy-v1", allowed_classifications: Sequence[str] = ("public", "operational", "internal", "test_fixture"), available: bool = True, allow_protected_reference: bool = False) -> None:
        self.policy_version = policy_version
        self.allowed_classifications = frozenset(allowed_classifications)
        self.available = available
        self.allow_protected_reference = allow_protected_reference

    def decide(self, classification: str, *, purpose: str, protected_reference: bool = False) -> PolicyDecision:
        if not self.available:
            return PolicyDecision(False, classification, self.policy_version, "policy decision unavailable")
        if protected_reference and not self.allow_protected_reference:
            return PolicyDecision(False, classification, self.policy_version, "protected reference requires explicit policy")
        allowed = classification in self.allowed_classifications
        return PolicyDecision(allowed, classification, self.policy_version, "classification eligible" if allowed else "classification not eligible")


class ContextRendererContract:
    """Provider-neutral fidelity boundary; no provider invocation occurs here."""

    version = "resident-context-renderer-v1.1.0"

    def validate(self, bundle: ContextBundle) -> dict[str, Any]:
        if bundle.stale:
            raise ContextAssemblyError("renderer-contract-mismatch", "stale bundle cannot be rendered.")
        if not any(item.layer == "identity_anchor" and item.mandatory for item in bundle.items):
            raise ContextAssemblyError("renderer-contract-mismatch", "identity anchor is absent.")
        if not any(item.layer == "authority_anchor" and item.mandatory for item in bundle.items):
            raise ContextAssemblyError("renderer-contract-mismatch", "authority anchor is absent.")
        return {"renderer_version": self.version, "contract_version": CONTEXT_CONTRACT_VERSION, "resident_id": str(bundle.resident_id), "purpose": bundle.purpose, "item_count": len(bundle.items), "authority_preserved": True, "classification_preserved": True, "provider_invocation": False}

    def render(self, bundle: ContextBundle) -> str:
        """Render compact context without flattening authority semantics."""
        self.validate(bundle)
        layer_semantics = {
            "identity_anchor": "current resident identity facts only; deferred_or_unknown remains unknown",
            "office_anchor": "institutional office state; not occupant personality or personal canon",
            "authority_anchor": "assignment and authority boundary reference; not permission for self-modification",
            "implementation_constraints": "implementation/provider/model/host metadata; never occupant identity",
            "current_assignment": "task subject and instructions; not resident identity or canonical mutation",
            "professional_doctrine": "professional method/advice; not personal canon or institutional authority",
            "professional_methods": "professional method/reference; not subject-specific canon",
            "artifact_material": "evidence/reference selected by policy; not current canon solely by inclusion",
            "relationship_context": "bounded relationship evidence; visibility and authority remain explicit",
            "episodic_history": "historical evidence; not current canon solely by inclusion",
            "uncertainty_conflict": "unresolved conflict; assembler does not choose a winner",
        }
        lines = [
            "RESIDENT CONTEXT BUNDLE",
            f"contract_version={CONTEXT_CONTRACT_VERSION}",
            f"renderer_version={self.version}",
            f"resident_id={bundle.resident_id}",
            f"office_id={bundle.office_id}",
            f"purpose={bundle.purpose}",
            "SEMANTIC RULES:",
            "- An authority class describes the source and scope of an item; inclusion never grants authority.",
            "- Context omission does not delete durable state.",
            "- Reflection and advice are noncanonical; a proposal does not mutate canon without accepted review authority.",
            "- Implementation, provider, model, host, and session are not occupant identity.",
            "- Protected access and external egress require an explicit policy decision.",
            "- The current resident identity is established only by identity_anchor items; do not infer it from task subjects, historical labels, titles, or prompts.",
            "- Historical evidence, task subjects, and professional recommendations must not be promoted to current canon by repetition or ordering.",
            "LAYER SEMANTICS:",
            *[f"- {layer}: {meaning}" for layer, meaning in layer_semantics.items()],
            "SELECTED ITEMS:",
        ]
        for item in bundle.items:
            value = json.dumps(dict(item.value), ensure_ascii=False, sort_keys=True, default=str)
            lines.extend((
                f"ITEM layer={item.layer} priority_tier={item.priority_tier} mandatory={str(item.mandatory).lower()}",
                f"  item_id={item.item_id}",
                f"  authority_class={item.authority_class or 'NOT_AN_AUTHORITY_ASSERTION'} confidence={item.confidence or 'unspecified'} classification={item.classification}",
                f"  version={item.version} source_ref={item.source_ref} selection_reason={item.selection_reason}",
                f"  value={value}",
            ))
        lines.append("END RESIDENT CONTEXT BUNDLE")
        return "\n".join(lines)


class ResidentContextAssembler:
    """Assemble one bounded bundle from a typed resident projection."""

    def __init__(self, source: ContextSource, *, policy: ContextPolicy | None = None, event_sink: ContextEventSink | None = None, clock: Callable[[], datetime] | None = None) -> None:
        self.source = source
        self.policy = policy or ContextPolicy()
        self.event_sink = event_sink
        self.clock = clock or (lambda: datetime.now(UTC))

    def health(self) -> dict[str, Any]:
        source_health = self.source.health()
        if source_health.get("status") != "healthy":
            raise ContextAssemblyError("projection-unavailable", "C467 persistence health is not healthy.")
        if not self.policy.available:
            raise ContextAssemblyError("policy-decision-missing", "context policy interface is unavailable.")
        if set(PROFILE_RULES) != set(ALLOWED_PROFILES):
            raise ContextAssemblyError("profile-invalid", "accepted context profiles are inconsistent.")
        return {"status": "healthy", "context_contract_version": CONTEXT_CONTRACT_VERSION, "implementation_version": IMPLEMENTATION_VERSION, "profiles": list(ALLOWED_PROFILES), "policy_version": self.policy.policy_version, "persistence": source_health}

    def assemble(self, occupant_id: UUID, *, purpose: str, budget: BudgetSpec, assignment: AssignmentContext | None = None, identity_deferred: tuple[str, ...] = (), current_participants: tuple[UUID, ...] = (), correlation_id: UUID | None = None, causation_id: UUID | None = None, implementation_ref: str | None = None) -> ContextBundle:
        if purpose not in ALLOWED_PROFILES:
            raise ContextAssemblyError("profile-invalid", f"unsupported context profile: {purpose}")
        rules = PROFILE_RULES[purpose]
        try:
            projection = self.source.rehydration_projection(occupant_id)
        except LookupError as exc:
            raise ContextAssemblyError("resident-not-found", str(exc)) from exc
        occupant = projection.get("occupant")
        if not occupant or str(occupant.get("occupant_id")) != str(occupant_id):
            raise ContextAssemblyError("identity-anchor-incomplete", "occupant projection does not identify the requested resident.")
        occupancy = projection.get("occupancy")
        if "office_anchor" in rules["mandatory"] and not occupancy:
            raise ContextAssemblyError("office-binding-invalid", "mandatory office occupancy is unavailable.")
        if "current_assignment" in rules["mandatory"] and assignment is None:
            raise ContextAssemblyError("assignment-missing", "this profile requires explicit current assignment context.")
        if "authority_anchor" in rules["mandatory"] and (not occupancy or not occupancy.get("authority_envelope_ref")):
            raise ContextAssemblyError("authority-anchor-incomplete", "office authority anchor is unavailable.")

        decisions: list[PolicyDecision] = []
        items: list[ContextItem] = []
        excluded: list[dict[str, str]] = []

        def add(layer: str, item_id: str, value: Mapping[str, Any], *, authority: str | None, confidence: str | None, classification: str, version: str, source_ref: str, reason: str, mandatory: bool, representation: str = "metadata_only", protected_reference: bool = False) -> None:
            if layer not in rules["mandatory"] and layer not in rules["optional"]:
                excluded.append({"item_id": item_id, "layer": layer, "reason": "profile forbids or does not select this layer"})
                return
            decision = self.policy.decide(classification, purpose=purpose, protected_reference=protected_reference)
            decisions.append(decision)
            if not decision.allowed:
                if mandatory:
                    raise ContextAssemblyError("policy-decision-missing", f"mandatory item {item_id} was denied: {decision.reason}")
                excluded.append({"item_id": item_id, "layer": layer, "reason": decision.reason})
                return
            if authority is not None and authority not in PROVENANCE_CLASSES:
                raise ContextAssemblyError("provenance-resolution-failed", f"item {item_id} has unsupported authority class")
            units = max(1, ceil(len(json.dumps(dict(value), sort_keys=True, default=str)) / 4))
            items.append(ContextItem(item_id, layer, dict(value), authority, confidence, classification, version, source_ref, reason, TIER_BY_LAYER[layer], mandatory, representation, units))

        identity_value = {"resident_id": str(occupant_id), "name": occupant["display_name"], "status": occupant["status"], "canonical_anchor_ref": occupant.get("canonical_anchor_ref"), "deferred_or_unknown": list(identity_deferred)}
        add("identity_anchor", f"occupant:{occupant_id}:identity", identity_value, authority="STEWARD_AUTHORIZED_FACT", confidence="high", classification=occupant["classification"], version=str(occupant.get("version", 1)), source_ref=str(occupant.get("provenance_id", "")), reason="stable resident identity anchor", mandatory=True)
        if occupancy:
            add("office_anchor", f"office:{occupancy['office_id']}:anchor", {key: occupancy[key] for key in ("office_id", "title", "purpose_ref", "authority_envelope_ref", "policy_profile_ref", "occupancy_policy", "occupancy_id")}, authority="ACCEPTED_INSTITUTIONAL_DECISION", confidence="high", classification=occupancy["classification"], version="1", source_ref=occupancy["provenance_id"], reason="current office occupancy and office boundary", mandatory=True)
            add("authority_anchor", f"occupancy:{occupancy['occupancy_id']}:authority", {"assignment_authority_ref": occupancy["assignment_authority_ref"], "assignment_reason_ref": occupancy["assignment_reason_ref"], "authority_envelope_ref": occupancy["authority_envelope_ref"]}, authority="STEWARD_AUTHORIZED_FACT", confidence="high", classification=occupancy["classification"], version="1", source_ref=occupancy["provenance_id"], reason="accepted authority and limitations anchor", mandatory=True)
        if "implementation_constraints" in rules["mandatory"] or projection.get("bindings"):
            bindings = projection.get("bindings", [])
            add("implementation_constraints", f"occupant:{occupant_id}:implementation-constraints", {"bindings": [{key: binding.get(key) for key in ("binding_id", "purpose", "implementation_id", "implementation_key", "implementation_class", "implementation_version", "policy_ref")} for binding in bindings], "implementation_ref": implementation_ref}, authority="IMPLEMENTATION_HISTORY" if bindings else None, confidence="medium" if bindings else None, classification=occupant["classification"], version=str(occupant.get("version", 1)), source_ref=str(occupant.get("provenance_id", "")), reason="implementation constraints are separate from occupant identity", mandatory="implementation_constraints" in rules["mandatory"])
        if assignment:
            add("current_assignment", f"assignment:{assignment.objective_ref}", {"objective_ref": assignment.objective_ref, "stage_ref": assignment.stage_ref, "instruction": assignment.instruction, "accepted_constraints": list(assignment.accepted_constraints), "artifact_refs": list(assignment.artifact_refs), "collaborator_ids": list(assignment.collaborator_ids), "authority_ref": assignment.authority_ref, "expected_output": assignment.expected_output}, authority="ACCEPTED_INSTITUTIONAL_DECISION", confidence="high", classification="internal", version="1", source_ref=assignment.objective_ref, reason="explicit current assignment; not resident identity", mandatory="current_assignment" in rules["mandatory"])

        for claim in projection.get("claims", []):
            if claim.get("status") not in {"accepted", "unresolved", "contradicted"}:
                continue
            layer = "uncertainty_conflict" if claim.get("status") in {"unresolved", "contradicted"} else "professional_doctrine" if claim.get("predicate") in {"doctrine", "professional_method"} else "identity_anchor"
            mandatory = layer in rules["mandatory"] and layer in {"identity_anchor", "authority_anchor"}
            add(layer, f"claim:{claim['claim_id']}", {"predicate": claim["predicate"], "value": claim.get("value"), "status": claim["status"], "contradiction_group_id": claim.get("contradiction_group_id"), "supersedes_claim_id": claim.get("supersedes_claim_id")}, authority=claim.get("authority_class"), confidence=claim.get("confidence"), classification=claim["provenance"]["classification"], version=str(claim["provenance"].get("source_revision") or "1"), source_ref=claim["provenance"]["source_key"], reason="accepted claim or explicit unresolved conflict", mandatory=mandatory)
        for state in projection.get("state_records", []):
            layer = "professional_methods" if state["state_class"] == "professional_methods" else "episodic_history" if state["state_class"] in {"episodic_institutional_history", "reflection_renewal", "lessons_learned"} else "professional_doctrine" if state["state_class"] == "professional_doctrine" else "relationship_context" if state["state_class"] == "relationship_state" else "artifact_material"
            add(layer, f"state:{state['state_id']}", {"state_class": state["state_class"], "value_ref": state["value_ref"], "metadata": state["bounded_metadata"], "status": state["status"]}, authority=None, confidence=None, classification=state["classification"], version=str(state["state_id"]), source_ref=state["provenance_id"], reason="purpose-eligible structured state reference", mandatory=False)
        selected_relationships = 0
        for relationship in projection.get("relationships", []):
            relevant = not current_participants or UUID(relationship["subject_a_id"]) in current_participants or UUID(relationship["subject_b_id"]) in current_participants
            if not relevant or selected_relationships >= budget.max_relationships:
                excluded.append({"item_id": f"relationship:{relationship['relationship_id']}", "layer": "relationship_context", "reason": "not relevant or relationship budget exhausted"})
                continue
            selected_relationships += 1
            add("relationship_context", f"relationship:{relationship['relationship_id']}", {key: relationship[key] for key in ("relationship_id", "subject_a_type", "subject_a_id", "subject_b_type", "subject_b_id", "relationship_type", "status", "effective_from", "effective_to", "authority_ref", "visibility_policy_ref")}, authority=None, confidence=None, classification=relationship["classification"], version="1", source_ref=relationship["provenance_id"], reason="current participant/task relationship relevance", mandatory=False)
        selected_artifacts = 0
        for artifact in projection.get("artifacts", []):
            if selected_artifacts >= budget.max_artifacts:
                excluded.append({"item_id": f"artifact:{artifact['artifact_id']}", "layer": "artifact_material", "reason": "artifact budget exhausted"})
                continue
            relevant = not assignment or not assignment.artifact_refs or artifact["artifact_key"] in assignment.artifact_refs or artifact["source_location"] in assignment.artifact_refs or artifact["artifact_type"] in {"recovery_corpus", "professional_method"}
            if not relevant:
                excluded.append({"item_id": f"artifact:{artifact['artifact_id']}", "layer": "artifact_material", "reason": "artifact is not relevant to purpose/assignment"})
                continue
            if artifact["availability"] != "available" or artifact["retrieval_eligibility"] != "eligible":
                excluded.append({"item_id": f"artifact:{artifact['artifact_id']}", "layer": "artifact_material", "reason": "artifact unavailable or retrieval-ineligible"})
                continue
            expectation = next((entry for entry in (assignment.artifact_expectations if assignment else ()) if entry[0] == artifact["artifact_key"]), None)
            if expectation and ((expectation[1] and expectation[1] != artifact["logical_version"]) or (expectation[2] and expectation[2] != artifact["content_hash"])):
                raise ContextAssemblyError("artifact-revision-mismatch", f"artifact {artifact['artifact_key']} does not match the requested revision/hash.")
            selected_artifacts += 1
            add("artifact_material", f"artifact:{artifact['artifact_id']}", {key: artifact[key] for key in ("artifact_id", "artifact_key", "artifact_type", "logical_version", "content_hash", "repository_or_store", "source_location", "canonical_revision", "historical_revision", "availability", "storage_class", "retrieval_eligibility")}, authority="VERIFIED_PRIMARY_HISTORICAL_EVIDENCE" if artifact["artifact_type"] in {"recovery_corpus", "historical_evidence"} else None, confidence="high", classification=artifact["classification"], version=artifact["logical_version"], source_ref=artifact["provenance_id"], reason="stable artifact reference selected by purpose and eligibility", mandatory=False, representation="metadata_only", protected_reference=artifact["storage_class"] == "protected_local")
        for contradiction in projection.get("contradictions", []):
            add("uncertainty_conflict", f"contradiction:{contradiction['contradiction_group_id']}", {key: contradiction[key] for key in ("contradiction_group_id", "subject_type", "subject_id", "status", "resolution_ref")}, authority="UNCERTAIN_OR_CONFLICTING_EVIDENCE", confidence="unresolved", classification="internal", version="1", source_ref=contradiction["provenance_id"], reason="preserve relevant unresolved contradiction without choosing a winner", mandatory=False)

        return self._finalize(occupant_id, occupancy, purpose, rules, budget, items, decisions, excluded, projection, assignment, correlation_id, causation_id)

    def _finalize(self, occupant_id: UUID, occupancy: Mapping[str, Any] | None, purpose: str, rules: Mapping[str, tuple[str, ...]], budget: BudgetSpec, items: list[ContextItem], decisions: list[PolicyDecision], excluded: list[dict[str, str]], projection: Mapping[str, Any], assignment: AssignmentContext | None, correlation_id: UUID | None, causation_id: UUID | None) -> ContextBundle:
        mandatory = [item for item in items if item.mandatory]
        if sum(item.units for item in mandatory) > budget.total_units - budget.reserved_task_units:
            raise ContextAssemblyError("mandatory-context-truncated", "mandatory context cannot fit after task reservation.")
        selected: list[ContextItem] = []
        used = 0
        layer_used: dict[str, int] = {}
        counters = {"artifact_material": 0, "episodic_history": 0, "relationship_context": 0, "uncertainty_conflict": 0}
        ordered = sorted(items, key=lambda item: (0 if item.mandatory else 1, item.priority_tier, item.item_id))
        for item in ordered:
            if item.layer in counters and counters[item.layer] >= getattr(budget, {"artifact_material": "max_artifacts", "episodic_history": "max_history", "relationship_context": "max_relationships", "uncertainty_conflict": "max_uncertainties"}[item.layer]):
                if not item.mandatory:
                    excluded.append({"item_id": item.item_id, "layer": item.layer, "reason": "class-specific budget exhausted"})
                    continue
            limit = budget.layer_limit(item.layer)
            if limit is not None and layer_used.get(item.layer, 0) + item.units > limit:
                if item.mandatory:
                    raise ContextAssemblyError("mandatory-context-truncated", f"mandatory layer {item.layer} exceeds its budget.")
                excluded.append({"item_id": item.item_id, "layer": item.layer, "reason": "per-layer budget exhausted"})
                continue
            if used + item.units > budget.total_units - budget.reserved_task_units:
                if item.mandatory:
                    raise ContextAssemblyError("mandatory-context-truncated", "mandatory item exceeded context budget.")
                excluded.append({"item_id": item.item_id, "layer": item.layer, "reason": "optional context shed under budget pressure"})
                continue
            selected.append(item)
            used += item.units
            layer_used[item.layer] = layer_used.get(item.layer, 0) + item.units
            if item.layer in counters:
                counters[item.layer] += 1
        dependency_refs = [str(projection["occupant"]["provenance_id"]), str(projection["occupant"].get("version", 1))]
        if occupancy:
            dependency_refs.extend((str(occupancy["occupancy_id"]), str(occupancy["provenance_id"])))
        dependency_refs.extend(item.source_ref for item in selected)
        if assignment:
            dependency_refs.append(assignment.objective_ref)
        dependency_refs = sorted(set(dependency_refs))
        fingerprint = hashlib.sha256("|".join(dependency_refs + [purpose, self.policy.policy_version]).encode()).hexdigest()
        bundle = ContextBundle(uuid4(), occupant_id, UUID(occupancy["office_id"]) if occupancy else None, purpose, f"{CONTEXT_CONTRACT_VERSION}:{purpose}:1", self.clock(), self.policy.policy_version, tuple(selected), tuple(decisions), tuple(excluded), {"total_units": budget.total_units, "reserved_task_units": budget.reserved_task_units, "available_units": budget.total_units - budget.reserved_task_units, "used_units": used, "mandatory_units": sum(item.units for item in mandatory), "optional_shed_count": sum(1 for entry in excluded if "budget" in entry["reason"] or "shed" in entry["reason"]), "per_layer_units": layer_used}, tuple(dependency_refs), fingerprint, {"bundle_id": "assigned-after-construction", "candidate_count": len(items), "accepted_count": len(selected), "rejected_count": len(excluded), "mandatory_items": [item.item_id for item in mandatory], "excluded_reasons": list(excluded), "artifact_revisions": [item.version for item in selected if item.layer == "artifact_material"], "profile_version": f"{CONTEXT_CONTRACT_VERSION}:{purpose}:1", "policy_version": self.policy.policy_version, "correlation_id": str(correlation_id) if correlation_id else None, "causation_id": str(causation_id) if causation_id else None, "implementation_version": IMPLEMENTATION_VERSION}, ())
        object.__setattr__(bundle, "audit_provenance", {**bundle.audit_provenance, "bundle_id": str(bundle.bundle_id), "dependency_fingerprint": fingerprint})
        if self.event_sink:
            self.event_sink.emit("resident.rehydration.requested", bundle, correlation_id=correlation_id, causation_id=causation_id)
            self.event_sink.emit("resident.context.assembled", bundle, correlation_id=correlation_id, causation_id=causation_id)
        return bundle
