"""Contract and fresh-context discovery tests for Riverview Comms5."""

from __future__ import annotations

from uuid import UUID

import pytest

from riverview.mcp.comms5 import CONTRACT_VERSION, Comms5Error, Comms5Service


def test_comms5_is_self_describing_for_a_fresh_client() -> None:
    service = Comms5Service()
    discovered = service.help()
    assert discovered["contract"]["contract"] == CONTRACT_VERSION
    operations = discovered["capabilities"]["operations"]
    names = {item["name"] for item in operations}
    required = {"submit_steward_seed", "store_specification", "seed_status", "seed_lineage", "objective_status", "cme_status", "cancel_draft", "supersede_seed"}
    assert required <= names
    assert discovered["do_not"]
    for operation in names:
        assert service.describe_operation(operation)["authorization"]
    assert service.describe_operation("cancel_draft")["authorization"] == "STEWARD-GATED_WRITE"
    assert service.describe_operation("supersede_seed")["authorization"] == "STEWARD-GATED_WRITE"


def test_comms5_does_not_treat_client_identity_as_steward_authority() -> None:
    try:
        Comms5Service().confirm_and_promote_seed({"seed_id": "not-used", "idempotency_key": "client-attempt", "authenticated_principal": "authorized-ai", "explicit_steward_confirmation": True, "client_id": "agent", "client_type": "external_ai", "client_name": "Test Agent"})
    except Comms5Error as error:
        assert error.code == "RIV-COMMS5-0009"
    else:  # pragma: no cover
        raise AssertionError("client identity was treated as Steward authority")


def test_comms5_promotion_denial_is_stable() -> None:
    try:
        Comms5Service().confirm_and_promote_seed({"seed_id": "00000000-0000-4000-8000-000000000001", "idempotency_key": "denial-attempt", "authenticated_principal": "authorized-ai", "explicit_steward_confirmation": False, "client_id": "agent", "client_type": "external_ai", "client_name": "Test Agent"})
    except Comms5Error as error:
        assert error.code == "RIV-COMMS5-0009"
        assert error.steward_action_required is True
    else:  # pragma: no cover
        raise AssertionError("unauthorized promotion was accepted")


def test_comms5_promotion_requires_transport_attestation_not_body_principal(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[UUID, str, str]] = []

    def promoted(_store: object, seed_id: UUID, *, confirmer: str, idempotency_key: str) -> UUID:
        calls.append((seed_id, confirmer, idempotency_key))
        return UUID("00000000-0000-4000-8000-000000000002")

    monkeypatch.setattr("riverview.mcp.comms5.StewardSeedStore.confirm_and_promote", promoted)
    request = {
        "seed_id": "00000000-0000-4000-8000-000000000001",
        "idempotency_key": "attested-approval",
        "authenticated_principal": "spoofed-body-value",
        "explicit_steward_confirmation": True,
        "client_id": "chatgpt:riverview_001",
        "client_type": "external_ai",
        "client_name": "Riverview Comms5",
    }
    with pytest.raises(Comms5Error, match="client identity is not authority"):
        Comms5Service().confirm_and_promote_seed(request)
    result = Comms5Service().confirm_and_promote_seed(request, transport_principal="steward")
    assert result["authority_source"] == "authenticated_comms5_connector"
    assert calls == [(UUID("00000000-0000-4000-8000-000000000001"), "steward", "attested-approval")]
