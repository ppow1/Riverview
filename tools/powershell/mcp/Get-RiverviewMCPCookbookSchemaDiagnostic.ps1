# Riverview MCP Cookbook Schema Diagnostic
# Version: 0.9.8
# Purpose: Diagnose the RV-004.4 cookbook_entries schema contract mismatch before any repair.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.9.8'
$ExpectedHead='c496b01f86ccdf21b3b1a0914c5e48d9bf300043'
$CheckpointId='RIV-MCP-0007'
$ReportLines=[Collections.Generic.List[string]]::new()

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
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\mcp-relay'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path=Join-Path $Directory "MCP-Cookbook-Schema-Diagnostic-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){
            Set-Clipboard $Report
        } else {
            $Report | clip.exe
            if($LASTEXITCODE -ne 0){ throw "clip.exe exited with code $LASTEXITCODE." }
        }
        Write-Host "`nComplete diagnostic report copied to the Windows clipboard." -ForegroundColor Cyan
    } catch {
        Write-Host "`nClipboard copy failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW MCP COOKBOOK SCHEMA DIAGNOSTIC'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){
        throw "${CheckpointId}: Riverview Git repository not found."
    }

    $Head=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    $Branch=(git.exe -C $RepositoryPath branch --show-current).Trim()
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    $CookbookSync=Join-Path $RepositoryPath 'src\riverview\mcp\cookbook_sync.py'
    $Migration=Join-Path $RepositoryPath 'database\migrations\0008_readonly_mcp_relay.sql'

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Branch: $Branch"
    Add-Line "Local HEAD: $Head"
    Add-Line "Expected HEAD: $ExpectedHead"
    Add-Line "Diagnostic version: $ToolVersion"

    Add-Section 'CHARTER AND RV-004.4 SCOPE ANCHOR'
    Add-Line 'Current dependency-ready waypoint: RV-004.4 - Read-only MCP Relay.'
    Add-Line 'Exact action: inspect authoritative cookbook_entries schema and local schema assumptions.'
    Add-Line 'No source repair, schema migration, installer replay, database mutation, commit, or push is permitted.'
    Add-Line 'PostgreSQL remains authoritative operational state; no file fallback or alternate workflow authority is allowed.'

    if($Branch -ne 'main'){ throw "${CheckpointId}: Expected branch main, observed $Branch." }
    if($Head -ne $ExpectedHead){ throw "${CheckpointId}: Local HEAD differs from reconciled base." }
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    if(-not(Test-Path $CookbookSync)){ throw "${CheckpointId}: cookbook_sync.py not found." }
    if(-not(Test-Path $Migration)){ throw "${CheckpointId}: migration 0008 not found." }

    Add-Section 'SELF-INSTALLATION'
    $Canonical=Join-Path $RepositoryPath 'tools\powershell\mcp\Get-RiverviewMCPCookbookSchemaDiagnostic.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $Canonical) -Force | Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Canonical)){
        Copy-Item $PSCommandPath $Canonical -Force
        Add-Line "Installed diagnostic tool: $Canonical" Green
    }

    Add-Section 'PRE-DIAGNOSTIC WORKING TREE'
    $Before=@(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)
    foreach($Line in $Before){ Add-Line $Line Yellow }

    Add-Section 'LOCAL MIGRATION 0008'
    Add-Line "Path: $Migration"
    Add-Line "SHA256: $((Get-FileHash $Migration -Algorithm SHA256).Hash)"
    $MigrationLines=@(Get-Content $Migration -Encoding UTF8)
    $i=0
    foreach($Line in $MigrationLines){
        $i++
        Add-Line ("L{0}: {1}" -f $i,$Line)
    }

    Add-Section 'LOCAL COOKBOOK SYNC SQL CONTRACT'
    Add-Line "Path: $CookbookSync"
    Add-Line "SHA256: $((Get-FileHash $CookbookSync -Algorithm SHA256).Hash)"
    $SyncLines=@(Get-Content $CookbookSync -Encoding UTF8)
    for($n=0;$n -lt $SyncLines.Count;$n++){
        if($SyncLines[$n] -match 'cookbook_entries|checkpoint_id|ON CONFLICT|INSERT INTO|UPDATE SET'){
            $Start=[Math]::Max(0,$n-4)
            $End=[Math]::Min($SyncLines.Count-1,$n+20)
            for($j=$Start;$j -le $End;$j++){
                Add-Line ("L{0}: {1}" -f ($j+1),$SyncLines[$j])
            }
            Add-Line '---'
        }
    }

    Add-Section 'AUTHORITATIVE POSTGRESQL SCHEMA PROBE'
    $CaptureDirectory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\mcp-relay\runtime-capture'
    New-Item -ItemType Directory -Path $CaptureDirectory -Force | Out-Null
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
    $ProbePath=Join-Path $CaptureDirectory "cookbook-schema-$Stamp.py"
    $StdoutPath=Join-Path $CaptureDirectory "cookbook-schema-$Stamp.stdout.txt"
    $StderrPath=Join-Path $CaptureDirectory "cookbook-schema-$Stamp.stderr.txt"

    $Probe=@'
from __future__ import annotations

import json

from riverview.database import connect


def fetch_dicts(cursor):
    names = [column.name for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def emit(title, value):
    print(f"\n--- {title} ---")
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


with connect() as connection, connection.cursor() as cursor:
    cursor.execute(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name='cookbook_entries'
        ORDER BY table_schema
        """
    )
    emit("TABLE PRESENCE", fetch_dicts(cursor))

    cursor.execute(
        """
        SELECT
          ordinal_position,
          column_name,
          data_type,
          udt_name,
          is_nullable,
          column_default
        FROM information_schema.columns
        WHERE table_schema='public'
          AND table_name='cookbook_entries'
        ORDER BY ordinal_position
        """
    )
    emit("COLUMNS", fetch_dicts(cursor))

    cursor.execute(
        """
        SELECT
          tc.constraint_name,
          tc.constraint_type,
          kcu.column_name,
          kcu.ordinal_position
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name=kcu.constraint_name
         AND tc.table_schema=kcu.table_schema
         AND tc.table_name=kcu.table_name
        WHERE tc.table_schema='public'
          AND tc.table_name='cookbook_entries'
        ORDER BY tc.constraint_name,kcu.ordinal_position
        """
    )
    emit("CONSTRAINTS", fetch_dicts(cursor))

    cursor.execute(
        """
        SELECT indexname,indexdef
        FROM pg_indexes
        WHERE schemaname='public'
          AND tablename='cookbook_entries'
        ORDER BY indexname
        """
    )
    emit("INDEXES", fetch_dicts(cursor))

    cursor.execute("SELECT COUNT(*) AS row_count FROM cookbook_entries")
    emit("ROW COUNT", fetch_dicts(cursor))

    cursor.execute(
        """
        SELECT *
        FROM cookbook_entries
        ORDER BY 1
        LIMIT 10
        """
    )
    rows = fetch_dicts(cursor)

    safe_rows = []
    for row in rows:
        safe = {}
        for key, value in row.items():
            if key.lower() in {
                "secret", "credential", "token", "password", "payload",
                "private_payload", "undercurrent_payload"
            }:
                safe[key] = "<redacted>"
            else:
                safe[key] = value
        safe_rows.append(safe)
    emit("FIRST 10 ROWS SAFE METADATA", safe_rows)

    cursor.execute(
        """
        SELECT version,checksum,applied_at
        FROM schema_migrations
        WHERE version IN ('0003','0006','0008')
        ORDER BY version
        """
    )
    emit("RELEVANT MIGRATION LEDGER", fetch_dicts(cursor))

    connection.rollback()
'@

    Write-Utf8NoBom -Path $ProbePath -Content $Probe

    $Process=Start-Process `
        -FilePath $Python `
        -ArgumentList @($ProbePath) `
        -WorkingDirectory $RepositoryPath `
        -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath `
        -Wait `
        -PassThru

    Add-Line "Schema probe exit code: $($Process.ExitCode)" $(if($Process.ExitCode -eq 0){'Green'}else{'Red'})

    if(Test-Path $StdoutPath){
        foreach($Line in @(Get-Content $StdoutPath -Encoding UTF8)){ Add-Line $Line }
    }
    if(Test-Path $StderrPath){
        foreach($Line in @(Get-Content $StderrPath -Encoding UTF8)){ Add-Line $Line Red }
    }
    if($Process.ExitCode -ne 0){
        throw "${CheckpointId}: Authoritative schema probe failed with exit code $($Process.ExitCode)."
    }

    Add-Section 'POST-DIAGNOSTIC WORKING TREE'
    $After=@(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)
    foreach($Line in $After){ Add-Line $Line Yellow }

    # Self-install is the only intended repository status addition.
    $Unexpected=@()
    foreach($Line in $After){
        if($Before -notcontains $Line -and $Line -notmatch 'Get-RiverviewMCPCookbookSchemaDiagnostic\.ps1$'){
            $Unexpected += $Line
        }
    }
    if($Unexpected.Count -gt 0){
        foreach($Line in $Unexpected){ Add-Line "UNEXPECTED CHANGE  $Line" Red }
        throw "${CheckpointId}: Diagnostic changed unexpected repository state."
    }

    Add-Section 'DIAGNOSTIC RESULT'
    Add-Line 'Authoritative cookbook_entries schema and local RV-004.4 assumptions captured.' Green
    Add-Line 'Use this evidence to choose the smallest schema-compatible repair.' Yellow
    Add-Line 'No source repair, migration application, database mutation, commit, or push was performed.' Green

    Save-Report
}
catch {
    Add-Section 'MCP COOKBOOK SCHEMA DIAGNOSTIC BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'No source repair, migration application, commit, or push was performed.' Yellow
    if(Test-Path $RepositoryPath -PathType Container){ Save-Report }
    throw
}
