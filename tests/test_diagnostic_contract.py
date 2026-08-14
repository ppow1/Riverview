"""Tests for the Riverview diagnostic event contract.

Version: 0.1.0
"""

from datetime import UTC, datetime

import pytest

from riverview.diagnostics import DiagnosticEvent, RecoveryState, Severity


def test_diagnostic_event_produces_transport_safe_record() -> None:
    event = DiagnosticEvent(
        checkpoint_id="RIV-EVT-0001",
        component="river.event_store",
        operation="append",
        severity=Severity.ERROR,
        failure_class="database_unavailable",
        summary="The event store could not reach PostgreSQL.",
        cookbook_entry="CB-RIV-EVT-0001",
        dependency_state={"postgresql": "unavailable"},
        occurred_at=datetime(2026, 8, 14, tzinfo=UTC),
    )

    record = event.as_record()

    assert record["checkpoint_id"] == "RIV-EVT-0001"
    assert record["severity"] == "error"
    assert record["recovery_state"] == RecoveryState.UNVERIFIED.value
    assert record["dependency_state"] == {"postgresql": "unavailable"}


def test_checkpoint_namespace_is_required() -> None:
    with pytest.raises(ValueError, match="checkpoint_id"):
        DiagnosticEvent(
            checkpoint_id="EVT-0001",
            component="river.event_store",
            operation="append",
            severity=Severity.ERROR,
            failure_class="invalid_checkpoint",
            summary="Invalid checkpoint namespace.",
            cookbook_entry="CB-EVT-0001",
        )


def test_attempt_must_be_positive() -> None:
    with pytest.raises(ValueError, match="attempt"):
        DiagnosticEvent(
            checkpoint_id="RIV-EVT-0002",
            component="river.event_store",
            operation="append",
            severity=Severity.ERROR,
            failure_class="invalid_attempt",
            summary="Attempt number was invalid.",
            cookbook_entry="CB-RIV-EVT-0002",
            attempt=0,
        )
