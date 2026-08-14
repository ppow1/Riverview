"""Tests for diagnostic persistence routing.

Version: 0.3.0
"""

import json
from contextlib import contextmanager

from riverview.diagnostics import DiagnosticEvent, DiagnosticStore, Severity


def test_database_failure_uses_non_authoritative_spool(tmp_path) -> None:
    @contextmanager
    def failed_connection(_config=None):
        raise RuntimeError("induced")
        yield

    event = DiagnosticEvent(
        checkpoint_id="RIV-DIA-0001",
        component="test",
        operation="emit",
        severity=Severity.ERROR,
        failure_class="induced",
        summary="Induced failure.",
        cookbook_entry="CB-RIV-DIA-0001",
    )
    result = DiagnosticStore(spool_root=tmp_path, connection_factory=failed_connection).emit(event)
    record = json.loads((tmp_path / next(tmp_path.iterdir()).name).read_text(encoding="utf-8"))
    assert result.destination == "emergency_spool"
    assert record["authoritative"] is False
    assert record["diagnostic"]["event_id"] == str(event.event_id)