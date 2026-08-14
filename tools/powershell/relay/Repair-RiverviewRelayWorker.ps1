# Riverview Relay Worker Startup-Race Repair
# Version: 0.6.1
# Purpose: Establish readiness only after backlog drain and replay full acceptance.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\repo')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ToolVersion='0.6.1'
$ReportLines=[Collections.Generic.List[string]]::new()

function Add-Line {param([Parameter(Mandatory)][AllowEmptyString()][string]$Text,[ConsoleColor]$Color='Gray');$ReportLines.Add($Text);Write-Host $Text -ForegroundColor $Color}
function Add-Section {param([Parameter(Mandatory)][string]$Title);Add-Line '';Add-Line "=== $Title ===" Cyan}
function Invoke-Checked {param([string]$Label,[scriptblock]$Command);$global:LASTEXITCODE=0;$Output=@(& $Command 2>&1|ForEach-Object{"$_"});foreach($Line in $Output){Add-Line $Line};if($LASTEXITCODE -ne 0){throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE."};Add-Line "$Label passed." Green}
function Save-Report {$Directory=Join-Path(Split-Path -Parent $RepositoryPath)'runtime\diagnostics\relay-worker';New-Item -ItemType Directory -Path $Directory -Force|Out-Null;$Path=Join-Path $Directory "Relay-Worker-Repair-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt";$Report=($ReportLines-join[Environment]::NewLine)+[Environment]::NewLine;Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline;if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){Set-Clipboard $Report}else{$Report|clip.exe};Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan;Write-Host "Durable report: $Path" -ForegroundColor Green}

try {
    Add-Section 'RIVERVIEW RELAY WORKER REPAIR VALIDATION'
    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){throw 'Riverview Git repository not found.'}
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe';if(-not(Test-Path $Python)){throw 'RIV-BLD-0006: Riverview virtual environment not found.'}
    Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    $Installed=Join-Path $RepositoryPath 'tools\powershell\relay\Repair-RiverviewRelayWorker.ps1';New-Item -ItemType Directory -Path(Split-Path -Parent $Installed)-Force|Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Installed)){Copy-Item $PSCommandPath $Installed -Force;Add-Line "Installed reusable repair: $Installed" Green}else{Add-Line "Running repository repair: $Installed" Green}

    Add-Section 'KNOWN FAILURE RECONCILIATION'
    $Old=@'
                self._record("idle")
                if ready is not None:
                    ready.set()
                self.drain()
'@
    $New=@'
                self._record("idle")
                self.drain()
                if ready is not None:
                    ready.set()
'@
    foreach($Relative in @('src\riverview\relay\worker.py','tools\powershell\relay\Install-RiverviewRelayWorker.ps1')){
        $Path=Join-Path $RepositoryPath $Relative;$Content=Get-Content $Path -Raw
        if($Content.Contains($Old)){$Content=$Content.Replace($Old,$New);if($Relative.EndsWith('.ps1')){$Content=$Content.Replace('# Version: 0.6.0','# Version: 0.6.1').Replace("`$ToolVersion = '0.6.0'","`$ToolVersion = '0.6.1'")}else{$Content=$Content.Replace('Version: 0.6.0','Version: 0.6.1')};Set-Content $Path $Content -Encoding utf8NoBOM -NoNewline;Add-Line "REPAIRED  $Relative" Green}elseif($Content.Contains($New)){Add-Line "CURRENT   $Relative" DarkGray}else{throw "RIV-WRK-0009: Startup-order seam was not recognized in $Relative"}
    }

    $OldInvariant=@'
    if state != "succeeded" or not row or row[0] != "stopped" or row[1] is None or row[2] < 1:
        raise RuntimeError("RIV-WRK-0009: Notification-driven worker invariants failed.")
'@
    $NewInvariant=@'
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
'@
    foreach($Relative in @('src\riverview\relay_worker_health.py','tools\powershell\relay\Install-RiverviewRelayWorker.ps1')){
        $Path=Join-Path $RepositoryPath $Relative;$Content=Get-Content $Path -Raw
        if($Content.Contains($OldInvariant)){$Content=$Content.Replace($OldInvariant,$NewInvariant);if(-not $Relative.EndsWith('.ps1')){$Content=$Content.Replace('Version: 0.6.0','Version: 0.6.1')};Set-Content $Path $Content -Encoding utf8NoBOM -NoNewline;Add-Line "INSTRUMENTED $Relative" Green}elseif($Content.Contains($NewInvariant)){Add-Line "CURRENT   $Relative" DarkGray}else{throw "RIV-WRK-0009: Acceptance invariant seam was not recognized in $Relative"}
    }

    $ProjectPath=Join-Path $RepositoryPath 'pyproject.toml';$Project=Get-Content $ProjectPath -Raw;$Project=$Project.Replace('# Version: 0.6.0','# Version: 0.6.1').Replace('version = "0.6.0"','version = "0.6.1"');Set-Content $ProjectPath $Project -Encoding utf8NoBOM -NoNewline;Add-Line 'UPDATED   pyproject.toml' Green
    $Checkpoint=Join-Path $RepositoryPath 'docs\operations\troubleshooting\checkpoints\RIV-WRK-0009_WORKER_INVARIANT.md';$Text=Get-Content $Checkpoint -Raw
    if(-not $Text.Contains('startup readiness race')){$Text=$Text.Replace('<!-- Version: 0.6.0 -->','<!-- Version: 0.6.1 -->');$Text += "`nObserved startup readiness race: readiness was signaled before backlog drain, allowing new work to complete before notification accounting. Drain backlog before signaling readiness, then require explicit invariant evidence.`n";Set-Content $Checkpoint $Text -Encoding utf8NoBOM -NoNewline;Add-Line 'Updated RIV-WRK-0009 with observed startup-race evidence.' Green}

    Add-Section 'FULL ACCEPTANCE REPLAY'
    Push-Location $RepositoryPath
    try {
        & $Python -m pip install -e '.[dev]';if($LASTEXITCODE -ne 0){throw 'Dependency installation failed.'}
        $Migration=@'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed=apply_migration(Path('database/migrations/0005_relay_worker.sql'),'0005','0.6.0')
print('Migration 0005 applied.' if changed else 'Migration 0005 checksum verified.')
'@
        $Migration|& $Python -;if($LASTEXITCODE -ne 0){throw 'RIV-DB-0006: Migration 0005 validation failed.'}
        Invoke-Checked 'Ruff check' {& $Python -m ruff check src tests}
        Invoke-Checked 'Pytest' {& $Python -m pytest}
        Invoke-Checked 'Python compilation' {& $Python -m compileall -q src}
        Invoke-Checked 'Database health' {& $Python -m riverview.health database}
        Invoke-Checked 'Relay worker live acceptance' {& $Python -m riverview.relay_worker_health}
        Add-Section 'GIT CHANGE SUMMARY';foreach($Line in @(git status --short)){Add-Line $Line}
    } finally {Pop-Location}
    Add-Section 'REPAIR RESULT';Add-Line 'Backlog drain now precedes readiness; notification evidence and the full acceptance chain passed.' Green;Add-Line 'No commit or push was performed.' Yellow;Add-Line "Repair version: $ToolVersion";Save-Report
} catch {Add-Section 'REPAIR BLOCKED';Add-Line $_.Exception.Message Red;Add-Line 'No commit or push was performed.' Yellow;if(Test-Path $RepositoryPath -PathType Container){Save-Report};throw}
