"""Mailbox contract tests that do not require PostgreSQL.

Version: 0.10.0
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from riverview.mailbox.store import MAX_PAYLOAD_BYTES, MailboxStore, _claim_action


def test_mailbox_rejects_oversized_payload_before_database_access() -> None:
    with pytest.raises(ValueError, match="exceeds"):
        MailboxStore().submit(
            sender_id="test",
            requester_id="test",
            message_type="test.request",
            idempotency_key=f"test.{uuid4()}",
            payload={"content": "x" * MAX_PAYLOAD_BYTES},
        )


def test_mailbox_rejects_protected_classification_before_database_access() -> None:
    with pytest.raises(ValueError, match="classification"):
        MailboxStore().submit(
            sender_id="test",
            requester_id="test",
            message_type="test.request",
            idempotency_key=f"test.{uuid4()}",
            payload={"bounded": True},
            classification="undercurrent",
        )


def test_mailbox_retry_contract_methods_are_available() -> None:
    assert callable(MailboxStore.acknowledge)
    assert callable(MailboxStore.claim)
    assert callable(MailboxStore.acknowledge_reasoning)
    assert callable(MailboxStore.claim_reasoning)
    assert callable(MailboxStore.respond_reasoning)
    assert callable(MailboxStore.expire_and_escalate)


def test_reasoning_consumer_identity_is_fixed() -> None:
    from riverview.mailbox import REASONING_CONSUMER_ID

    assert REASONING_CONSUMER_ID == "chatgpt:riverview_001"


def test_claim_recovery_allows_expired_lease_without_changing_lineage() -> None:
    now = datetime.now(UTC)
    message = SimpleNamespace(
        completion_state="pending",
        expires_at=now + timedelta(minutes=5),
        claim_state="claimed",
        claim_owner="chatgpt:riverview_001",
        claim_expires_at=now - timedelta(seconds=1),
    )
    assert _claim_action(message, "chatgpt:riverview_001", now) == "reclaim_expired"


def test_claim_retry_and_active_foreign_conflict_remain_bounded() -> None:
    now = datetime.now(UTC)
    message = SimpleNamespace(
        completion_state="pending",
        expires_at=now + timedelta(minutes=5),
        claim_state="claimed",
        claim_owner="chatgpt:riverview_001",
        claim_expires_at=now + timedelta(minutes=1),
    )
    assert _claim_action(message, "chatgpt:riverview_001", now) == "retry"
    with pytest.raises(RuntimeError, match="already claimed"):
        _claim_action(message, "foreign-consumer", now)


def test_claim_recovery_rejects_expired_request() -> None:
    now = datetime.now(UTC)
    message = SimpleNamespace(
        completion_state="pending",
        expires_at=now - timedelta(seconds=1),
        claim_state="claimed",
        claim_owner="chatgpt:riverview_001",
        claim_expires_at=now - timedelta(seconds=1),
    )
    with pytest.raises(RuntimeError, match="expired"):
        _claim_action(message, "chatgpt:riverview_001", now)
