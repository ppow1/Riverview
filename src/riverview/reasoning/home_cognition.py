"""Bounded GRC-003-E1 HOME cognition execution path.

Version: 1.0.0

This service composes the accepted F1/F2/F3/P1/P2 seams.  It deliberately
does not reserve capacity, dispatch execution, select a model or GPU, or
grant authority beyond an advisory cognition result.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from riverview.residents.context import ContextBundle
from riverview.river import Classification, RiverEvent

from .binding import CapabilityBindingDecision, CognitionBindingAdapter, ProviderResourceCandidate
from .cognition_contracts import (
    MAX_CONTEXT_CHARS,
    CapabilityResourceRequest,
    CognitionActorClass,
    CognitionFailureCode,
    CognitionResult,
    CognitionResultStatus,
    CognitionTier,
    EscalationAssessment,
    EscalationDecision,
    ResidentReasoningPacket,
)
from .context_assembler import ReasoningAssemblyRequest, ResidentReasoningPacketAssembler
from .contracts import MAX_INSTRUCTION, MAX_REFS, ReasoningRequest, ReasoningResponse
from .escalation_policy import ConsequenceClass, EscalationPolicy, PolicyDecisionRecorder
from .provenance import (
    PROVENANCE_AGGREGATE_TYPE,
    CognitionProvenance,
    CognitionProvenanceEventType,
    CognitionProvenanceWriter,
)
from .session import CognitionSession, CognitionSessionBoundary, CognitionSessionTurn

HOME_COGNITION_VERSION = "grace-home-cognition-e1-v1"
HOME_COGNITION_CHECKPOINT = "RIV-COG-E1-0001"
HOME_COGNITION_CAPABILITY = "HOME_COGNITION"
HOME_OBSERVATION_EVENT = "cognition.home_generation_observed"
_ADVISORY_AUTHORITY = ("return:advisory",)
_OUTPUT_KEYS = frozenset(
    {
        "recommendation",
        "rationale",
        "uncertainty",
        "confidence",
        "constraints",
        "unresolved_questions",
        "further_escalation_warranted",
        "authority_scope",
        "live_generation",
        "provenance_refs",
    }
)
_OUTPUT_FORMAT: dict[str, Any] = {
    "type": "object",
    "properties": {
        "recommendation": {"type": "string"},
        "rationale": {"type": "string"},
        "uncertainty": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "constraints": {"type": "array", "items": {"type": "string"}, "maxItems": 32},
        "unresolved_questions": {"type": "array", "items": {"type": "string"}, "maxItems": 32},
        "further_escalation_warranted": {"type": "boolean"},
        "authority_scope": {"const": ["return:advisory"]},
        "live_generation": {"const": True},
        "provenance_refs": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 32,
        },
    },
    "required": sorted(_OUTPUT_KEYS),
    "additionalProperties": False,
}


class HomeCognitionExecutionError(RuntimeError):
    """E1 stopped without returning an advisory success."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(f"{HOME_COGNITION_CHECKPOINT}: {message}")
        self.reason = reason
        self.checkpoint = HOME_COGNITION_CHECKPOINT


class HomeCognitionEventStore(Protocol):
    def append(self, event: RiverEvent) -> Any: ...

    def read_aggregate(self, aggregate_type: str, aggregate_id: UUID) -> list[dict[str, Any]]: ...


@dataclass(frozen=True, slots=True)
class AuthoritativeGraceState:
    """One already-authoritative Grace identity/current-state projection."""

    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    authority_ref: str
    context_bundle: ContextBundle
    authoritative_state_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    observed_at: datetime
    classification: str = "internal"

    def __post_init__(self) -> None:
        for name in ("resident_id", "occupant_id", "office_id", "implementation_id"):
            if not isinstance(getattr(self, name), UUID):
                raise HomeCognitionExecutionError(
                    "authoritative-state-invalid", f"{name} is not authoritative identity."
                )
        if self.resident_id != self.occupant_id:
            raise HomeCognitionExecutionError(
                "authoritative-state-invalid", "Grace resident and occupant identity differ."
            )
        if not isinstance(self.context_bundle, ContextBundle) or self.context_bundle.stale:
            raise HomeCognitionExecutionError(
                "authoritative-state-unavailable",
                "authoritative Grace context is unavailable or stale.",
            )
        if (self.context_bundle.resident_id, self.context_bundle.office_id) != (
            self.occupant_id,
            self.office_id,
        ):
            raise HomeCognitionExecutionError(
                "authoritative-state-mismatch",
                "Grace state and context identity do not correspond.",
            )
        if not isinstance(self.authority_ref, str) or not self.authority_ref.strip():
            raise HomeCognitionExecutionError(
                "authoritative-state-invalid", "Grace authority reference is unavailable."
            )
        for values, name in (
            (self.authoritative_state_refs, "authoritative_state_refs"),
            (self.evidence_refs, "evidence_refs"),
        ):
            if (
                not values
                or len(values) > 64
                or any(
                    not isinstance(value, str) or not value.strip() or len(value) > 500
                    for value in values
                )
            ):
                raise HomeCognitionExecutionError(
                    "authoritative-state-invalid", f"{name} is missing or unbounded."
                )
        if not isinstance(self.observed_at, datetime) or self.observed_at.tzinfo is None:
            raise HomeCognitionExecutionError(
                "authoritative-state-invalid", "state observation time is invalid."
            )
        if self.classification not in {"public", "operational", "private", "river", "internal"}:
            raise HomeCognitionExecutionError(
                "authoritative-state-invalid", "state classification is invalid."
            )


class AuthoritativeGraceStateSource(Protocol):
    def load(self) -> AuthoritativeGraceState | None: ...


@dataclass(frozen=True, slots=True)
class AuthorizedHomeProvider:
    """An already-authorized provider adapter; model/topology are outside E1."""

    provider_id: str
    authorization_ref: str
    generate: Callable[[ReasoningRequest], ReasoningResponse]

    def __post_init__(self) -> None:
        if (
            not self.provider_id.strip()
            or not self.authorization_ref.strip()
            or not callable(self.generate)
        ):
            raise HomeCognitionExecutionError(
                "provider-invalid", "authorized provider binding is invalid."
            )


@dataclass(frozen=True, slots=True)
class HomeCognitionInvocation:
    objective_id: UUID
    source_cognition_event_id: UUID
    correlation_id: UUID
    request_class: str
    objective: str
    question: str
    consequence: ConsequenceClass
    classification: str
    expires_at: datetime
    authorization_ref: str
    home_belief: bool = False
    home_belief_reason: str = "The bounded decision belongs at HOME cognition."
    constraints: tuple[str, ...] = ("advisory only",)
    unresolved_ambiguity: tuple[str, ...] = ()
    relevant_prior_decisions: tuple[str, ...] = ()
    known_deterministic_results: tuple[str, ...] = ()
    max_budget: int = 16_000

    def __post_init__(self) -> None:
        for name in ("objective_id", "source_cognition_event_id", "correlation_id"):
            if not isinstance(getattr(self, name), UUID):
                raise HomeCognitionExecutionError("invocation-invalid", f"{name} is invalid.")
        if self.max_budget < 1 or self.max_budget > MAX_CONTEXT_CHARS:
            raise HomeCognitionExecutionError(
                "unbounded-context", "invocation budget is outside the F1 bound."
            )
        if self.expires_at.tzinfo is None or self.expires_at <= datetime.now(UTC):
            raise HomeCognitionExecutionError("invocation-expired", "invocation expiry is invalid.")


@dataclass(frozen=True, slots=True)
class HomeGenerationObservation:
    observation_id: UUID
    request_id: UUID
    provider_id: str
    resource_class_ref: str
    capacity_observed: int
    started_at: datetime
    finished_at: datetime
    latency_ms: float
    outcome: str
    request_evidence_ref: str
    response_evidence_ref: str | None

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": HOME_COGNITION_VERSION,
            "observation_id": str(self.observation_id),
            "request_id": str(self.request_id),
            "provider_id": self.provider_id,
            "resource_class_ref": self.resource_class_ref,
            "capacity_observed": self.capacity_observed,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "latency_ms": self.latency_ms,
            "outcome": self.outcome,
            "request_evidence_ref": self.request_evidence_ref,
            "response_evidence_ref": self.response_evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class HomeCognitionOutcome:
    status: str
    assessment: EscalationAssessment
    session: CognitionSession
    packet: ResidentReasoningPacket
    request: CapabilityResourceRequest | None = None
    turn: CognitionSessionTurn | None = None
    binding: CapabilityBindingDecision | None = None
    result: CognitionResult | None = None
    observation: HomeGenerationObservation | None = None


class HomeCognitionService:
    """Execute exactly one bounded, provider-neutral Grace HOME cognition turn."""

    def __init__(
        self,
        *,
        grace_resident_id: UUID,
        state_source: AuthoritativeGraceStateSource,
        event_store: HomeCognitionEventStore,
        binding_adapter: CognitionBindingAdapter,
        provider: AuthorizedHomeProvider,
        packet_assembler: ResidentReasoningPacketAssembler | None = None,
        escalation_policy: EscalationPolicy | None = None,
        clock: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self.grace_resident_id = grace_resident_id
        self.state_source = state_source
        self.event_store = event_store
        self.binding_adapter = binding_adapter
        self.provider = provider
        self.packet_assembler = packet_assembler or ResidentReasoningPacketAssembler()
        self.escalation_policy = escalation_policy or EscalationPolicy()
        self.clock = clock or (lambda: datetime.now(UTC))
        self.monotonic = monotonic or time.monotonic
        self.sessions = CognitionSessionBoundary(event_store)
        self.provenance = CognitionProvenanceWriter(event_store)
        self.policy_recorder = PolicyDecisionRecorder(event_store)

    def execute(self, invocation: HomeCognitionInvocation) -> HomeCognitionOutcome:
        state = self.state_source.load()
        if state is None:
            raise HomeCognitionExecutionError(
                "authoritative-state-unavailable", "authoritative Grace state is unavailable."
            )
        if (
            not isinstance(state, AuthoritativeGraceState)
            or state.resident_id != self.grace_resident_id
        ):
            raise HomeCognitionExecutionError(
                "authoritative-state-mismatch", "loaded identity is not authoritative Grace."
            )
        if invocation.classification != state.classification:
            raise HomeCognitionExecutionError(
                "authoritative-state-mismatch",
                "invocation classification differs from Grace state.",
            )

        session = self.sessions.open(
            resident_id=state.resident_id,
            occupant_id=state.occupant_id,
            office_id=state.office_id,
            implementation_id=state.implementation_id,
            authority_ref=state.authority_ref,
            state_refs=state.authoritative_state_refs,
        )
        packet = self.packet_assembler.assemble(
            state.context_bundle,
            ReasoningAssemblyRequest(
                packet_id=uuid4(),
                resident_id=state.resident_id,
                occupant_id=state.occupant_id,
                implementation_id=state.implementation_id,
                source_cognition_event_id=invocation.source_cognition_event_id,
                objective_id=invocation.objective_id,
                correlation_id=invocation.correlation_id,
                cognition_tier=CognitionTier.HOME_COGNITION,
                request_class=invocation.request_class,
                objective=invocation.objective,
                exact_question=invocation.question,
                home_assessment="HOME cognition requested through GRC-003-E1.",
                requested_output_schema=HOME_COGNITION_VERSION,
                egress_policy="provider-neutral-authorized-local-advisory",
                classification=invocation.classification,
                max_budget=invocation.max_budget,
                expires_at=invocation.expires_at,
                constraints=invocation.constraints,
                unresolved_ambiguity=invocation.unresolved_ambiguity,
                relevant_prior_decisions=invocation.relevant_prior_decisions,
                known_deterministic_results=invocation.known_deterministic_results,
                causation_id=invocation.source_cognition_event_id,
            ),
        )
        if packet.authority_ref != state.authority_ref:
            raise HomeCognitionExecutionError(
                "authoritative-state-mismatch", "packet authority differs from loaded Grace state."
            )

        assessment = self.escalation_policy.evaluate(
            packet,
            consequence=invocation.consequence,
            home_belief=invocation.home_belief,
            home_belief_reason=invocation.home_belief_reason,
            now=self.clock(),
        )
        if assessment.decision is EscalationDecision.DETERMINISTIC:
            return HomeCognitionOutcome("deterministic", assessment, session, packet)
        if assessment.decision is not EscalationDecision.HOME_DECISION:
            return HomeCognitionOutcome("not-authorized-for-home", assessment, session, packet)

        request = CapabilityResourceRequest(
            request_id=uuid4(),
            correlation_id=invocation.correlation_id,
            resident_id=state.resident_id,
            occupant_id=state.occupant_id,
            office_id=state.office_id,
            implementation_id=state.implementation_id,
            authority_ref=state.authority_ref,
            cognition_tier=CognitionTier.HOME_COGNITION,
            required_capability=HOME_COGNITION_CAPABILITY,
            classification=invocation.classification,
            policy_ref=assessment.policy_ref,
            authorization_ref=invocation.authorization_ref,
            packet_id=packet.packet_id,
            deadline_at=min(invocation.expires_at, assessment.expires_at),
            latency_requirement="bounded-routine-home-cognition",
            constraints=tuple(
                dict.fromkeys((*invocation.constraints, "return advisory reasoning only"))
            ),
        )
        request_fact = CognitionProvenance.for_request(
            request,
            source_event_id=invocation.source_cognition_event_id,
            office_id=state.office_id,
            implementation_id=state.implementation_id,
            authority_ref=state.authority_ref,
            authoritative_state_refs=state.authoritative_state_refs,
            evidence_refs=state.evidence_refs,
            causation_id=invocation.source_cognition_event_id,
        )
        self.provenance.record(request_fact)
        self._require_f2(request.request_id, request_fact.event_id)
        self.policy_recorder.record(
            assessment,
            request_id=request.request_id,
            causation_id=invocation.source_cognition_event_id,
        )
        turn = self.sessions.bind_request(session, request)
        current_session, turns = self.sessions.reconstruct(session.session_id)
        if current_session != session or not turns or turns[-1] != turn:
            raise HomeCognitionExecutionError(
                "session-mismatch", "F3 session/request readback did not correspond."
            )

        if request.authorization_ref != self.provider.authorization_ref:
            return self._failed(
                "failed",
                assessment,
                session,
                packet,
                request,
                turn,
                None,
                CognitionResultStatus.DENIED,
                CognitionFailureCode.DENIED,
                "authorized provider reference does not match the request",
            )

        decision = self.binding_adapter.candidates(request)
        if not self._binding_corresponds(decision, request):
            return self._failed(
                "failed",
                assessment,
                session,
                packet,
                request,
                turn,
                decision,
                CognitionResultStatus.CORRELATION_MISMATCH,
                CognitionFailureCode.CORRELATION_MISMATCH,
                "P2 binding identity, correlation, tier, or policy mismatch",
            )
        matches = tuple(
            candidate
            for candidate in decision.candidates
            if candidate.provider_id == self.provider.provider_id
        )
        if decision.status != "available" or len(matches) != 1:
            return self._failed(
                "failed",
                assessment,
                session,
                packet,
                request,
                turn,
                decision,
                CognitionResultStatus.UNAVAILABLE,
                CognitionFailureCode.UNAVAILABLE,
                "authorized HOME cognition provider is unavailable",
            )
        candidate = matches[0]
        resource_class = candidate.resource_class_ref or candidate.capability_name

        provider_request = self._provider_request(packet, request)
        started = CognitionProvenance(
            event_id=uuid4(),
            event_type=CognitionProvenanceEventType.STARTED,
            actor_class=CognitionActorClass.GRACE_HOME_COGNITION,
            resident_id=request.resident_id,
            occupant_id=request.occupant_id,
            office_id=request.office_id,
            implementation_id=request.implementation_id,
            authority_ref=request.authority_ref,
            source_event_id=invocation.source_cognition_event_id,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            causation_id=request_fact.event_id,
            cognition_tier=request.cognition_tier,
            provider_ref=candidate.provider_id,
            resource_class_ref=resource_class,
            packet_id=packet.packet_id,
            result_id=None,
            policy_decision_ref=assessment.policy_ref,
            status="started",
            failure_code=None,
            classification=request.classification,
            live_generation=False,
            evidence_refs=candidate.evidence_refs(),
            authoritative_state_refs=state.authoritative_state_refs,
            occurred_at=self.clock(),
        )
        self.provenance.record(started)
        self._require_f2(request.request_id, started.event_id)

        started_at = self.clock()
        started_tick = self.monotonic()
        response: ReasoningResponse | None = None
        provider_error: Exception | None = None
        try:
            response = self.provider.generate(provider_request)
        except Exception as exc:  # noqa: BLE001 - provider plugins have no shared exception base.
            provider_error = exc
        finished_tick = self.monotonic()
        finished_at = self.clock()
        observation = HomeGenerationObservation(
            observation_id=uuid4(),
            request_id=request.request_id,
            provider_id=candidate.provider_id,
            resource_class_ref=resource_class,
            capacity_observed=candidate.capacity,
            started_at=started_at,
            finished_at=finished_at,
            latency_ms=max(0.0, (finished_tick - started_tick) * 1000),
            outcome="provider-error" if provider_error else "response-received",
            request_evidence_ref=f"provider-request:{provider_request.request_id}",
            response_evidence_ref=f"provider-response:{response.response_id}" if response else None,
        )
        self._record_observation(observation, request, started.event_id)

        if provider_error is not None:
            status = (
                CognitionResultStatus.TIMEOUT
                if isinstance(provider_error, TimeoutError)
                or "timed out" in str(provider_error).casefold()
                else CognitionResultStatus.UNAVAILABLE
            )
            code = (
                CognitionFailureCode.TIMEOUT
                if status is CognitionResultStatus.TIMEOUT
                else CognitionFailureCode.UNAVAILABLE
            )
            return self._failed(
                "failed",
                assessment,
                session,
                packet,
                request,
                turn,
                decision,
                status,
                code,
                f"authorized provider generation failed: {type(provider_error).__name__}",
                candidate=candidate,
                observation=observation,
            )
        assert response is not None
        try:
            result = self._validated_result(
                response, request, packet, assessment, candidate, observation
            )
        except (HomeCognitionExecutionError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return self._failed(
                "failed",
                assessment,
                session,
                packet,
                request,
                turn,
                decision,
                CognitionResultStatus.MALFORMED,
                CognitionFailureCode.MALFORMED_RESPONSE,
                f"provider output failed strict E1 validation: {type(exc).__name__}",
                candidate=candidate,
                observation=observation,
            )

        completed = CognitionProvenance.for_result(
            result,
            source_event_id=invocation.source_cognition_event_id,
            causation_id=started.event_id,
            authoritative_state_refs=state.authoritative_state_refs,
        )
        self.provenance.record(completed)
        self._require_f2(request.request_id, completed.event_id)
        return HomeCognitionOutcome(
            "completed", assessment, session, packet, request, turn, decision, result, observation
        )

    @staticmethod
    def _binding_corresponds(
        decision: CapabilityBindingDecision, request: CapabilityResourceRequest
    ) -> bool:
        return (
            isinstance(decision, CapabilityBindingDecision)
            and decision.request_id == request.request_id
            and decision.correlation_id == request.correlation_id
            and decision.cognition_tier is CognitionTier.HOME_COGNITION
            and decision.policy_ref == request.policy_ref
        )

    @staticmethod
    def _provider_request(
        packet: ResidentReasoningPacket, request: CapabilityResourceRequest
    ) -> ReasoningRequest:
        instruction = json.dumps(
            {
                "schema_version": HOME_COGNITION_VERSION,
                "resident_identity": {
                    "resident_id": str(packet.resident_id),
                    "occupant_id": str(packet.occupant_id),
                    "office_id": str(packet.office_id),
                    "implementation_id": str(packet.implementation_id),
                },
                "objective": packet.objective,
                "question": packet.question,
                "constraints": list(packet.constraints),
                "known_deterministic_results": list(packet.known_deterministic_results),
                "requested_output": _OUTPUT_FORMAT,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        if len(instruction) > MAX_INSTRUCTION:
            raise HomeCognitionExecutionError(
                "unbounded-context", "provider instruction exceeds its bounded envelope."
            )
        refs = tuple(
            dict.fromkeys(
                (
                    *packet.authoritative_current_state_refs,
                    *packet.evidence_refs,
                    *packet.operational_state_refs,
                )
            )
        )
        if len(refs) > MAX_REFS:
            raise HomeCognitionExecutionError(
                "unbounded-context",
                "provider context reference count exceeds its bounded envelope.",
            )
        return ReasoningRequest(
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            request_type="decision_proposal",
            instruction=instruction,
            context_refs=refs,
            classification=request.classification,
            required_output_schema=HOME_COGNITION_VERSION,
            evidence_requirements=(
                "provider-request",
                "provider-response",
                "latency",
                "capacity",
                "f2-lineage",
            ),
            expires_at=request.deadline_at or packet.expires_at,
            allowed_authority=_ADVISORY_AUTHORITY,
            causation_id=packet.source_cognition_event_id,
            objective_id=packet.objective_id,
            response_format=_OUTPUT_FORMAT,
        )

    def _validated_result(
        self,
        response: ReasoningResponse,
        request: CapabilityResourceRequest,
        packet: ResidentReasoningPacket,
        assessment: EscalationAssessment,
        candidate: ProviderResourceCandidate,
        observation: HomeGenerationObservation,
    ) -> CognitionResult:
        if not isinstance(response, ReasoningResponse):
            raise HomeCognitionExecutionError(
                "malformed-output", "provider did not return a typed response."
            )
        if (
            response.request_id,
            response.correlation_id,
            response.classification,
            response.provider_id,
        ) != (
            request.request_id,
            request.correlation_id,
            request.classification,
            candidate.provider_id,
        ):
            raise HomeCognitionExecutionError(
                "provider-response-mismatch", "provider response correspondence failed."
            )
        value = json.loads(response.summary)
        if not isinstance(value, Mapping) or frozenset(value) != _OUTPUT_KEYS:
            raise HomeCognitionExecutionError(
                "malformed-output", "provider result schema is not exact."
            )
        if value.get("live_generation") is not True:
            raise HomeCognitionExecutionError(
                "false-live-generation",
                "provider result did not truthfully attest live generation.",
            )
        if value.get("authority_scope") != ["return:advisory"]:
            raise HomeCognitionExecutionError(
                "authority-widening", "provider result attempted to widen advisory authority."
            )
        refs = value.get("provenance_refs")
        if (
            not isinstance(refs, list)
            or not refs
            or any(not isinstance(item, str) or not item.strip() for item in refs)
        ):
            raise HomeCognitionExecutionError(
                "missing-provenance", "provider result provenance is absent."
            )
        constraints = value.get("constraints")
        unresolved = value.get("unresolved_questions")
        if not isinstance(constraints, list) or not isinstance(unresolved, list):
            raise HomeCognitionExecutionError("malformed-output", "result collections are invalid.")
        evidence = tuple(
            dict.fromkeys(
                (
                    *refs,
                    *response.evidence_refs,
                    *candidate.evidence_refs(),
                    observation.request_evidence_ref,
                    observation.response_evidence_ref or "",
                    f"observation:{observation.observation_id}",
                )
            )
        )
        evidence = tuple(item for item in evidence if item)
        result = CognitionResult(
            result_id=response.response_id,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            resident_id=request.resident_id,
            occupant_id=request.occupant_id,
            office_id=request.office_id,
            implementation_id=request.implementation_id,
            authority_ref=request.authority_ref,
            source_cognition_event_id=packet.source_cognition_event_id,
            cognition_tier=CognitionTier.HOME_COGNITION,
            status=CognitionResultStatus.COMPLETED,
            recommendation=value.get("recommendation"),
            rationale=value.get("rationale"),
            uncertainty=value.get("uncertainty"),
            confidence=value.get("confidence"),
            constraints=tuple(constraints),
            unresolved_questions=tuple(unresolved),
            further_escalation_warranted=value.get("further_escalation_warranted"),
            provider_ref=candidate.provider_id,
            resource_class_ref=candidate.resource_class_ref or candidate.capability_name,
            packet_id=packet.packet_id,
            policy_decision_ref=assessment.policy_ref,
            provenance_refs=evidence,
            live_generation=True,
            actor_class=CognitionActorClass.GRACE_HOME_COGNITION,
            classification=request.classification,
            created_at=self.clock(),
            authority_scope=_ADVISORY_AUTHORITY,
        )
        result.validate_against(request)
        return result

    def _failed(
        self,
        status_label: str,
        assessment: EscalationAssessment,
        session: CognitionSession,
        packet: ResidentReasoningPacket,
        request: CapabilityResourceRequest,
        turn: CognitionSessionTurn | None,
        binding: CapabilityBindingDecision | None,
        status: CognitionResultStatus,
        code: CognitionFailureCode,
        reason: str,
        *,
        candidate: ProviderResourceCandidate | None = None,
        observation: HomeGenerationObservation | None = None,
    ) -> HomeCognitionOutcome:
        refs = [f"failure:{code.value}"]
        if candidate:
            refs.extend(candidate.evidence_refs())
        if observation:
            refs.append(f"observation:{observation.observation_id}")
        result = CognitionResult(
            result_id=uuid4(),
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            resident_id=request.resident_id,
            occupant_id=request.occupant_id,
            office_id=request.office_id,
            implementation_id=request.implementation_id,
            authority_ref=request.authority_ref,
            source_cognition_event_id=packet.source_cognition_event_id,
            cognition_tier=CognitionTier.HOME_COGNITION,
            status=status,
            recommendation=None,
            rationale=None,
            uncertainty=None,
            confidence=None,
            constraints=(),
            unresolved_questions=(),
            further_escalation_warranted=False,
            provider_ref=candidate.provider_id if candidate else None,
            resource_class_ref=(candidate.resource_class_ref or candidate.capability_name)
            if candidate
            else None,
            packet_id=packet.packet_id,
            policy_decision_ref=assessment.policy_ref,
            provenance_refs=tuple(refs),
            live_generation=False,
            actor_class=CognitionActorClass.GRACE_HOME_COGNITION,
            classification=request.classification,
            created_at=self.clock(),
            authority_scope=_ADVISORY_AUTHORITY,
            failure_code=code,
            failure_reason=reason,
        )
        result.validate_against(request)
        failure = CognitionProvenance.for_result(
            result, source_event_id=packet.source_cognition_event_id
        )
        self.provenance.record(failure)
        self._require_f2(request.request_id, failure.event_id)
        return HomeCognitionOutcome(
            status_label, assessment, session, packet, request, turn, binding, result, observation
        )

    def _record_observation(
        self,
        observation: HomeGenerationObservation,
        request: CapabilityResourceRequest,
        causation_id: UUID,
    ) -> None:
        event = RiverEvent(
            event_type=HOME_OBSERVATION_EVENT,
            aggregate_type=PROVENANCE_AGGREGATE_TYPE,
            aggregate_id=request.request_id,
            idempotency_key=f"cognition:home-observation:{observation.observation_id}",
            payload=observation.as_payload(),
            correlation_id=request.correlation_id,
            causation_id=causation_id,
            classification=Classification.INTERNAL
            if request.classification == "internal"
            else Classification.RIVER,
            occurred_at=observation.finished_at,
        )
        self.event_store.append(event)
        rows = self.event_store.read_aggregate(PROVENANCE_AGGREGATE_TYPE, request.request_id)
        if not any(
            row.get("payload", {}).get("observation_id") == str(observation.observation_id)
            for row in rows
        ):
            raise HomeCognitionExecutionError(
                "missing-provenance", "latency/capacity observation readback failed."
            )

    def _require_f2(self, request_id: UUID, event_id: UUID) -> None:
        records = self.provenance.reconstruct(request_id)
        if not any(record.event_id == event_id for record in records):
            raise HomeCognitionExecutionError(
                "missing-provenance", "F2 cognition provenance readback failed."
            )
