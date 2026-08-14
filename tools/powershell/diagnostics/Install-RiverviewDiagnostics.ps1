# Riverview Diagnostic Persistence Installer
# Version: 0.3.2
# Purpose: Install PostgreSQL diagnostic persistence, emergency evidence spooling, and Cookbook seed synchronization.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath = 'A:\Riverview\repo')

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ToolVersion = '0.3.2'
$ReportLines = [Collections.Generic.List[string]]::new()

function Add-Line {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text, [ConsoleColor]$Color = 'Gray')
    $ReportLines.Add($Text); Write-Host $Text -ForegroundColor $Color
}
function Add-Section { param([Parameter(Mandatory)][string]$Title); Add-Line ''; Add-Line "=== $Title ===" Cyan }
function Write-VersionedFile {
    param([Parameter(Mandatory)][string]$RelativePath, [Parameter(Mandatory)][string]$Content)
    $Path = Join-Path $RepositoryPath $RelativePath
    New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force | Out-Null
    if (Test-Path $Path) {
        $Existing = Get-Content $Path -Raw
        if ($Existing -eq $Content) { Add-Line "CURRENT   $RelativePath" DarkGray; return }
        Copy-Item $Path "$Path.pre-$ToolVersion.bak" -Force
        Add-Line "BACKUP    $RelativePath" Yellow
    }
    Set-Content -LiteralPath $Path -Value $Content -Encoding utf8NoBOM -NoNewline
    Add-Line "WRITTEN   $RelativePath" Green
}
function Invoke-Checked {
    param([Parameter(Mandatory)][string]$Label, [Parameter(Mandatory)][scriptblock]$Command)
    $Output = @(& $Command 2>&1 | ForEach-Object { "$_" }); foreach ($Line in $Output) { Add-Line $Line }
    if ($LASTEXITCODE -ne 0) { throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE." }
    Add-Line "$Label passed." Green
}
function Save-Report {
    $Directory = Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\diagnostic-engine'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path = Join-Path $Directory "Diagnostic-Engine-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard $Report } else { $Report | clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW DIAGNOSTIC ENGINE VALIDATION'
    $RepositoryPath = (Resolve-Path $RepositoryPath).Path
    if (-not (Test-Path (Join-Path $RepositoryPath '.git'))) { throw 'Riverview Git repository not found.' }
    $Python = Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    if (-not (Test-Path $Python)) { throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    $InstalledTool = Join-Path $RepositoryPath 'tools\powershell\diagnostics\Install-RiverviewDiagnostics.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $InstalledTool) -Force | Out-Null
    if ([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($InstalledTool)) {
        Copy-Item $PSCommandPath $InstalledTool -Force; Add-Line "Installed reusable tool: $InstalledTool" Green
    } else { Add-Line "Running repository tool: $InstalledTool" Green }

    Add-Section 'DIAGNOSTIC ENGINE FILES'
    $ProjectPath = Join-Path $RepositoryPath 'pyproject.toml'
    $Project = Get-Content $ProjectPath -Raw
    if ($Project.Contains('version = "0.2.0"')) {
        Copy-Item $ProjectPath "$ProjectPath.pre-$ToolVersion.bak" -Force
        $Project = $Project.Replace('# Version: 0.2.0', '# Version: 0.3.2').Replace('version = "0.2.0"', 'version = "0.3.0"')
        Set-Content $ProjectPath $Project -Encoding utf8NoBOM -NoNewline
        Add-Line 'UPDATED   pyproject.toml' Green
    }
    elseif (-not $Project.Contains('version = "0.3.0"')) { throw 'RIV-BLD-0008: Unexpected project version.' }

    Write-VersionedFile 'database\migrations\0002_diagnostic_runtime.sql' @'
-- Riverview Diagnostic Runtime Seed
-- Version: 0.3.0
-- Migration: 0002

BEGIN;

INSERT INTO cookbook_entries (
    cookbook_entry, checkpoint_id, component, failure_classes,
    diagnostic_procedure, repair_procedure, verification_procedure,
    applicability, validation_state
) VALUES
(
    'CB-RIV-DIA-0001', 'RIV-DIA-0001', 'riverview.diagnostics.store',
    '["database_unavailable", "transaction_failed", "invalid_record"]'::jsonb,
    '["Inspect the checkpoint and database health", "Inspect the emergency evidence spool"]'::jsonb,
    '["Restore PostgreSQL first", "Replay only verified spooled evidence"]'::jsonb,
    '["Run diagnostic health acceptance", "Confirm one database record"]'::jsonb,
    '{"kernel": ">=0.3.0"}'::jsonb, 'validated'
),
(
    'CB-RIV-DIA-0002', 'RIV-DIA-0002', 'riverview.diagnostics.spool',
    '["directory_unavailable", "permission_denied", "serialization_failed"]'::jsonb,
    '["Inspect the reported spool path", "Check the Windows runtime identity and ACL"]'::jsonb,
    '["Restore the local runtime directory ACL", "Do not discard the original failure"]'::jsonb,
    '["Induce database failure", "Confirm one append-only fallback record"]'::jsonb,
    '{"kernel": ">=0.3.0"}'::jsonb, 'validated'
)
ON CONFLICT (cookbook_entry) DO UPDATE SET
    failure_classes = EXCLUDED.failure_classes,
    diagnostic_procedure = EXCLUDED.diagnostic_procedure,
    repair_procedure = EXCLUDED.repair_procedure,
    verification_procedure = EXCLUDED.verification_procedure,
    applicability = EXCLUDED.applicability,
    validation_state = EXCLUDED.validation_state,
    updated_at = now();

COMMIT;
'@

    Write-VersionedFile 'src\riverview\database\migrations.py' @'
"""Small, ordered PostgreSQL migration runner.

Version: 0.3.0
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from riverview.database.connection import connect


def apply_migration(path: Path, migration_id: str, version: str) -> bool:
    """Apply an unapplied migration and record its exact checksum."""

    sql = path.read_text(encoding="utf-8-sig")
    checksum = hashlib.sha256(sql.encode()).hexdigest()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT checksum_sha256 FROM schema_migrations WHERE migration_id = %s", (migration_id,))
        row = cursor.fetchone()
        if row:
            if row[0] != checksum:
                raise RuntimeError(f"RIV-DB-0006: Applied migration {migration_id} checksum differs from source.")
            return False
        cursor.execute(sql)
        cursor.execute(
            "INSERT INTO schema_migrations (migration_id, version, checksum_sha256) VALUES (%s, %s, %s)",
            (migration_id, version, checksum),
        )
    return True
'@

    Write-VersionedFile 'src\riverview\diagnostics\__init__.py' @'
"""Riverview diagnostic contracts and persistence.

Version: 0.3.0
"""

from .models import DiagnosticEvent, RecoveryState, Severity
from .store import DiagnosticStore, PersistenceResult

__all__ = [
    "DiagnosticEvent",
    "DiagnosticStore",
    "PersistenceResult",
    "RecoveryState",
    "Severity",
]
'@

    Write-VersionedFile 'src\riverview\diagnostics\store.py' @'
"""PostgreSQL diagnostic persistence with a bounded local evidence fallback.

Version: 0.3.0
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from riverview.database import DatabaseConfig, connect
from riverview.diagnostics.models import DiagnosticEvent

DEFAULT_SPOOL = Path(r"A:\Riverview\runtime\diagnostics\spool")


@dataclass(frozen=True, slots=True)
class PersistenceResult:
    """Where diagnostic evidence was durably written."""

    destination: str
    event_id: str
    checkpoint_id: str
    fallback_path: str | None = None


class DiagnosticStore:
    """Persist diagnostics to PostgreSQL or an append-only emergency spool."""

    def __init__(
        self,
        config: DatabaseConfig | None = None,
        spool_root: Path = DEFAULT_SPOOL,
        connection_factory: Callable[..., AbstractContextManager[Any]] = connect,
    ) -> None:
        self._config = config
        self._spool_root = spool_root
        self._connection_factory = connection_factory

    def emit(self, event: DiagnosticEvent) -> PersistenceResult:
        """Write a diagnostic once; fall back locally when PostgreSQL cannot accept it."""

        record = event.as_record()
        try:
            with self._connection_factory(self._config) as connection, connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO diagnostic_events (
                        event_id, checkpoint_id, component, operation, workflow_id, attempt,
                        severity, failure_class, summary, evidence_refs, dependency_state,
                        cookbook_entry, recovery_state, occurred_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING""",
                    (
                        record["event_id"], record["checkpoint_id"], record["component"],
                        record["operation"], record["workflow_id"], record["attempt"],
                        record["severity"], record["failure_class"], record["summary"],
                        json.dumps(record["evidence_refs"]), json.dumps(record["dependency_state"]),
                        record["cookbook_entry"], record["recovery_state"], record["occurred_at"],
                    ),
                )
            return PersistenceResult("postgresql", record["event_id"], record["checkpoint_id"])
        except (RuntimeError, OSError, TypeError, ValueError) as database_error:
            return self._spool(event, database_error)

    def _spool(self, event: DiagnosticEvent, database_error: Exception) -> PersistenceResult:
        """Append emergency evidence without treating it as authoritative state."""

        try:
            self._spool_root.mkdir(parents=True, exist_ok=True)
            path = self._spool_root / f"diagnostics-{datetime.now(UTC):%Y%m%d}.ndjson"
            envelope = {
                "spool_version": "0.3.0",
                "authoritative": False,
                "spooled_at": datetime.now(UTC).isoformat(),
                "database_failure": type(database_error).__name__,
                "diagnostic": event.as_record(),
            }
            line = json.dumps(envelope, sort_keys=True, separators=(",", ":")) + os.linesep
            with path.open("a", encoding="utf-8", newline="") as stream:
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())
            return PersistenceResult("emergency_spool", str(event.event_id), event.checkpoint_id, str(path))
        except Exception as spool_error:
            raise RuntimeError(f"RIV-DIA-0002: Database and emergency spool both failed: {spool_error}") from spool_error
'@

    Write-VersionedFile 'src\riverview\diagnostic_health.py' @'
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
'@

    Write-VersionedFile 'tests\test_diagnostic_store.py' @'
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
'@

    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-DIA-0001_DIAGNOSTIC_PERSISTENCE.md' @'
<!-- Version: 0.3.0 -->
# RIV-DIA-0001 — Diagnostic persistence used its emergency seam

Trigger: A diagnostic could not be recorded in PostgreSQL and was written to the local emergency spool.

Failure classes: database unavailable, transaction failure, rejected record, or missing Cookbook foreign key.

Distinguish: Run the database health check, then inspect the latest spool envelope's failure type without exposing its diagnostic payload outside the authorized local environment.

Smallest repair: Restore the identified PostgreSQL boundary. Do not treat the spool as workflow state and do not delete it before verified replay tooling exists.

Verify: Run `.venv\Scripts\python.exe -m riverview.diagnostic_health database`; require destination `postgresql`.
'@

    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-DIA-0002_EMERGENCY_SPOOL.md' @'
<!-- Version: 0.3.0 -->
# RIV-DIA-0002 — Emergency diagnostic spool failed

Trigger: Both PostgreSQL diagnostic persistence and the append-only local evidence spool failed.

Failure classes: missing runtime directory, permission denied, full disk, serialization failure, or filesystem fault.

Distinguish: Check the reported path, free space, Windows identity, and directory ACL. Preserve the originating exception and checkpoint.

Smallest repair: Restore only the local runtime directory or its ACL, then rerun the induced fallback check.

Verify: Run `.venv\Scripts\python.exe -m riverview.diagnostic_health fallback`; require one non-authoritative emergency record.
'@

    $CookbookIndex = Join-Path $RepositoryPath 'docs\operations\troubleshooting\README.md'
    $Index = Get-Content $CookbookIndex -Raw
    if (-not $Index.Contains('`RIV-DIA-*`')) {
        $Index = $Index.Replace('- `RIV-DB-*` — database, migration, transaction, and projection', "- ``RIV-DB-*`` — database, migration, transaction, and projection`n- ``RIV-DIA-*`` — diagnostic persistence and emergency evidence spooling")
        $Index = $Index.Replace('<!-- Version: 0.1.2 -->', '<!-- Version: 0.3.0 -->')
        Set-Content $CookbookIndex $Index -Encoding utf8NoBOM -NoNewline
        Add-Line 'UPDATED   docs\operations\troubleshooting\README.md' Green
    }

    Add-Section 'MIGRATION AND ACCEPTANCE'
    Push-Location $RepositoryPath
    try {
        & $Python -m pip install -e '.[dev]'; if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
        $MigrationCommand = @'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed = apply_migration(Path('database/migrations/0002_diagnostic_runtime.sql'), '0002', '0.3.0')
print('Migration 0002 applied.' if changed else 'Migration 0002 already current.')
'@
        $MigrationCommand | & $Python -
        if ($LASTEXITCODE -ne 0) { throw 'RIV-DB-0006: Migration 0002 failed.' }
        Add-Line 'Migration 0002 acceptance passed.' Green
        Invoke-Checked 'Ruff check' { & $Python -m ruff check src tests }
        Invoke-Checked 'Pytest' { & $Python -m pytest }
        Invoke-Checked 'Python compilation' { & $Python -m compileall -q src }
        Invoke-Checked 'Database health' { & $Python -m riverview.health database }
        Invoke-Checked 'Diagnostic database persistence' { & $Python -m riverview.diagnostic_health database }
        Invoke-Checked 'Induced diagnostic fallback' { & $Python -m riverview.diagnostic_health fallback }
        Add-Section 'GIT CHANGE SUMMARY'
        foreach ($Line in @(git status --short)) { Add-Line $Line }
    } finally { Pop-Location }

    Add-Section 'DIAGNOSTIC ENGINE RESULT'
    Add-Line 'Diagnostic persistence, Cookbook seed synchronization, and induced fallback acceptance passed.' Green
    Add-Line 'No commit or push was performed.' Yellow
    Add-Line "Installer version: $ToolVersion"
    Save-Report
}
catch {
    Add-Section 'DIAGNOSTIC ENGINE BLOCKED'; Add-Line $_.Exception.Message Red
    Add-Line 'No commit or push was performed.' Yellow
    if (Test-Path $RepositoryPath -PathType Container) { Save-Report }; throw
}
