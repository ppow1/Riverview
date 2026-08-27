"""Production composition of the accepted Grace HOME cognition seams."""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any
from uuid import UUID, uuid4

from riverview.reasoning.binding import BindingConfigurationLoader, CognitionBindingAdapter
from riverview.reasoning.contracts import ReasoningRequest, ReasoningResponse
from riverview.reasoning.home_cognition import AuthorizedHomeProvider, HomeCognitionInvocation, HomeCognitionService
from riverview.reasoning.cognition_contracts import CognitionTier
from riverview.reasoning.grace_state import GRACE_AUTHORITY_REF, GRACE_IMPLEMENTATION_ID, GRACE_OCCUPANT_ID, PostgresAuthoritativeGraceStateSource
from riverview.reasoning.escalation_policy import ConsequenceClass
from riverview.river.store import EventStore


class _MeasuredLocalCatalog:
    def __init__(self, provider_id: str, model: str) -> None:
        self.provider_id = provider_id
        self.model = model

    def available_for(self, *, request_classification: str, required_capability: str, max_age_seconds: int = 300) -> Sequence[Mapping[str, object]]:
        return ({
            "participant_id": "local:ollama:rtx4090",
            "provider_id": self.provider_id,
            "provider_type": "ollama",
            "role": "advisory",
            "capability_name": required_capability,
            "health": "healthy",
            "capacity": 1,
            "contract_version": "ollama-reasoning-envelope-v1",
            "eligible_classifications": (request_classification,),
        },)


def build_grace_home_cognition(provider: Callable[[str, ReasoningRequest], ReasoningResponse], model: str) -> HomeCognitionService:
    provider_id = f"ollama:{model}"
    configuration = BindingConfigurationLoader.from_mapping({
        CognitionTier.HOME_COGNITION.value: {
            "capability_name": "HOME_COGNITION",
            "policy_ref": "grace-home-cognition-policy:v1",
            "configuration_ref": "riverview:home-cognition:ollama",
            "resource_class_ref": "local:RTX4090",
        }
    })
    authorized = AuthorizedHomeProvider(
        provider_id=provider_id,
        authorization_ref="resident-implementation-policy:v1",
        generate=lambda request: provider(model, request),
    )
    return HomeCognitionService(
        grace_resident_id=GRACE_OCCUPANT_ID,
        state_source=PostgresAuthoritativeGraceStateSource(),
        event_store=EventStore(),
        binding_adapter=CognitionBindingAdapter(_MeasuredLocalCatalog(provider_id, model), configuration),
        provider=authorized,
    )


def invocation_for_message(*, instruction: str, correlation_id: UUID, classification: str, prior_history: tuple[str, ...] = ()) -> HomeCognitionInvocation:
    return HomeCognitionInvocation(
        objective_id=uuid4(),
        source_cognition_event_id=uuid4(),
        correlation_id=correlation_id,
        request_class="operator-grace-conversation",
        objective="Provide bounded operational judgment for the current Riverview conversation.",
        question=instruction,
        consequence=ConsequenceClass.MEDIUM,
        classification=classification,
        expires_at=__import__("datetime").datetime.now(__import__("datetime").UTC).replace(microsecond=0) + __import__("datetime").timedelta(minutes=5),
        authorization_ref=GRACE_AUTHORITY_REF,
        home_belief=True,
        home_belief_reason="Grace's bounded Director of Operations conversation is assigned to HOME cognition.",
        constraints=("advisory only", "no execution", "no authority expansion", "preserve evidence/assumption distinction"),
        relevant_prior_decisions=prior_history,
    )
