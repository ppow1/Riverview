"""Focused GRC-003-E1 HOME cognition execution and adversarial tests."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from uuid import UUID, uuid4

import pytest
from test_resident_context import OCCUPANT, OFFICE, FixtureSource, assignment

from riverview.reasoning import (
    HOME_COGNITION_CAPABILITY,
    HOME_OBSERVATION_EVENT,
    AuthoritativeGraceState,
    AuthorizedHomeProvider,
    BindingConfigurationLoader,
    CognitionBindingAdapter,
    CognitionProvenanceEventType,
    CognitionProvenanceWriter,
    CognitionResultStatus,
    ConsequenceClass,
    HomeCognitionExecutionError,
    HomeCognitionInvocation,
    HomeCognitionService,
    OllamaReasoningAdapter,
    ReasoningContextAssemblyError,
)
from riverview.reasoning.escalation_policy import POLICY_VERSION
from riverview.residents.context import BudgetSpec, ResidentContextAssembler
from riverview.river import RiverEvent

IMPLEMENTATION = UUID("33333333-3333-4333-8333-333333333333")
AUTHORITY = "c465:office-authority"
AUTHORIZATION = "authority://grace/home-cognition/e1"
PROVIDER_ID = "ollama:e1-fixture"


@dataclass(frozen=True)
class Ack:
    event_id: UUID
    inserted: bool = True


class MemoryEventStore:
    def __init__(self) -> None:
        self.events: list[RiverEvent] = []

    def append(self, event: RiverEvent) -> Ack:
        existing = next(
            (item for item in self.events if item.idempotency_key == event.idempotency_key), None
        )
        if existing is not None:
            return Ack(existing.event_id, False)
        self.events.append(event)
        return Ack(event.event_id)

    def read_aggregate(self, aggregate_type: str, aggregate_id: UUID) -> list[dict[str, Any]]:
        return [
            {
                "sequence_id": index,
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "payload": dict(event.payload),
                "occurred_at": event.occurred_at.isoformat(),
            }
            for index, event in enumerate(self.events, 1)
            if event.aggregate_type == aggregate_type and event.aggregate_id == aggregate_id
        ]


class StateSource:
    def __init__(self, value: AuthoritativeGraceState | None) -> None:
        self.value = value

    def load(self) -> AuthoritativeGraceState | None:
        return self.value


class Catalog:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    def available_for(self, **_: object) -> list[dict[str, object]]:
        return self.rows


def grace_state() -> AuthoritativeGraceState:
    bundle = ResidentContextAssembler(FixtureSource(name="Grace")).assemble(
        OCCUPANT, purpose="ENGINEERING_REVIEW", budget=BudgetSpec(), assignment=assignment()
    )
    return AuthoritativeGraceState(
        resident_id=OCCUPANT,
        occupant_id=OCCUPANT,
        office_id=OFFICE,
        implementation_id=IMPLEMENTATION,
        authority_ref=AUTHORITY,
        context_bundle=bundle,
        authoritative_state_refs=("state://grace/current", "assignment://fixture"),
        evidence_refs=("evidence://grace/identity",),
        observed_at=datetime.now(UTC),
    )


def candidate(provider_id: str = PROVIDER_ID) -> dict[str, object]:
    return {
        "participant_id": "participant:grace-home",
        "provider_id": provider_id,
        "provider_type": "local-fixture",
        "role": "advisory",
        "health": "healthy",
        "capacity": 3,
        "capability_name": HOME_COGNITION_CAPABILITY,
        "contract_version": "fixture-v1",
        "classification": True,
    }


def output(**changes: object) -> str:
    value: dict[str, object] = {
        "recommendation": "Continue the accepted bounded stage.",
        "rationale": "The authoritative state and evidence support that recommendation.",
        "uncertainty": None,
        "confidence": 0.91,
        "constraints": ["advisory only"],
        "unresolved_questions": [],
        "further_escalation_warranted": False,
        "authority_scope": ["return:advisory"],
        "live_generation": True,
        "provenance_refs": ["provider://fixture/request-response"],
    }
    value.update(changes)
    return json.dumps(value)


def invocation(**changes: object) -> HomeCognitionInvocation:
    values: dict[str, object] = {
        "objective_id": uuid4(),
        "source_cognition_event_id": uuid4(),
        "correlation_id": uuid4(),
        "request_class": "routine_operational_cognition",
        "objective": "Keep the accepted objective moving safely.",
        "question": "What is the next bounded advisory decision?",
        "consequence": ConsequenceClass.DIFFICULT,
        "classification": "internal",
        "expires_at": datetime.now(UTC) + timedelta(minutes=5),
        "authorization_ref": AUTHORIZATION,
    }
    values.update(changes)
    return HomeCognitionInvocation(**values)  # type: ignore[arg-type]


def service(
    provider_function,
    *,
    store: MemoryEventStore | None = None,
    state: AuthoritativeGraceState | None = None,
    rows: list[dict[str, object]] | None = None,
    provider_id: str = PROVIDER_ID,
) -> tuple[HomeCognitionService, MemoryEventStore]:
    event_store = store or MemoryEventStore()
    configuration = BindingConfigurationLoader.from_mapping(
        {
            "HOME_COGNITION": {
                "capability_name": HOME_COGNITION_CAPABILITY,
                "policy_ref": POLICY_VERSION,
                "configuration_ref": "config://grace/home/e1",
                "resource_class_ref": "resource-class://home-cognition",
            }
        }
    )
    result = HomeCognitionService(
        grace_resident_id=OCCUPANT,
        state_source=StateSource(state if state is not None else grace_state()),
        event_store=event_store,
        binding_adapter=CognitionBindingAdapter(
            Catalog(rows if rows is not None else [candidate(provider_id)]), configuration
        ),
        provider=AuthorizedHomeProvider(provider_id, AUTHORIZATION, provider_function),
    )
    return result, event_store


def typed_provider(summary: str = output(), **response_changes: object):
    calls = []

    def generate(request):
        from riverview.reasoning import ReasoningResponse

        calls.append(request)
        values = {
            "response_id": uuid4(),
            "request_id": request.request_id,
            "correlation_id": request.correlation_id,
            "provider_id": PROVIDER_ID,
            "response_type": "decision_proposal",
            "summary": summary,
            "evidence_refs": ("provider://fixture/response",),
            "classification": request.classification,
            "created_at": datetime.now(UTC),
        }
        values.update(response_changes)
        return ReasoningResponse(**values)

    return generate, calls


def test_home_cognition_happy_path_has_f2_readback_and_latency_capacity_evidence() -> None:
    generate, calls = typed_provider()
    cognition, store = service(generate)
    outcome = cognition.execute(invocation())

    assert outcome.status == "completed"
    assert outcome.result is not None and outcome.result.live_generation is True
    assert outcome.result.authority_scope == ("return:advisory",)
    assert (
        outcome.request is not None
        and outcome.request.required_capability == HOME_COGNITION_CAPABILITY
    )
    assert len(calls) == 1 and calls[0].response_format is not None
    assert outcome.observation is not None
    assert outcome.observation.capacity_observed == 3
    assert outcome.observation.latency_ms >= 0
    assert (
        outcome.observation.request_evidence_ref == f"provider-request:{outcome.request.request_id}"
    )
    lineage = CognitionProvenanceWriter(store).reconstruct(outcome.request.request_id)
    assert [item.event_type for item in lineage] == [
        CognitionProvenanceEventType.REQUESTED,
        CognitionProvenanceEventType.STARTED,
        CognitionProvenanceEventType.COMPLETED,
    ]
    assert any(event.event_type == HOME_OBSERVATION_EVENT for event in store.events)
    assert outcome.turn is not None and outcome.turn.session_id == outcome.session.session_id


def test_actual_loopback_provider_request_and_response_are_observed() -> None:
    received: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers["Content-Length"])
            received.append(json.loads(self.rfile.read(length)))
            body = json.dumps({"response": output()}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        adapter = OllamaReasoningAdapter(
            endpoint=f"http://127.0.0.1:{server.server_port}", timeout_seconds=5
        )
        cognition, _ = service(lambda request: adapter.complete("e1-fixture", request))
        outcome = cognition.execute(invocation())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert outcome.status == "completed"
    assert len(received) == 1
    assert received[0]["model"] == "e1-fixture"
    assert "home-cognition" in str(received[0]["prompt"]).casefold().replace("_", "-")
    assert outcome.observation is not None and outcome.observation.response_evidence_ref is not None


def test_deterministic_work_never_calls_provider_or_emits_home_generation_event() -> None:
    generate, calls = typed_provider()
    cognition, store = service(generate)
    outcome = cognition.execute(invocation(consequence=ConsequenceClass.ROUTINE))
    assert outcome.status == "deterministic"
    assert outcome.request is None and outcome.result is None and not calls
    assert not any(
        event.event_type in {HOME_OBSERVATION_EVENT, "cognition.started", "cognition.completed"}
        for event in store.events
    )


def test_unavailable_authoritative_state_fails_before_session_or_provider() -> None:
    generate, calls = typed_provider()
    event_store = MemoryEventStore()
    configuration = BindingConfigurationLoader.from_mapping(
        {
            "HOME_COGNITION": {
                "capability_name": HOME_COGNITION_CAPABILITY,
                "policy_ref": POLICY_VERSION,
                "configuration_ref": "config://home",
            }
        }
    )
    cognition = HomeCognitionService(
        grace_resident_id=OCCUPANT,
        state_source=StateSource(None),
        event_store=event_store,
        binding_adapter=CognitionBindingAdapter(Catalog([candidate()]), configuration),
        provider=AuthorizedHomeProvider(PROVIDER_ID, AUTHORIZATION, generate),
    )
    with pytest.raises(HomeCognitionExecutionError, match="authoritative Grace state"):
        cognition.execute(invocation())
    assert not calls and not event_store.events


def test_unavailable_provider_returns_truthful_f2_failure_without_generation() -> None:
    generate, calls = typed_provider()
    cognition, store = service(generate, rows=[])
    outcome = cognition.execute(invocation())
    assert outcome.result is not None
    assert outcome.result.status is CognitionResultStatus.UNAVAILABLE
    assert outcome.result.live_generation is False and not calls
    lineage = CognitionProvenanceWriter(store).reconstruct(outcome.request.request_id)  # type: ignore[union-attr]
    assert lineage[-1].event_type is CognitionProvenanceEventType.UNAVAILABLE
    assert not any(event.event_type == HOME_OBSERVATION_EVENT for event in store.events)


@pytest.mark.parametrize(
    "summary",
    [
        "not-json",
        output(provenance_refs=[]),
        output(live_generation=False),
        output(authority_scope=["execute"]),
        output(recommendation=""),
    ],
)
def test_malformed_missing_provenance_false_live_and_authority_widening_fail_closed(
    summary: str,
) -> None:
    generate, calls = typed_provider(summary)
    cognition, store = service(generate)
    outcome = cognition.execute(invocation())
    assert len(calls) == 1
    assert outcome.result is not None
    assert outcome.result.status is CognitionResultStatus.MALFORMED
    assert outcome.result.live_generation is False
    lineage = CognitionProvenanceWriter(store).reconstruct(outcome.request.request_id)  # type: ignore[union-attr]
    assert lineage[-1].event_type is CognitionProvenanceEventType.REJECTED
    assert any(event.event_type == HOME_OBSERVATION_EVENT for event in store.events)


@pytest.mark.parametrize(
    "field,value",
    [
        ("request_id", uuid4()),
        ("correlation_id", uuid4()),
        ("provider_id", "ollama:forged"),
        ("classification", "public"),
    ],
)
def test_provider_response_correspondence_mismatch_fails_closed(field: str, value: object) -> None:
    generate, _ = typed_provider(**{field: value})
    cognition, _ = service(generate)
    outcome = cognition.execute(invocation())
    assert outcome.result is not None and outcome.result.status is CognitionResultStatus.MALFORMED


def test_binding_correspondence_mismatch_fails_without_provider_call() -> None:
    generate, calls = typed_provider()
    cognition, _ = service(generate)
    original = cognition.binding_adapter

    class ForgedBinding:
        def candidates(self, request):
            decision = original.candidates(request)
            return replace(decision, correlation_id=uuid4())

    cognition.binding_adapter = ForgedBinding()  # type: ignore[assignment]
    outcome = cognition.execute(invocation())
    assert (
        outcome.result is not None
        and outcome.result.status is CognitionResultStatus.CORRELATION_MISMATCH
    )
    assert not calls


def test_session_request_readback_mismatch_fails_before_provider() -> None:
    generate, calls = typed_provider()

    class CorruptSessionStore(MemoryEventStore):
        def read_aggregate(self, aggregate_type: str, aggregate_id: UUID):
            rows = super().read_aggregate(aggregate_type, aggregate_id)
            if aggregate_type == "cognition_session":
                for row in rows:
                    if row["event_type"] == "cognition.session.request_attached":
                        row["payload"]["implementation_id"] = str(uuid4())
            return rows

    cognition, _ = service(generate, store=CorruptSessionStore())
    with pytest.raises(ValueError, match="does not correspond to session"):
        cognition.execute(invocation())
    assert not calls


def test_unbounded_invocation_is_rejected_without_generation() -> None:
    with pytest.raises(HomeCognitionExecutionError, match="outside the F1 bound"):
        invocation(max_budget=65_000)

    generate, calls = typed_provider()
    cognition, _ = service(generate)
    with pytest.raises(ReasoningContextAssemblyError, match="bounded"):
        cognition.execute(invocation(objective="x" * 4_001))
    assert not calls


def test_missing_f2_request_readback_stops_before_provider() -> None:
    generate, calls = typed_provider()

    class MissingF2ReadbackStore(MemoryEventStore):
        def read_aggregate(self, aggregate_type: str, aggregate_id: UUID):
            rows = super().read_aggregate(aggregate_type, aggregate_id)
            if aggregate_type == "cognition_request":
                return [row for row in rows if row["event_type"] != "cognition.requested"]
            return rows

    cognition, _ = service(generate, store=MissingF2ReadbackStore())
    with pytest.raises(HomeCognitionExecutionError, match="F2 cognition provenance readback"):
        cognition.execute(invocation())
    assert not calls


def test_non_grace_authoritative_identity_is_rejected_before_generation() -> None:
    generate, calls = typed_provider()
    cognition, _ = service(generate)
    cognition.grace_resident_id = uuid4()
    with pytest.raises(HomeCognitionExecutionError, match="not authoritative Grace"):
        cognition.execute(invocation())
    assert not calls


def test_stale_or_classification_mismatched_authoritative_state_is_rejected() -> None:
    state = grace_state()
    with pytest.raises(HomeCognitionExecutionError, match="unavailable or stale"):
        replace(state, context_bundle=state.context_bundle.with_stale_reason("superseded"))

    generate, calls = typed_provider()
    cognition, _ = service(generate, state=state)
    with pytest.raises(HomeCognitionExecutionError, match="classification differs"):
        cognition.execute(invocation(classification="operational"))
    assert not calls


def test_missing_terminal_f2_readback_rejects_generated_result() -> None:
    generate, calls = typed_provider()

    class MissingTerminalReadbackStore(MemoryEventStore):
        def read_aggregate(self, aggregate_type: str, aggregate_id: UUID):
            rows = super().read_aggregate(aggregate_type, aggregate_id)
            if aggregate_type == "cognition_request":
                return [row for row in rows if row["event_type"] != "cognition.completed"]
            return rows

    cognition, _ = service(generate, store=MissingTerminalReadbackStore())
    with pytest.raises(HomeCognitionExecutionError, match="F2 cognition provenance readback"):
        cognition.execute(invocation())
    assert len(calls) == 1


def test_missing_latency_capacity_observation_readback_fails_closed() -> None:
    generate, calls = typed_provider()

    class MissingObservationReadbackStore(MemoryEventStore):
        def read_aggregate(self, aggregate_type: str, aggregate_id: UUID):
            rows = super().read_aggregate(aggregate_type, aggregate_id)
            if aggregate_type == "cognition_request":
                return [row for row in rows if row["event_type"] != HOME_OBSERVATION_EVENT]
            return rows

    cognition, _ = service(generate, store=MissingObservationReadbackStore())
    with pytest.raises(HomeCognitionExecutionError, match="observation readback"):
        cognition.execute(invocation())
    assert len(calls) == 1


def test_provider_timeout_has_truthful_failure_and_latency_observation() -> None:
    def timed_out(_):
        raise TimeoutError("provider timed out")

    cognition, store = service(timed_out)
    outcome = cognition.execute(invocation())
    assert outcome.result is not None and outcome.result.status is CognitionResultStatus.TIMEOUT
    assert outcome.result.live_generation is False
    assert outcome.observation is not None and outcome.observation.outcome == "provider-error"
    lineage = CognitionProvenanceWriter(store).reconstruct(outcome.request.request_id)  # type: ignore[union-attr]
    assert lineage[-1].event_type is CognitionProvenanceEventType.TIMED_OUT


def test_provider_or_authorization_substitution_is_denied() -> None:
    generate, calls = typed_provider()
    cognition, _ = service(generate, rows=[candidate("ollama:other")])
    unavailable = cognition.execute(invocation())
    assert (
        unavailable.result is not None
        and unavailable.result.status is CognitionResultStatus.UNAVAILABLE
    )
    assert not calls

    cognition, _ = service(generate)
    denied = cognition.execute(invocation(authorization_ref="authority://forged"))
    assert denied.result is not None and denied.result.status is CognitionResultStatus.DENIED
    assert not calls
