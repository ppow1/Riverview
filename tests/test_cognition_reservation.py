from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from riverview.reasoning import (
    BindingConfiguration,
    BindingConfigurationLoader,
    CapabilityBindingDecision,
    CapabilityResourceRequest,
    CognitionBindingAdapter,
    CognitionTier,
    ProviderResourceCandidate,
    ReservationError,
    ReservationState,
    ResidentCognitionReservationAdapter,
)


class Catalog:
    def __init__(self, capacity: int = 2) -> None:
        self.capacity = capacity

    def available_for(self, **_kwargs):
        return [{
            "participant_id": "participant:shared-home",
            "provider_id": "provider:shared-home",
            "provider_type": "fixture",
            "role": "advisory",
            "health": "healthy",
            "capacity": self.capacity,
            "capability_name": "home-capability",
            "contract_version": "fixture-v1",
            "classification": True,
        }]


def request() -> CapabilityResourceRequest:
    now = datetime.now(UTC)
    return CapabilityResourceRequest(
        request_id=uuid4(), correlation_id=uuid4(), resident_id=uuid4(), occupant_id=uuid4(),
        office_id=uuid4(), implementation_id=uuid4(), authority_ref="authority:fixture",
        cognition_tier=CognitionTier.HOME_COGNITION, required_capability="home-capability",
        classification="internal", policy_ref="policy:home", authorization_ref="authorization:fixture",
        deadline_at=now + timedelta(minutes=5),
    )


def binding_for(req: CapabilityResourceRequest, *, capacity: int = 2) -> tuple[CapabilityResourceRequest, CapabilityBindingDecision, ProviderResourceCandidate]:
    decision = CognitionBindingAdapter(
        Catalog(capacity),
        BindingConfigurationLoader.from_mapping({
            "HOME_COGNITION": {
                "capability_name": "home-capability",
                "policy_ref": "policy:home",
                "configuration_ref": "config:home",
            },
        }),
    ).candidates(req)
    return req, decision, decision.candidates[0]


def test_valid_reservation_preserves_exact_identity_and_is_observable() -> None:
    req, decision, candidate = binding_for(request())
    adapter = ResidentCognitionReservationAdapter()
    reservation = adapter.reserve(req, decision, candidate, priority=50, fairness_class="interactive", idempotency_key="r-1")
    assert reservation.state is ReservationState.HELD
    assert reservation.resident_id == req.resident_id
    assert reservation.occupant_id == req.occupant_id
    assert reservation.office_id == req.office_id
    assert reservation.request_id == req.request_id
    assert reservation.resource_participant_id == candidate.participant_id
    assert adapter.capacity(candidate).available_units == 1
    assert adapter.snapshot(candidate.participant_id) == (reservation,)


def test_binding_resource_and_request_correspondence_fails_closed() -> None:
    req, decision, candidate = binding_for(request())
    adapter = ResidentCognitionReservationAdapter()
    other_req, other_decision, _ = binding_for(request())
    with pytest.raises(ReservationError, match="correspond"):
        adapter.reserve(other_req, decision, candidate, priority=1, fairness_class="fair", idempotency_key="wrong-request")
    with pytest.raises(ReservationError, match="candidate"):
        adapter.reserve(req, decision, ProviderResourceCandidate(
            "participant:other", "provider:other", "fixture", "advisory", "home-capability",
            "healthy", 1, "fixture-v1", "config:home",
        ), priority=1, fairness_class="fair", idempotency_key="wrong-resource")
    wrong_binding = replace(decision, policy_ref="policy:other")
    with pytest.raises(ReservationError, match="binding"):
        adapter.reserve(req, wrong_binding, candidate, priority=1, fairness_class="fair", idempotency_key="wrong-binding")
    assert other_decision.request_id != req.request_id


def test_capacity_exhaustion_is_bounded_and_does_not_oversubscribe() -> None:
    first_req, decision, candidate = binding_for(request(), capacity=1)
    second_req, second_decision, second_candidate = binding_for(request(), capacity=1)
    adapter = ResidentCognitionReservationAdapter()
    adapter.reserve(first_req, decision, candidate, priority=50, fairness_class="interactive", idempotency_key="first")
    with pytest.raises(ReservationError, match="exhausted"):
        adapter.reserve(second_req, second_decision, second_candidate, priority=50, fairness_class="fair", idempotency_key="second")
    assert adapter.capacity(candidate).held_units == 1
    assert adapter.capacity(candidate).available_units == 0


def test_concurrent_reservation_contenders_have_one_winner_for_one_unit() -> None:
    first_req, decision, candidate = binding_for(request(), capacity=1)
    second_req, second_decision, second_candidate = binding_for(request(), capacity=1)
    adapter = ResidentCognitionReservationAdapter()

    def attempt(args):
        req, selected_decision, selected_candidate, key = args
        try:
            return adapter.reserve(req, selected_decision, selected_candidate, priority=50, fairness_class="fair", idempotency_key=key)
        except ReservationError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(attempt, ((first_req, decision, candidate, "concurrent-a"), (second_req, second_decision, second_candidate, "concurrent-b"))))
    assert sum(result is not None for result in results) == 1
    assert adapter.capacity(candidate).held_units == 1


def test_equivalent_retry_is_idempotent_but_changed_parameters_conflict() -> None:
    req, decision, candidate = binding_for(request())
    adapter = ResidentCognitionReservationAdapter()
    first = adapter.reserve(req, decision, candidate, priority=50, fairness_class="interactive", idempotency_key="same")
    retry = adapter.reserve(req, decision, candidate, priority=50, fairness_class="interactive", idempotency_key="same")
    assert retry == first
    with pytest.raises(ReservationError, match="idempotency"):
        adapter.reserve(req, decision, candidate, priority=60, fairness_class="interactive", idempotency_key="same")


def test_release_requires_owner_and_expiry_recovers_capacity() -> None:
    now = datetime.now(UTC)
    req, decision, candidate = binding_for(request())
    adapter = ResidentCognitionReservationAdapter()
    reservation = adapter.reserve(req, decision, candidate, priority=50, fairness_class="interactive", idempotency_key="release", lease_seconds=10, now=now)
    with pytest.raises(ReservationError, match="ownership"):
        adapter.release(reservation.reservation_id, request_id=req.request_id, resident_id=uuid4(), occupant_id=req.occupant_id, office_id=req.office_id, reason="foreign")
    expired = adapter.expire(now=now + timedelta(seconds=11))
    assert expired[0].state is ReservationState.EXPIRED
    assert adapter.capacity(candidate).available_units == 2
    released = adapter.release(reservation.reservation_id, request_id=req.request_id, resident_id=req.resident_id, occupant_id=req.occupant_id, office_id=req.office_id, reason="completed")
    assert released.state is ReservationState.EXPIRED


def test_priority_and_fairness_are_observable_without_claiming_scheduler_fairness() -> None:
    req, decision, candidate = binding_for(request(), capacity=2)
    second_req, second_decision, second_candidate = binding_for(request(), capacity=2)
    adapter = ResidentCognitionReservationAdapter()
    low = adapter.reserve(req, decision, candidate, priority=10, fairness_class="background", idempotency_key="low")
    high = adapter.reserve(second_req, second_decision, second_candidate, priority=90, fairness_class="interactive", idempotency_key="high")
    assert adapter.snapshot(candidate.participant_id) == (high, low)
    assert not hasattr(adapter, "dispatch")
