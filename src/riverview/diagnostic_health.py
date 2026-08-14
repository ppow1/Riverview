"""Live acceptance checks for diagnostic persistence and failure fallback.

Version: 0.3.0
"""

from __future__ import annotations

import argparse
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

from riverview.diagnostics import DiagnosticEvent, DiagnosticStore, RecoveryState, Severity


def database_acceptance() -> dict[str, object]:
    event = DiagnosticEvent(
        checkpoint_id="RIV-DIA-0001",
        component="riverview.diagnostics.acceptance",
        operation="database_probe",
        severity=Severity.INFO,
        failure_class="acceptance_probe",
        summary="Diagnostic persistence acceptance probe.",
        cookbook_entry="CB-RIV-DIA-0001",
        recovery_state=RecoveryState.RECOVERED,
    )
    result = DiagnosticStore().emit(event)
    if result.destination != "postgresql":
        raise RuntimeError(f"RIV-DIA-0001: Expected PostgreSQL; used {result.destination}.")
    return {"status": "healthy", "destination": result.destination, "checkpoint_id": result.checkpoint_id}


def fallback_acceptance() -> dict[str, object]:
    @contextmanager
    def failed_connection(_config=None):
        raise RuntimeError("induced_database_unavailable")
        yield

    with tempfile.TemporaryDirectory(prefix="riverview-diagnostic-") as temporary:
        event = DiagnosticEvent(
            checkpoint_id="RIV-DIA-0001",
            component="riverview.diagnostics.acceptance",
            operation="fallback_probe",
            severity=Severity.ERROR,
            failure_class="induced_database_unavailable",
            summary="Induced failure used to verify the emergency evidence seam.",
            cookbook_entry="CB-RIV-DIA-0001",
        )
        result = DiagnosticStore(spool_root=Path(temporary), connection_factory=failed_connection).emit(event)
        path = Path(result.fallback_path or "")
        lines = path.read_text(encoding="utf-8").splitlines()
        envelope = json.loads(lines[-1])
        if result.destination != "emergency_spool" or envelope["authoritative"] is not False:
            raise RuntimeError("RIV-DIA-0002: Emergency spool invariant failed.")
    return {"status": "healthy", "destination": "emergency_spool", "authoritative": False, "records": 1}


def main() -> None:
    parser = argparse.ArgumentParser(description="Riverview diagnostic acceptance")
    parser.add_argument("check", choices=("database", "fallback"))
    args = parser.parse_args()
    result = database_acceptance() if args.check == "database" else fallback_acceptance()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()