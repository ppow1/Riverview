"""Mailbox contract tests that do not require PostgreSQL.

Version: 0.10.0
"""

from uuid import uuid4

import pytest

from riverview.mailbox.store import MAX_PAYLOAD_BYTES, MailboxStore


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
