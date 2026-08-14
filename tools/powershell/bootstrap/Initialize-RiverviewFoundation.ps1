# Riverview Foundation Initializer
# Version: 0.1.0
# Purpose: Create the diagnostics-first Riverview repository foundation without committing or pushing.
# Updated: 2026-08-14

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$RepositoryPath = 'A:\Riverview\repo'
)

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ToolVersion = [version]'0.1.0'
$CanonicalToolName = 'Initialize-RiverviewFoundation.ps1'
$CanonicalToolDirectory = 'tools\powershell\bootstrap'
$ReportLines = [System.Collections.Generic.List[string]]::new()
$Created = [System.Collections.Generic.List[string]]::new()
$Unchanged = [System.Collections.Generic.List[string]]::new()
$Conflicts = [System.Collections.Generic.List[string]]::new()

function Add-ReportLine {
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$Text,
        [ConsoleColor]$Color = [ConsoleColor]::Gray
    )

    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}

function Add-Section {
    param([Parameter(Mandatory)][string]$Title)

    Add-ReportLine -Text ''
    Add-ReportLine -Text "=== $Title ===" -Color Cyan
}

function Get-HeaderVersion {
    param([Parameter(Mandatory)][string]$Path)

    $Line = Get-Content -LiteralPath $Path -TotalCount 12 |
        Where-Object { $_ -match '^(#|--|<!--)\s*Version:\s*(?<Version>\d+\.\d+\.\d+)' } |
        Select-Object -First 1

    if (-not $Line) {
        throw "No version header was found in: $Path"
    }

    return [version]([regex]::Match($Line, 'Version:\s*(?<Version>\d+\.\d+\.\d+)').Groups['Version'].Value)
}

function Install-Self {
    param([Parameter(Mandatory)][string]$Root)

    if (-not $PSCommandPath) {
        throw 'Run this initializer from a saved .ps1 file.'
    }

    $Source = (Resolve-Path -LiteralPath $PSCommandPath).Path
    $DestinationDirectory = Join-Path $Root $CanonicalToolDirectory
    $Destination = Join-Path $DestinationDirectory $CanonicalToolName
    New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null

    $SourceVersion = Get-HeaderVersion -Path $Source
    if ($SourceVersion -ne $ToolVersion) {
        throw "Initializer version mismatch: header=$SourceVersion runtime=$ToolVersion"
    }

    if ($Source -ieq $Destination) {
        Add-ReportLine -Text "Running installed tool: $Destination" -Color Green
        return $Destination
    }

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $DestinationVersion = Get-HeaderVersion -Path $Destination
        $SourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
        $DestinationHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash

        if ($DestinationVersion -gt $SourceVersion) {
            throw "A newer initializer is already installed: $Destination"
        }

        if (($DestinationVersion -eq $SourceVersion) -and ($SourceHash -ne $DestinationHash)) {
            throw "Initializer content differs at the same version: $Destination"
        }

        if ($SourceHash -eq $DestinationHash) {
            Add-ReportLine -Text "Initializer already current: $Destination" -Color Green
            return $Destination
        }

        $Backup = "$Destination.pre-$SourceVersion.bak"
        Copy-Item -LiteralPath $Destination -Destination $Backup -Force
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
        Add-ReportLine -Text "Updated initializer: $Destination" -Color Green
        Add-ReportLine -Text "Previous initializer preserved: $Backup" -Color Yellow
        return $Destination
    }

    Copy-Item -LiteralPath $Source -Destination $Destination
    Add-ReportLine -Text "Installed initializer: $Destination" -Color Green
    return $Destination
}

function Add-FoundationFile {
    param(
        [Parameter(Mandatory)][string]$RelativePath,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )

    $Destination = Join-Path $RepositoryPath $RelativePath
    $Parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $Parent -Force | Out-Null

    $NormalizedContent = $Content.TrimStart("`r", "`n")
    if (-not $NormalizedContent.EndsWith("`n")) {
        $NormalizedContent += "`n"
    }

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $Existing = Get-Content -LiteralPath $Destination -Raw
        $ComparableExisting = $Existing -replace "`r`n", "`n"
        $ComparableNew = $NormalizedContent -replace "`r`n", "`n"

        if ($ComparableExisting -eq $ComparableNew) {
            $Unchanged.Add($RelativePath)
        }
        else {
            $Conflicts.Add($RelativePath)
        }
        return
    }

    Set-Content -LiteralPath $Destination -Value $NormalizedContent -Encoding utf8NoBOM -NoNewline
    $Created.Add($RelativePath)
}

Add-Section -Title 'RIVERVIEW FOUNDATION VALIDATION'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git was not found on PATH.'
}

if (-not (Test-Path -LiteralPath $RepositoryPath -PathType Container)) {
    throw "Riverview repository was not found: $RepositoryPath"
}

$RepositoryPath = (Resolve-Path -LiteralPath $RepositoryPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $RepositoryPath '.git') -PathType Container)) {
    throw "Riverview Git metadata was not found: $RepositoryPath"
}

Set-Location -LiteralPath $RepositoryPath
Add-ReportLine -Text "Repository validated: $RepositoryPath" -Color Green

Add-Section -Title 'SELF-INSTALLATION'
$InstalledTool = Install-Self -Root $RepositoryPath

Add-Section -Title 'FOUNDATION FILES'

$Files = [ordered]@{
    '.gitignore' = @'
# Riverview Ignore Rules
# Version: 0.1.0

.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.env
.env.*
!.env.example
runtime/
data/
artifacts/
*.log
*.sqlite
*.sqlite3
*.db
*.bak
'@
    'README.md' = @'
<!-- Version: 0.1.0 -->
# Project Riverview

Project Riverview is the purposeful rebuild of the Estate's operational mechanism. The final environment is **The Estate at Riverview**, its core architecture is **The River**, and the first technical implementation is **Riverview Kernel v0.1**.

The River is local-first, event-driven, durable, diagnostics-first, and designed to sustain momentum without making the Steward the routine router.

## Foundation commitments

- PostgreSQL is authoritative operational state.
- JSON is transport, configuration, fixtures, or export—not the workflow database.
- Grace owns workflow progression and capability routing.
- The Continuous Momentum Engine detects and advances eligible work.
- MCP is the reasoning data bus; Playwright is the ChatGPT doorbell.
- Local AI and Codex CLI are bounded execution providers.
- OpenAI API models are excluded from the architecture.
- The Undercurrent is the protected high-trust domain.
- Data is separated from actions and classified at ingestion.
- Every capability is delivered with diagnostics, failure checkpoints, tests, and Cookbook knowledge.

Start with `AI_HINTS.md` and `docs/operations/RIVERVIEW_EXECUTION_PLAN.md`.
'@
    'AI_HINTS.md' = @'
<!-- Version: 0.1.0 -->
# Riverview AI Hints

Status: Canonical fast-recovery entry point.

Pat is the Steward and final authority. Grace coordinates operational progression but is not the whole Estate at Riverview.

Before creating, modifying, testing, deploying, or promoting Riverview software, read completely:

1. `docs/architecture/RIVERVIEW_FOUNDATION.md`
2. `docs/operations/RIVERVIEW_EXECUTION_PLAN.md`
3. `docs/operations/troubleshooting/README.md`
4. `docs/decisions/ADR-0001_POSTGRESQL_AUTHORITY.md`
5. `docs/decisions/ADR-0002_DIAGNOSTICS_FIRST.md`

Rules:

- Inspect before adding.
- Preserve unrelated work.
- Do not claim GitHub publication until the remote commit is verified.
- Diagnostics are part of implementation.
- Tests must exercise the boundary being claimed.
- Conversation memory is not authoritative state.
- Do not add governance unless an existing document cannot absorb the requirement.
- Do not route work through an OpenAI API model.
- Do not expose Undercurrent or sensitive data through ordinary River paths.
- A capability is not complete until its failure behavior is diagnosable and recovery is verifiable.
'@
    'docs/architecture/RIVERVIEW_FOUNDATION.md' = @'
<!-- Version: 0.1.0 -->
# Riverview Foundation Architecture

Status: Designed

## Mission

Preserve the Estate's mission, residents, offices, continuity, engineering capacity, and human-centered character while replacing accumulated internal complexity with a small, explicit, self-diagnosing mechanism.

## Governing model

- **Project Riverview** is the endeavor.
- **The Estate at Riverview** is the final environment.
- **The River** is the core event-driven architecture.
- **Riverview Kernel v0.1** is the first implementation.
- **The Undercurrent** is the restricted high-trust domain.

## Kernel boundaries

The kernel initially owns only:

1. Durable event recording.
2. Objective and workflow state.
3. Work assignment, ownership, attempts, and leases.
4. Diagnostic checkpoints and evidence.
5. Cookbook linkage and staleness.
6. Capability/provider registration.
7. Grace and Continuous Momentum Engine progression contracts.
8. MCP mailbox correlation.

Interfaces, residents, visual environments, Open WebUI, SillyTavern, Stream Deck, command-chair devices, voice, Bluetooth, remote access, and Quest/3D presentation remain adapters or consumers—not kernel responsibilities.

## Operational sentence

Playwright is the doorbell. MCP is the data bus. PostgreSQL is durable River memory. Grace controls progression. The Steward supplies ideation, bounded authority, selected checkpoints, exceptions, and final acceptance.

## Data boundary

Runtime data, private material, transcripts, screenshots, generated media, credentials, and large artifacts remain outside source code. PostgreSQL records identity, classification, ownership, hashes, lifecycle, and storage references. The Undercurrent uses explicit access and promotion boundaries.

## Anti-complexity rule

New mechanisms require a distinct responsibility that cannot be absorbed by an existing kernel component or adapter. Compatibility with the Estate is implemented through bounded adapters rather than copying entire subsystems.
'@
    'docs/operations/RIVERVIEW_EXECUTION_PLAN.md' = @'
<!-- Version: 0.1.0 -->
# Riverview Persistent Execution Plan

Status: Active

This file is the persistent scope-control reference for the Riverview build.

## Phase 0 — Foundation

- Repository structure and source provenance
- PostgreSQL authority decision and initial migration
- Diagnostic event contract
- Troubleshooting Cookbook structure
- Tests for the diagnostic contract
- Local audit and synchronization tools

Exit: foundation tests pass locally; Cookbook covers every implemented failure checkpoint; exact commit is published and verified.

## Phase 1 — The River

- Append-only event ledger
- Transactional projections
- Objectives, workflows, stages, dependencies, attempts, and leases
- Idempotency and correlation
- Discovery and health surfaces
- Induced-failure acceptance

## Phase 2 — Momentum and routing

- Grace progression loop
- Continuous Momentum Engine
- Capability-aware worker registry
- Parallel lanes and path ownership
- Stalled-work recovery
- Execution envelopes that avoid routine approval drip

## Phase 3 — Execution adapters

- Deterministic local commands
- RTX 4090 local-AI adapter
- P100 local-AI adapter
- Codex CLI adapter
- Evidence capture and result reconciliation

## Phase 4 — Reasoning bridge

- MCP mailbox lifecycle
- Playwright ChatGPT wake worker
- Correlated structured responses
- `submit_seed_to_grace` interactive Steward path
- No OpenAI API model path

## Phase 5 — Operator environment

- Open WebUI and SillyTavern adapters
- Notification adapter, initially compatible with the Estate
- Stream Deck and command-chair input adapters
- Dictation, screenshots, voice, remote, and later Quest/3D surfaces

## Scope controls

- Revisit this plan before every material addition.
- Park useful non-current ideas rather than implementing them.
- Prefer working vertical slices over broad scaffolding.
- Do not mark later phases complete from documents or mocks.
- Every phase preserves diagnostics, rollback provenance, data separation, and Undercurrent boundaries.
'@
    'docs/operations/troubleshooting/README.md' = @'
<!-- Version: 0.1.0 -->
# Riverview Troubleshooting Cookbook

Status: Designed; initial kernel entries pending implementation evidence.

The Cookbook is a living operational knowledge system connected to implementation revisions, diagnostic events, induced-failure tests, and recovery verification.

## Required checkpoint knowledge

Every checkpoint records:

- Stable checkpoint ID
- Component and seam ownership
- Triggering operation
- Known failure classes
- Evidence captured automatically
- Safe distinguishing probes
- Smallest permitted repair
- Recovery verification
- Escalation boundary
- Applicable implementation revisions
- Validation and staleness state

## Initial checkpoint namespace

- `RIV-DB-*` — database, migration, transaction, and projection
- `RIV-EVT-*` — event acceptance and delivery
- `RIV-WRK-*` — worker assignment, attempts, ownership, and leases
- `RIV-CME-*` — momentum detection and recovery
- `RIV-MCP-*` — mailbox, correlation, claims, and responses
- `RIV-PLY-*` — Playwright doorbell and conversation state
- `RIV-LOC-*` — local execution adapters
- `RIV-SEC-*` — classification and Undercurrent boundaries

## Acceptance rule

No capability is operationally complete until a new AI conversation can identify the checkpoint, distinguish modeled failures, perform the smallest safe repair, and verify recovery from repository guidance and captured evidence.
'@
    'docs/decisions/ADR-0001_POSTGRESQL_AUTHORITY.md' = @'
<!-- Version: 0.1.0 -->
# ADR-0001: PostgreSQL Is the Authoritative River State Store

Status: Accepted

## Decision

PostgreSQL stores authoritative operational state for events, objectives, workflows, work, leases, mailbox messages, diagnostics, Cookbook knowledge, and audit provenance.

SQLite is permitted only for isolated caches, offline adapters, and tests that do not claim PostgreSQL concurrency equivalence. JSON remains a bounded payload and interchange format, not the workflow database.

## Reason

Riverview requires concurrent writers, transactional claims, leases, idempotency, indexing, recovery, and durable correlation. PostgreSQL provides these without constructing a custom file-state system.

## Consequences

- All schema changes use ordered migrations.
- Important searchable state uses typed columns.
- JSONB is permitted for bounded extensible payloads.
- Large artifacts remain outside PostgreSQL and are referenced by metadata.
- Concurrency and recovery acceptance run against PostgreSQL.
'@
    'docs/decisions/ADR-0002_DIAGNOSTICS_FIRST.md' = @'
<!-- Version: 0.1.0 -->
# ADR-0002: Diagnostics Are Part of Implementation

Status: Accepted

## Decision

Every material Riverview change includes first-pass diagnostic metadata, stable checkpoints, focused probes, induced-failure tests where feasible, Cookbook candidate knowledge, and recovery verification.

## Reason

The Estate demonstrated that implementation without immediate diagnostic knowledge creates architectural archaeology and consumes excessive Steward attention.

## Consequences

- Missing diagnostic coverage blocks operational completion.
- Cookbook prose without linked code, tests, and evidence is not canonical.
- Changed code can mark applicable Cookbook knowledge stale.
- The implementing worker supplies first-pass knowledge; validation promotes it.
'@
    'pyproject.toml' = @'
# Riverview Python Project Configuration
# Version: 0.1.0

[build-system]
requires = ["hatchling>=1.27,<2"]
build-backend = "hatchling.build"

[project]
name = "riverview-kernel"
version = "0.1.0"
description = "Diagnostics-first kernel for The Estate at Riverview"
requires-python = ">=3.12"
dependencies = []

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
'@
    'src/riverview/__init__.py' = @'
"""Riverview Kernel package.

Version: 0.1.0
"""

__version__ = "0.1.0"
'@
    'src/riverview/diagnostics/__init__.py' = @'
"""Riverview diagnostic contracts.

Version: 0.1.0
"""

from .models import DiagnosticEvent, RecoveryState, Severity

__all__ = ["DiagnosticEvent", "RecoveryState", "Severity"]
'@
    'src/riverview/diagnostics/models.py' = @'
"""Typed diagnostic event contract for the Riverview Kernel.

Version: 0.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


class Severity(StrEnum):
    """Diagnostic severity values."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryState(StrEnum):
    """Recovery lifecycle for a diagnostic event."""

    UNVERIFIED = "unverified"
    DIAGNOSED = "diagnosed"
    REPAIRING = "repairing"
    RECOVERED = "recovered"
    ESCALATED = "escalated"


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    """Immutable first-pass diagnostic event emitted at a stable checkpoint."""

    checkpoint_id: str
    component: str
    operation: str
    severity: Severity
    failure_class: str
    summary: str
    cookbook_entry: str
    workflow_id: UUID | None = None
    attempt: int = 1
    evidence_refs: tuple[str, ...] = ()
    dependency_state: Mapping[str, Any] = field(default_factory=dict)
    recovery_state: RecoveryState = RecoveryState.UNVERIFIED
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.checkpoint_id.startswith("RIV-"):
            raise ValueError("checkpoint_id must begin with 'RIV-'")
        if self.attempt < 1:
            raise ValueError("attempt must be at least 1")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        object.__setattr__(self, "dependency_state", MappingProxyType(dict(self.dependency_state)))

    def as_record(self) -> dict[str, Any]:
        """Return a database/transport-safe record."""

        return {
            "checkpoint_id": self.checkpoint_id,
            "event_id": str(self.event_id),
            "component": self.component,
            "operation": self.operation,
            "workflow_id": str(self.workflow_id) if self.workflow_id else None,
            "attempt": self.attempt,
            "severity": self.severity.value,
            "failure_class": self.failure_class,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "dependency_state": dict(self.dependency_state),
            "cookbook_entry": self.cookbook_entry,
            "recovery_state": self.recovery_state.value,
            "occurred_at": self.occurred_at.isoformat(),
        }
'@
    'tests/test_diagnostic_contract.py' = @'
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
'@
    'database/migrations/0001_river_foundation.sql' = @'
-- Riverview River Foundation Migration
-- Version: 0.1.0
-- Migration: 0001

BEGIN;

CREATE TABLE schema_migrations (
    migration_id text PRIMARY KEY,
    version text NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now(),
    checksum_sha256 text NOT NULL
);

CREATE TABLE river_events (
    sequence_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id uuid NOT NULL UNIQUE,
    event_type text NOT NULL,
    aggregate_type text NOT NULL,
    aggregate_id uuid NOT NULL,
    correlation_id uuid NOT NULL,
    causation_id uuid,
    idempotency_key text NOT NULL UNIQUE,
    classification text NOT NULL,
    payload jsonb NOT NULL,
    occurred_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX river_events_aggregate_sequence_idx
    ON river_events (aggregate_type, aggregate_id, sequence_id);

CREATE INDEX river_events_correlation_idx
    ON river_events (correlation_id, sequence_id);

CREATE TABLE cookbook_entries (
    cookbook_entry text PRIMARY KEY,
    checkpoint_id text NOT NULL UNIQUE,
    component text NOT NULL,
    failure_classes jsonb NOT NULL,
    diagnostic_procedure jsonb NOT NULL,
    repair_procedure jsonb NOT NULL,
    verification_procedure jsonb NOT NULL,
    applicability jsonb NOT NULL,
    validation_state text NOT NULL,
    validated_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE diagnostic_events (
    event_id uuid PRIMARY KEY,
    checkpoint_id text NOT NULL,
    component text NOT NULL,
    operation text NOT NULL,
    workflow_id uuid,
    attempt integer NOT NULL CHECK (attempt >= 1),
    severity text NOT NULL,
    failure_class text NOT NULL,
    summary text NOT NULL,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    dependency_state jsonb NOT NULL DEFAULT '{}'::jsonb,
    cookbook_entry text NOT NULL REFERENCES cookbook_entries(cookbook_entry),
    recovery_state text NOT NULL,
    occurred_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX diagnostic_events_checkpoint_time_idx
    ON diagnostic_events (checkpoint_id, occurred_at DESC);

COMMIT;
'@
}

foreach ($Entry in $Files.GetEnumerator()) {
    Add-FoundationFile -RelativePath $Entry.Key -Content $Entry.Value
}

foreach ($Path in $Created) {
    Add-ReportLine -Text "CREATED   $Path" -Color Green
}
foreach ($Path in $Unchanged) {
    Add-ReportLine -Text "UNCHANGED $Path"
}
foreach ($Path in $Conflicts) {
    Add-ReportLine -Text "CONFLICT  $Path (preserved; not overwritten)" -Color Red
}

Add-Section -Title 'STATIC VALIDATION'

$RequiredPaths = @($Files.Keys) + @($CanonicalToolDirectory + '\' + $CanonicalToolName)
$MissingPaths = @(
    foreach ($Path in $RequiredPaths) {
        if (-not (Test-Path -LiteralPath (Join-Path $RepositoryPath $Path) -PathType Leaf)) {
            $Path
        }
    }
)

if ($MissingPaths.Count -gt 0) {
    foreach ($Path in $MissingPaths) {
        Add-ReportLine -Text "MISSING   $Path" -Color Red
    }
}
else {
    Add-ReportLine -Text 'All required foundation files exist.' -Color Green
}

$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($PythonCommand) {
    $CompileOutput = & python -m compileall -q (Join-Path $RepositoryPath 'src') 2>&1
    $CompileExit = $LASTEXITCODE
    if ($CompileExit -eq 0) {
        Add-ReportLine -Text 'Python source compilation passed.' -Color Green
    }
    else {
        Add-ReportLine -Text "Python source compilation failed (exit $CompileExit)." -Color Red
        foreach ($Line in $CompileOutput) { Add-ReportLine -Text "  $Line" -Color Red }
    }
}
else {
    $CompileExit = -1
    Add-ReportLine -Text 'Python was not found on PATH; compilation was not run.' -Color Yellow
}

Add-Section -Title 'GIT CHANGE SUMMARY'
$GitStatus = @(& git status --short 2>&1 | ForEach-Object { "$_" })
foreach ($Line in $GitStatus) {
    Add-ReportLine -Text $Line
}

Add-Section -Title 'FOUNDATION RESULT'
$HasFailure = ($Conflicts.Count -gt 0) -or ($MissingPaths.Count -gt 0) -or ($CompileExit -gt 0)
if ($HasFailure) {
    Add-ReportLine -Text 'Foundation completed with blockers. No commit or push was performed.' -Color Red
}
else {
    Add-ReportLine -Text 'Foundation files created and statically validated. No commit or push was performed.' -Color Green
}
Add-ReportLine -Text "Initializer: $InstalledTool"
Add-ReportLine -Text "Initializer version: $ToolVersion"

$WorkspaceRoot = Split-Path -Parent $RepositoryPath
$ReportDirectory = Join-Path $WorkspaceRoot 'runtime\diagnostics\foundation'
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$ReportPath = Join-Path $ReportDirectory "Riverview-Foundation-$Timestamp.txt"
$Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine

New-Item -ItemType Directory -Path $ReportDirectory -Force | Out-Null
Set-Content -LiteralPath $ReportPath -Value $Report -Encoding utf8NoBOM -NoNewline

if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
    Set-Clipboard -Value $Report
}
elseif (Get-Command clip.exe -ErrorAction SilentlyContinue) {
    $Report | & clip.exe
}
else {
    Add-ReportLine -Text 'Clipboard command unavailable; use the durable report path.' -Color Yellow
}

Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
Write-Host "Durable report: $ReportPath" -ForegroundColor Green
Write-Host 'Paste the report into the Riverview conversation.' -ForegroundColor Cyan

if ($HasFailure) {
    throw 'Riverview foundation validation reported blockers. Review the copied report.'
}
