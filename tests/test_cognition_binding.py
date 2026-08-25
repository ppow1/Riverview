from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from riverview.reasoning import (
    BindingConfiguration,
    BindingConfigurationLoader,
    CapabilityBindingError,
    CapabilityResourceRequest,
    CognitionBindingAdapter,
    CognitionTier,
    TierBinding,
)


class FixtureCatalog:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.calls: list[dict[str, object]] = []

    def available_for(self, **kwargs):
        self.calls.append(kwargs)
        return self.rows


def request(*, tier=CognitionTier.HOME_COGNITION, capability="home-capability", policy="policy:home", classification="internal", exclusions=()):
    now = datetime.now(UTC)
    return CapabilityResourceRequest(
        request_id=uuid4(), correlation_id=uuid4(), resident_id=uuid4(), occupant_id=uuid4(),
        office_id=uuid4(), implementation_id=uuid4(), authority_ref="authority:fixture",
        cognition_tier=tier, required_capability=capability, classification=classification,
        policy_ref=policy, authorization_ref="authorization:fixture", exclusions=exclusions,
        deadline_at=now + timedelta(minutes=5),
    )


def configuration() -> BindingConfiguration:
    return BindingConfigurationLoader.from_mapping({
        "HOME_COGNITION": {"capability_name": "home-capability", "policy_ref": "policy:home", "configuration_ref": "config:home", "resource_class_ref": "resident-reasoning"},
        "HIGH_REASONING": {"capability_name": "high-capability", "policy_ref": "policy:high", "configuration_ref": "config:high"},
        "EXTERNAL_ESCALATION": {"capability_name": "external-capability", "policy_ref": "policy:external", "configuration_ref": "config:external"},
    })


def row(provider_id="provider-a", *, health="healthy", capacity=2, capability_name="home-capability", classification=True):
    return {"participant_id": f"participant:{provider_id}", "provider_id": provider_id, "provider_type": "fixture", "role": "advisory", "health": health, "capacity": capacity, "capability_name": capability_name, "contract_version": "fixture-v1", "classification": classification}


def test_request_and_candidates_are_topology_neutral() -> None:
    catalog = FixtureCatalog([row()])
    req = request()
    decision = CognitionBindingAdapter(catalog, configuration()).candidates(req)
    assert decision.status == "available"
    assert decision.candidates[0].provider_id == "provider-a"
    assert decision.selected is None
    assert not {"gpu", "gpu_id", "model", "model_ref", "endpoint", "host"}.intersection(decision.as_payload())
    assert catalog.calls == [{"request_classification": "internal", "required_capability": "home-capability", "max_age_seconds": 300}]


def test_ineligible_health_capacity_classification_and_capability_are_denied() -> None:
    adapter = CognitionBindingAdapter(FixtureCatalog([row(health="disabled")]), configuration())
    assert adapter.candidates(request()).status == "unavailable"
    adapter = CognitionBindingAdapter(FixtureCatalog([row(capacity=0)]), configuration())
    assert adapter.candidates(request()).status == "unavailable"
    adapter = CognitionBindingAdapter(FixtureCatalog([row(capability_name="other")]), configuration())
    assert adapter.candidates(request()).status == "unavailable"
    assert adapter.candidates(request(classification="private")).status == "unavailable"


def test_provider_exclusion_and_replacement_are_configuration_concerns() -> None:
    catalog = FixtureCatalog([row("provider-old"), row("provider-new")])
    adapter = CognitionBindingAdapter(catalog, configuration())
    decision = adapter.candidates(request(exclusions=("provider-old",)))
    assert [candidate.provider_id for candidate in decision.candidates] == ["provider-new"]
    replacement = BindingConfigurationLoader.from_mapping({"HOME_COGNITION": {"capability_name": "replacement-capability", "policy_ref": "policy:home", "configuration_ref": "config:replacement"}})
    replacement_decision = CognitionBindingAdapter(FixtureCatalog([row(capability_name="replacement-capability")]), replacement).candidates(request(capability="replacement-capability"))
    assert replacement_decision.status == "available"
    assert adapter.configuration.for_tier(CognitionTier.HOME_COGNITION).capability_name == "home-capability"


def test_no_candidate_and_missing_binding_are_truthful() -> None:
    assert CognitionBindingAdapter(FixtureCatalog([]), configuration()).candidates(request()).status == "unavailable"
    only_high = BindingConfiguration((TierBinding(CognitionTier.HIGH_REASONING, "high-capability", "policy:high", "config:high"),))
    assert CognitionBindingAdapter(FixtureCatalog([]), only_high).candidates(request()).status == "unavailable"


def test_physical_topology_and_resident_identity_cannot_enter_binding_configuration() -> None:
    with pytest.raises(CapabilityBindingError, match="not allowed"):
        BindingConfigurationLoader.from_mapping({"HOME_COGNITION": {"capability_name": "home-capability", "policy_ref": "policy:home", "configuration_ref": "config:home", "gpu_id": "gpu-0"}})
    with pytest.raises(CapabilityBindingError, match="not allowed"):
        BindingConfigurationLoader.from_mapping({"HOME_COGNITION": {"capability_name": "home-capability", "policy_ref": "policy:home", "configuration_ref": "config:home", "resident_id": str(uuid4())}})


def test_request_policy_and_capability_mismatch_fails_without_fallback() -> None:
    adapter = CognitionBindingAdapter(FixtureCatalog([row()]), configuration())
    assert adapter.candidates(request(capability="high-capability")).status == "unavailable"
    assert adapter.candidates(request(policy="policy:other")).status == "unavailable"
