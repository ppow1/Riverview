"""GRC-003-P1 deterministic escalation decision policy.

This module evaluates an already bounded resident reasoning packet.  It does
not invoke cognition, select a provider/resource, reserve capacity, or grant
execution authority.  Home cognition supplies the belief that stronger
reasoning may help; this policy independently evaluates permission and the
reported capability-class capacity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID, uuid4

from riverview.river import Classification, RiverEvent

from .cognition_contracts import (
    CognitionTier,
    EscalationAssessment,
    EscalationDecision,
    ResidentReasoningPacket,
)


POLICY_VERSION = "grace-escalation-policy-p1-v1"
POLICY_EVENT_TYPE = "cognition.policy_decided"
POLICY_AGGREGATE_TYPE = "cognition_request"
POLICY_CHECKPOINT = "RIV-COG-P1-0001"


class ConsequenceClass(StrEnum):
    """Bounded risk/consequence classes accepted by the policy."""

    ROUTINE = "routine"
    DIFFICULT = "difficult"
    CONSEQUENTIAL_AMBIGUITY = "consequential_ambiguity"
    PROTECTED_BOUNDARY = "protected_boundary"
    UNKNOWN = "unknown"


class PolicyInputError(ValueError):
    """A policy input is absent, malformed, or outside the bounded contract."""


@dataclass(frozen=True, slots=True)
class CapacitySnapshot:
    """Observable capability-class eligibility, not a scheduler reservation."""

    high_reasoning_available: bool = False
    external_escalation_available: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.high_reasoning_available, bool) or not isinstance(self.external_escalation_available, bool):
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: capacity eligibility must be boolean.")


@dataclass(frozen=True, slots=True)
class EscalationPolicy:
    """Evaluate belief, policy permission, and capacity as separate facts."""

    policy_version: str = POLICY_VERSION
    external_classifications: frozenset[str] = frozenset({"public", "operational"})
    decision_ttl: timedelta = timedelta(minutes=10)

    def __post_init__(self) -> None:
        if not isinstance(self.policy_version, str) or not self.policy_version.strip() or len(self.policy_version) > 100:
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: policy version is required.")
        if not self.external_classifications or not all(isinstance(item, str) and item.strip() for item in self.external_classifications):
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: external classification policy is empty or malformed.")
        if self.decision_ttl <= timedelta(0):
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: decision lifetime must be positive.")

    def evaluate(
        self,
        packet: ResidentReasoningPacket,
        *,
        consequence: ConsequenceClass | str,
        home_belief: bool,
        home_belief_reason: str,
        requested_tier: CognitionTier | str | None = None,
        capacity: CapacitySnapshot | None = None,
        now: datetime | None = None,
        assessment_id: UUID | None = None,
    ) -> EscalationAssessment:
        """Return one truthful assessment without invoking or selecting a provider."""

        if not isinstance(packet, ResidentReasoningPacket):
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: a bounded F1 reasoning packet is required.")
        if not isinstance(home_belief, bool) or not isinstance(home_belief_reason, str) or not home_belief_reason.strip():
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: home belief and reason are required.")
        try:
            consequence_class = consequence if isinstance(consequence, ConsequenceClass) else ConsequenceClass(consequence)
        except (TypeError, ValueError) as exc:
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: consequence class is unknown.") from exc
        if requested_tier is None:
            target = CognitionTier.HIGH_REASONING
        else:
            try:
                target = requested_tier if isinstance(requested_tier, CognitionTier) else CognitionTier(requested_tier)
            except (TypeError, ValueError) as exc:
                raise PolicyInputError(f"{POLICY_CHECKPOINT}: requested tier is unsupported.") from exc
            if target not in {CognitionTier.HIGH_REASONING, CognitionTier.EXTERNAL_ESCALATION}:
                raise PolicyInputError(f"{POLICY_CHECKPOINT}: policy target must be high or external reasoning.")
        capacity_snapshot = capacity or CapacitySnapshot()
        created = now or datetime.now(UTC)
        if created.tzinfo is None or created.utcoffset() is None:
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: policy timestamp must be timezone-aware.")
        expires = min(packet.expires_at, created + self.decision_ttl)
        if expires <= created:
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: packet is expired for policy evaluation.")

        policy_permitted = True
        policy_reason = "Policy permits the bounded decision class."
        capacity_eligible = True
        capacity_reason = "No stronger capability was requested."
        decision = EscalationDecision.HOME_DECISION
        reason_class = consequence_class.value
        selected_target: CognitionTier | None = None

        if consequence_class in {ConsequenceClass.UNKNOWN, ConsequenceClass.PROTECTED_BOUNDARY, ConsequenceClass.CONSEQUENTIAL_AMBIGUITY}:
            policy_permitted = False
            policy_reason = "Deterministic policy cannot resolve this consequence class without Steward judgment."
            decision = EscalationDecision.STEWARD_REQUIRED
            capacity_reason = "Capacity is not consulted for a policy-refused Steward boundary."
            capacity_eligible = False
        elif not home_belief:
            decision = EscalationDecision.DETERMINISTIC if consequence_class is ConsequenceClass.ROUTINE else EscalationDecision.HOME_DECISION
            policy_reason = "Home cognition did not establish that stronger reasoning would help; no escalation is implied."
            capacity_reason = "Capacity is independent and does not create an escalation request."
        elif target is CognitionTier.EXTERNAL_ESCALATION and packet.classification not in self.external_classifications:
            policy_permitted = False
            policy_reason = "The packet classification is not eligible for external advisory reasoning."
            capacity_eligible = True
            capacity_reason = "External capability may exist, but policy denies this classification."
            decision = EscalationDecision.POLICY_DENIED
            selected_target = target
        else:
            selected_target = target
            capacity_eligible = (
                capacity_snapshot.high_reasoning_available
                if target is CognitionTier.HIGH_REASONING
                else capacity_snapshot.external_escalation_available
            )
            capacity_reason = (
                "The requested capability class is presently eligible."
                if capacity_eligible
                else "The requested capability class is presently unavailable."
            )
            if capacity_eligible:
                decision = (
                    EscalationDecision.HIGH_REASONING_REQUIRED
                    if target is CognitionTier.HIGH_REASONING
                    else EscalationDecision.EXTERNAL_ADVISORY_REQUIRED
                )
            else:
                decision = EscalationDecision.CAPACITY_UNAVAILABLE

        generated_id = assessment_id or uuid4()
        return EscalationAssessment(
            assessment_id=generated_id,
            resident_id=packet.resident_id,
            occupant_id=packet.occupant_id,
            office_id=packet.office_id,
            implementation_id=packet.implementation_id,
            authority_ref=packet.authority_ref,
            source_cognition_event_id=packet.source_cognition_event_id,
            packet_id=packet.packet_id,
            objective_id=packet.objective_id,
            correlation_id=packet.correlation_id,
            question=packet.question,
            authoritative_current_state_refs=packet.authoritative_current_state_refs,
            evidence_refs=packet.evidence_refs,
            constraints=packet.constraints,
            home_belief=home_belief,
            home_belief_reason=home_belief_reason,
            policy_permitted=policy_permitted,
            policy_reason=policy_reason,
            capacity_eligible=capacity_eligible,
            capacity_reason=capacity_reason,
            decision=decision,
            reason_class=reason_class,
            policy_ref=self.policy_version,
            provenance_refs=(f"policy:{self.policy_version}", f"assessment:{generated_id}"),
            classification=packet.classification,
            created_at=created,
            expires_at=expires,
            target_tier=selected_target,
        )


class PolicyEventStore(Protocol):
    def append(self, event: RiverEvent) -> Any: ...

    def read_aggregate(self, aggregate_type: str, aggregate_id: UUID) -> list[dict[str, Any]]: ...


class PolicyDecisionRecorder:
    """Persist policy decisions as immutable F2/River facts."""

    def __init__(self, event_store: PolicyEventStore) -> None:
        self.event_store = event_store

    def record(self, assessment: EscalationAssessment, *, request_id: UUID, causation_id: UUID | None = None) -> Any:
        if not isinstance(request_id, UUID):
            raise PolicyInputError(f"{POLICY_CHECKPOINT}: request identity is required for policy lineage.")
        payload = {
            "schema_version": POLICY_VERSION,
            "event_type": POLICY_EVENT_TYPE,
            "request_id": str(request_id),
            "assessment": assessment.as_typed_payload(),
            "policy_version": assessment.policy_ref,
            "decision": assessment.decision.value,
            "home_belief": assessment.home_belief,
            "policy_permitted": assessment.policy_permitted,
            "capacity_eligible": assessment.capacity_eligible,
            "reason_class": assessment.reason_class,
        }
        event = RiverEvent(
            event_type=POLICY_EVENT_TYPE,
            aggregate_type=POLICY_AGGREGATE_TYPE,
            aggregate_id=request_id,
            correlation_id=assessment.correlation_id,
            causation_id=causation_id or assessment.source_cognition_event_id,
            idempotency_key=f"cognition:policy:{request_id}:{assessment.assessment_id}",
            classification=Classification.INTERNAL if assessment.classification == "internal" else Classification.RIVER,
            payload=payload,
            occurred_at=assessment.created_at,
        )
        return self.event_store.append(event)

