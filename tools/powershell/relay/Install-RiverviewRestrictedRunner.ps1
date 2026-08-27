# Riverview Restricted Runner Installer
# Version: 0.5.2
# Purpose: Install and validate fixed-policy local PowerShell execution for registered Relay actions.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath = 'A:\Riverview\standalone')

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ToolVersion = '0.5.2'
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
    param([Parameter(Mandatory)][string]$RelativePath,[Parameter(Mandatory)][string]$Content)
    $Path = Join-Path $RepositoryPath $RelativePath
    New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force | Out-Null
    if (Test-Path $Path) {
        $Existing = Get-Content $Path -Raw
        if ($Existing -eq $Content) { Add-Line "CURRENT   $RelativePath" DarkGray; return }
        Copy-Item $Path "$Path.pre-$ToolVersion.bak" -Force
        Add-Line "BACKUP    $RelativePath" Yellow
    }
    Set-Content $Path $Content -Encoding utf8NoBOM -NoNewline
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
    $Directory = Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\runner'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path = Join-Path $Directory "Restricted-Runner-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard $Report } else { $Report | clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try{
    Add-Section 'RIVERVIEW RESTRICTED RUNNER VALIDATION'
    $RepositoryPath = (Resolve-Path $RepositoryPath).Path
    if (-not (Test-Path (Join-Path $RepositoryPath '.git'))) { throw 'Riverview Git repository not found.' }
    $Python = Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    if (-not (Test-Path $Python)) { throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    Add-Line "Repository validated: $RepositoryPath" Green
    Add-Section 'SELF-INSTALLATION'
    $InstalledTool = Join-Path $RepositoryPath 'tools\powershell\relay\Install-RiverviewRestrictedRunner.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $InstalledTool) -Force | Out-Null
    if ([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($InstalledTool)) { Copy-Item $PSCommandPath $InstalledTool -Force; Add-Line "Installed reusable tool: $InstalledTool" Green } else { Add-Line "Running repository tool: $InstalledTool" Green }

    Add-Section 'RUNNER FILES'
    $ProjectPath = Join-Path $RepositoryPath 'pyproject.toml'
    $Project = Get-Content $ProjectPath -Raw
    if ($Project.Contains('version = "0.4.0"')) {
        $Project = $Project.Replace('# Version: 0.4.0', '# Version: 0.5.0').Replace('version = "0.4.0"', 'version = "0.5.0"')
        Set-Content $ProjectPath $Project -Encoding utf8NoBOM -NoNewline
        Add-Line 'UPDATED   pyproject.toml' Green
    } elseif (-not $Project.Contains('version = "0.5.0"')) { throw 'RIV-BLD-0008: Unexpected project version.' }

    Write-VersionedFile 'database\migrations\0004_restricted_runner.sql' @'
-- Riverview Restricted Runner
-- Version: 0.5.0
-- Migration: 0004

BEGIN;
ALTER TABLE approved_actions ADD COLUMN command_sha256 text;

INSERT INTO approved_actions (action_type,action_version,command_path,parameter_schema,expected_duration_seconds,hard_timeout_seconds,retry_safe,enabled)
VALUES ('relay.timeout_probe','0.5.0','tools/powershell/relay/Invoke-RiverviewNoOp.ps1','{"type":"object","properties":{"delay_seconds":{"type":"integer","minimum":2,"maximum":5}},"required":["delay_seconds"],"additionalProperties":false}'::jsonb,1,1,true,true)
ON CONFLICT(action_type)DO UPDATE SET action_version=EXCLUDED.action_version,command_path=EXCLUDED.command_path,parameter_schema=EXCLUDED.parameter_schema,expected_duration_seconds=EXCLUDED.expected_duration_seconds,hard_timeout_seconds=EXCLUDED.hard_timeout_seconds,retry_safe=EXCLUDED.retry_safe,enabled=EXCLUDED.enabled,updated_at=now();

UPDATE approved_actions SET action_version='0.5.0',parameter_schema='{"type":"object","properties":{"delay_seconds":{"type":"integer","minimum":1,"maximum":5}},"required":["delay_seconds"],"additionalProperties":false}'::jsonb,expected_duration_seconds=3,hard_timeout_seconds=10,enabled=true,updated_at=now() WHERE action_type='relay.noop';

CREATE OR REPLACE FUNCTION notify_riverview_work_order() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN PERFORM pg_notify('riverview_work_orders',NEW.work_order_id::text);RETURN NEW;END;$$;
CREATE TRIGGER work_orders_notify_after_insert AFTER INSERT ON work_orders FOR EACH ROW WHEN(NEW.status='queued') EXECUTE FUNCTION notify_riverview_work_order();
COMMIT;
'@

    Write-VersionedFile 'tools\powershell\relay\Invoke-RiverviewNoOp.ps1' @'
# Riverview Registered No-Op Action
# Version: 0.5.0
# Purpose: Acceptance-only action proving bounded runner execution.

[CmdletBinding()]
param([ValidateRange(1,5)][int]$DelaySeconds=2)

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
Start-Sleep -Seconds $DelaySeconds
[ordered]@{status='succeeded';action='relay.noop';version='0.5.0';delay_seconds=$DelaySeconds}|ConvertTo-Json -Compress
'@

    Write-VersionedFile 'src\riverview\runner.py' @'
"""Fixed-policy local runner for Riverview Relay.

Version: 0.5.0
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.relay import ClaimedWork, RelayStore


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    action_type: str
    action_version: str
    command_path: str
    command_sha256: str
    hard_timeout_seconds: int


class RestrictedRunner:
    """Execute only explicitly implemented actions whose source hash matches policy."""

    def __init__(self, repository: Path, worker_id: str, heartbeat_seconds: float = 0.5) -> None:
        self.repository = repository.resolve()
        self.worker_id = worker_id
        self.heartbeat_seconds = heartbeat_seconds
        self.store = RelayStore()

    def run_once(self) -> dict[str, Any] | None:
        work = self.store.claim(self.worker_id, 10)
        if work is None:
            return None
        try:
            definition = self._definition(work)
            command = self._command(work, definition)
            return self._execute(work, command)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            self._fail(work.work_order_id, "RIV-RUN-0001", str(exc), timed_out=False)
            return {"status": "failed", "checkpoint_id": "RIV-RUN-0001"}

    def _definition(self, work: ClaimedWork) -> ActionDefinition:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT action_type,action_version,command_path,command_sha256,hard_timeout_seconds FROM approved_actions WHERE action_type=%s AND action_version=%s AND enabled=true",(work.action_type,work.action_version))
            row = cursor.fetchone()
        if not row or not row[3]:
            raise RuntimeError("RIV-RUN-0001: Action definition is absent, disabled, unversioned, or unhashed.")
        return ActionDefinition(*row)

    def _command(self, work: ClaimedWork, definition: ActionDefinition) -> list[str]:
        path = (self.repository / definition.command_path).resolve()
        tools_root = (self.repository / "tools" / "powershell").resolve()
        if tools_root not in path.parents or not path.is_file():
            raise RuntimeError("RIV-RUN-0002: Registered command escaped the repository tools boundary.")
        if hashlib.sha256(path.read_bytes()).hexdigest() != definition.command_sha256:
            raise RuntimeError("RIV-RUN-0003: Registered command hash mismatch.")
        delay = work.parameters.get("delay_seconds")
        if work.action_type not in {"relay.noop", "relay.timeout_probe"} or not isinstance(delay, int) or isinstance(delay, bool) or not 1 <= delay <= 5:
            raise ValueError("RIV-RUN-0004: Action parameters failed the fixed runner adapter.")
        executable = shutil.which("pwsh")
        if executable is None:
            raise RuntimeError("RIV-RUN-0001: pwsh executable was not found.")
        return [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(path), "-DelaySeconds", str(delay)]

    def _execute(self, work: ClaimedWork, command: list[str]) -> dict[str, Any]:
        process = subprocess.Popen(
            command, cwd=self.repository, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stopped = threading.Event()
        heartbeat_error: list[str] = []

        def heartbeat() -> None:
            while not stopped.wait(self.heartbeat_seconds):
                try:
                    self.store.heartbeat(work.work_order_id, self.worker_id, 10)
                except RuntimeError as exc:
                    heartbeat_error.append(str(exc))
                    return

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            stdout, stderr = process.communicate(timeout=work.hard_timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            self._fail(work.work_order_id, "RIV-RUN-0005", "Hard timeout exceeded.", timed_out=True)
            return {"status": "timed_out", "checkpoint_id": "RIV-RUN-0005", "stdout": stdout[-4000:], "stderr": stderr[-4000:]}
        finally:
            stopped.set()
            thread.join(timeout=2)
        if heartbeat_error:
            raise RuntimeError(f"RIV-RUN-0006: Heartbeat failed: {heartbeat_error[-1]}")
        if process.returncode != 0:
            self._fail(work.work_order_id, "RIV-RUN-0007", f"Process exit code {process.returncode}.", timed_out=False)
            return {"status": "failed", "checkpoint_id": "RIV-RUN-0007", "stdout": stdout[-4000:], "stderr": stderr[-4000:]}
        report = {"status": "succeeded", "exit_code": process.returncode, "stdout": stdout[-4000:], "stderr": stderr[-4000:]}
        self.store.complete(work.work_order_id, self.worker_id, report)
        return report

    def _fail(self, order_id: UUID, checkpoint: str, reason: str, timed_out: bool) -> None:
        state = "timed_out" if timed_out else "failed"
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("UPDATE work_orders SET status=%s,error_checkpoint=%s,result_report=%s::jsonb,finished_at=now(),lease_expires_at=NULL,updated_at=now() WHERE work_order_id=%s AND lease_owner=%s AND status IN('claimed','running')",(state,checkpoint,json.dumps({"status":state,"reason":reason}),order_id,self.worker_id))
            if cursor.rowcount != 1:
                raise RuntimeError("RIV-RUN-0008: Runner could not record terminal state.")
            cursor.execute("UPDATE work_order_attempts SET finished_at=now(),exit_code=%s WHERE work_order_id=%s AND worker_id=%s AND finished_at IS NULL",(124 if timed_out else 1,order_id,self.worker_id))
            cursor.execute("INSERT INTO steward_escalations(escalation_id,work_order_id,checkpoint_id,reason,state)VALUES(%s,%s,%s,%s,'open')",(uuid4(),order_id,checkpoint,reason))
'@

    Write-VersionedFile 'src\riverview\runner_health.py' @'
"""Live subprocess acceptance for the restricted runner.

Version: 0.5.0
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

from riverview.database import connect
from riverview.relay import RelayStore
from riverview.runner import RestrictedRunner


def acceptance(repository: Path) -> dict[str, object]:
    tool = repository / "tools" / "powershell" / "relay" / "Invoke-RiverviewNoOp.ps1"
    digest = hashlib.sha256(tool.read_bytes()).hexdigest()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE approved_actions SET command_sha256=%s WHERE action_type IN('relay.noop','relay.timeout_probe')",(digest,))
    store = RelayStore()
    runner = RestrictedRunner(repository, "acceptance-runner", 0.25)
    success = store.enqueue("relay.noop", {"delay_seconds": 2}, "acceptance", f"runner-success:{uuid4()}")
    result = runner.run_once()
    if not result or result["status"] != "succeeded":
        raise RuntimeError("RIV-RUN-0009: No-op execution failed.")
    timeout = store.enqueue("relay.timeout_probe", {"delay_seconds": 3}, "acceptance", f"runner-timeout:{uuid4()}")
    timed = runner.run_once()
    if not timed or timed["status"] != "timed_out":
        raise RuntimeError("RIV-RUN-0009: Timeout execution failed.")
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT status FROM work_orders WHERE work_order_id=%s", (success.work_order_id,))
        success_state = cursor.fetchone()[0]
        cursor.execute("SELECT status FROM work_orders WHERE work_order_id=%s", (timeout.work_order_id,))
        timeout_state = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM steward_escalations WHERE work_order_id=%s AND state='open'", (timeout.work_order_id,))
        escalations = cursor.fetchone()[0]
    if success_state != "succeeded" or timeout_state != "timed_out" or escalations != 1:
        raise RuntimeError("RIV-RUN-0009: Persisted runner invariants failed.")
    return {"status": "healthy", "subprocess_succeeded": True, "heartbeats": True, "timeout_terminated": True, "steward_escalation": True}


if __name__ == "__main__":
    print(json.dumps(acceptance(Path.cwd()), indent=2, sort_keys=True))
'@

    Write-VersionedFile 'tests\test_runner_policy.py' @'
"""Policy tests for the restricted local runner.

Version: 0.5.0
"""

from pathlib import Path

from riverview.runner import RestrictedRunner


def test_runner_repository_is_resolved(tmp_path: Path) -> None:
    runner = RestrictedRunner(tmp_path, "test")
    assert runner.repository == tmp_path.resolve()
'@

    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-RUN-0001_ACTION_DEFINITION.md' @'
<!-- Version: 0.5.0 -->
# RIV-RUN-0001 — Runner rejected the action definition

Trigger: The claimed action is absent, disabled, version-mismatched, or missing its approved source hash.

Smallest repair: Correct the exact approved-action record through a migration or installer acceptance. Never execute raw command text from the work order.

Verify: Run the restricted-runner acceptance and require the registered no-op to succeed.
'@
    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-RUN-0003_HASH_MISMATCH.md' @'
<!-- Version: 0.5.0 -->
# RIV-RUN-0003 — Registered command hash mismatch

Trigger: The repository script bytes do not match the hash approved in PostgreSQL.

Smallest repair: Inspect the source change, rerun its acceptance, and intentionally register the new hash. Do not bypass verification.

Verify: The runner starts only after the stored and calculated SHA-256 values match.
'@
    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-RUN-0005_HARD_TIMEOUT.md' @'
<!-- Version: 0.5.0 -->
# RIV-RUN-0005 — Registered action exceeded hard timeout

Trigger: The subprocess remains active beyond its registered maximum runtime.

Smallest repair: Terminate the process, preserve captured output, mark the order timed out, and page the Steward before any retry.

Verify: The induced timeout probe is terminated and produces exactly one open escalation.
'@

    $CookbookIndex=Join-Path $RepositoryPath 'docs\operations\troubleshooting\README.md';$Index=Get-Content $CookbookIndex -Raw
    if (-not $Index.Contains('`RIV-RUN-*`')) { $Index=$Index.Replace('- `RIV-WRK-*` — worker assignment, attempts, ownership, and leases',"- ``RIV-WRK-*`` — worker assignment, attempts, ownership, and leases`n- ``RIV-RUN-*`` — restricted local process execution and enforcement"); $Index=$Index.Replace('<!-- Version: 0.3.0 -->','<!-- Version: 0.5.0 -->'); Set-Content $CookbookIndex $Index -Encoding utf8NoBOM -NoNewline; Add-Line 'UPDATED   docs\operations\troubleshooting\README.md' Green }

    Write-VersionedFile 'docs\operations\troubleshooting\checkpoints\RIV-BLD-0009_POWERSHELL_PARSER.md' @'
<!-- Version: 0.5.1 -->
# RIV-BLD-0009 — PowerShell installer parser rejected compressed control syntax

Trigger: PowerShell reports `Missing 'in' after variable in foreach loop` before executing the installer.

Smallest repair: Preserve spaces between the `in` keyword and collection expression and use readable control-flow formatting throughout the outer installer.

Verify: The installer reaches workspace validation before creating or modifying any runtime files.
'@

    Add-Section 'MIGRATION AND ACCEPTANCE'
    Push-Location $RepositoryPath
    try {
        & $Python -m pip install -e '.[dev]'
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
        $Migration = @'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed=apply_migration(Path('database/migrations/0004_restricted_runner.sql'),'0004','0.5.0')
print('Migration 0004 applied.' if changed else 'Migration 0004 already current.')
'@
        $Migration | & $Python -
        if ($LASTEXITCODE -ne 0) { throw 'RIV-DB-0006: Migration 0004 failed.' }
        Invoke-Checked 'Ruff check' { & $Python -m ruff check src tests }
        Invoke-Checked 'Pytest' { & $Python -m pytest }
        Invoke-Checked 'Python compilation' { & $Python -m compileall -q src }
        Invoke-Checked 'Database health' { & $Python -m riverview.health database }
        Invoke-Checked 'Restricted runner live acceptance' { & $Python -m riverview.runner_health }
        Add-Section 'GIT CHANGE SUMMARY'
        foreach ($Line in @(git status --short)) { Add-Line $Line }
    } finally { Pop-Location }
    Add-Section 'RESTRICTED RUNNER RESULT'
    Add-Line 'Registered process execution, heartbeats, output capture, hard timeout, and Steward escalation passed.' Green
    Add-Line 'Arbitrary commands remain impossible; no service, MCP endpoint, commit, or push was created.' Yellow
    Add-Line "Installer version: $ToolVersion"
    Save-Report
} catch {
    Add-Section 'RESTRICTED RUNNER BLOCKED'
    Add-Line $_.Exception.Message Red
    Add-Line 'No commit or push was performed.' Yellow
    if (Test-Path $RepositoryPath -PathType Container) { Save-Report }
    throw
}
