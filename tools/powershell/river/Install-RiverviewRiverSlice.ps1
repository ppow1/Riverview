# Riverview River Runtime Slice Installer
# Version: 0.2.0
# Purpose: Install and validate the first PostgreSQL-backed River event runtime.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath = 'A:\Riverview\repo')

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ToolVersion = '0.2.0'
$ReportLines = [Collections.Generic.List[string]]::new()

function Add-Line {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text, [ConsoleColor]$Color = 'Gray')
    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}

function Add-Section {
    param([Parameter(Mandatory)][string]$Title)
    Add-Line ''
    Add-Line "=== $Title ===" Cyan
}

function Write-VersionedFile {
    param([Parameter(Mandatory)][string]$RelativePath, [Parameter(Mandatory)][string]$Content)
    $Path = Join-Path $RepositoryPath $RelativePath
    $Directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    if (Test-Path -LiteralPath $Path) {
        $Existing = Get-Content -LiteralPath $Path -Raw
        if ($Existing -eq $Content) { Add-Line "CURRENT   $RelativePath" DarkGray; return }
        $Backup = "$Path.pre-$ToolVersion.bak"
        Copy-Item -LiteralPath $Path -Destination $Backup -Force
        Add-Line "BACKUP    $RelativePath" Yellow
    }
    Set-Content -LiteralPath $Path -Value $Content -Encoding utf8NoBOM -NoNewline
    Add-Line "WRITTEN   $RelativePath" Green
}

function Invoke-Checked {
    param([Parameter(Mandatory)][string]$Label, [Parameter(Mandatory)][scriptblock]$Command)
    $Output = @(& $Command 2>&1 | ForEach-Object { "$_" })
    foreach ($Line in $Output) { Add-Line $Line }
    if ($LASTEXITCODE -ne 0) { throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE." }
    Add-Line "$Label passed." Green
}

function Save-Report {
    $RuntimeRoot = Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\river'
    New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
    $Path = Join-Path $RuntimeRoot "River-Slice-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    Set-Content -LiteralPath $Path -Value $Report -Encoding utf8NoBOM -NoNewline
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard $Report }
    else { $Report | clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW RIVER SLICE VALIDATION'
    $RepositoryPath = (Resolve-Path $RepositoryPath).Path
    if (-not (Test-Path (Join-Path $RepositoryPath '.git'))) { throw 'Riverview Git repository not found.' }
    if (-not (Test-Path (Join-Path $RepositoryPath '.venv\Scripts\python.exe'))) { throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    $Python = Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    $SecretMetadata = 'A:\Riverview\data\secrets\postgresql\credential-metadata.json'
    if (-not (Test-Path $SecretMetadata)) { throw 'RIV-DB-0002: PostgreSQL credential metadata was not found.' }
    Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    $InstalledTool = Join-Path $RepositoryPath 'tools\powershell\river\Install-RiverviewRiverSlice.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $InstalledTool) -Force | Out-Null
    if ([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($InstalledTool)) {
        Copy-Item -LiteralPath $PSCommandPath -Destination $InstalledTool -Force
        Add-Line "Installed reusable tool: $InstalledTool" Green
    }
    else { Add-Line "Running repository tool: $InstalledTool" Green }

    Add-Section 'RUNTIME FILES'
    Write-VersionedFile 'pyproject.toml' @'
# Riverview Python Project Configuration
# Version: 0.2.0
[build-system]
requires = ["hatchling>=1.27,<2"]
build-backend = "hatchling.build"

[project]
name = "riverview-kernel"
version = "0.2.0"
description = "Diagnostics-first kernel for The Estate at Riverview"
requires-python = ">=3.12"
dependencies = [
  "psycopg[binary]>=3.2,<4",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3,<9",
  "ruff>=0.9,<1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.hatch.build.targets.wheel]
packages = ["src/riverview"]
'@

    Write-VersionedFile 'src\riverview\database\__init__.py' @'
"""PostgreSQL access for Riverview Kernel.

Version: 0.2.0
"""

from .connection import DatabaseConfig, connect, load_database_config

__all__ = ["DatabaseConfig", "connect", "load_database_config"]
'@

    Write-VersionedFile 'src\riverview\database\connection.py' @'
"""DPAPI-backed PostgreSQL connection boundary.

Version: 0.2.0
"""

from __future__ import annotations

import ctypes
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import psycopg

DEFAULT_METADATA = Path(r"A:\Riverview\data\secrets\postgresql\credential-metadata.json")


class DataBlob(ctypes.Structure):
    """Windows DATA_BLOB used by CryptUnprotectData."""

    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    """Non-secret connection settings plus the recovered application password."""

    host: str
    port: int
    database: str
    user: str
    password: str


def _unprotect_dpapi(ciphertext_hex: str) -> str:
    if os.name != "nt":
        raise RuntimeError("RIV-DB-0003: DPAPI credentials require the provisioning Windows user.")
    encrypted = bytes.fromhex(ciphertext_hex.strip())
    buffer = ctypes.create_string_buffer(encrypted)
    source = DataBlob(len(encrypted), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    destination = DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(destination)
    ):
        raise RuntimeError(f"RIV-DB-0003: DPAPI recovery failed with Windows error {ctypes.GetLastError()}.")
    try:
        raw = ctypes.string_at(destination.pbData, destination.cbData)
        return raw.decode("utf-16-le")
    finally:
        kernel32.LocalFree(destination.pbData)


def load_database_config(metadata_path: Path = DEFAULT_METADATA) -> DatabaseConfig:
    """Load metadata and recover the application credential for the current user."""

    try:
        metadata: dict[str, Any] = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        secret_path = Path(metadata["application_secret"])
        password = _unprotect_dpapi(secret_path.read_text(encoding="ascii"))
        return DatabaseConfig(
            host=str(metadata["host"]),
            port=int(metadata["port"]),
            database=str(metadata["database"]),
            user=str(metadata["application_role"]),
            password=password,
        )
    except RuntimeError:
        raise
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"RIV-DB-0002: Credential configuration is invalid: {exc}") from exc


@contextmanager
def connect(config: DatabaseConfig | None = None) -> Iterator[psycopg.Connection[Any]]:
    """Open a transaction-scoped database connection."""

    active = config or load_database_config()
    try:
        with psycopg.connect(
            host=active.host,
            port=active.port,
            dbname=active.database,
            user=active.user,
            password=active.password,
            connect_timeout=5,
        ) as connection:
            yield connection
    except psycopg.Error as exc:
        raise RuntimeError(f"RIV-DB-0004: PostgreSQL connection or transaction failed: {exc}") from exc
'@

    Write-VersionedFile 'src\riverview\river\__init__.py' @'
"""The River event runtime.

Version: 0.2.0
"""

from .events import Classification, RiverEvent
from .store import EventStore

__all__ = ["Classification", "EventStore", "RiverEvent"]
'@

    Write-VersionedFile 'src\riverview\river\events.py' @'
"""Immutable River event contract.

Version: 0.2.0
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4


class Classification(StrEnum):
    """Initial routing classifications; Undercurrent never uses ordinary River storage."""

    RIVER = "river"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True)
class RiverEvent:
    """A single immutable fact accepted by The River."""

    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    idempotency_key: str
    payload: Mapping[str, Any]
    correlation_id: UUID = field(default_factory=uuid4)
    causation_id: UUID | None = None
    classification: Classification = Classification.RIVER
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        for name in ("event_type", "aggregate_type", "idempotency_key"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
'@

    Write-VersionedFile 'src\riverview\river\store.py' @'
"""Transactional PostgreSQL event store.

Version: 0.2.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from riverview.database import DatabaseConfig, connect
from riverview.river.events import RiverEvent


@dataclass(frozen=True, slots=True)
class AppendResult:
    """Stable acknowledgement for accepted or previously accepted events."""

    sequence_id: int
    event_id: UUID
    inserted: bool


class EventStore:
    """Append and read River events without leaking connection mechanics."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def append(self, event: RiverEvent) -> AppendResult:
        """Append once by idempotency key and return the canonical event identity."""

        statement = """
            INSERT INTO river_events (
                event_id, event_type, aggregate_type, aggregate_id, correlation_id,
                causation_id, idempotency_key, classification, payload, occurred_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING sequence_id, event_id
        """
        try:
            with connect(self._config) as connection, connection.cursor() as cursor:
                cursor.execute(
                    statement,
                    (
                        event.event_id,
                        event.event_type,
                        event.aggregate_type,
                        event.aggregate_id,
                        event.correlation_id,
                        event.causation_id,
                        event.idempotency_key,
                        event.classification.value,
                        json.dumps(dict(event.payload)),
                        event.occurred_at,
                    ),
                )
                row = cursor.fetchone()
                if row:
                    return AppendResult(sequence_id=row[0], event_id=row[1], inserted=True)
                cursor.execute(
                    "SELECT sequence_id, event_id FROM river_events WHERE idempotency_key = %s",
                    (event.idempotency_key,),
                )
                existing = cursor.fetchone()
                if not existing:
                    raise RuntimeError("RIV-EVT-0002: Idempotency reconciliation found no event.")
                return AppendResult(sequence_id=existing[0], event_id=existing[1], inserted=False)
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"RIV-EVT-0001: Event append failed: {exc}") from exc

    def read_aggregate(self, aggregate_type: str, aggregate_id: UUID) -> list[dict[str, Any]]:
        """Read an aggregate stream in authoritative sequence order."""

        try:
            with connect(self._config) as connection, connection.cursor() as cursor:
                cursor.execute(
                    """SELECT sequence_id, event_id, event_type, payload, occurred_at
                       FROM river_events
                       WHERE aggregate_type = %s AND aggregate_id = %s
                       ORDER BY sequence_id""",
                    (aggregate_type, aggregate_id),
                )
                return [
                    {
                        "sequence_id": row[0],
                        "event_id": str(row[1]),
                        "event_type": row[2],
                        "payload": row[3],
                        "occurred_at": row[4].isoformat(),
                    }
                    for row in cursor.fetchall()
                ]
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"RIV-EVT-0003: Aggregate read failed: {exc}") from exc
'@

    Write-VersionedFile 'src\riverview\health.py' @'
"""Executable health and event-store smoke checks.

Version: 0.2.0
"""

from __future__ import annotations

import argparse
import json
from uuid import uuid4

from riverview.database import connect
from riverview.river import EventStore, RiverEvent


def database_health() -> dict[str, object]:
    """Verify identity, migration, and required table visibility."""

    required = {"schema_migrations", "river_events", "diagnostic_events", "cookbook_entries"}
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_user")
        database, user = cursor.fetchone()
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = {row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT migration_id FROM schema_migrations ORDER BY migration_id")
        migrations = [row[0] for row in cursor.fetchall()]
    missing = sorted(required - tables)
    if missing:
        raise RuntimeError(f"RIV-DB-0005: Required tables are missing: {', '.join(missing)}")
    return {"status": "healthy", "database": database, "user": user, "migrations": migrations}


def event_smoke() -> dict[str, object]:
    """Append, idempotently replay, and read one acceptance event."""

    aggregate_id = uuid4()
    key = f"acceptance:{uuid4()}"
    event = RiverEvent(
        event_type="riverview.acceptance.probe",
        aggregate_type="acceptance_probe",
        aggregate_id=aggregate_id,
        idempotency_key=key,
        payload={"tool_version": "0.2.0"},
    )
    store = EventStore()
    first = store.append(event)
    replay = store.append(event)
    stream = store.read_aggregate("acceptance_probe", aggregate_id)
    if not first.inserted or replay.inserted or len(stream) != 1:
        raise RuntimeError("RIV-EVT-0004: Event acceptance invariant failed.")
    return {
        "status": "healthy",
        "sequence_id": first.sequence_id,
        "idempotent_replay": True,
        "stream_length": len(stream),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Riverview runtime acceptance")
    parser.add_argument("check", choices=("database", "event"))
    args = parser.parse_args()
    result = database_health() if args.check == "database" else event_smoke()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
'@

    Write-VersionedFile 'tests\test_river_event.py' @'
"""Unit tests for the first River event contract.

Version: 0.2.0
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from riverview.river import Classification, RiverEvent


def test_event_is_immutable_and_payload_is_detached() -> None:
    source = {"step": 147}
    event = RiverEvent(
        event_type="workflow.step.ready",
        aggregate_type="workflow",
        aggregate_id=uuid4(),
        idempotency_key="workflow:one:147",
        payload=source,
        occurred_at=datetime(2026, 8, 14, tzinfo=UTC),
    )
    source["step"] = 999
    assert event.payload["step"] == 147
    assert event.classification is Classification.RIVER


def test_event_rejects_empty_identity_fields() -> None:
    with pytest.raises(ValueError, match="event_type"):
        RiverEvent(
            event_type=" ",
            aggregate_type="workflow",
            aggregate_id=uuid4(),
            idempotency_key="key",
            payload={},
        )


def test_event_requires_timezone_aware_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        RiverEvent(
            event_type="workflow.step.ready",
            aggregate_type="workflow",
            aggregate_id=uuid4(),
            idempotency_key="key",
            payload={},
            occurred_at=datetime(2026, 8, 14),
        )
'@

    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-DB-0002_CREDENTIAL_CONFIGURATION.md' @'
<!-- Version: 0.2.0 -->
# RIV-DB-0002 — Credential configuration unavailable

Trigger: River cannot read PostgreSQL metadata or its application-secret path.

Distinguish: Confirm `A:\Riverview\data\secrets\postgresql\credential-metadata.json` and the referenced `riverview-app.dpapi` file exist. Never paste their contents into chat.

Smallest repair: Rerun `tools\powershell\database\Initialize-RiverviewDatabase.ps1` as the intended Windows runtime user.

Verify: Run `.venv\Scripts\python.exe -m riverview.health database`; require `status: healthy`.
'@

    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-DB-0003_DPAPI_RECOVERY.md' @'
<!-- Version: 0.2.0 -->
# RIV-DB-0003 — DPAPI credential recovery failed

Trigger: The application credential cannot be decrypted by the running Windows identity.

Distinguish: Compare the current Windows user with the user that ran database provisioning. Do not move or disclose the encrypted value.

Smallest repair: Run provisioning again as the service/runtime identity so DPAPI creates a CurrentUser-protected replacement.

Verify: Run `.venv\Scripts\python.exe -m riverview.health database`; require `status: healthy`.
'@

    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-DB-0004_CONNECTION_TRANSACTION.md' @'
<!-- Version: 0.2.0 -->
# RIV-DB-0004 — PostgreSQL connection or transaction failed

Trigger: psycopg cannot connect, authenticate, or commit a transaction.

Distinguish: Check service `postgresql-x64-18`, listener port 5432, metadata host/port, then DPAPI recovery. Do not reset credentials until those probes identify authentication as the fault.

Smallest repair: Start the stopped service, correct metadata, or rerun provisioning only for confirmed credential failure.

Verify: Run `.venv\Scripts\python.exe -m riverview.health database`; require `status: healthy`.
'@

    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-EVT-0001_EVENT_APPEND.md' @'
<!-- Version: 0.2.0 -->
# RIV-EVT-0001 — River event append failed

Trigger: A validated event cannot be appended to `river_events`.

Distinguish: First run the database health check. If healthy, inspect field shape, UUIDs, classification, JSON serialization, and unique keys. Preserve the original event and correlation identifiers.

Smallest repair: Correct only the rejected event field or the identified database boundary; do not bypass idempotency.

Verify: Run `.venv\Scripts\python.exe -m riverview.health event`; require one insertion, one non-inserting replay, and stream length one.
'@

    Add-Section 'DEPENDENCIES AND STATIC ACCEPTANCE'
    Push-Location $RepositoryPath
    try {
        & $Python -m pip install -e '.[dev]'
        if ($LASTEXITCODE -ne 0) { throw 'RIV-BLD-0007: Riverview dependency installation failed.' }
        Invoke-Checked 'Ruff check' { & $Python -m ruff check src tests }
        Invoke-Checked 'Pytest' { & $Python -m pytest }
        Invoke-Checked 'Python compilation' { & $Python -m compileall -q src }

        Add-Section 'LIVE DATABASE ACCEPTANCE'
        Invoke-Checked 'Database health' { & $Python -m riverview.health database }
        Invoke-Checked 'River event smoke test' { & $Python -m riverview.health event }

        Add-Section 'GIT CHANGE SUMMARY'
        $Status = @(git status --short)
        foreach ($Line in $Status) { Add-Line $Line }
        if ($LASTEXITCODE -ne 0) { throw 'Git status failed.' }
    }
    finally { Pop-Location }

    Add-Section 'RIVER SLICE RESULT'
    Add-Line 'First PostgreSQL-backed River runtime slice passed acceptance.' Green
    Add-Line 'No commit or push was performed.' Yellow
    Add-Line "Installer version: $ToolVersion"
    Save-Report
}
catch {
    Add-Section 'RIVER SLICE BLOCKED'
    Add-Line $_.Exception.Message Red
    Add-Line 'No commit or push was performed.' Yellow
    if (Test-Path $RepositoryPath -PathType Container) { Save-Report }
    throw
}
