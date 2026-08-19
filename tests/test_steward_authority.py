from __future__ import annotations

from pathlib import Path

import pytest

from riverview.intake.authority import StewardAuthorityError, StewardAuthorityStore
from riverview.intake.engineering import EngineeringIntentStore
from riverview.mcp.comms5 import Comms5Error, Comms5Service


def _contract() -> dict[str, object]:
    return {
        "repository_identity": "ppow1/Riverview",
        "repository_root": str(Path.cwd()),
        "expected_base_sha": "a" * 40,
        "bounded_instruction": "Read-only repository inspection.",
        "allowed_paths": ["AI_HINTS.md", "docs/governance/RIVERVIEW_CHARTER.md"],
        "acceptance_criteria": ["return structured evidence"],
        "evidence_requirements": ["exact Git HEAD", "zero changed files"],
        "capability_name": "codex.engineering.v1",
        "action_type": "codex.engineering.v1",
        "timeout_seconds": 300,
        "write_policy": "read_only",
    }


def test_typed_contract_is_bounded_and_rejects_unregistered_action() -> None:
    contract = StewardAuthorityStore.validate_formation_contract(_contract())
    assert contract["action_type"] == "codex.engineering.v1"
    invalid = {**contract, "action_type": "shell.execute"}
    with pytest.raises(StewardAuthorityError, match="registered bounded Codex"):
        StewardAuthorityStore.validate_formation_contract(invalid)


def test_free_form_or_missing_authority_cannot_bind() -> None:
    with pytest.raises(PermissionError, match="durable Steward authority"):
        EngineeringIntentStore().bind(None, explicit_steward_confirmation=True)  # type: ignore[arg-type]


def test_contract_shape_is_not_authority() -> None:
    contract = _contract()
    with pytest.raises(StewardAuthorityError, match="incomplete or unrecognized"):
        StewardAuthorityStore.validate_formation_contract({**contract, "shell": "never"})


def test_comms5_rejects_malformed_formation_contract_before_storage() -> None:
    with pytest.raises(Comms5Error, match="registered bounded Codex"):
        Comms5Service().store_specification({
            "content": "bounded",
            "summary": "invalid formation",
            "idempotency_key": "authority-test-invalid-contract",
            "client_id": "test",
            "client_type": "test",
            "client_name": "test",
            "authenticated_principal": "authorized-ai-session",
            "formation_contract": {**_contract(), "action_type": "shell.execute"},
        })


def test_bounded_write_contract_is_typed_and_not_a_wildcard() -> None:
    contract = {**_contract(), "write_policy": "bounded_write"}
    assert StewardAuthorityStore.validate_formation_contract(contract)["write_policy"] == "bounded_write"
    with pytest.raises(StewardAuthorityError, match="incomplete"):
        StewardAuthorityStore.validate_formation_contract({**contract, "arbitrary": "write"})
