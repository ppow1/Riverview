"""GRC-003-E2 bounded HIGH_REASONING request path.

E2 consumes an already evaluated P1 escalation assessment.  It owns neither
policy nor resource scheduling and never turns a high-reasoning result into
execution authority.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Protocol
from uuid import UUID, uuid4

from riverview.river import Classification, RiverEvent

from .binding import CapabilityBindingDecision, CognitionBindingAdapter, ProviderResourceCandidate
from .cognition_contracts import (
    CapabilityResourceRequest, CognitionActorClass, CognitionFailureCode,
    CognitionResult, CognitionResultStatus, CognitionTier, EscalationAssessment,
    EscalationDecision, ResidentReasoningPacket,
)
from .contracts import MAX_INSTRUCTION, MAX_REFS, ReasoningRequest, ReasoningResponse
from .provenance import (
    PROVENANCE_AGGREGATE_TYPE, CognitionProvenance, CognitionProvenanceEventType,
    CognitionProvenanceWriter,
)
from .escalation_policy import PolicyDecisionRecorder
from .session import CognitionSession, CognitionSessionBoundary, CognitionSessionTurn

HIGH_REASONING_VERSION = "grace-high-reasoning-e2-v1"
HIGH_REASONING_CAPABILITY = "HIGH_REASONING"
HIGH_REASONING_CHECKPOINT = "RIV-COG-E2-0001"
HIGH_OBSERVATION_EVENT = "cognition.high_generation_observed"
_AUTHORITY = ("return:advisory",)
_KEYS = frozenset({"recommendation", "rationale", "uncertainty", "confidence", "constraints",
                   "unresolved_questions", "further_escalation_warranted", "authority_scope",
                   "live_generation", "provenance_refs"})


class HighReasoningExecutionError(RuntimeError):
    def __init__(self, reason: str, message: str) -> None:
        super().__init__(f"{HIGH_REASONING_CHECKPOINT}: {message}")
        self.reason, self.checkpoint = reason, HIGH_REASONING_CHECKPOINT


class HighReasoningEventStore(Protocol):
    def append(self, event: RiverEvent) -> Any: ...
    def read_aggregate(self, aggregate_type: str, aggregate_id: UUID) -> list[dict[str, Any]]: ...


@dataclass(frozen=True, slots=True)
class HighReasoningInvocation:
    packet: ResidentReasoningPacket
    assessment: EscalationAssessment
    authorization_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.packet, ResidentReasoningPacket) or not isinstance(self.assessment, EscalationAssessment):
            raise HighReasoningExecutionError("invocation-invalid", "packet and P1 assessment are required.")
        if not isinstance(self.authorization_ref, str) or not self.authorization_ref.strip():
            raise HighReasoningExecutionError("authorization-invalid", "high-reasoning authorization is required.")
        a, p = self.assessment, self.packet
        if (a.source_cognition_event_id != p.source_cognition_event_id or a.packet_id != p.packet_id or
                a.correlation_id != p.correlation_id or a.objective_id != p.objective_id or
                a.resident_id != p.resident_id or a.occupant_id != p.occupant_id or
                a.office_id != p.office_id or a.implementation_id != p.implementation_id or
                a.authority_ref != p.authority_ref or a.classification != p.classification):
            raise HighReasoningExecutionError("lineage-mismatch", "P1 assessment does not correspond to packet.")


@dataclass(frozen=True, slots=True)
class HighGenerationObservation:
    observation_id: UUID
    request_id: UUID
    provider_id: str
    resource_class_ref: str
    capacity_observed: int
    latency_ms: float
    outcome: str
    request_evidence_ref: str
    response_evidence_ref: str | None
    finished_at: datetime

    def as_payload(self) -> dict[str, Any]:
        return {"schema_version": HIGH_REASONING_VERSION, "observation_id": str(self.observation_id),
                "request_id": str(self.request_id), "provider_id": self.provider_id,
                "resource_class_ref": self.resource_class_ref, "capacity_observed": self.capacity_observed,
                "latency_ms": self.latency_ms, "outcome": self.outcome,
                "request_evidence_ref": self.request_evidence_ref,
                "response_evidence_ref": self.response_evidence_ref,
                "finished_at": self.finished_at.isoformat()}


@dataclass(frozen=True, slots=True)
class AuthorizedHighReasoningProvider:
    provider_id: str
    authorization_ref: str
    generate: Callable[[ReasoningRequest], ReasoningResponse]


@dataclass(frozen=True, slots=True)
class HighReasoningOutcome:
    status: str
    session: CognitionSession
    turn: CognitionSessionTurn | None
    request: CapabilityResourceRequest
    binding: CapabilityBindingDecision | None
    result: CognitionResult
    observation: HighGenerationObservation | None


class HighReasoningCoordinator:
    """Execute exactly one authorized, bounded E2 high-reasoning request."""

    def __init__(self, *, event_store: HighReasoningEventStore,
                 binding_adapter: CognitionBindingAdapter,
                 provider: AuthorizedHighReasoningProvider,
                 tier: CognitionTier = CognitionTier.HIGH_REASONING,
                 capability: str = HIGH_REASONING_CAPABILITY,
                 actor_class: CognitionActorClass = CognitionActorClass.GRACE_HIGH_REASONING,
                 version: str = HIGH_REASONING_VERSION,
                 observation_event: str = HIGH_OBSERVATION_EVENT,
                 required_decision: EscalationDecision = EscalationDecision.HIGH_REASONING_REQUIRED,
                 clock: Callable[[], datetime] | None = None,
                 monotonic: Callable[[], float] | None = None) -> None:
        self.event_store, self.binding_adapter, self.provider = event_store, binding_adapter, provider
        self.tier, self.capability, self.actor_class = tier, capability, actor_class
        self.version, self.observation_event, self.required_decision = version, observation_event, required_decision
        self.clock, self.monotonic = clock or (lambda: datetime.now(UTC)), monotonic or time.monotonic
        self.sessions, self.provenance = CognitionSessionBoundary(event_store), CognitionProvenanceWriter(event_store)

    def execute(self, invocation: HighReasoningInvocation) -> HighReasoningOutcome:
        p, a = invocation.packet, invocation.assessment
        if (a.decision is not self.required_decision or
                a.target_tier is not self.tier or
                not a.policy_permitted or not a.capacity_eligible):
            raise HighReasoningExecutionError("policy-denied", "accepted P1 high-reasoning authorization is required.")
        if a.expires_at <= self.clock():
            raise HighReasoningExecutionError("stale-lineage", "P1 authorization has expired.")
        session = self.sessions.open(resident_id=p.resident_id, occupant_id=p.occupant_id,
                                     office_id=p.office_id, implementation_id=p.implementation_id,
                                     authority_ref=p.authority_ref,
                                     state_refs=p.authoritative_current_state_refs)
        request = CapabilityResourceRequest(
            request_id=uuid4(), correlation_id=p.correlation_id, resident_id=p.resident_id,
            occupant_id=p.occupant_id, office_id=p.office_id, implementation_id=p.implementation_id,
            authority_ref=p.authority_ref, cognition_tier=self.tier,
            required_capability=self.capability, classification=p.classification,
            policy_ref=a.policy_ref, authorization_ref=invocation.authorization_ref,
            packet_id=p.packet_id, deadline_at=a.expires_at,
            latency_requirement="bounded-high-reasoning", constraints=tuple(dict.fromkeys((*p.constraints, "return advisory reasoning only"))))
        fact = CognitionProvenance.for_request(request, source_event_id=p.source_cognition_event_id,
                                               office_id=p.office_id, implementation_id=p.implementation_id,
                                               authority_ref=p.authority_ref,
                                               authoritative_state_refs=p.authoritative_current_state_refs,
                                               evidence_refs=p.evidence_refs, causation_id=p.source_cognition_event_id)
        self.provenance.record(fact); self._require_f2(request.request_id, fact.event_id)
        # P1 remains the policy authority; E2 records the consumed decision
        # against this exact request rather than re-evaluating escalation.
        PolicyDecisionRecorder(self.event_store).record(
            a, request_id=request.request_id, causation_id=p.source_cognition_event_id
        )
        turn = self.sessions.bind_request(session, request)
        decision = self.binding_adapter.candidates(request)
        if not self._binding_ok(decision, request):
            return self._failed(session, turn, request, decision, p, CognitionResultStatus.CORRELATION_MISMATCH,
                                CognitionFailureCode.CORRELATION_MISMATCH, "P2 binding does not correspond.")
        matches = tuple(c for c in decision.candidates if c.provider_id == self.provider.provider_id)
        if decision.status != "available" or len(matches) != 1:
            return self._failed(session, turn, request, decision, p, CognitionResultStatus.UNAVAILABLE,
                                CognitionFailureCode.UNAVAILABLE, "authorized high-reasoning provider is unavailable.")
        candidate = matches[0]
        if request.authorization_ref != self.provider.authorization_ref:
            return self._failed(session, turn, request, decision, p, CognitionResultStatus.DENIED,
                                CognitionFailureCode.DENIED, "provider authorization does not correspond.", candidate=candidate)
        instruction = json.dumps({"schema_version": self.version,
            "resident_identity": {"resident_id": str(p.resident_id), "occupant_id": str(p.occupant_id),
                                   "office_id": str(p.office_id), "implementation_id": str(p.implementation_id)},
            "objective": p.objective, "question": p.question, "constraints": list(p.constraints),
            "escalation": {"decision": a.decision.value, "policy_ref": a.policy_ref,
                            "reason_class": a.reason_class}, "requested_output": sorted(_KEYS)},
            sort_keys=True, separators=(",", ":"))
        if len(instruction) > MAX_INSTRUCTION:
            raise HighReasoningExecutionError("unbounded-context", "provider instruction exceeds its bound.")
        refs = tuple(dict.fromkeys((*p.authoritative_current_state_refs, *p.evidence_refs, *p.operational_state_refs)))
        if len(refs) > MAX_REFS:
            raise HighReasoningExecutionError("unbounded-context", "provider context references exceed their bound.")
        provider_request = ReasoningRequest(request_id=request.request_id, correlation_id=request.correlation_id,
            request_type="analysis", instruction=instruction, context_refs=refs,
            classification=request.classification, required_output_schema=self.version,
            evidence_requirements=("provider-request", "provider-response", "latency", "capacity", "f2-lineage"),
            expires_at=request.deadline_at, allowed_authority=_AUTHORITY,
            causation_id=p.source_cognition_event_id, objective_id=p.objective_id, response_format={"type":"object"})
        started = CognitionProvenance(event_id=uuid4(), event_type=CognitionProvenanceEventType.STARTED,
            actor_class=self.actor_class, resident_id=request.resident_id,
            occupant_id=request.occupant_id, office_id=request.office_id, implementation_id=request.implementation_id,
            authority_ref=request.authority_ref, source_event_id=p.source_cognition_event_id, request_id=request.request_id,
            correlation_id=request.correlation_id, causation_id=fact.event_id, cognition_tier=request.cognition_tier,
            provider_ref=candidate.provider_id, resource_class_ref=candidate.resource_class_ref or candidate.capability_name,
            packet_id=p.packet_id, result_id=None, policy_decision_ref=a.policy_ref, status="started", failure_code=None,
            classification=request.classification, live_generation=False, evidence_refs=candidate.evidence_refs(),
            authoritative_state_refs=p.authoritative_current_state_refs, occurred_at=self.clock())
        self.provenance.record(started); self._require_f2(request.request_id, started.event_id)
        tick = self.monotonic(); response = None; error = None
        try: response = self.provider.generate(provider_request)
        except Exception as exc: error = exc
        latency = max(0.0, (self.monotonic() - tick) * 1000)
        obs = HighGenerationObservation(uuid4(), request.request_id, candidate.provider_id,
            candidate.resource_class_ref or candidate.capability_name, candidate.capacity, latency,
            "provider-error" if error else "response-received", f"provider-request:{request.request_id}",
            f"provider-response:{response.response_id}" if response else None, self.clock())
        self._record_observation(obs, request, started.event_id)
        if error:
            status, code = (CognitionResultStatus.TIMEOUT, CognitionFailureCode.TIMEOUT) if isinstance(error, TimeoutError) else (CognitionResultStatus.UNAVAILABLE, CognitionFailureCode.UNAVAILABLE)
            return self._failed(session, turn, request, decision, p, status, code, f"provider generation failed: {type(error).__name__}", candidate=candidate, observation=obs)
        try:
            value = json.loads(response.summary) if isinstance(response, ReasoningResponse) else None
            if (not isinstance(value, Mapping) or frozenset(value) != _KEYS or value.get("live_generation") is not True or
                value.get("authority_scope") != ["return:advisory"] or not isinstance(value.get("provenance_refs"), list) or
                not value["provenance_refs"] or not isinstance(value.get("constraints"), list) or not isinstance(value.get("unresolved_questions"), list)):
                raise ValueError("strict high result envelope rejected")
            if (response.request_id, response.correlation_id, response.classification, response.provider_id) != (request.request_id, request.correlation_id, request.classification, candidate.provider_id):
                raise ValueError("provider correspondence mismatch")
            result = CognitionResult(response.response_id, request.request_id, request.correlation_id, request.resident_id,
                request.occupant_id, request.office_id, request.implementation_id, request.authority_ref,
            p.source_cognition_event_id, self.tier, CognitionResultStatus.COMPLETED,
                value["recommendation"], value["rationale"], value["uncertainty"], value["confidence"],
                tuple(value["constraints"]), tuple(value["unresolved_questions"]), value["further_escalation_warranted"],
                candidate.provider_id, candidate.resource_class_ref or candidate.capability_name, p.packet_id, a.policy_ref,
                tuple(dict.fromkeys((*value["provenance_refs"], *response.evidence_refs, *candidate.evidence_refs(), obs.request_evidence_ref, obs.response_evidence_ref or ""))),
                True, self.actor_class, request.classification, self.clock(), request.deadline_at, _AUTHORITY)
            result.validate_against(request)
        except Exception as exc:
            return self._failed(session, turn, request, decision, p, CognitionResultStatus.MALFORMED,
                                CognitionFailureCode.MALFORMED_RESPONSE, f"strict E2 result validation failed: {type(exc).__name__}", candidate=candidate, observation=obs)
        completed = CognitionProvenance.for_result(result, source_event_id=p.source_cognition_event_id,
                                                   causation_id=started.event_id, authoritative_state_refs=p.authoritative_current_state_refs)
        self.provenance.record(completed); self._require_f2(request.request_id, completed.event_id)
        return HighReasoningOutcome("completed", session, turn, request, decision, result, obs)

    @staticmethod
    def _binding_ok(decision: CapabilityBindingDecision, request: CapabilityResourceRequest) -> bool:
        return isinstance(decision, CapabilityBindingDecision) and decision.request_id == request.request_id and decision.correlation_id == request.correlation_id and decision.cognition_tier is request.cognition_tier and decision.policy_ref == request.policy_ref

    def _failed(self, session, turn, request, binding, packet, status, code, reason, *, candidate=None, observation=None):
        refs = [f"failure:{code.value}"] + (list(candidate.evidence_refs()) if candidate else []) + ([f"observation:{observation.observation_id}"] if observation else [])
        result = CognitionResult(uuid4(), request.request_id, request.correlation_id, request.resident_id, request.occupant_id, request.office_id, request.implementation_id, request.authority_ref, packet.source_cognition_event_id, self.tier, status, None, None, None, None, (), (), False, candidate.provider_id if candidate else None, (candidate.resource_class_ref or candidate.capability_name) if candidate else None, packet.packet_id, request.policy_ref, tuple(refs), False, self.actor_class, request.classification, self.clock(), request.deadline_at, _AUTHORITY, code, reason)
        self.provenance.record(CognitionProvenance.for_result(result, source_event_id=packet.source_cognition_event_id, authoritative_state_refs=packet.authoritative_current_state_refs)); self._require_f2(request.request_id, self.provenance.reconstruct(request.request_id)[-1].event_id)
        return HighReasoningOutcome("failed", session, turn, request, binding, result, observation)

    def _record_observation(self, observation, request, causation_id):
        self.event_store.append(RiverEvent(self.observation_event, PROVENANCE_AGGREGATE_TYPE, request.request_id, f"cognition:high-observation:{observation.observation_id}", observation.as_payload(), request.correlation_id, causation_id, Classification.INTERNAL if request.classification == "internal" else Classification.RIVER, observation.finished_at))
        if not any(row.get("payload", {}).get("observation_id") == str(observation.observation_id) for row in self.event_store.read_aggregate(PROVENANCE_AGGREGATE_TYPE, request.request_id)):
            raise HighReasoningExecutionError("missing-provenance", "high latency observation readback failed.")

    def _require_f2(self, request_id, event_id):
        if not any(item.event_id == event_id for item in self.provenance.reconstruct(request_id)):
            raise HighReasoningExecutionError("missing-provenance", "F2 high-reasoning readback failed.")


EXTERNAL_ADVISORY_VERSION = "grace-external-advisory-e3-v1"
EXTERNAL_ADVISORY_CAPABILITY = "EXTERNAL_ESCALATION"
EXTERNAL_ADVISORY_CHECKPOINT = "RIV-COG-E3-0001"
EXTERNAL_OBSERVATION_EVENT = "cognition.external_generation_observed"


class ExternalAdvisoryCoordinator(HighReasoningCoordinator):
    """E3 external-advisory mode over the shared bounded lineage machinery."""

    def __init__(self, *, event_store: HighReasoningEventStore,
                 binding_adapter: CognitionBindingAdapter,
                 provider: AuthorizedHighReasoningProvider,
                 clock: Callable[[], datetime] | None = None,
                 monotonic: Callable[[], float] | None = None) -> None:
        super().__init__(event_store=event_store, binding_adapter=binding_adapter, provider=provider,
                         tier=CognitionTier.EXTERNAL_ESCALATION, capability=EXTERNAL_ADVISORY_CAPABILITY,
                         actor_class=CognitionActorClass.EXTERNAL_REASONING, version=EXTERNAL_ADVISORY_VERSION,
                         observation_event=EXTERNAL_OBSERVATION_EVENT,
                         required_decision=EscalationDecision.EXTERNAL_ADVISORY_REQUIRED,
                         clock=clock, monotonic=monotonic)
