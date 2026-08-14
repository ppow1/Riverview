# Riverview Steward Status Controlled Restart
# Version: 0.7.2
# Purpose: Safely restart the localhost-only Steward Status process after the bounded RIV-UI-0007 repair and verify the live boundary.
# Updated: 2026-08-14

[CmdletBinding()]
param(
    [string]$RepositoryPath='A:\Riverview\repo',
    [int]$Port=8770
)

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
    $Path=Join-Path $Directory "Steward-Status-Controlled-Restart-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){
            Set-Clipboard $Report
        } else {
            $Report | clip.exe
            if($LASTEXITCODE -ne 0){ throw "clip.exe exited with code $LASTEXITCODE." }
        }
        Write-Host "`nComplete restart report copied to the Windows clipboard." -ForegroundColor Cyan
    } catch {
        Write-Host "`nClipboard copy failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

function Get-ListeningProcessId {
    param([int]$ListenPort)
    $Connections=@(
        Get-NetTCPConnection -State Listen -LocalPort $ListenPort -ErrorAction SilentlyContinue
    )
    $Ids=@($Connections | Select-Object -ExpandProperty OwningProcess -Unique)
    return $Ids
}

function Get-ProcessEvidence {
    param([int]$ProcessId)
    $Process=Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId"
    if($null -eq $Process){
        throw "${CheckpointId}: Listener process $ProcessId disappeared before identity verification."
    }
    return $Process
}

try {
    Add-Section 'RIVERVIEW STEWARD STATUS CONTROLLED RESTART'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){
        throw "${CheckpointId}: Riverview Git repository not found."
    }

    $Launcher=Join-Path $RepositoryPath 'tools\powershell\status\Start-RiverviewStewardStatus.ps1'
    $ServerPath=Join-Path $RepositoryPath 'src\riverview\status\server.py'
    $SnapshotPath=Join-Path $RepositoryPath 'src\riverview\status\snapshot.py'

    foreach($Required in @($Launcher,$ServerPath,$SnapshotPath)){
        if(-not(Test-Path $Required)){
            throw "${CheckpointId}: Required Steward Status file missing: $Required"
        }
    }

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Local HEAD: $((git -C $RepositoryPath rev-parse HEAD).Trim())"
    Add-Line "Branch: $((git -C $RepositoryPath branch --show-current).Trim())"
    Add-Line "Restart tool version: $ToolVersion"
    Add-Line "Port: $Port"

    Add-Section 'CHARTER AND SCOPE ANCHOR'
    Add-Line 'Current dependency-ready waypoint remains RV-004.4 - Read-only MCP Relay.'
    Add-Line 'This stage only reloads the already-repaired localhost-only Steward Status source.'
    Add-Line 'No schema change, roadmap mutation, MCP authority change, supervisor implementation, commit, or push.'
    Add-Line 'Only a verified Riverview Steward Status listener on the requested localhost port may be terminated.'

    Add-Section 'SELF-INSTALLATION'
    $Canonical=Join-Path $RepositoryPath 'tools\powershell\status\Restart-RiverviewStewardStatus.ps1'
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Canonical)){
        Copy-Item $PSCommandPath $Canonical -Force
        Add-Line "Installed restart tool: $Canonical" Green
    } else {
        Add-Line "Running repository restart tool: $Canonical" Green
    }

    Add-Section 'SOURCE PRECHECK'
    $ServerText=Get-Content $ServerPath -Raw
    $SnapshotText=Get-Content $SnapshotPath -Raw
    if($ServerText -notmatch 'Version:\s+0\.7\.1'){
        throw "${CheckpointId}: Steward Status server source does not identify version 0.7.1."
    }
    if($ServerText -notmatch "status_changed_at"){
        throw "${CheckpointId}: Steward Status server source does not reference status_changed_at."
    }
    if($SnapshotText -notmatch "status_changed_at"){
        throw "${CheckpointId}: Steward Status snapshot source does not project status_changed_at."
    }
    Add-Line 'Repaired Steward Status source precheck passed.' Green

    Add-Section 'CURRENT LISTENER IDENTITY'
    $ListenerIds=@(Get-ListeningProcessId -ListenPort $Port)
    if($ListenerIds.Count -gt 1){
        throw "${CheckpointId}: Multiple listeners own port $Port. Stop rather than terminate ambiguous processes."
    }

    if($ListenerIds.Count -eq 1){
        $OldPid=[int]$ListenerIds[0]
        $Evidence=Get-ProcessEvidence -ProcessId $OldPid
        $Executable=[string]$Evidence.ExecutablePath
        $CommandLine=[string]$Evidence.CommandLine

        Add-Line "Existing listener PID: $OldPid"
        Add-Line "Existing executable: $Executable"
        Add-Line "Existing command line: $CommandLine"

        if($CommandLine -notmatch 'riverview\.status\.server'){
            throw "${CheckpointId}: Port $Port listener is not identifiable as riverview.status.server. No process was stopped."
        }
        if($CommandLine -notmatch [regex]::Escape($RepositoryPath)){
            Add-Line 'Listener command line does not contain repository path; validating Python executable location instead.' Yellow
            $ExpectedPython=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
            if([IO.Path]::GetFullPath($Executable) -ne [IO.Path]::GetFullPath($ExpectedPython)){
                throw "${CheckpointId}: Listener identity does not match the Riverview repository Python environment."
            }
        }

        Add-Line 'Existing listener identity verified as Riverview Steward Status.' Green

        Add-Section 'BOUNDED SHUTDOWN'
        Stop-Process -Id $OldPid -ErrorAction Stop
        $Deadline=(Get-Date).AddSeconds(10)
        do {
            Start-Sleep -Milliseconds 250
            $Remaining=@(Get-ListeningProcessId -ListenPort $Port)
        } while($Remaining.Count -gt 0 -and (Get-Date) -lt $Deadline)

        if($Remaining.Count -gt 0){
            throw "${CheckpointId}: Steward Status did not release port $Port within 10 seconds."
        }
        Add-Line "Previous Steward Status listener PID $OldPid stopped and port $Port released." Green
    } else {
        Add-Line "No existing listener on port $Port; proceeding with bounded start." Yellow
    }

    Add-Section 'START REPAIRED STEWARD STATUS'
    $StdoutDirectory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\steward-status\service'
    New-Item -ItemType Directory -Path $StdoutDirectory -Force | Out-Null
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
    $StdoutPath=Join-Path $StdoutDirectory "steward-status-$Stamp.stdout.txt"
    $StderrPath=Join-Path $StdoutDirectory "steward-status-$Stamp.stderr.txt"

    $ArgumentList=@(
        '-NoProfile',
        '-ExecutionPolicy','Bypass',
        '-File',"`"$Launcher`"",
        '-RepositoryPath',"`"$RepositoryPath`"",
        '-Port',$Port
    )

    $Started=Start-Process `
        -FilePath 'powershell.exe' `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $RepositoryPath `
        -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath `
        -PassThru

    Add-Line "Launcher PID: $($Started.Id)"
    Add-Line "Stdout: $StdoutPath"
    Add-Line "Stderr: $StderrPath"

    $Deadline=(Get-Date).AddSeconds(15)
    $NewListenerIds=@()
    do {
        Start-Sleep -Milliseconds 300
        $NewListenerIds=@(Get-ListeningProcessId -ListenPort $Port)
    } while($NewListenerIds.Count -eq 0 -and (Get-Date) -lt $Deadline)

    if($NewListenerIds.Count -ne 1){
        if(Test-Path $StderrPath){
            foreach($Line in @(Get-Content $StderrPath)){ Add-Line $Line Red }
        }
        throw "${CheckpointId}: Expected exactly one Steward Status listener on port $Port after restart."
    }

    $NewPid=[int]$NewListenerIds[0]
    $NewEvidence=Get-ProcessEvidence -ProcessId $NewPid
    Add-Line "New listener PID: $NewPid"
    Add-Line "New listener command line: $([string]$NewEvidence.CommandLine)"

    if(([string]$NewEvidence.CommandLine) -notmatch 'riverview\.status\.server'){
        throw "${CheckpointId}: New listener identity does not match Riverview Steward Status."
    }
    Add-Line 'New listener identity verified.' Green

    Add-Section 'LIVE HTTP ACCEPTANCE'
    $BaseUri="http://127.0.0.1:$Port"
    $ApiUri="$BaseUri/api/status"

    $Response=Invoke-RestMethod -Uri $ApiUri -Method Get -TimeoutSec 10
    if($Response.authority -ne 'read_only'){
        throw "${CheckpointId}: Live Steward Status authority is not read_only."
    }

    $Roadmap=@{}
    foreach($Row in $Response.roadmap){
        $Roadmap[[string]$Row.waypoint_id]=$Row
    }

    foreach($RequiredWaypoint in @('RV-001','RV-004.1','RV-004.2','RV-004.3','RV-004.4')){
        if(-not $Roadmap.ContainsKey($RequiredWaypoint)){
            throw "${CheckpointId}: Live API is missing roadmap waypoint $RequiredWaypoint."
        }
    }

    if($null -eq $Roadmap['RV-001'].status_changed_at){
        throw "${CheckpointId}: RV-001 has no live truthful status timestamp."
    }
    if($null -eq $Roadmap['RV-004.3'].status_changed_at){
        throw "${CheckpointId}: RV-004.3 has no live transition timestamp."
    }
    if($null -ne $Roadmap['RV-004.4'].status_changed_at){
        throw "${CheckpointId}: Pending RV-004.4 is still exposing a fabricated status timestamp."
    }

    $Page=Invoke-WebRequest -Uri "$BaseUri/" -UseBasicParsing -TimeoutSec 10
    if($Page.Content -notmatch 'status_changed_at'){
        throw "${CheckpointId}: Live HTML has not loaded the repaired status_changed_at field."
    }

    Add-Line 'Live HTTP boundary acceptance passed.' Green
    Add-Line "RV-001 displayed timestamp: $($Roadmap['RV-001'].status_changed_at)"
    Add-Line "RV-004.1 displayed timestamp: $($Roadmap['RV-004.1'].status_changed_at)"
    Add-Line "RV-004.2 displayed timestamp: $($Roadmap['RV-004.2'].status_changed_at)"
    Add-Line "RV-004.3 displayed timestamp: $($Roadmap['RV-004.3'].status_changed_at)"
    Add-Line 'RV-004.4 displayed timestamp: NULL (rendered as em dash)' Green

    Add-Section 'RESTART RESULT'
    Add-Line "Steward Status is listening at $BaseUri/ with repaired roadmap timestamp semantics." Green
    Add-Line "Listener PID: $NewPid" Green
    Add-Line 'The restart changed no PostgreSQL state and performed no migration.' Green
    Add-Line 'No unified-runtime supervisor work was introduced.' Green
    Add-Line 'No commit or push was performed.' Yellow
    Add-Line 'The source repair is now verified at the live localhost HTTP boundary.' Green

    Save-Report
}
catch {
    Add-Section 'STEWARD STATUS CONTROLLED RESTART BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'No commit or push was performed.' Yellow
    if(Test-Path $RepositoryPath -PathType Container){ Save-Report }
    throw
}
