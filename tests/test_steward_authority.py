from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from riverview.intake.authority import StewardAuthorityError, StewardAuthorityStore
from riverview.intake.engineering import EngineeringIntentStore
from riverview.mcp.comms5 import Comms5Error, Comms5Service


def test_promoted_seed_authority_lock_excludes_nullable_specification_join() -> None:
    sql = Path("src/riverview/intake/authority.py").read_text(encoding="utf-8")
    assert "LEFT JOIN comms5_specifications s" in sql
    assert "FOR UPDATE OF sd,o,st" in sql
    assert "objective_id=%s FOR UPDATE\"\"\"" not in sql


def test_for_stage_uses_transaction_context_manager_for_runtime_recovery() -> None:
    class Cursor:
        def __init__(self) -> None:
            self.closed = False

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.closed = True

        def execute(self, *_args) -> None:
            return None

        def fetchone(self):
            return None

    class Connection:
        def __init__(self) -> None:
            self.cursor_instance = Cursor()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def cursor(self):
            return self.cursor_instance

    connection = Connection()

    @contextmanager
    def fake_connect():
        yield connection

    with patch("riverview.intake.authority.connect", fake_connect):
        result = StewardAuthorityStore().for_stage(uuid4(), uuid4())

    assert result is None
    assert connection.cursor_instance.closed is True


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


def test_intent_derives_write_policy_from_approved_contract() -> None:
    contract = {**_contract(), "write_policy": "bounded_write"}
    authority = {
        "authority_id": uuid4(), "seed_id": uuid4(), "objective_id": uuid4(), "stage_id": uuid4(),
        "classification": "river", "correlation_id": uuid4(), "causation_id": uuid4(),
        "scope": {"contract": contract},
    }
    assert StewardAuthorityStore.intent_from_contract(authority).write_policy == "bounded_write"
