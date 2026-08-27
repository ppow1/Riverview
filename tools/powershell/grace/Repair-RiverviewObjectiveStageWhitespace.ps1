# Riverview RV-005.2 Full Publication Whitespace Sweep
# Version: 0.3.0
# Date: 2026-08-14
# Purpose: Byte-scan and normalize trailing ASCII spaces/tabs across the complete RV-005.2 publication scope, then validate the entire staged slice with Git's own whitespace rules.
#
# Checkpoint: RIV-GRC-0002
# No functional logic change, commit, push, roadmap mutation, or migration rewrite is permitted.

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.3.0'
$ExpectedHead='34b672f2acb7dd60ea2536505ff3bd39b93ce40b'
$CheckpointId='RIV-GRC-0002'
$ReportLines=[Collections.Generic.List[string]]::new()
$ValidationWorktree=$null

function Add-Line {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text,[ConsoleColor]$Color='Gray')
    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}
function Add-Section {
    param([Parameter(Mandatory)][string]$Title)
    Add-Line ''
    Add-Line "=== $Title ===" Cyan
}
function Write-Utf8NoBom {
    param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][AllowEmptyString()][string]$Content)
    $Encoding=New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path,$Content,$Encoding)
}
function Save-Report {
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path=Join-Path $Directory "RV-005.2-Full-Whitespace-Sweep-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){ Set-Clipboard $Report }
        else { $Report | clip.exe }
        Write-Host "`nComplete sweep report copied to the Windows clipboard." -ForegroundColor Cyan
    } catch {
        Write-Host "`nClipboard copy failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host "Durable report: $Path" -ForegroundColor Green
}
function Invoke-Captured {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$Label
    )
    $Capture=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\whitespace-capture'
    New-Item -ItemType Directory -Path $Capture -Force | Out-Null
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmssfff'
    $Safe=($Label -replace '[^A-Za-z0-9_-]','_')
    $Out=Join-Path $Capture "$Safe-$Stamp.stdout.txt"
    $Err=Join-Path $Capture "$Safe-$Stamp.stderr.txt"
    $Process=Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $Out -RedirectStandardError $Err -Wait -PassThru
    if(Test-Path $Out){ foreach($Line in @(Get-Content $Out -Encoding UTF8)){ Add-Line $Line } }
    if(Test-Path $Err){ foreach($Line in @(Get-Content $Err -Encoding UTF8)){ Add-Line $Line $(if($Process.ExitCode -eq 0){'Yellow'}else{'Red'}) } }
    if($Process.ExitCode -ne 0){ throw "${CheckpointId}: $Label failed with exit code $($Process.ExitCode)." }
}

try {
    Add-Section 'RIVERVIEW RV-005.2 FULL PUBLICATION WHITESPACE SWEEP'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    $Head=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    $Branch=(git.exe -C $RepositoryPath branch --show-current).Trim()

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Branch: $Branch"
    Add-Line "Local HEAD: $Head"
    Add-Line "Sweep version: $ToolVersion"

    Add-Section 'CHARTER AND RV-005.2 SCOPE ANCHOR'
    Add-Line 'Current waypoint: RV-005.2 - Objective and stage model.'
    Add-Line 'Exact action: scan every approved RV-005.2 publication file at byte level, remove all trailing ASCII spaces/tabs, then validate the full staged slice with git diff --cached --check.'
    Add-Line 'Git staged whitespace validation is the acceptance authority for this repair.'
    Add-Line 'Prohibited: functional logic changes, migration 0010 content change, RV-005.3 behavior, roadmap mutation, commit, or push.'

    if($Branch -ne 'main'){ throw "${CheckpointId}: Expected main branch, observed $Branch." }
    if($Head -ne $ExpectedHead){ throw "${CheckpointId}: Expected HEAD $ExpectedHead, observed $Head." }
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: Riverview virtual environment not found.' }

    Add-Section 'SELF-INSTALLATION'
    $Canonical=Join-Path $RepositoryPath 'tools\powershell\grace\Repair-RiverviewObjectiveStageWhitespace.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $Canonical) -Force | Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Canonical)){
        Copy-Item $PSCommandPath $Canonical -Force
        Add-Line "Installed sweep tool: $Canonical" Green
    }

    $Scope=@(
        'database/migrations/0010_objective_stage_model.sql',
        'docs/operations/troubleshooting/checkpoints/RIV-GRC-0002_OBJECTIVE_STAGE_MODEL.md',
        'src/riverview/grace/objective_acceptance.py',
        'src/riverview/grace/objectives.py',
        'tests/test_objective_stage_model.py',
        'tools/powershell/grace/Install-RiverviewObjectiveStageModel.ps1',
        'tools/powershell/grace/Repair-RiverviewObjectiveStageAcceptance.ps1',
        'tools/powershell/grace/Repair-RiverviewObjectiveStageWhitespace.ps1',
        'tools/powershell/synchronization/Publish-RiverviewObjectiveStageModel.ps1'
    )

    foreach($Relative in $Scope){
        $Full=Join-Path $RepositoryPath ($Relative -replace '/','\')
        if(-not(Test-Path $Full -PathType Leaf)){ throw "${CheckpointId}: scope file missing: $Relative" }
    }

    $MigrationPath=Join-Path $RepositoryPath 'database\migrations\0010_objective_stage_model.sql'
    $MigrationHashBefore=(Get-FileHash $MigrationPath -Algorithm SHA256).Hash
    Add-Line "Migration 0010 pre-sweep SHA256: $MigrationHashBefore"

    Add-Section 'BYTE-LEVEL COMPLETE-SCOPE SCAN AND NORMALIZATION'
    $Runtime=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\runtime'
    New-Item -ItemType Directory -Path $Runtime -Force | Out-Null
    $ScopeJson=Join-Path $Runtime 'rv0052-whitespace-scope.json'
    $ScanScript=Join-Path $Runtime 'rv0052_full_whitespace_sweep.py'

    $Scope | ConvertTo-Json | Set-Content -Path $ScopeJson -Encoding UTF8

    $ScanText=@'
from __future__ import annotations

import json
from pathlib import Path

root = Path(r"__ROOT__")
scope = json.loads(Path(r"__SCOPE__").read_text(encoding="utf-8-sig"))

summary = []
total_before = 0
total_after = 0

for rel in scope:
    path = root / Path(rel)
    data = path.read_bytes()

    # Preserve all bytes except ASCII space/tab immediately before CRLF, LF,
    # or EOF. This deliberately does not normalize line endings.
    out = bytearray()
    lines_changed = []
    line_no = 1
    i = 0
    line_start = 0

    while i < len(data):
        if data[i:i+2] == b"\r\n":
            content = data[line_start:i]
            trimmed = content.rstrip(b" \t")
            if trimmed != content:
                lines_changed.append(line_no)
            out.extend(trimmed)
            out.extend(b"\r\n")
            i += 2
            line_start = i
            line_no += 1
            continue
        if data[i:i+1] == b"\n":
            content = data[line_start:i]
            trimmed = content.rstrip(b" \t")
            if trimmed != content:
                lines_changed.append(line_no)
            out.extend(trimmed)
            out.extend(b"\n")
            i += 1
            line_start = i
            line_no += 1
            continue
        i += 1

    if line_start < len(data):
        content = data[line_start:]
        trimmed = content.rstrip(b" \t")
        if trimmed != content:
            lines_changed.append(line_no)
        out.extend(trimmed)

    before = len(lines_changed)
    total_before += before

    if bytes(out) != data:
        path.write_bytes(bytes(out))

    verify = path.read_bytes()
    remaining = []
    line_no = 1
    for raw in verify.splitlines(keepends=True):
        body = raw[:-2] if raw.endswith(b"\r\n") else raw[:-1] if raw.endswith(b"\n") else raw
        if body.endswith((b" ", b"\t")):
            remaining.append(line_no)
        line_no += 1

    total_after += len(remaining)
    summary.append(
        {
            "path": rel,
            "trailing_lines_before": lines_changed,
            "remaining_after": remaining,
            "changed": bool(lines_changed),
        }
    )

print(json.dumps(
    {
        "status": "healthy" if total_after == 0 else "failed",
        "total_trailing_lines_found": total_before,
        "total_remaining_after": total_after,
        "files": summary,
    },
    indent=2,
))
if total_after:
    raise SystemExit(2)
'@
    $ScanText=$ScanText.Replace('__ROOT__',$RepositoryPath.Replace('\','\\'))
    $ScanText=$ScanText.Replace('__SCOPE__',$ScopeJson.Replace('\','\\'))
    Write-Utf8NoBom -Path $ScanScript -Content $ScanText

    Invoke-Captured -FilePath $Python -ArgumentList @($ScanScript) -WorkingDirectory $RepositoryPath -Label 'byte_whitespace_sweep'

    $MigrationHashAfter=(Get-FileHash $MigrationPath -Algorithm SHA256).Hash
    Add-Line "Migration 0010 post-sweep SHA256: $MigrationHashAfter"
    if($MigrationHashAfter -ne $MigrationHashBefore){
        throw "${CheckpointId}: migration 0010 changed during whitespace sweep."
    }
    Add-Line 'Migration 0010 remained byte-for-byte unchanged.' Green

    Add-Section 'STATIC AND BEHAVIORAL ACCEPTANCE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','compileall','-q','src\riverview\grace') -WorkingDirectory $RepositoryPath -Label 'compile'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','ruff','check','src\riverview\grace','tests\test_objective_stage_model.py') -WorkingDirectory $RepositoryPath -Label 'ruff'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','pytest','-q','tests\test_objective_stage_model.py') -WorkingDirectory $RepositoryPath -Label 'tests'

    $AcceptanceKey="acceptance.rv0052.whitespace.$([Guid]::NewGuid().ToString('N'))"
    Add-Line "Acceptance key: $AcceptanceKey"
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','seed',$AcceptanceKey) -WorkingDirectory $RepositoryPath -Label 'seed'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','read',$AcceptanceKey) -WorkingDirectory $RepositoryPath -Label 'read'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.acceptance') -WorkingDirectory $RepositoryPath -Label 'grace_authority'
    Add-Line 'Behavioral acceptance passed after complete-scope whitespace normalization.' Green

    Add-Section 'DISPOSABLE GIT STAGED-WHITESPACE VALIDATION'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'fetch','--prune','origin','main') -WorkingDirectory $RepositoryPath -Label 'git_fetch'
    $Remote=(git.exe -C $RepositoryPath rev-parse 'origin/main').Trim()
    Add-Line "Observed remote main: $Remote"
    if($Remote -ne $ExpectedHead){ throw "${CheckpointId}: remote main moved from expected base." }

    $ValidationRoot=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\validation'
    New-Item -ItemType Directory -Path $ValidationRoot -Force | Out-Null
    $ValidationWorktree=Join-Path $ValidationRoot "rv0052-whitespace-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'worktree','add','--detach',$ValidationWorktree,$Remote) -WorkingDirectory $RepositoryPath -Label 'git_worktree_add'

    foreach($Relative in $Scope){
        $Source=Join-Path $RepositoryPath ($Relative -replace '/','\')
        $Destination=Join-Path $ValidationWorktree ($Relative -replace '/','\')
        New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
        Copy-Item $Source $Destination -Force

        $A=(Get-FileHash $Source -Algorithm SHA256).Hash
        $B=(Get-FileHash $Destination -Algorithm SHA256).Hash
        if($A -ne $B){ throw "${CheckpointId}: byte copy mismatch: $Relative" }
    }

    Invoke-Captured -FilePath 'git.exe' -ArgumentList (@('-C',$ValidationWorktree,'add','--')+$Scope) -WorkingDirectory $ValidationWorktree -Label 'git_stage_full_scope'

    Add-Section 'GIT AUTHORITATIVE FULL-SCOPE WHITESPACE CHECK'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$ValidationWorktree,'diff','--cached','--check') -WorkingDirectory $ValidationWorktree -Label 'git_diff_cached_check'
    Add-Line 'git diff --cached --check returned zero errors across the full RV-005.2 publication scope.' Green

    Add-Section 'STAGED SCOPE VERIFICATION'
    $Staged=@(git.exe -C $ValidationWorktree diff --cached --name-only)
    foreach($Path in $Staged){ Add-Line $Path }
    foreach($Path in $Staged){
        if($Scope -notcontains ($Path -replace '\','/')){
            throw "${CheckpointId}: unexpected staged path during whitespace validation: $Path"
        }
    }
    if($Staged.Count -ne $Scope.Count){
        throw "${CheckpointId}: expected $($Scope.Count) staged scope files, observed $($Staged.Count)."
    }
    Add-Line 'All and only approved RV-005.2 publication files were staged.' Green

    Add-Section 'FINAL WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }

    Add-Section 'RV-005.2 FULL WHITESPACE SWEEP RESULT'
    Add-Line 'Every approved publication file was byte-scanned for trailing ASCII spaces/tabs.' Green
    Add-Line 'All detected trailing whitespace was normalized in one pass.' Green
    Add-Line 'Migration 0010 remained byte-for-byte unchanged.' Green
    Add-Line 'Behavioral acceptance remains healthy.' Green
    Add-Line 'The full copied/staged RV-005.2 slice passed git diff --cached --check with zero errors.' Green
    Add-Line 'No commit, push, or roadmap mutation was performed.' Green
    Add-Line 'Next stage: rerun exact-scope publication.' Green

    Save-Report
}
catch {
    Add-Section 'RV-005.2 FULL WHITESPACE SWEEP BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'No commit or push was performed.' Yellow
    if($ValidationWorktree){ Add-Line "Validation worktree retained for evidence: $ValidationWorktree" Yellow }
    Save-Report
    throw
}
finally {
    if($ValidationWorktree -and (Test-Path $ValidationWorktree)){
        try {
            & git.exe -C $RepositoryPath worktree remove --force $ValidationWorktree 2>$null | Out-Null
            & git.exe -C $RepositoryPath worktree prune 2>$null | Out-Null
        } catch {}
    }
}
