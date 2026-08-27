"""F1 cognition-tier and reasoning-envelope contracts.

These contracts describe resident cognition capability requests and bounded
results. They do not select or invoke a provider, model, endpoint, GPU, or
resource scheduler. Provider-neutral ReasoningRequest/ReasoningResponse remain
backward-compatible adapter envelopes; these types are the resident-facing F1
contract layer used by later cognition packages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from .contracts import ALLOWED_CLASSIFICATIONS, MAX_REFS, _bounded_text

COGNITION_CONTRACT_VERSION = "riverview-cognition-f1-v1"
MAX_PACKET_TEXT = 4_000
MAX_REASONING_TEXT = 8_000
MAX_CONSTRAINTS = 32
MAX_EXCLUSIONS = 32
MAX_CONTEXT_REFS = 64
MAX_CONTEXT_CHARS = 64_000
MAX_PRIORITY = 100
PACKET_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class CognitionTier(StrEnum):
    """Capability class, deliberately independent of physical topology."""

    HOME_COGNITION = "HOME_COGNITION"
    HIGH_REASONING = "HIGH_REASONING"
    EXTERNAL_ESCALATION = "EXTERNAL_ESCALATION"


class EscalationDecision(StrEnum):
    """Outcome of the separate belief, policy, and capacity assessment."""

    DETERMINISTIC = "deterministic"
    HOME_DECISION = "home_decision"
    HIGH_REASONING_REQUIRED = "high_reasoning_required"
    EXTERNAL_ADVISORY_REQUIRED = "external_advisory_required"
    STEWARD_REQUIRED = "steward_required"
    POLICY_DENIED = "policy_denied"
    CAPACITY_UNAVAILABLE = "capacity_unavailable"


class CognitionResultStatus(StrEnum):
    """Truthful terminal/request outcomes; success is never implied by shape."""

    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
    DENIED = "denied"
    TIMEOUT = "timeout"
    MALFORMED = "malformed"
    POLICY_REFUSED = "policy_refused"
    CAPACITY_UNAVAILABLE = "capacity_unavailable"
    CLASSIFICATION_REFUSED = "classification_refused"
    CORRELATION_MISMATCH = "correlation_mismatch"
    EXPIRED = "expired"


class CognitionActorClass(StrEnum):
    """Attribution classes needed by the later F2 provenance event layer."""

    DETERMINISTIC_SUBSTRATE = "deterministic_substrate"
    GRACE_HOME_COGNITION = "grace_home_cognition"
    GRACE_HIGH_REASONING = "grace_high_reasoning"
    EXTERNAL_REASONING = "external_reasoning"
    CODEX_WORKER_EXECUTION = "codex_worker_execution"
    ENGINEERING_VALIDATION = "engineering_validation"
    STEWARD_DECISION = "steward_decision"


class CognitionFailureCode(StrEnum):
    """Failure vocabulary shared by unavailable/failed result envelopes."""

    UNAVAILABLE = "unavailable"
    DENIED = "denied"
    TIMEOUT = "timeout"
    MALFORMED_RESPONSE = "malformed_response"
    POLICY_REFUSED = "policy_refused"
    CAPACITY_UNAVAILABLE = "capacity_unavailable"
    CLASSIFICATION_REFUSED = "classification_refused"
    CORRELATION_MISMATCH = "correlation_mismatch"
    EXPIRED_REQUEST = "expired_request"


_ADVISORY_AUTHORITY = frozenset({"read:bounded", "return:advisory", "return:diagnostic"})
_FAILURE_STATUSES = frozenset(item for item in CognitionResultStatus if item != CognitionResultStatus.COMPLETED)


def _uuid(value: UUID, name: str) -> None:
    if not isinstance(value, UUID):
        raise ValueError(f"RIV-COG-0001: {name} must be a UUID.")


def _optional_uuid(value: UUID | None, name: str) -> None:
    if value is not None:
        _uuid(value, name)


def _aware(value: datetime, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"RIV-COG-0001: {name} must be timezone-aware.")


def _future(value: datetime, name: str) -> None:
    _aware(value, name)
    if value <= datetime.now(UTC):
        raise ValueError(f"RIV-COG-0002: {name} is expired.")


def _past_or_present(value: datetime, name: str) -> None:
    _aware(value, name)
    if value > datetime.now(UTC):
        raise ValueError(f"RIV-COG-0001: {name} cannot be in the future.")


def _refs(values: tuple[str, ...], name: str, limit: int = MAX_REFS) -> None:
    if not isinstance(values, tuple) or len(values) > limit:
        raise ValueError(f"RIV-COG-0001: {name} exceeds its bound.")
    if not all(isinstance(item, str) and item.strip() and len(item) <= 500 for item in values):
        raise ValueError(f"RIV-COG-0001: {name} contains an invalid reference.")


def _context_refs(values: tuple[str, ...], name: str) -> None:
    """Validate reference-only context and its aggregate bound."""

    _refs(values, name, MAX_CONTEXT_REFS)


def _context_texts(values: tuple[str, ...], name: str) -> None:
    """Validate bounded context text and prevent collection aggregation bypasses."""

    _texts(values, name, MAX_CONTEXT_REFS)
    if sum(len(item) for item in values) > MAX_CONTEXT_CHARS:
        raise ValueError(f"RIV-COG-0001: {name} exceeds its aggregate context bound.")


def _packet_context_total(*values: str | None | tuple[str, ...]) -> None:
    total = 0
    for value in values:
        if isinstance(value, tuple):
            total += sum(len(item) for item in value)
        elif value is not None:
            total += len(value)
    if total > MAX_CONTEXT_CHARS:
        raise ValueError("RIV-COG-0001: packet context exceeds its aggregate bound.")


def _texts(values: tuple[str, ...], name: str, limit: int = MAX_CONSTRAINTS) -> None:
    if not isinstance(values, tuple) or len(values) > limit:
        raise ValueError(f"RIV-COG-0001: {name} exceeds its bound.")
    if not all(isinstance(item, str) and item.strip() and len(item) <= MAX_PACKET_TEXT for item in values):
        raise ValueError(f"RIV-COG-0001: {name} contains invalid bounded text.")


def _tier(value: CognitionTier | str, name: str = "cognition_tier") -> CognitionTier:
    try:
        return value if isinstance(value, CognitionTier) else CognitionTier(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"RIV-COG-0001: {name} is unsupported.") from exc


def _enum(value: Any, enum_type: type[StrEnum], name: str) -> StrEnum:
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"RIV-COG-0001: {name} is unsupported.") from exc


def _classification(value: str) -> None:
    if value not in ALLOWED_CLASSIFICATIONS:
        raise ValueError("RIV-COG-0003: classification is not eligible.")


@dataclass(frozen=True, slots=True)
class ResidentReasoningPacket:
    """Bounded, source-referenced context for one cognition operation."""

    packet_id: UUID
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    source_cognition_event_id: UUID
    objective_id: UUID
    authority_ref: str
    cognition_tier: CognitionTier
    request_class: str
    objective: str
    question: str
    operational_state_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    constraints: tuple[str, ...]
    authoritative_current_state_refs: tuple[str, ...]
    unresolved_ambiguity: tuple[str, ...]
    relevant_prior_decisions: tuple[str, ...]
    known_deterministic_results: tuple[str, ...]
    home_assessment: str
    requested_output_schema: str
    egress_policy: str
    max_budget: int
    classification: str
    correlation_id: UUID
    packet_digest: str
    expires_at: datetime
    source_context_id: UUID | None = None
    causation_id: UUID | None = None
    context_material: tuple[str, ...] = ()
    conversation_context: tuple[str, ...] = ()
    contract_version: str = COGNITION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        for value, name in ((self.packet_id, "packet_id"), (self.resident_id, "resident_id"), (self.occupant_id, "occupant_id"), (self.office_id, "office_id"), (self.implementation_id, "implementation_id"), (self.source_cognition_event_id, "source_cognition_event_id"), (self.objective_id, "objective_id"), (self.correlation_id, "correlation_id")):
            _uuid(value, name)
        _optional_uuid(self.source_context_id, "source_context_id")
        _optional_uuid(self.causation_id, "causation_id")
        _context_texts(self.context_material, "context_material")
        _context_texts(self.conversation_context, "conversation_context")
        _bounded_text(self.authority_ref, "authority_ref", 500)
        object.__setattr__(self, "cognition_tier", _tier(self.cognition_tier))
        _bounded_text(self.request_class, "request_class", 200)
        _bounded_text(self.objective, "objective", MAX_PACKET_TEXT)
        _bounded_text(self.question, "question", MAX_PACKET_TEXT)
        _context_refs(self.operational_state_refs, "operational_state_refs")
        _context_refs(self.evidence_refs, "evidence_refs")
        _context_texts(self.constraints, "constraints")
        _context_refs(self.authoritative_current_state_refs, "authoritative_current_state_refs")
        _context_texts(self.unresolved_ambiguity, "unresolved_ambiguity")
        _context_refs(self.relevant_prior_decisions, "relevant_prior_decisions")
        _context_texts(self.known_deterministic_results, "known_deterministic_results")
        for value, name in ((self.home_assessment, "home_assessment"), (self.requested_output_schema, "requested_output_schema"), (self.egress_policy, "egress_policy")):
            _bounded_text(value, name, MAX_PACKET_TEXT)
        if not isinstance(self.max_budget, int) or not 0 < self.max_budget <= MAX_CONTEXT_CHARS:
            raise ValueError("RIV-COG-0001: max_budget is outside its bound.")
        _packet_context_total(self.objective, self.question, self.operational_state_refs, self.constraints, self.authoritative_current_state_refs, self.evidence_refs, self.unresolved_ambiguity, self.relevant_prior_decisions, self.known_deterministic_results, self.home_assessment, self.requested_output_schema, self.egress_policy)
        _classification(self.classification)
        if not isinstance(self.packet_digest, str) or not PACKET_DIGEST_PATTERN.fullmatch(self.packet_digest):
            raise ValueError("RIV-COG-0001: packet_digest must be a SHA-256 hexadecimal digest.")
        _future(self.expires_at, "expires_at")
        _bounded_text(self.contract_version, "contract_version", 100)

    def as_typed_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.contract_version,
            "packet_id": str(self.packet_id),
            "resident_id": str(self.resident_id),
            "occupant_id": str(self.occupant_id),
            "office_id": str(self.office_id),
            "implementation_id": str(self.implementation_id),
            "source_cognition_event_id": str(self.source_cognition_event_id),
            "objective_id": str(self.objective_id),
            "authority_ref": self.authority_ref,
            "cognition_tier": self.cognition_tier.value,
            "request_class": self.request_class,
            "objective": self.objective,
            "question": self.question,
            "operational_state_refs": list(self.operational_state_refs),
            "evidence_refs": list(self.evidence_refs),
            "constraints": list(self.constraints),
            "authoritative_current_state_refs": list(self.authoritative_current_state_refs),
            "unresolved_ambiguity": list(self.unresolved_ambiguity),
            "relevant_prior_decisions": list(self.relevant_prior_decisions),
            "known_deterministic_results": list(self.known_deterministic_results),
            "home_assessment": self.home_assessment,
            "requested_output_schema": self.requested_output_schema,
            "egress_policy": self.egress_policy,
            "max_budget": self.max_budget,
            "classification": self.classification,
            "correlation_id": str(self.correlation_id),
            "causation_id": str(self.causation_id) if self.causation_id else None,
            "source_context_id": str(self.source_context_id) if self.source_context_id else None,
            "context_material": list(self.context_material),
            "conversation_context": list(self.conversation_context),
            "packet_digest": self.packet_digest,
            "expires_at": self.expires_at.isoformat(),
        }

    @classmethod
    def from_typed_payload(cls, payload: dict[str, Any]) -> "ResidentReasoningPacket":
        _payload_version(payload)
        return cls(
            packet_id=_payload_uuid(payload, "packet_id"),
            resident_id=_payload_uuid(payload, "resident_id"),
            occupant_id=_payload_uuid(payload, "occupant_id"),
            office_id=_payload_uuid(payload, "office_id"),
            implementation_id=_payload_uuid(payload, "implementation_id"),
            source_cognition_event_id=_payload_uuid(payload, "source_cognition_event_id"),
            objective_id=_payload_uuid(payload, "objective_id"),
            authority_ref=payload["authority_ref"],
            cognition_tier=payload["cognition_tier"],
            request_class=payload["request_class"],
            objective=payload["objective"],
            question=payload["question"],
            operational_state_refs=_payload_tuple(payload, "operational_state_refs"),
            evidence_refs=_payload_tuple(payload, "evidence_refs"),
            constraints=_payload_tuple(payload, "constraints"),
            authoritative_current_state_refs=_payload_tuple(payload, "authoritative_current_state_refs"),
            unresolved_ambiguity=_payload_tuple(payload, "unresolved_ambiguity"),
            relevant_prior_decisions=_payload_tuple(payload, "relevant_prior_decisions"),
            known_deterministic_results=_payload_tuple(payload, "known_deterministic_results"),
            home_assessment=payload["home_assessment"],
            requested_output_schema=payload["requested_output_schema"],
            egress_policy=payload["egress_policy"],
            max_budget=payload["max_budget"],
            classification=payload["classification"],
            correlation_id=_payload_uuid(payload, "correlation_id"),
            packet_digest=payload["packet_digest"],
            expires_at=_payload_datetime(payload, "expires_at"),
            source_context_id=_payload_optional_uuid(payload, "source_context_id"),
            causation_id=_payload_optional_uuid(payload, "causation_id"),
            context_material=_payload_tuple(payload, "context_material"),
            conversation_context=_payload_tuple(payload, "conversation_context"),
            contract_version=payload["schema_version"],
        )


@dataclass(frozen=True, slots=True)
class EscalationAssessment:
    """Separate home belief, policy permission, and capacity eligibility."""

    assessment_id: UUID
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    authority_ref: str
    source_cognition_event_id: UUID
    packet_id: UUID
    objective_id: UUID
    correlation_id: UUID
    question: str
    authoritative_current_state_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    constraints: tuple[str, ...]
    home_belief: bool
    home_belief_reason: str
    policy_permitted: bool
    policy_reason: str
    capacity_eligible: bool
    capacity_reason: str
    decision: EscalationDecision
    reason_class: str
    policy_ref: str
    provenance_refs: tuple[str, ...]
    classification: str
    created_at: datetime
    expires_at: datetime
    target_tier: CognitionTier | None = None
    contract_version: str = COGNITION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        for value, name in ((self.assessment_id, "assessment_id"), (self.resident_id, "resident_id"), (self.occupant_id, "occupant_id"), (self.office_id, "office_id"), (self.implementation_id, "implementation_id"), (self.source_cognition_event_id, "source_cognition_event_id"), (self.packet_id, "packet_id"), (self.objective_id, "objective_id"), (self.correlation_id, "correlation_id")):
            _uuid(value, name)
        for value, name in ((self.authority_ref, "authority_ref"), (self.question, "question"), (self.home_belief_reason, "home_belief_reason"), (self.policy_reason, "policy_reason"), (self.capacity_reason, "capacity_reason"), (self.reason_class, "reason_class"), (self.policy_ref, "policy_ref")):
            _bounded_text(value, name, 1_000)
        _context_refs(self.authoritative_current_state_refs, "authoritative_current_state_refs")
        _context_refs(self.evidence_refs, "evidence_refs")
        _context_texts(self.constraints, "constraints")
        _refs(self.provenance_refs, "provenance_refs")
        object.__setattr__(self, "decision", _enum(self.decision, EscalationDecision, "decision"))
        if self.target_tier is not None:
            object.__setattr__(self, "target_tier", _tier(self.target_tier, "target_tier"))
            if self.target_tier not in {CognitionTier.HIGH_REASONING, CognitionTier.EXTERNAL_ESCALATION}:
                raise ValueError("RIV-COG-0001: escalation target tier is not an escalation tier.")
        if not self.home_belief and self.target_tier is not None:
            raise ValueError("RIV-COG-0004: a non-belief cannot target stronger cognition.")
        if not isinstance(self.home_belief, bool) or not isinstance(self.policy_permitted, bool) or not isinstance(self.capacity_eligible, bool):
            raise ValueError("RIV-COG-0001: escalation outcomes must be boolean.")
        if not self.policy_permitted and self.decision not in {EscalationDecision.POLICY_DENIED, EscalationDecision.STEWARD_REQUIRED}:
            raise ValueError("RIV-COG-0004: denied policy cannot produce an executable escalation decision.")
        _classification(self.classification)
        _aware(self.created_at, "created_at")
        _future(self.expires_at, "expires_at")
        if self.expires_at <= self.created_at:
            raise ValueError("RIV-COG-0001: escalation expiry must follow creation.")
        _bounded_text(self.contract_version, "contract_version", 100)

    def as_typed_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.contract_version,
            "assessment_id": str(self.assessment_id),
            "resident_id": str(self.resident_id),
            "occupant_id": str(self.occupant_id),
            "office_id": str(self.office_id),
            "implementation_id": str(self.implementation_id),
            "authority_ref": self.authority_ref,
            "source_cognition_event_id": str(self.source_cognition_event_id),
            "packet_id": str(self.packet_id),
            "objective_id": str(self.objective_id),
            "correlation_id": str(self.correlation_id),
            "question": self.question,
            "authoritative_current_state_refs": list(self.authoritative_current_state_refs),
            "evidence_refs": list(self.evidence_refs),
            "constraints": list(self.constraints),
            "home_belief": self.home_belief,
            "home_belief_reason": self.home_belief_reason,
            "policy_permitted": self.policy_permitted,
            "policy_reason": self.policy_reason,
            "capacity_eligible": self.capacity_eligible,
            "capacity_reason": self.capacity_reason,
            "decision": self.decision.value,
            "reason_class": self.reason_class,
            "target_tier": self.target_tier.value if self.target_tier else None,
            "policy_ref": self.policy_ref,
            "provenance_refs": list(self.provenance_refs),
            "classification": self.classification,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }

    @classmethod
    def from_typed_payload(cls, payload: dict[str, Any]) -> "EscalationAssessment":
        _payload_version(payload)
        return cls(
            assessment_id=_payload_uuid(payload, "assessment_id"),
            resident_id=_payload_uuid(payload, "resident_id"),
            occupant_id=_payload_uuid(payload, "occupant_id"),
            office_id=_payload_uuid(payload, "office_id"),
            implementation_id=_payload_uuid(payload, "implementation_id"),
            authority_ref=payload["authority_ref"],
            source_cognition_event_id=_payload_uuid(payload, "source_cognition_event_id"),
            packet_id=_payload_uuid(payload, "packet_id"),
            objective_id=_payload_uuid(payload, "objective_id"),
            correlation_id=_payload_uuid(payload, "correlation_id"),
            question=payload["question"],
            authoritative_current_state_refs=_payload_tuple(payload, "authoritative_current_state_refs"),
            evidence_refs=_payload_tuple(payload, "evidence_refs"),
            constraints=_payload_tuple(payload, "constraints"),
            home_belief=payload["home_belief"],
            home_belief_reason=payload["home_belief_reason"],
            policy_permitted=payload["policy_permitted"],
            policy_reason=payload["policy_reason"],
            capacity_eligible=payload["capacity_eligible"],
            capacity_reason=payload["capacity_reason"],
            decision=payload["decision"],
            reason_class=payload["reason_class"],
            policy_ref=payload["policy_ref"],
            provenance_refs=_payload_tuple(payload, "provenance_refs"),
            classification=payload["classification"],
            created_at=_payload_datetime(payload, "created_at"),
            expires_at=_payload_datetime(payload, "expires_at"),
            target_tier=payload.get("target_tier"),
            contract_version=payload["schema_version"],
        )


@dataclass(frozen=True, slots=True)
class CapabilityResourceRequest:
    """A topology-neutral request for a cognition capability class."""

    request_id: UUID
    correlation_id: UUID
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    authority_ref: str
    cognition_tier: CognitionTier
    required_capability: str
    classification: str
    policy_ref: str
    authorization_ref: str
    packet_id: UUID | None = None
    priority: int | None = None
    deadline_at: datetime | None = None
    latency_requirement: str | None = None
    exclusions: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    contract_version: str = COGNITION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        for value, name in ((self.request_id, "request_id"), (self.correlation_id, "correlation_id"), (self.resident_id, "resident_id"), (self.occupant_id, "occupant_id"), (self.office_id, "office_id"), (self.implementation_id, "implementation_id")):
            _uuid(value, name)
        _optional_uuid(self.packet_id, "packet_id")
        object.__setattr__(self, "cognition_tier", _tier(self.cognition_tier))
        _bounded_text(self.required_capability, "required_capability", 500)
        _classification(self.classification)
        _bounded_text(self.authority_ref, "authority_ref", 500)
        _bounded_text(self.policy_ref, "policy_ref", 500)
        _bounded_text(self.authorization_ref, "authorization_ref", 500)
        if self.priority is not None and (not isinstance(self.priority, int) or not 0 <= self.priority <= MAX_PRIORITY):
            raise ValueError("RIV-COG-0001: priority is outside its bound.")
        if self.deadline_at is not None:
            _future(self.deadline_at, "deadline_at")
        if self.latency_requirement is not None:
            _bounded_text(self.latency_requirement, "latency_requirement", 200)
        _refs(self.exclusions, "exclusions", MAX_EXCLUSIONS)
        _texts(self.constraints, "constraints")
        _bounded_text(self.contract_version, "contract_version", 100)

    def as_typed_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.contract_version,
            "request_id": str(self.request_id),
            "correlation_id": str(self.correlation_id),
            "resident_id": str(self.resident_id),
            "occupant_id": str(self.occupant_id),
            "office_id": str(self.office_id),
            "implementation_id": str(self.implementation_id),
            "authority_ref": self.authority_ref,
            "cognition_tier": self.cognition_tier.value,
            "required_capability": self.required_capability,
            "classification": self.classification,
            "policy_ref": self.policy_ref,
            "authorization_ref": self.authorization_ref,
            "packet_id": str(self.packet_id) if self.packet_id else None,
            "priority": self.priority,
            "deadline_at": self.deadline_at.isoformat() if self.deadline_at else None,
            "latency_requirement": self.latency_requirement,
            "exclusions": list(self.exclusions),
            "constraints": list(self.constraints),
        }

    @classmethod
    def from_typed_payload(cls, payload: dict[str, Any]) -> "CapabilityResourceRequest":
        _payload_version(payload)
        deadline = payload.get("deadline_at")
        return cls(
            request_id=_payload_uuid(payload, "request_id"),
            correlation_id=_payload_uuid(payload, "correlation_id"),
            resident_id=_payload_uuid(payload, "resident_id"),
            occupant_id=_payload_uuid(payload, "occupant_id"),
            office_id=_payload_uuid(payload, "office_id"),
            implementation_id=_payload_uuid(payload, "implementation_id"),
            authority_ref=payload["authority_ref"],
            cognition_tier=payload["cognition_tier"],
            required_capability=payload["required_capability"],
            classification=payload["classification"],
            policy_ref=payload["policy_ref"],
            authorization_ref=payload["authorization_ref"],
            packet_id=_payload_optional_uuid(payload, "packet_id"),
            priority=payload.get("priority"),
            deadline_at=datetime.fromisoformat(deadline) if deadline else None,
            latency_requirement=payload.get("latency_requirement"),
            exclusions=_payload_tuple(payload, "exclusions"),
            constraints=_payload_tuple(payload, "constraints"),
            contract_version=payload["schema_version"],
        )


@dataclass(frozen=True, slots=True)
class CognitionResult:
    """Typed advisory result, including truthful failure outcomes."""

    result_id: UUID
    request_id: UUID
    correlation_id: UUID
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    authority_ref: str
    source_cognition_event_id: UUID
    cognition_tier: CognitionTier
    status: CognitionResultStatus
    recommendation: str | None
    rationale: str | None
    uncertainty: str | None
    confidence: float | None
    constraints: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    further_escalation_warranted: bool
    provider_ref: str | None
    resource_class_ref: str | None
    packet_id: UUID | None
    policy_decision_ref: str | None
    provenance_refs: tuple[str, ...]
    live_generation: bool
    actor_class: CognitionActorClass
    classification: str
    created_at: datetime
    expires_at: datetime | None = None
    authority_scope: tuple[str, ...] = ("return:advisory",)
    failure_code: CognitionFailureCode | None = None
    failure_reason: str | None = None
    contract_version: str = COGNITION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        for value, name in ((self.result_id, "result_id"), (self.request_id, "request_id"), (self.correlation_id, "correlation_id"), (self.resident_id, "resident_id"), (self.occupant_id, "occupant_id"), (self.office_id, "office_id"), (self.implementation_id, "implementation_id"), (self.source_cognition_event_id, "source_cognition_event_id")):
            _uuid(value, name)
        _optional_uuid(self.packet_id, "packet_id")
        object.__setattr__(self, "cognition_tier", _tier(self.cognition_tier))
        object.__setattr__(self, "status", _enum(self.status, CognitionResultStatus, "status"))
        object.__setattr__(self, "actor_class", _enum(self.actor_class, CognitionActorClass, "actor_class"))
        _bounded_text(self.authority_ref, "authority_ref", 500)
        if self.failure_code is not None:
            object.__setattr__(self, "failure_code", _enum(self.failure_code, CognitionFailureCode, "failure_code"))
        _optional_bounded(self.recommendation, "recommendation", MAX_REASONING_TEXT)
        _optional_bounded(self.rationale, "rationale", MAX_REASONING_TEXT)
        _optional_bounded(self.uncertainty, "uncertainty", MAX_REASONING_TEXT)
        if self.confidence is not None and (not isinstance(self.confidence, (int, float)) or not 0 <= self.confidence <= 1):
            raise ValueError("RIV-COG-0001: confidence must be between zero and one.")
        _texts(self.constraints, "constraints")
        _texts(self.unresolved_questions, "unresolved_questions")
        if not isinstance(self.further_escalation_warranted, bool):
            raise ValueError("RIV-COG-0001: further_escalation_warranted must be boolean.")
        _optional_bounded(self.provider_ref, "provider_ref", 500)
        _optional_bounded(self.resource_class_ref, "resource_class_ref", 500)
        _optional_bounded(self.policy_decision_ref, "policy_decision_ref", 500)
        _refs(self.provenance_refs, "provenance_refs")
        if not isinstance(self.live_generation, bool):
            raise ValueError("RIV-COG-0001: live_generation must be boolean.")
        _classification(self.classification)
        _past_or_present(self.created_at, "created_at")
        if self.expires_at is not None:
            _aware(self.expires_at, "expires_at")
            if self.expires_at <= self.created_at:
                raise ValueError("RIV-COG-0001: result expiry must follow creation.")
        if not isinstance(self.authority_scope, tuple) or not self.authority_scope or not set(self.authority_scope) <= _ADVISORY_AUTHORITY:
            raise ValueError("RIV-COG-0004: reasoning result authority is not advisory-only.")
        _bounded_text(self.contract_version, "contract_version", 100)
        if self.status == CognitionResultStatus.COMPLETED:
            if not self.recommendation or not self.rationale:
                raise ValueError("RIV-COG-0001: completed result requires recommendation and rationale.")
            if self.failure_code is not None or self.failure_reason is not None:
                raise ValueError("RIV-COG-0001: completed result cannot contain failure outcome.")
        else:
            if self.live_generation:
                raise ValueError("RIV-COG-0004: non-success result cannot claim live generation.")
            if self.failure_code is None or not self.failure_reason:
                raise ValueError("RIV-COG-0001: failed result requires failure code and reason.")
        if self.actor_class == CognitionActorClass.DETERMINISTIC_SUBSTRATE and self.live_generation:
            raise ValueError("RIV-COG-0004: deterministic substrate cannot claim live generation.")
        if self.actor_class == CognitionActorClass.GRACE_HOME_COGNITION and self.cognition_tier != CognitionTier.HOME_COGNITION:
            raise ValueError("RIV-COG-0004: home actor and cognition tier mismatch.")
        if self.actor_class == CognitionActorClass.GRACE_HIGH_REASONING and self.cognition_tier != CognitionTier.HIGH_REASONING:
            raise ValueError("RIV-COG-0004: high actor and cognition tier mismatch.")
        if self.actor_class == CognitionActorClass.EXTERNAL_REASONING and self.cognition_tier != CognitionTier.EXTERNAL_ESCALATION:
            raise ValueError("RIV-COG-0004: external actor and cognition tier mismatch.")

    def validate_against(self, request: Any) -> None:
        """Reject identity, tier, correlation, or classification mismatches."""

        for field in ("request_id", "correlation_id", "resident_id", "occupant_id", "office_id", "implementation_id", "authority_ref", "source_cognition_event_id", "cognition_tier", "classification"):
            if not hasattr(request, field):
                continue
            expected = getattr(request, field)
            actual = getattr(self, field)
            if field == "cognition_tier":
                expected = _tier(expected)
            if actual != expected:
                raise ValueError(f"RIV-COG-0005: result/request {field} mismatch.")
        packet_id = getattr(request, "packet_id", None)
        if packet_id is not None and self.packet_id != packet_id:
            raise ValueError("RIV-COG-0005: result/request packet_id mismatch.")

    def as_typed_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.contract_version,
            "result_id": str(self.result_id),
            "request_id": str(self.request_id),
            "correlation_id": str(self.correlation_id),
            "resident_id": str(self.resident_id),
            "occupant_id": str(self.occupant_id),
            "office_id": str(self.office_id),
            "implementation_id": str(self.implementation_id),
            "authority_ref": self.authority_ref,
            "source_cognition_event_id": str(self.source_cognition_event_id),
            "cognition_tier": self.cognition_tier.value,
            "status": self.status.value,
            "recommendation": self.recommendation,
            "rationale": self.rationale,
            "uncertainty": self.uncertainty,
            "confidence": self.confidence,
            "constraints": list(self.constraints),
            "unresolved_questions": list(self.unresolved_questions),
            "further_escalation_warranted": self.further_escalation_warranted,
            "provider_ref": self.provider_ref,
            "resource_class_ref": self.resource_class_ref,
            "packet_id": str(self.packet_id) if self.packet_id else None,
            "policy_decision_ref": self.policy_decision_ref,
            "provenance_refs": list(self.provenance_refs),
            "live_generation": self.live_generation,
            "actor_class": self.actor_class.value,
            "classification": self.classification,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "authority_scope": list(self.authority_scope),
            "failure_code": self.failure_code.value if self.failure_code else None,
            "failure_reason": self.failure_reason,
        }

    @classmethod
    def from_typed_payload(cls, payload: dict[str, Any]) -> "CognitionResult":
        _payload_version(payload)
        expires = payload.get("expires_at")
        return cls(
            result_id=_payload_uuid(payload, "result_id"),
            request_id=_payload_uuid(payload, "request_id"),
            correlation_id=_payload_uuid(payload, "correlation_id"),
            resident_id=_payload_uuid(payload, "resident_id"),
            occupant_id=_payload_uuid(payload, "occupant_id"),
            office_id=_payload_uuid(payload, "office_id"),
            implementation_id=_payload_uuid(payload, "implementation_id"),
            authority_ref=payload["authority_ref"],
            source_cognition_event_id=_payload_uuid(payload, "source_cognition_event_id"),
            cognition_tier=payload["cognition_tier"],
            status=payload["status"],
            recommendation=payload.get("recommendation"),
            rationale=payload.get("rationale"),
            uncertainty=payload.get("uncertainty"),
            confidence=payload.get("confidence"),
            constraints=_payload_tuple(payload, "constraints"),
            unresolved_questions=_payload_tuple(payload, "unresolved_questions"),
            further_escalation_warranted=payload["further_escalation_warranted"],
            provider_ref=payload.get("provider_ref"),
            resource_class_ref=payload.get("resource_class_ref"),
            packet_id=_payload_optional_uuid(payload, "packet_id"),
            policy_decision_ref=payload.get("policy_decision_ref"),
            provenance_refs=_payload_tuple(payload, "provenance_refs"),
            live_generation=payload["live_generation"],
            actor_class=payload["actor_class"],
            classification=payload["classification"],
            created_at=_payload_datetime(payload, "created_at"),
            expires_at=datetime.fromisoformat(expires) if expires else None,
            authority_scope=_payload_tuple(payload, "authority_scope"),
            failure_code=payload.get("failure_code"),
            failure_reason=payload.get("failure_reason"),
            contract_version=payload["schema_version"],
        )


def _optional_bounded(value: str | None, name: str, limit: int) -> None:
    if value is not None:
        _bounded_text(value, name, limit)


def _payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("RIV-COG-0001: typed payload must be an object.")


def _payload_version(payload: dict[str, Any]) -> None:
    _payload(payload)
    if payload.get("schema_version") != COGNITION_CONTRACT_VERSION:
        raise ValueError("RIV-COG-0001: cognition contract version is unsupported.")


def _payload_uuid(payload: dict[str, Any], name: str) -> UUID:
    try:
        value = UUID(str(payload[name]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"RIV-COG-0001: {name} is invalid.") from exc
    return value


def _payload_optional_uuid(payload: dict[str, Any], name: str) -> UUID | None:
    if payload.get(name) is None:
        return None
    return _payload_uuid(payload, name)


def _payload_datetime(payload: dict[str, Any], name: str) -> datetime:
    try:
        value = datetime.fromisoformat(str(payload[name]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"RIV-COG-0001: {name} is invalid.") from exc
    return value


def _payload_tuple(payload: dict[str, Any], name: str) -> tuple[str, ...]:
    value = payload.get(name)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"RIV-COG-0001: {name} must be a list of strings.")
    return tuple(value)


ReasoningResult = CognitionResult
