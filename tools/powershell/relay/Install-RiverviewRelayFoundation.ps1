# Riverview Relay Foundation Installer
# Version: 0.4.0
# Purpose: Install the canonical waypoint ledger and safe durable work-order lifecycle.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath = 'A:\Riverview\standalone')

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ToolVersion = '0.4.0'
$ReportLines = [Collections.Generic.List[string]]::new()

function Add-Line { param([Parameter(Mandatory)][AllowEmptyString()][string]$Text, [ConsoleColor]$Color = 'Gray'); $ReportLines.Add($Text); Write-Host $Text -ForegroundColor $Color }
function Add-Section { param([Parameter(Mandatory)][string]$Title); Add-Line ''; Add-Line "=== $Title ===" Cyan }
function Write-VersionedFile {
    param([Parameter(Mandatory)][string]$RelativePath, [Parameter(Mandatory)][string]$Content)
    $Path = Join-Path $RepositoryPath $RelativePath; New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force | Out-Null
    if (Test-Path $Path) { $Existing = Get-Content $Path -Raw; if ($Existing -eq $Content) { Add-Line "CURRENT   $RelativePath" DarkGray; return }; Copy-Item $Path "$Path.pre-$ToolVersion.bak" -Force; Add-Line "BACKUP    $RelativePath" Yellow }
    Set-Content $Path $Content -Encoding utf8NoBOM -NoNewline; Add-Line "WRITTEN   $RelativePath" Green
}
function Invoke-Checked {
    param([Parameter(Mandatory)][string]$Label, [Parameter(Mandatory)][scriptblock]$Command)
    $Output = @(& $Command 2>&1 | ForEach-Object { "$_" }); foreach ($Line in $Output) { Add-Line $Line }
    if ($LASTEXITCODE -ne 0) { throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE." }; Add-Line "$Label passed." Green
}
function Save-Report {
    $Directory = Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\relay'; New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path = Join-Path $Directory "Relay-Foundation-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"; $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline; if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard $Report } else { $Report | clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan; Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW RELAY FOUNDATION VALIDATION'
    $RepositoryPath = (Resolve-Path $RepositoryPath).Path; if (-not (Test-Path (Join-Path $RepositoryPath '.git'))) { throw 'Riverview Git repository not found.' }
    $Python = Join-Path $RepositoryPath '.venv\Scripts\python.exe'; if (-not (Test-Path $Python)) { throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    $InstalledTool = Join-Path $RepositoryPath 'tools\powershell\relay\Install-RiverviewRelayFoundation.ps1'; New-Item -ItemType Directory -Path (Split-Path -Parent $InstalledTool) -Force | Out-Null
    if ([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($InstalledTool)) { Copy-Item $PSCommandPath $InstalledTool -Force; Add-Line "Installed reusable tool: $InstalledTool" Green } else { Add-Line "Running repository tool: $InstalledTool" Green }

    Add-Section 'RELAY FOUNDATION FILES'
    $ProjectPath = Join-Path $RepositoryPath 'pyproject.toml'; $Project = Get-Content $ProjectPath -Raw
    if ($Project.Contains('version = "0.3.2"')) { $Project = $Project.Replace('# Version: 0.3.2', '# Version: 0.4.0').Replace('version = "0.3.2"', 'version = "0.4.0"'); Set-Content $ProjectPath $Project -Encoding utf8NoBOM -NoNewline; Add-Line 'UPDATED   pyproject.toml' Green }
    elseif (-not $Project.Contains('version = "0.4.0"')) { throw 'RIV-BLD-0008: Unexpected project version.' }

    Write-VersionedFile 'database\migrations\0003_relay_foundation.sql' @'
-- Riverview Relay Foundation
-- Version: 0.4.0
-- Migration: 0003

BEGIN;

CREATE TABLE roadmap_items (
    waypoint_id text PRIMARY KEY,
    parent_waypoint_id text REFERENCES roadmap_items(waypoint_id),
    sort_order integer NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    status text NOT NULL CHECK (status IN ('pending','active','blocked','completed','cancelled')),
    steward_checkpoint boolean NOT NULL DEFAULT false,
    acceptance_criteria jsonb NOT NULL DEFAULT '[]'::jsonb,
    completed_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (parent_waypoint_id, sort_order)
);

CREATE TABLE roadmap_transitions (
    transition_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    waypoint_id text NOT NULL REFERENCES roadmap_items(waypoint_id),
    from_status text,
    to_status text NOT NULL,
    reason text NOT NULL,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    correlation_id uuid,
    occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE approved_actions (
    action_type text PRIMARY KEY,
    action_version text NOT NULL,
    command_path text NOT NULL,
    parameter_schema jsonb NOT NULL,
    expected_duration_seconds integer NOT NULL CHECK (expected_duration_seconds > 0),
    hard_timeout_seconds integer NOT NULL CHECK (hard_timeout_seconds >= expected_duration_seconds),
    retry_safe boolean NOT NULL DEFAULT false,
    enabled boolean NOT NULL DEFAULT false,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE work_orders (
    work_order_id uuid PRIMARY KEY,
    action_type text NOT NULL REFERENCES approved_actions(action_type),
    action_version text NOT NULL,
    status text NOT NULL CHECK (status IN ('queued','claimed','running','succeeded','failed','timed_out','blocked','cancelled')),
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    requested_by text NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    correlation_id uuid NOT NULL,
    causation_id uuid,
    expected_duration_seconds integer NOT NULL CHECK (expected_duration_seconds > 0),
    hard_timeout_seconds integer NOT NULL CHECK (hard_timeout_seconds >= expected_duration_seconds),
    lease_owner text,
    lease_expires_at timestamptz,
    last_heartbeat_at timestamptz,
    started_at timestamptz,
    finished_at timestamptz,
    result_report jsonb,
    error_checkpoint text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX work_orders_dispatch_idx ON work_orders (status, created_at);
CREATE INDEX work_orders_lease_idx ON work_orders (lease_expires_at) WHERE status IN ('claimed','running');

CREATE TABLE work_order_attempts (
    attempt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    work_order_id uuid NOT NULL REFERENCES work_orders(work_order_id),
    attempt integer NOT NULL CHECK (attempt > 0),
    worker_id text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    exit_code integer,
    report_ref text,
    UNIQUE (work_order_id, attempt)
);

CREATE TABLE steward_escalations (
    escalation_id uuid PRIMARY KEY,
    work_order_id uuid REFERENCES work_orders(work_order_id),
    checkpoint_id text NOT NULL,
    reason text NOT NULL,
    state text NOT NULL CHECK (state IN ('open','acknowledged','resolved')),
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    acknowledged_at timestamptz,
    resolved_at timestamptz
);

INSERT INTO roadmap_items (waypoint_id, parent_waypoint_id, sort_order, title, description, status, acceptance_criteria, completed_at) VALUES
('RV-001', NULL, 10, 'Foundation', 'Repository, governing constraints, and PostgreSQL authority.', 'completed', '["foundation commit verified"]', now()),
('RV-002', NULL, 20, 'River event runtime', 'Transactional append, replay, and aggregate reading.', 'completed', '["live idempotency acceptance"]', now()),
('RV-003', NULL, 30, 'Diagnostic persistence', 'Database diagnostics plus non-authoritative emergency evidence.', 'completed', '["normal and induced fallback acceptance"]', now()),
('RV-004', NULL, 40, 'Riverview Relay', 'Waypoint, work-order, runner, dashboard, and MCP communication loop.', 'active', '["full loop acceptance"]', NULL),
('RV-004.1', 'RV-004', 10, 'Relay data foundation', 'Durable waypoints, actions, work orders, leases, and escalations.', 'active', '["claim heartbeat completion timeout acceptance"]', NULL),
('RV-004.2', 'RV-004', 20, 'Local runner', 'Execute only registered actions under bounded policy.', 'pending', '["no-op and induced timeout acceptance"]', NULL),
('RV-004.3', 'RV-004', 30, 'Steward status view', 'Auto-refreshing waypoint and run visibility.', 'pending', '["latest waypoint automatically visible"]', NULL),
('RV-004.4', 'RV-004', 40, 'Read-only MCP relay', 'Retrieve waypoints, reports, diagnostics, and Cookbook entries.', 'pending', '["conversation reads latest run"]', NULL),
('RV-004.5', 'RV-004', 50, 'Full-loop mailbox', 'Enqueue approved work and return its report with escalation.', 'pending', '["doorbell to completion loop"]', NULL)
ON CONFLICT (waypoint_id) DO NOTHING;

INSERT INTO approved_actions (action_type, action_version, command_path, parameter_schema, expected_duration_seconds, hard_timeout_seconds, retry_safe, enabled)
VALUES ('relay.noop', '0.4.0', 'tools/powershell/relay/Invoke-RiverviewNoOp.ps1', '{"type":"object","additionalProperties":false}'::jsonb, 5, 30, true, true)
ON CONFLICT (action_type) DO UPDATE SET action_version=EXCLUDED.action_version, parameter_schema=EXCLUDED.parameter_schema, updated_at=now();

COMMIT;
'@

    Write-VersionedFile 'src\riverview\relay\__init__.py' @'
"""Riverview Relay durable coordination contracts.

Version: 0.4.0
"""

from .store import ClaimedWork, RelayStore, WorkOrder

__all__ = ["ClaimedWork", "RelayStore", "WorkOrder"]
'@

    Write-VersionedFile 'src\riverview\relay\store.py' @'
"""Transactional waypoint and work-order state for Riverview Relay.

Version: 0.4.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from riverview.database import DatabaseConfig, connect


@dataclass(frozen=True, slots=True)
class WorkOrder:
    action_type: str
    parameters: dict[str, Any]
    requested_by: str
    idempotency_key: str
    correlation_id: UUID
    work_order_id: UUID
    action_version: str
    expected_duration_seconds: int
    hard_timeout_seconds: int
    status: str = "queued"


@dataclass(frozen=True, slots=True)
class ClaimedWork:
    work_order_id: UUID
    action_type: str
    action_version: str
    parameters: dict[str, Any]
    hard_timeout_seconds: int
    attempt: int


class RelayStore:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def enqueue(self, action_type: str, parameters: dict[str, Any], requested_by: str, idempotency_key: str, correlation_id: UUID | None = None) -> WorkOrder:
        """Create one durable order or return the existing idempotent order."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute("SELECT action_version, expected_duration_seconds, hard_timeout_seconds, enabled FROM approved_actions WHERE action_type=%s", (action_type,))
            action = cursor.fetchone()
            if not action or not action[3]:
                raise RuntimeError(f"RIV-WRK-0001: Action is unknown or disabled: {action_type}")
            order_id = uuid4(); correlation = correlation_id or uuid4()
            cursor.execute(
                """INSERT INTO work_orders (work_order_id, action_type, action_version, status, parameters, requested_by, idempotency_key, correlation_id, expected_duration_seconds, hard_timeout_seconds)
                   VALUES (%s,%s,%s,'queued',%s::jsonb,%s,%s,%s,%s,%s)
                   ON CONFLICT (idempotency_key) DO NOTHING
                   RETURNING work_order_id""",
                (order_id, action_type, action[0], json.dumps(parameters), requested_by, idempotency_key, correlation, action[1], action[2]),
            )
            inserted = cursor.fetchone()
            if not inserted:
                cursor.execute("SELECT work_order_id FROM work_orders WHERE idempotency_key=%s", (idempotency_key,)); order_id = cursor.fetchone()[0]
            cursor.execute("SELECT action_type, parameters, requested_by, idempotency_key, correlation_id, work_order_id, action_version, expected_duration_seconds, hard_timeout_seconds, status FROM work_orders WHERE work_order_id=%s", (order_id,))
            return WorkOrder(*cursor.fetchone())

    def claim(self, worker_id: str, lease_seconds: int = 30) -> ClaimedWork | None:
        """Claim one queued order without permitting duplicate workers."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute(
                """WITH candidate AS (
                       SELECT work_order_id FROM work_orders WHERE status='queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1
                   ), claimed AS (
                       UPDATE work_orders w SET status='claimed', lease_owner=%s, lease_expires_at=now()+make_interval(secs=>%s), last_heartbeat_at=now(), started_at=COALESCE(started_at,now()), updated_at=now()
                       FROM candidate c WHERE w.work_order_id=c.work_order_id
                       RETURNING w.work_order_id,w.action_type,w.action_version,w.parameters,w.hard_timeout_seconds
                   ) SELECT * FROM claimed""",
                (worker_id, lease_seconds),
            )
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute("SELECT COALESCE(MAX(attempt),0)+1 FROM work_order_attempts WHERE work_order_id=%s", (row[0],)); attempt = cursor.fetchone()[0]
            cursor.execute("INSERT INTO work_order_attempts (work_order_id,attempt,worker_id) VALUES (%s,%s,%s)", (row[0], attempt, worker_id))
            return ClaimedWork(*row, attempt)

    def heartbeat(self, work_order_id: UUID, worker_id: str, lease_seconds: int = 30) -> None:
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE work_orders SET status='running',last_heartbeat_at=now(),lease_expires_at=now()+make_interval(secs=>%s),updated_at=now() WHERE work_order_id=%s AND lease_owner=%s AND status IN ('claimed','running')", (lease_seconds, work_order_id, worker_id))
            if cursor.rowcount != 1: raise RuntimeError("RIV-WRK-0002: Heartbeat did not own an active lease.")

    def complete(self, work_order_id: UUID, worker_id: str, result: dict[str, Any]) -> None:
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE work_orders SET status='succeeded',result_report=%s::jsonb,finished_at=now(),lease_expires_at=NULL,updated_at=now() WHERE work_order_id=%s AND lease_owner=%s AND status IN ('claimed','running')", (json.dumps(result), work_order_id, worker_id))
            if cursor.rowcount != 1: raise RuntimeError("RIV-WRK-0003: Completion did not own an active lease.")
            cursor.execute("UPDATE work_order_attempts SET finished_at=now(),exit_code=0 WHERE work_order_id=%s AND worker_id=%s AND finished_at IS NULL", (work_order_id, worker_id))

    def sweep_expired(self) -> list[UUID]:
        """Mark expired leases and open one Steward escalation per order."""
        with connect(self._config) as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE work_orders SET status='timed_out',error_checkpoint='RIV-WRK-0004',finished_at=now(),updated_at=now() WHERE status IN ('claimed','running') AND lease_expires_at < now() RETURNING work_order_id")
            expired = [row[0] for row in cursor.fetchall()]
            for order_id in expired:
                cursor.execute("INSERT INTO steward_escalations (escalation_id,work_order_id,checkpoint_id,reason,state) VALUES (%s,%s,'RIV-WRK-0004','Worker lease expired without completion.','open')", (uuid4(), order_id))
            return expired
'@

    Write-VersionedFile 'src\riverview\relay_health.py' @'
"""Live lifecycle acceptance for Riverview Relay.

Version: 0.4.0
"""

from __future__ import annotations

import json
from uuid import uuid4

from riverview.database import connect
from riverview.relay import RelayStore


def acceptance() -> dict[str, object]:
    store = RelayStore()
    key = f"relay-acceptance:{uuid4()}"
    first = store.enqueue("relay.noop", {}, "acceptance", key)
    duplicate = store.enqueue("relay.noop", {}, "acceptance", key)
    claimed = store.claim("acceptance-worker", 30)
    if not claimed or claimed.work_order_id != first.work_order_id or duplicate.work_order_id != first.work_order_id:
        raise RuntimeError("RIV-WRK-0005: Claim or idempotency invariant failed.")
    store.heartbeat(claimed.work_order_id, "acceptance-worker", 30)
    store.complete(claimed.work_order_id, "acceptance-worker", {"status": "accepted"})

    timeout = store.enqueue("relay.noop", {}, "acceptance", f"relay-timeout:{uuid4()}")
    timed_claim = store.claim("timeout-worker", 30)
    if not timed_claim or timed_claim.work_order_id != timeout.work_order_id:
        raise RuntimeError("RIV-WRK-0005: Timeout probe claim failed.")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE work_orders SET lease_expires_at=now()-interval '1 second' WHERE work_order_id=%s", (timeout.work_order_id,))
    expired = store.sweep_expired()
    if timeout.work_order_id not in expired:
        raise RuntimeError("RIV-WRK-0004: Expired lease was not escalated.")
    return {"status":"healthy","idempotent_enqueue":True,"claim_heartbeat_complete":True,"timeout_escalated":True}


if __name__ == "__main__":
    print(json.dumps(acceptance(), indent=2, sort_keys=True))
'@

    Write-VersionedFile 'tests\test_relay_contract.py' @'
"""Contract tests for Riverview Relay records.

Version: 0.4.0
"""

from uuid import uuid4

from riverview.relay import WorkOrder


def test_work_order_contract_keeps_structured_parameters() -> None:
    order = WorkOrder("relay.noop", {"step": 147}, "test", "key", uuid4(), uuid4(), "0.4.0", 5, 30)
    assert order.parameters == {"step": 147}
    assert order.status == "queued"
'@

    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-WRK-0001_ACTION_POLICY.md' @'
<!-- Version: 0.4.0 -->
# RIV-WRK-0001 — Action unknown or disabled

Trigger: A producer requests an action absent from the enabled approved-action registry.

Smallest repair: Verify the intended `action_type`; register and test a versioned action through an approved migration. Never substitute arbitrary shell text.

Verify: Enqueue the registered action and require one queued work order with its declared version and limits.
'@
    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-WRK-0002_LEASE_OWNERSHIP.md' @'
<!-- Version: 0.4.0 -->
# RIV-WRK-0002 — Worker heartbeat lacks lease ownership

Trigger: A worker heartbeats an order it does not currently own or whose lifecycle is terminal.

Smallest repair: Stop the stale worker, inspect the current owner and attempt, and reclaim only when the action is explicitly retry-safe.

Verify: One worker claims the order; a different worker must be unable to heartbeat it.
'@
    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-WRK-0004_LEASE_TIMEOUT.md' @'
<!-- Version: 0.4.0 -->
# RIV-WRK-0004 — Worker lease expired

Trigger: A claimed or running work order stops heartbeating before completion.

Smallest repair: Preserve the attempt evidence, page the Steward, and determine whether the registered action is retry-safe before requeueing.

Verify: The order is `timed_out` and exactly one open Steward escalation identifies the work order and checkpoint.
'@

    Add-Section 'MIGRATION AND ACCEPTANCE'
    Push-Location $RepositoryPath
    try {
        & $Python -m pip install -e '.[dev]'; if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
        $Migration = @'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed = apply_migration(Path('database/migrations/0003_relay_foundation.sql'), '0003', '0.4.0')
print('Migration 0003 applied.' if changed else 'Migration 0003 already current.')
'@
        $Migration | & $Python -; if ($LASTEXITCODE -ne 0) { throw 'RIV-DB-0006: Migration 0003 failed.' }
        Invoke-Checked 'Ruff check' { & $Python -m ruff check src tests }; Invoke-Checked 'Pytest' { & $Python -m pytest }
        Invoke-Checked 'Python compilation' { & $Python -m compileall -q src }; Invoke-Checked 'Database health' { & $Python -m riverview.health database }
        Invoke-Checked 'Relay lifecycle acceptance' { & $Python -m riverview.relay_health }
        Add-Section 'GIT CHANGE SUMMARY'; foreach ($Line in @(git status --short)) { Add-Line $Line }
    } finally { Pop-Location }

    Add-Section 'RELAY FOUNDATION RESULT'; Add-Line 'Waypoint and work-order state, leases, heartbeats, completion, and timeout escalation passed.' Green
    Add-Line 'No command runner, MCP endpoint, commit, or push was created.' Yellow; Add-Line "Installer version: $ToolVersion"; Save-Report
}
catch { Add-Section 'RELAY FOUNDATION BLOCKED'; Add-Line $_.Exception.Message Red; Add-Line 'No commit or push was performed.' Yellow; if (Test-Path $RepositoryPath -PathType Container) { Save-Report }; throw }
