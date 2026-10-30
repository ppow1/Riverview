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


@pytest.mark.parametrize(
    ("method_name", "payload_fields"),
    [
        (
            "cancel_draft",
            {
                "seed_id": "00000000-0000-4000-8000-000000000001",
                "reason": "test",
                "idempotency_key": "cancel-auth-test",
            },
        ),
        (
            "supersede_seed",
            {
                "seed_id": "00000000-0000-4000-8000-000000000001",
                "replacement_seed_id": "00000000-0000-4000-8000-000000000002",
                "reason": "test",
                "idempotency_key": "supersede-auth-test",
            },
        ),
    ],
)
def test_seed_lifecycle_writes_reject_spoofed_steward_body_principal(
    monkeypatch: pytest.MonkeyPatch, method_name: str, payload_fields: dict[str, object]
) -> None:
    from riverview.mcp.comms5 import CONTRACT_VERSION

    calls: list[object] = []

    def mutate(*args: object, **kwargs: object) -> dict[str, object]:
        calls.append((args, kwargs))
        return {}

    monkeypatch.setattr(f"riverview.mcp.comms5.StewardSeedStore.{method_name}", mutate)
    monkeypatch.setattr(Comms5Service, "_append_lifecycle_event", lambda *args: None)
    payload = {
        **payload_fields,
        "explicit_steward_confirmation": True,
        "client_id": "chatgpt:test",
        "client_type": "external_ai",
        "client_name": "Comms5 test",
        "authenticated_principal": "steward",
        "protocol_version": CONTRACT_VERSION,
    }

    with pytest.raises(Comms5Error) as error:
        getattr(Comms5Service(), method_name)(payload)
    assert error.value.code == "RIV-COMMS5-0009"
    assert calls == []


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        (
            "comms5_cancel_draft",
            {
                "seed_id": "00000000-0000-4000-8000-000000000001",
                "reason": "test",
                "idempotency_key": "cancel-wrapper-auth-test",
                "explicit_steward_confirmation": True,
                "client_id": "chatgpt:test",
                "client_type": "external_ai",
                "client_name": "Comms5 test",
                "authenticated_principal": "steward",
            },
        ),
        (
            "comms5_supersede_seed",
            {
                "seed_id": "00000000-0000-4000-8000-000000000001",
                "replacement_seed_id": "00000000-0000-4000-8000-000000000002",
                "reason": "test",
                "idempotency_key": "supersede-wrapper-auth-test",
                "explicit_steward_confirmation": True,
                "client_id": "chatgpt:test",
                "client_type": "external_ai",
                "client_name": "Comms5 test",
                "authenticated_principal": "steward",
            },
        ),
    ],
)
def test_seed_lifecycle_mcp_wrappers_use_transport_attestation(
    monkeypatch: pytest.MonkeyPatch, tool_name: str, arguments: dict[str, object]
) -> None:
    from types import SimpleNamespace

    from riverview.mcp import comms5_server

    captured: list[object] = []

    def denied(request: dict[str, object], *, transport_principal: str | None = None) -> object:
        captured.append((request, transport_principal))
        raise Comms5Error("RIV-COMMS5-0009", "denied", tool_name.removeprefix("comms5_"), retry_safe=False)

    method_name = tool_name.removeprefix("comms5_")
    monkeypatch.setattr(comms5_server.service, method_name, denied)
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={}))
    )
    result = getattr(comms5_server, tool_name)(**arguments, ctx=ctx)
    assert result["error"]["code"] == "RIV-COMMS5-0009"
    assert captured and captured[0][1] is None


def test_seed_lifecycle_mutation_tool_schemas_explain_transport_authority() -> None:
    from riverview.mcp.comms5_server import mcp

    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    for name in ("comms5_cancel_draft", "comms5_supersede_seed"):
        description = tools[name].parameters["properties"]["authenticated_principal"]["description"]
        assert "provenance only" in description
        assert "authenticated transport" in description


@pytest.mark.parametrize(
    ("method_name", "payload_fields"),
    [
        (
            "cancel_draft",
            {
                "seed_id": "00000000-0000-4000-8000-000000000001",
                "reason": "approved cancellation",
                "idempotency_key": "cancel-authorized-test",
            },
        ),
        (
            "supersede_seed",
            {
                "seed_id": "00000000-0000-4000-8000-000000000001",
                "replacement_seed_id": "00000000-0000-4000-8000-000000000002",
                "reason": "approved replacement",
                "idempotency_key": "supersede-authorized-test",
            },
        ),
    ],
)
def test_seed_lifecycle_writes_use_attested_steward_as_audit_actor(
    monkeypatch: pytest.MonkeyPatch, method_name: str, payload_fields: dict[str, object]
) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    seed_id = payload_fields["seed_id"]
    result = {
        "seed_id": seed_id,
        "correlation_id": "00000000-0000-4000-8000-000000000003",
        "classification": "river",
        "lifecycle_event_id": "00000000-0000-4000-8000-000000000004",
    }

    def mutate(*args: object, **kwargs: object) -> dict[str, object]:
        calls.append((args, kwargs))
        return result

    monkeypatch.setattr(f"riverview.mcp.comms5.StewardSeedStore.{method_name}", mutate)
    monkeypatch.setattr(Comms5Service, "_append_lifecycle_event", lambda *args: None)
    payload = {
        **payload_fields,
        "explicit_steward_confirmation": True,
        "client_id": "chatgpt:test",
        "client_type": "external_ai",
        "client_name": "Comms5 test",
        "authenticated_principal": "spoofed-client-value",
    }

    output = getattr(Comms5Service(), method_name)(payload, transport_principal="steward")
    assert output["steward_action_required"] is False
    assert len(calls) == 1
    assert calls[0][1]["actor"] == "steward"
