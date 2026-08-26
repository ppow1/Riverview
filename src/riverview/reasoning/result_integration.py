"""GRC-003-E4 return/integration boundary for higher-tier cognition results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from riverview.river import Classification, RiverEvent

from .cognition_contracts import (CapabilityResourceRequest, CognitionActorClass,
    CognitionResult, CognitionResultStatus, CognitionTier)
from .provenance import (PROVENANCE_AGGREGATE_TYPE, CognitionProvenance,
    CognitionProvenanceEventType, CognitionProvenanceWriter,
    ProvenanceLineageError)
from .session import CognitionSession, CognitionSessionTurn

INTEGRATION_CHECKPOINT = "RIV-COG-E4-0001"
INTEGRATION_EVENT = "cognition.integrated"
INTEGRATION_AGGREGATE = "grace_cognition_integration"
_ADVISORY = ("return:advisory",)


class ResultIntegrationError(ValueError):
    """Fail-closed E4 correspondence, authority, or replay error."""


class ResultIntegrationEventStore(Protocol):
    def append(self, event: RiverEvent) -> Any: ...
    def read_aggregate(self, aggregate_type: str, aggregate_id: UUID) -> list[dict[str, Any]]: ...


@dataclass(frozen=True, slots=True)
class IntegratedGraceResult:
    integration_id: UUID
    result_id: UUID
    request_id: UUID
    session_id: UUID
    resident_id: UUID
    occupant_id: UUID
    office_id: UUID
    implementation_id: UUID
    cognition_tier: CognitionTier
    provider_ref: str
    resource_class_ref: str
    correlation_id: UUID
    status: str
    recommendation: str | None
    rationale: str | None
    uncertainty: str | None
    constraints: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    further_escalation_warranted: bool
    authority_scope: tuple[str, ...]
    live_generation: bool
    event_id: UUID
    idempotent_replay: bool = False


class GraceResultIntegrator:
    """Integrate one completed high/external result without granting authority."""

    def __init__(self, event_store: ResultIntegrationEventStore, *, clock=None) -> None:
        self.event_store = event_store
        self.clock = clock or (lambda: datetime.now(UTC))

    def integrate(self, result: CognitionResult, session: CognitionSession,
                  request: CapabilityResourceRequest, *, turn: CognitionSessionTurn | None = None) -> IntegratedGraceResult:
        self._validate(result, session, request, turn)
        rows = self.event_store.read_aggregate(PROVENANCE_AGGREGATE_TYPE, request.request_id)
        integrated = [row for row in rows if row.get("event_type") == INTEGRATION_EVENT]
        for row in integrated:
            payload = row.get("payload", {})
            if payload.get("result_id") == str(result.result_id):
                return self._from_payload(payload, UUID(str(row["event_id"])), idempotent=True)
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: conflicting result already integrated for request.")
        lineage = CognitionProvenanceWriter(self.event_store).reconstruct(request.request_id)
        completed = [item for item in lineage if item.event_type is CognitionProvenanceEventType.COMPLETED and item.result_id == result.result_id]
        if len(completed) != 1 or not completed[0].live_generation:
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: completed F2 result lineage is missing or false.")
        integration_id = uuid4()
        provenance = CognitionProvenance.for_result(
            result,
            source_event_id=result.source_cognition_event_id,
            event_type=CognitionProvenanceEventType.INTEGRATED,
            causation_id=completed[0].event_id,
            authoritative_state_refs=(),
        )
        payload = provenance.as_typed_payload() | {
            "integration_schema_version": "grace-result-integration-e4-v1", "integration_id": str(integration_id),
            "result_id": str(result.result_id), "request_id": str(result.request_id),
            "session_id": str(session.session_id), "resident_id": str(session.resident_id),
            "occupant_id": str(session.occupant_id), "office_id": str(session.office_id),
            "implementation_id": str(session.implementation_id), "cognition_tier": result.cognition_tier.value,
            "provider_ref": result.provider_ref, "resource_class_ref": result.resource_class_ref,
            "correlation_id": str(result.correlation_id), "status": result.status.value,
            "recommendation": result.recommendation, "rationale": result.rationale,
            "uncertainty": result.uncertainty, "constraints": list(result.constraints),
            "unresolved_questions": list(result.unresolved_questions),
            "further_escalation_warranted": result.further_escalation_warranted,
            "authority_scope": list(_ADVISORY), "live_generation": result.live_generation,
            "source_event_id": str(result.source_cognition_event_id), "policy_decision_ref": result.policy_decision_ref,
            "provenance_refs": list(result.provenance_refs), "integrated_at": self.clock().isoformat(),
        }
        event = RiverEvent(event_type=INTEGRATION_EVENT, aggregate_type=PROVENANCE_AGGREGATE_TYPE,
            aggregate_id=request.request_id, idempotency_key=f"cognition:integrated:{result.request_id}:{result.result_id}",
            payload=payload, correlation_id=result.correlation_id, causation_id=result.source_cognition_event_id,
            classification=Classification.INTERNAL if result.classification == "internal" else Classification.RIVER,
            event_id=provenance.event_id, occurred_at=provenance.occurred_at)
        self.event_store.append(event)
        readback = [row for row in self.event_store.read_aggregate(PROVENANCE_AGGREGATE_TYPE, request.request_id)
                    if row.get("event_type") == INTEGRATION_EVENT and row.get("payload", {}).get("result_id") == str(result.result_id)]
        if len(readback) != 1:
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: integrated result readback failed.")
        return self._from_payload(payload, event.event_id, idempotent=False)

    @staticmethod
    def _validate(result, session, request, turn) -> None:
        if not isinstance(result, CognitionResult) or result.status is not CognitionResultStatus.COMPLETED:
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: only completed cognition results may return.")
        if result.cognition_tier not in {CognitionTier.HIGH_REASONING, CognitionTier.EXTERNAL_ESCALATION}:
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: E4 accepts only higher-tier results.")
        if result.actor_class not in {CognitionActorClass.GRACE_HIGH_REASONING, CognitionActorClass.EXTERNAL_REASONING}:
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: result actor is not an E2/E3 actor.")
        if not result.live_generation or result.authority_scope != _ADVISORY or not result.provider_ref or not result.resource_class_ref:
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: result is not truthful bounded advisory output.")
        try:
            result.validate_against(request)
        except (ValueError, ProvenanceLineageError) as exc:
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: request/result correspondence failed.") from exc
        for name in ("resident_id", "occupant_id", "office_id", "implementation_id", "authority_ref"):
            if getattr(result, name) != getattr(session, name) or getattr(request, name) != getattr(session, name):
                raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: {name} does not correspond to Grace session.")
        if result.request_id != request.request_id or result.correlation_id != request.correlation_id:
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: request/correlation correspondence failed.")
        if result.policy_decision_ref != request.policy_ref:
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: policy correspondence failed.")
        if result.expires_at is not None and result.expires_at <= datetime.now(UTC):
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: stale result cannot be integrated.")
        if turn is not None and (turn.session_id != session.session_id or turn.request_id != request.request_id):
            raise ResultIntegrationError(f"{INTEGRATION_CHECKPOINT}: session turn does not correspond.")

    @staticmethod
    def _from_payload(payload, event_id, *, idempotent):
        return IntegratedGraceResult(UUID(payload["integration_id"]), UUID(payload["result_id"]), UUID(payload["request_id"]), UUID(payload["session_id"]), UUID(payload["resident_id"]), UUID(payload["occupant_id"]), UUID(payload["office_id"]), UUID(payload["implementation_id"]), CognitionTier(payload["cognition_tier"]), payload["provider_ref"], payload["resource_class_ref"], UUID(payload["correlation_id"]), payload["status"], payload.get("recommendation"), payload.get("rationale"), payload.get("uncertainty"), tuple(payload["constraints"]), tuple(payload["unresolved_questions"]), payload["further_escalation_warranted"], tuple(payload["authority_scope"]), payload["live_generation"], event_id, idempotent)
