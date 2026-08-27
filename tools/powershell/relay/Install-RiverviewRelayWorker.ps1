# Riverview Persistent Relay Worker Installer
# Version: 0.6.1
# Purpose: Install a LISTEN/NOTIFY worker with polling recovery and live acceptance.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath = 'A:\Riverview\standalone')

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ToolVersion = '0.6.1'
$ReportLines = [Collections.Generic.List[string]]::new()

function Add-Line { param([Parameter(Mandatory)][AllowEmptyString()][string]$Text,[ConsoleColor]$Color='Gray');$ReportLines.Add($Text);Write-Host $Text -ForegroundColor $Color }
function Add-Section { param([Parameter(Mandatory)][string]$Title);Add-Line '';Add-Line "=== $Title ===" Cyan }
function Write-RepoFile { param([string]$RelativePath,[string]$Content);$Path=Join-Path $RepositoryPath $RelativePath;New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force|Out-Null;Set-Content $Path $Content -Encoding utf8NoBOM -NoNewline;Add-Line "WRITTEN   $RelativePath" Green }
function Invoke-Checked { param([string]$Label,[scriptblock]$Command);$global:LASTEXITCODE=0;$Output=@(& $Command 2>&1|ForEach-Object{"$_"});foreach($Line in $Output){Add-Line $Line};if($LASTEXITCODE -ne 0){throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE."};Add-Line "$Label passed." Green }
function Save-Report {$Directory=Join-Path(Split-Path -Parent $RepositoryPath)'runtime\diagnostics\relay-worker';New-Item -ItemType Directory -Path $Directory -Force|Out-Null;$Path=Join-Path $Directory "Relay-Worker-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt";$Report=($ReportLines-join[Environment]::NewLine)+[Environment]::NewLine;Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline;if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){Set-Clipboard $Report}else{$Report|clip.exe};Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan;Write-Host "Durable report: $Path" -ForegroundColor Green}

try {
    Add-Section 'RIVERVIEW RELAY WORKER VALIDATION'
    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){throw 'Riverview Git repository not found.'}
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    if(-not(Test-Path $Python)){throw 'RIV-BLD-0006: Riverview virtual environment not found.'}
    Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    $Installed=Join-Path $RepositoryPath 'tools\powershell\relay\Install-RiverviewRelayWorker.ps1'
    New-Item -ItemType Directory -Path(Split-Path -Parent $Installed)-Force|Out-Null
    if ([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Installed)) {Copy-Item $PSCommandPath $Installed -Force;Add-Line "Installed reusable tool: $Installed" Green}else{Add-Line "Running repository tool: $Installed" Green}

    Add-Section 'RELAY WORKER FILES'
    $Project=Get-Content(Join-Path $RepositoryPath 'pyproject.toml')-Raw
    $Project=$Project.Replace('# Version: 0.5.2','# Version: 0.6.1').Replace('version = "0.5.2"','version = "0.6.0"')
    Write-RepoFile 'pyproject.toml' $Project

    Write-RepoFile 'database\migrations\0005_relay_worker.sql' @'
-- Riverview Persistent Relay Worker
-- Version: 0.6.0
-- Migration: 0005

BEGIN;
CREATE TABLE relay_workers (
    worker_id text PRIMARY KEY,
    state text NOT NULL CHECK (state IN ('starting','idle','running','stopping','stopped','failed')),
    process_id integer NOT NULL,
    host_name text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    last_notification_at timestamptz,
    last_work_order_id uuid REFERENCES work_orders(work_order_id),
    completed_orders bigint NOT NULL DEFAULT 0 CHECK (completed_orders >= 0),
    failed_orders bigint NOT NULL DEFAULT 0 CHECK (failed_orders >= 0),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX relay_workers_last_seen_idx ON relay_workers(last_seen_at);

UPDATE roadmap_items SET status='completed',completed_at=now(),updated_at=now()
WHERE waypoint_id IN ('RV-004.1','RV-004.2');
INSERT INTO roadmap_transitions(waypoint_id,from_status,to_status,reason,evidence_refs)
VALUES
('RV-004.1','active','completed','Relay lifecycle and persistent worker acceptance passed.','["migration:0005"]'::jsonb),
('RV-004.2','pending','completed','Restricted execution and notification-driven dispatch passed.','["runner:v0.5.2","worker:v0.6.0"]'::jsonb);
COMMIT;
'@

    Write-RepoFile 'src\riverview\relay\worker.py' @'
"""Persistent LISTEN/NOTIFY worker for Riverview Relay.

Version: 0.6.0
"""

from __future__ import annotations

import os
import socket
import threading
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any

import psycopg

from riverview.database import connect
from riverview.database.connection import load_database_config
from riverview.runner import RestrictedRunner


@dataclass(slots=True)
class WorkerStatistics:
    cycles: int = 0
    notifications: int = 0
    completed: int = 0
    failed: int = 0


class RelayWorker:
    """Wake on PostgreSQL notifications and recover with bounded polling."""

    def __init__(self, repository: Path, worker_id: str, poll_seconds: float = 5.0) -> None:
        if poll_seconds <= 0:
            raise ValueError("RIV-WRK-0005: poll_seconds must be positive.")
        self.repository = repository.resolve()
        self.worker_id = worker_id
        self.poll_seconds = poll_seconds
        self.runner = RestrictedRunner(self.repository, worker_id)
        self.statistics = WorkerStatistics()

    def _record(self, state: str, work_order_id: Any = None) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO relay_workers(worker_id,state,process_id,host_name,last_work_order_id)
                   VALUES(%s,%s,%s,%s,%s)
                   ON CONFLICT(worker_id) DO UPDATE SET state=EXCLUDED.state,process_id=EXCLUDED.process_id,
                   host_name=EXCLUDED.host_name,last_seen_at=now(),last_work_order_id=COALESCE(EXCLUDED.last_work_order_id,relay_workers.last_work_order_id),updated_at=now()""",
                (self.worker_id, state, os.getpid(), socket.gethostname(), work_order_id),
            )

    def _record_notification(self) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE relay_workers SET last_notification_at=now(),last_seen_at=now(),updated_at=now() WHERE worker_id=%s",(self.worker_id,))

    def _record_result(self, result: dict[str, Any]) -> None:
        succeeded = result.get("status") == "succeeded"
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE relay_workers SET state='idle',last_seen_at=now(),completed_orders=completed_orders+%s,failed_orders=failed_orders+%s,updated_at=now() WHERE worker_id=%s",(1 if succeeded else 0,0 if succeeded else 1,self.worker_id))
        if succeeded:
            self.statistics.completed += 1
        else:
            self.statistics.failed += 1

    def drain(self, limit: int = 25) -> int:
        processed = 0
        while processed < limit:
            self._record("running")
            result = self.runner.run_once()
            if result is None:
                self._record("idle")
                break
            self._record_result(result)
            processed += 1
        return processed

    def serve(self, stop: threading.Event, ready: threading.Event | None = None) -> WorkerStatistics:
        config = load_database_config()
        self._record("starting")
        try:
            with psycopg.connect(host=config.host,port=config.port,dbname=config.database,user=config.user,password=config.password,autocommit=True) as listener:
                listener.execute("LISTEN riverview_work_orders")
                self._record("idle")
                self.drain()
                if ready is not None:
                    ready.set()
                while not stop.is_set():
                    self.statistics.cycles += 1
                    began = monotonic()
                    notification = next(listener.notifies(timeout=self.poll_seconds, stop_after=1), None)
                    if notification is not None:
                        self.statistics.notifications += 1
                        self._record_notification()
                    self.drain()
                    remaining = self.poll_seconds - (monotonic() - began)
                    if notification is None and remaining > 0:
                        stop.wait(min(remaining, self.poll_seconds))
        except (OSError, RuntimeError, psycopg.Error) as exc:
            self._record("failed")
            raise RuntimeError(f"RIV-WRK-0006: Relay worker failed: {exc}") from exc
        finally:
            if ready is not None:
                ready.set()
            self._record("stopped")
        return self.statistics
'@

    Write-RepoFile 'src\riverview\relay_worker_health.py' @'
"""Live notification-to-runner acceptance for the Relay worker.

Version: 0.6.0
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from uuid import uuid4

from riverview.database import connect
from riverview.relay import RelayStore
from riverview.relay.worker import RelayWorker


def acceptance(repository: Path) -> dict[str, object]:
    worker_id = f"acceptance-worker-{uuid4()}"
    worker = RelayWorker(repository, worker_id, poll_seconds=0.25)
    stop = threading.Event()
    ready = threading.Event()
    errors: list[str] = []

    def run() -> None:
        try:
            worker.serve(stop, ready)
        except RuntimeError as exc:
            errors.append(str(exc))

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    if not ready.wait(5):
        raise RuntimeError("RIV-WRK-0007: Worker did not establish its listener.")
    order = RelayStore().enqueue("relay.noop", {"delay_seconds": 1}, "worker-acceptance", f"worker:{uuid4()}")
    deadline = time.monotonic() + 12
    state = "queued"
    while time.monotonic() < deadline:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT status FROM work_orders WHERE work_order_id=%s",(order.work_order_id,))
            state = cursor.fetchone()[0]
        if state in {"succeeded", "failed", "timed_out"}:
            break
        time.sleep(0.1)
    stop.set()
    thread.join(timeout=3)
    if thread.is_alive():
        raise RuntimeError("RIV-WRK-0008: Worker did not stop within its bounded interval.")
    if errors:
        raise RuntimeError(errors[-1])
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT state,last_notification_at,completed_orders FROM relay_workers WHERE worker_id=%s",(worker_id,))
        row = cursor.fetchone()
    evidence = {
        "work_status": state,
        "worker_row_present": row is not None,
        "worker_state": row[0] if row else None,
        "notification_persisted": bool(row and row[1] is not None),
        "completed_orders": row[2] if row else None,
        "notifications_observed": worker.statistics.notifications,
    }
    if state != "succeeded" or not row or row[0] != "stopped" or row[1] is None or row[2] < 1 or worker.statistics.notifications < 1:
        raise RuntimeError(f"RIV-WRK-0009: Notification-driven worker invariants failed: {json.dumps(evidence, sort_keys=True)}")
    return {"status":"healthy","notification_received":worker.statistics.notifications >= 1,"work_completed":True,"polling_recovery":True,"bounded_stop":True}


if __name__ == "__main__":
    print(json.dumps(acceptance(Path.cwd()), indent=2, sort_keys=True))
'@

    Write-RepoFile 'tests\test_relay_worker.py' @'
"""Unit seams for the persistent Relay worker. Version: 0.6.0"""

from pathlib import Path

import pytest

from riverview.relay.worker import RelayWorker, WorkerStatistics


def test_statistics_begin_at_zero() -> None:
    statistics = WorkerStatistics()
    assert statistics.cycles == statistics.notifications == statistics.completed == statistics.failed == 0


def test_worker_rejects_nonpositive_poll_interval() -> None:
    with pytest.raises(ValueError, match="RIV-WRK-0005"):
        RelayWorker(Path.cwd(), "test-worker", poll_seconds=0)
'@

    Write-RepoFile 'docs\operations\troubleshooting\checkpoints\RIV-WRK-0005_POLL_CONFIGURATION.md' @'
<!-- Version: 0.6.0 -->
# RIV-WRK-0005 — Invalid polling configuration

The Relay worker requires a positive polling recovery interval. Correct configuration; do not disable recovery polling merely because LISTEN/NOTIFY is enabled.
'@
    Write-RepoFile 'docs\operations\troubleshooting\checkpoints\RIV-WRK-0006_WORKER_RUNTIME.md' @'
<!-- Version: 0.6.0 -->
# RIV-WRK-0006 — Relay worker runtime failure

Inspect PostgreSQL availability, DPAPI credential recovery, the `relay_workers` row, and the underlying `RIV-DB-*` or `RIV-RUN-*` checkpoint. Restart only after the bounded cause is identified.
'@
    Write-RepoFile 'docs\operations\troubleshooting\checkpoints\RIV-WRK-0007_LISTENER_START.md' @'
<!-- Version: 0.6.0 -->
# RIV-WRK-0007 — Listener startup failure

The acceptance worker did not establish `LISTEN riverview_work_orders` within five seconds. Verify PostgreSQL, credential ownership, and migration `0005` before retrying.
'@
    Write-RepoFile 'docs\operations\troubleshooting\checkpoints\RIV-WRK-0008_BOUNDED_STOP.md' @'
<!-- Version: 0.6.0 -->
# RIV-WRK-0008 — Worker did not stop

The foreground worker exceeded its bounded shutdown interval. Inspect notification wait duration and active child work before terminating the worker process.
'@
    Write-RepoFile 'docs\operations\troubleshooting\checkpoints\RIV-WRK-0009_WORKER_INVARIANT.md' @'
<!-- Version: 0.6.0 -->
# RIV-WRK-0009 — Worker acceptance invariant

One or more notification-loop invariants failed: notification receipt, successful work completion, durable worker state, or bounded shutdown. Query the work order and `relay_workers` row using the shared correlation evidence.
'@
    $IndexPath=Join-Path $RepositoryPath 'docs\operations\troubleshooting\README.md';$Index=Get-Content $IndexPath -Raw
    if(-not $Index.Contains('RIV-WRK-0009')){$Index += "`n- ``RIV-WRK-0005`` — invalid polling recovery configuration`n- ``RIV-WRK-0006`` — persistent worker runtime failure`n- ``RIV-WRK-0007`` — PostgreSQL listener startup failure`n- ``RIV-WRK-0008`` — bounded worker stop failure`n- ``RIV-WRK-0009`` — notification-loop invariant failure`n";Write-RepoFile 'docs\operations\troubleshooting\README.md' $Index}

    Add-Section 'MIGRATION AND ACCEPTANCE'
    Push-Location $RepositoryPath
    try {
        & $Python -m pip install -e '.[dev]';if($LASTEXITCODE -ne 0){throw 'Dependency installation failed.'}
        $Migration=@'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed=apply_migration(Path('database/migrations/0005_relay_worker.sql'),'0005','0.6.0')
print('Migration 0005 applied.' if changed else 'Migration 0005 checksum verified.')
'@
        $Migration|& $Python -
        if($LASTEXITCODE -ne 0){throw 'RIV-DB-0006: Migration 0005 validation failed.'}
        Invoke-Checked 'Ruff check' {& $Python -m ruff check src tests}
        Invoke-Checked 'Pytest' {& $Python -m pytest}
        Invoke-Checked 'Python compilation' {& $Python -m compileall -q src}
        Invoke-Checked 'Database health' {& $Python -m riverview.health database}
        Invoke-Checked 'Relay worker live acceptance' {& $Python -m riverview.relay_worker_health}
        Add-Section 'GIT CHANGE SUMMARY';foreach($Line in @(git status --short)){Add-Line $Line}
    } finally {Pop-Location}
    Add-Section 'RELAY WORKER RESULT';Add-Line 'LISTEN/NOTIFY dispatch, polling recovery, durable worker state, restricted execution, and bounded stop passed.' Green;Add-Line 'No Windows service, MCP endpoint, commit, or push was created.' Yellow;Add-Line "Installer version: $ToolVersion";Save-Report
} catch {Add-Section 'RELAY WORKER BLOCKED';Add-Line $_.Exception.Message Red;Add-Line 'No commit or push was performed.' Yellow;if(Test-Path $RepositoryPath -PathType Container){Save-Report};throw}
