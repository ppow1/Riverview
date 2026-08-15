from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from riverview.diagnostics import DiagnosticEvent, RecoveryState, Severity


def test_diagnostic_event_retains_stable_checkpoint_and_recovery_lineage() -> None:
    event = DiagnosticEvent(
        checkpoint_id="RIV-REASON-0001",
        component="reasoning",
        operation="provider_selection",
        severity=Severity.WARNING,
        failure_class="provider-unavailable",
        summary="No healthy compatible reasoning provider.",
        cookbook_entry="RIV-REASON-0001",
        workflow_id=uuid4(),
        evidence_refs=("table:reasoning_providers",),
        dependency_state={"capacity": "exhausted"},
        recovery_state=RecoveryState.DIAGNOSED,
        occurred_at=datetime.now(UTC),
    )
    record = event.as_record()
    assert record["checkpoint_id"] == "RIV-REASON-0001"
    assert record["cookbook_entry"] == "RIV-REASON-0001"
    assert record["recovery_state"] == "diagnosed"
    assert record["evidence_refs"] == ["table:reasoning_providers"]


def test_new_checkpoint_docs_are_stable_and_cookbook_linked() -> None:
    root = Path(__file__).parents[1]
    for checkpoint in ("RIV-REASON-0001", "RIV-SEC-0001", "RIV-INT-0001"):
        matches = list((root / "docs/operations/troubleshooting/checkpoints").glob(f"{checkpoint}_*.md"))
        assert len(matches) == 1
        content = matches[0].read_text(encoding="utf-8")
        assert all(section in content for section in ("SYMPTOM", "BOUNDARY", "VERIFY", "DO NOT", "EVIDENCE"))
