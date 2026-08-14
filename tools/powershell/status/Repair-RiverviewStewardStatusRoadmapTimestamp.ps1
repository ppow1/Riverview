# Riverview Steward Status Roadmap Timestamp Repair
# Version: 0.7.2
# Purpose: Repair the Steward Status roadmap Updated column so it reflects meaningful status history rather than roadmap synchronization time.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\repo')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.7.2'
$CheckpointId='RIV-UI-0007'
$ReportLines=[Collections.Generic.List[string]]::new()

function Add-Line {
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$Text,
        [ConsoleColor]$Color='Gray'
    )
    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}

function Add-Section {
    param([Parameter(Mandatory)][string]$Title)
    Add-Line ''
    Add-Line "=== $Title ===" Cyan
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content
    )
    $Encoding=New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path,$Content,$Encoding)
}

function Save-Report {
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\steward-status'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path=Join-Path $Directory "Steward-Status-Roadmap-Timestamp-Repair-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report

    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){
            Set-Clipboard $Report
        } else {
            $Report | clip.exe
            if($LASTEXITCODE -ne 0){ throw "clip.exe exited with code $LASTEXITCODE." }
        }
        Write-Host "`nComplete repair report copied to the Windows clipboard." -ForegroundColor Cyan
    } catch {
        Write-Host "`nClipboard copy failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

function Invoke-Captured {
    param(
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$CaptureDirectory
    )
    $SafeLabel=($Label -replace '[^A-Za-z0-9_-]','-')
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmssfff'
    $StdoutPath=Join-Path $CaptureDirectory "$SafeLabel-$Stamp.stdout.txt"
    $StderrPath=Join-Path $CaptureDirectory "$SafeLabel-$Stamp.stderr.txt"
    $Process=Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $StdoutPath -RedirectStandardError $StderrPath -Wait -PassThru
    foreach($Line in @(Get-Content $StdoutPath -ErrorAction SilentlyContinue)){ Add-Line $Line }
    foreach($Line in @(Get-Content $StderrPath -ErrorAction SilentlyContinue)){ Add-Line $Line Red }
    Add-Line "$Label exit code: $($Process.ExitCode)"
    if($Process.ExitCode -ne 0){ throw "${CheckpointId}: $Label failed with exit code $($Process.ExitCode)." }
}

try {
    Add-Section 'RIVERVIEW STEWARD STATUS ROADMAP TIMESTAMP REPAIR'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){
        throw "${CheckpointId}: Riverview Git repository not found."
    }
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    if(-not(Test-Path $Python)){
        throw 'RIV-BLD-0006: Riverview virtual environment not found.'
    }

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Local HEAD: $((git -C $RepositoryPath rev-parse HEAD).Trim())"
    Add-Line "Branch: $((git -C $RepositoryPath branch --show-current).Trim())"
    Add-Line "Repair version: $ToolVersion"
    Add-Line "Checkpoint: $CheckpointId"

    Add-Section 'CHARTER AND SCOPE ANCHOR'
    Add-Line 'Current dependency-ready waypoint remains RV-004.4 - Read-only MCP Relay.'
    Add-Line 'This is a separate bounded Steward Status correctness repair.'
    Add-Line 'Exact action: display meaningful roadmap status history instead of roadmap synchronization time.'
    Add-Line 'No schema change, no roadmap-state change, no MCP authority change, no supervisor work, no service restart, no commit, and no push.'
    Add-Line 'Undercurrent, credentials, protected payloads, arbitrary SQL, filesystem authority, and process-execution authority remain outside the product surface.'

    Add-Section 'SELF-INSTALLATION'
    $CanonicalRepair=Join-Path $RepositoryPath 'tools\powershell\status\Repair-RiverviewStewardStatusRoadmapTimestamp.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $CanonicalRepair) -Force | Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($CanonicalRepair)){
        Copy-Item $PSCommandPath $CanonicalRepair -Force
        Add-Line "Installed repair tool: $CanonicalRepair" Green
    } else {
        Add-Line "Running repository repair tool: $CanonicalRepair" Green
    }

    Add-Section 'PRE-REPAIR WORKING TREE'
    $BeforeStatus=@(git -C $RepositoryPath status --porcelain=v1 --untracked-files=all)
    foreach($Line in $BeforeStatus){ Add-Line $Line Yellow }

    $Targets=@(
        'src\riverview\status\snapshot.py',
        'src\riverview\status\server.py',
        'tools\powershell\status\Install-RiverviewStewardStatus.ps1'
    )
    foreach($Relative in $Targets){
        $StatusLine=@(git -C $RepositoryPath status --porcelain=v1 -- $Relative)
        if($StatusLine.Count -gt 0){
            throw "${CheckpointId}: Target file already has local changes: $Relative. Stop to preserve unrelated work."
        }
    }

    Add-Section 'BACKUP'
    $WorkspacePath=Split-Path -Parent $RepositoryPath
    $BackupDirectory=Join-Path $WorkspacePath 'runtime\diagnostics\steward-status\backups'
    $CaptureDirectory=Join-Path $WorkspacePath 'runtime\diagnostics\steward-status\runtime-capture'
    New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
    New-Item -ItemType Directory -Path $CaptureDirectory -Force | Out-Null
    $BackupStamp=Get-Date -Format 'yyyyMMdd-HHmmss'
    foreach($Relative in $Targets){
        $Source=Join-Path $RepositoryPath $Relative
        if(-not(Test-Path $Source)){ throw "${CheckpointId}: Required target missing: $Relative" }
        $BackupName=($Relative -replace '[\\/:*?"<>|]','_')
        $Backup=Join-Path $BackupDirectory "$BackupStamp-$BackupName"
        Copy-Item $Source $Backup -Force
        Add-Line "BACKUP    $Relative -> $Backup"
    }

    Add-Section 'PATCH SOURCE AND CANONICAL INSTALLER'
    $PatcherPath=Join-Path $CaptureDirectory "status-timestamp-patcher-$BackupStamp.py"
    $Patcher=@'
from __future__ import annotations

import pathlib
import sys

repo = pathlib.Path(sys.argv[1])
checkpoint = "RIV-UI-0007"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{checkpoint}: expected exactly one {label} seam, found {count}")
    return text.replace(old, new, 1)


def write(path: pathlib.Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")
    print(f"UPDATED   {path.relative_to(repo)}")

old_query = 'cursor.execute("SELECT waypoint_id,parent_waypoint_id,sort_order,title,status,steward_checkpoint,updated_at FROM roadmap_items ORDER BY COALESCE(parent_waypoint_id,waypoint_id),sort_order")'
new_query = '''cursor.execute(
            """SELECT
                   i.waypoint_id,
                   i.parent_waypoint_id,
                   i.sort_order,
                   i.title,
                   i.status,
                   i.steward_checkpoint,
                   COALESCE(
                       t.occurred_at,
                       CASE WHEN i.status='completed' THEN i.completed_at END
                   ) AS status_changed_at
               FROM roadmap_items i
               LEFT JOIN LATERAL (
                   SELECT rt.occurred_at
                   FROM roadmap_transitions rt
                   WHERE rt.waypoint_id=i.waypoint_id
                   ORDER BY rt.occurred_at DESC
                   LIMIT 1
               ) t ON TRUE
               ORDER BY COALESCE(i.parent_waypoint_id,i.waypoint_id),i.sort_order"""
        )'''

snapshot_path = repo / "src/riverview/status/snapshot.py"
snapshot = snapshot_path.read_text(encoding="utf-8")
snapshot = replace_once(snapshot, "Version: 0.7.0", "Version: 0.7.1", "snapshot version")
snapshot = replace_once(snapshot, old_query, new_query, "roadmap projection")
write(snapshot_path, snapshot)

server_path = repo / "src/riverview/status/server.py"
server = server_path.read_text(encoding="utf-8")
server = replace_once(server, "Version: 0.7.0", "Version: 0.7.1", "server version")
server = replace_once(server, "RiverviewStatus/0.7.0", "RiverviewStatus/0.7.1", "HTTP version")
server = replace_once(server, "esc(r[c[1]])", "esc(r[c[1]] ?? '--')", "null-cell display")
server = replace_once(server, "['Updated','updated_at']", "['Updated','status_changed_at']", "roadmap Updated field")
write(server_path, server)

installer_path = repo / "tools/powershell/status/Install-RiverviewStewardStatus.ps1"
installer = installer_path.read_text(encoding="utf-8")
installer = installer.replace("Version: 0.7.0", "Version: 0.7.1")
installer = installer.replace("$ToolVersion='0.7.0'", "$ToolVersion='0.7.1'")
installer = installer.replace("RiverviewStatus/0.7.0", "RiverviewStatus/0.7.1")
installer = replace_once(installer, old_query, new_query, "embedded roadmap projection")
installer = replace_once(installer, "esc(r[c[1]])", "esc(r[c[1]] ?? '--')", "embedded null-cell display")
installer = replace_once(installer, "['Updated','updated_at']", "['Updated','status_changed_at']", "embedded roadmap Updated field")
write(installer_path, installer)
'@
    Write-Utf8NoBom -Path $PatcherPath -Content $Patcher
    Invoke-Captured -Label 'Source patcher' -FilePath $Python -ArgumentList @($PatcherPath,$RepositoryPath) -WorkingDirectory $RepositoryPath -CaptureDirectory $CaptureDirectory

    Add-Section 'COOKBOOK CHECKPOINT'
    $CheckpointRelative='docs\operations\troubleshooting\checkpoints\RIV-UI-0007_ROADMAP_TIMESTAMP_SEMANTICS.md'
    $CheckpointPath=Join-Path $RepositoryPath $CheckpointRelative
    $Checkpoint=@'
<!-- Version: 0.7.2 -->
# RIV-UI-0007 - Roadmap timestamp semantics

Component and seam owner: Steward Status roadmap projection and display.

Triggering operation: Viewing the Roadmap table after a master-roadmap synchronization.

Observed failure class: all 103 roadmap rows display the same `roadmap_items.updated_at` timestamp even though the waypoints did not all change state at that time.

Evidence signature:
- `roadmap_items` has 103 rows and one distinct `updated_at` value matching `roadmap_revisions.applied_at`.
- `roadmap_transitions.occurred_at` contains truthful state-change history where recorded.
- older completed rows may have truthful `completed_at` but no transition history.
- pending/active rows with no transition history have no truthful historical status-change timestamp.

Smallest permitted repair:
1. keep `roadmap_items.updated_at` as internal synchronization metadata;
2. project `status_changed_at` as the latest transition time;
3. fall back to `completed_at` only for completed rows without transition history;
4. return NULL where no truthful status-change time exists;
5. render NULL explicitly in Steward Status.

Recovery verification:
- RV-004.1, RV-004.2, and RV-004.3 display their transition times;
- RV-001 through RV-003 fall back to recorded completion time;
- untouched pending waypoints such as RV-004.4 display no fabricated timestamp;
- the dashboard no longer presents master-roadmap publication time as waypoint progress.

Escalation boundary: do not invent timestamps, rewrite transition history, add schema merely for display convenience, or alter roadmap state to repair the UI.

Applicable implementation revision: Steward Status 0.7.1; repair tool 0.7.2.

Validation state: observed; repair acceptance required.
'@
    New-Item -ItemType Directory -Path (Split-Path -Parent $CheckpointPath) -Force | Out-Null
    Write-Utf8NoBom -Path $CheckpointPath -Content $Checkpoint
    Add-Line "WRITTEN   $CheckpointRelative" Green
    Add-Line 'Troubleshooting README intentionally not modified because it already belongs to active RV-004.4 local work.' Yellow

    Add-Section 'STATIC ACCEPTANCE'
    Invoke-Captured -Label 'Python compilation' -FilePath $Python -ArgumentList @('-m','compileall','-q','src\riverview\status') -WorkingDirectory $RepositoryPath -CaptureDirectory $CaptureDirectory
    Invoke-Captured -Label 'Ruff' -FilePath $Python -ArgumentList @('-m','ruff','check','src\riverview\status') -WorkingDirectory $RepositoryPath -CaptureDirectory $CaptureDirectory

    Add-Section 'LIVE READ-ONLY ACCEPTANCE'
    $AcceptancePath=Join-Path $CaptureDirectory "status-timestamp-acceptance-$BackupStamp.py"
    $Acceptance=@'
from __future__ import annotations

import json

from riverview.status.server import HTML
from riverview.status.snapshot import status_snapshot

snapshot = status_snapshot()
roadmap = {row["waypoint_id"]: row for row in snapshot["roadmap"]}

required = ["RV-001", "RV-002", "RV-003", "RV-004.1", "RV-004.2", "RV-004.3", "RV-004.4"]
missing = [waypoint for waypoint in required if waypoint not in roadmap]
if missing:
    raise RuntimeError(f"RIV-UI-0007: missing roadmap rows: {missing}")

for waypoint in ["RV-001", "RV-002", "RV-003", "RV-004.1", "RV-004.2", "RV-004.3"]:
    if roadmap[waypoint]["status_changed_at"] is None:
        raise RuntimeError(f"RIV-UI-0007: completed waypoint {waypoint} has no truthful displayed timestamp")

if roadmap["RV-004.4"]["status_changed_at"] is not None:
    raise RuntimeError("RIV-UI-0007: pending RV-004.4 must not display a fabricated status-change timestamp")

completed_times = {
    str(roadmap[waypoint]["status_changed_at"])
    for waypoint in ["RV-001", "RV-002", "RV-003", "RV-004.1", "RV-004.2", "RV-004.3"]
}
if len(completed_times) < 3:
    raise RuntimeError("RIV-UI-0007: completed timestamps still collapse to an implausible shared synchronization time")

if "['Updated','status_changed_at']" not in HTML:
    raise RuntimeError("RIV-UI-0007: HTML is not rendering status_changed_at")
if "?? '--'" not in HTML:
    raise RuntimeError("RIV-UI-0007: HTML does not explicitly render missing truthful timestamps")

print(json.dumps({
    "status": "healthy",
    "checkpoint": "RIV-UI-0007",
    "authority": snapshot["authority"],
    "roadmap_rows": len(snapshot["roadmap"]),
    "rv001": str(roadmap["RV-001"]["status_changed_at"]),
    "rv004_1": str(roadmap["RV-004.1"]["status_changed_at"]),
    "rv004_2": str(roadmap["RV-004.2"]["status_changed_at"]),
    "rv004_3": str(roadmap["RV-004.3"]["status_changed_at"]),
    "rv004_4": roadmap["RV-004.4"]["status_changed_at"],
    "pending_without_history_is_null": True,
}, indent=2, sort_keys=True, default=str))
'@
    Write-Utf8NoBom -Path $AcceptancePath -Content $Acceptance
    Invoke-Captured -Label 'Live read-only timestamp acceptance' -FilePath $Python -ArgumentList @($AcceptancePath) -WorkingDirectory $RepositoryPath -CaptureDirectory $CaptureDirectory

    Add-Section 'POST-REPAIR WORKING TREE'
    $AfterStatus=@(git -C $RepositoryPath status --porcelain=v1 --untracked-files=all)
    foreach($Line in $AfterStatus){ Add-Line $Line }

    Add-Section 'REPAIR RESULT'
    Add-Line 'Steward Status source now projects meaningful status history rather than roadmap synchronization time.' Green
    Add-Line 'No migration or roadmap-state mutation was required.' Green
    Add-Line 'No transition history was invented or rewritten.' Green
    Add-Line 'The running 127.0.0.1:8770 process was NOT restarted; restart is a separate controlled stage after this report passes.' Yellow
    Add-Line 'The active RV-004.4 MCP working tree was preserved.' Green
    Add-Line 'No commit or push was performed.' Yellow
    Add-Line "Repair tool version: $ToolVersion"
    Save-Report
}
catch {
    Add-Section 'STEWARD STATUS ROADMAP TIMESTAMP REPAIR BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'No commit or push was performed.' Yellow
    if(Test-Path $RepositoryPath -PathType Container){ Save-Report }
    throw
}
