"""Contract and fresh-context discovery tests for Riverview Comms5."""

from __future__ import annotations

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
