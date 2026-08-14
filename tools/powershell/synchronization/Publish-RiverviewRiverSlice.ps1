# Riverview River Runtime Slice Publisher
# Version: 0.2.1
# Purpose: Validate, commit, push, and remotely verify the accepted River v0.2 runtime slice.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath = 'A:\Riverview\repo')

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ToolVersion = '0.2.1'
$CommitMessage = 'Implement PostgreSQL-backed River event runtime'
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

function Invoke-Checked {
    param([Parameter(Mandatory)][string]$Label, [Parameter(Mandatory)][scriptblock]$Command)
    $Output = @(& $Command 2>&1 | ForEach-Object { "$_" })
    foreach ($Line in $Output) { Add-Line $Line }
    if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE." }
    Add-Line "$Label passed." Green
}

function Save-Report {
    $Directory = Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\publication'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path = Join-Path $Directory "Riverview-River-Publication-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    Set-Content -LiteralPath $Path -Value $Report -Encoding utf8NoBOM -NoNewline
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard $Report }
    else { $Report | clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW PUBLICATION VALIDATION'
    foreach ($Prerequisite in @('git', 'gh')) {
        if (-not (Get-Command $Prerequisite -ErrorAction SilentlyContinue)) {
            throw "RIV-PUB-0001: Missing prerequisite: $Prerequisite"
        }
        Add-Line "Found prerequisite: $Prerequisite" Green
    }
    $RepositoryPath = (Resolve-Path $RepositoryPath).Path
    if (-not (Test-Path (Join-Path $RepositoryPath '.git'))) { throw 'Riverview Git repository not found.' }
    $Python = Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    if (-not (Test-Path $Python)) { throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    if (-not $PSCommandPath) { throw 'Run this publisher from a saved .ps1 file.' }
    $InstalledTool = Join-Path $RepositoryPath 'tools\powershell\synchronization\Publish-RiverviewRiverSlice.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $InstalledTool) -Force | Out-Null
    if ([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($InstalledTool)) {
        Copy-Item -LiteralPath $PSCommandPath -Destination $InstalledTool -Force
        Add-Line "Installed publisher: $InstalledTool" Green
    }
    else { Add-Line "Running repository publisher: $InstalledTool" Green }

    Add-Section 'KNOWN FAILURE RECONCILIATION'
    $ScopeCheckpointPath = Join-Path $RepositoryPath 'docs\operations\troubleshooting\checkpoints\RIV-PUB-0005_UNEXPECTED_SCOPE.md'
    $ScopeCheckpoint = @'
<!-- Version: 0.2.1 -->
# RIV-PUB-0005 — Unexpected publication scope

Trigger: A modified or untracked path is not present in the publisher's explicit manifest.

Failure classes:

1. Legitimate project work was omitted from the manifest.
2. Unrelated user work is present in the working tree.
3. A generated, backup, credential, or runtime file escaped its ignore boundary.
4. A path was renamed or normalized differently than the manifest expects.

Diagnostic procedure: Read the exact `CHANGE` path in the publication report, inspect its contents and origin, and compare it with the accepted build scope. Never broaden the manifest to a directory merely to clear the gate.

Smallest repair: Add the single verified project file to the explicit manifest, move unrelated work out of the publication, or correct `.gitignore` for non-source artifacts.

Verification: Rerun the publisher. Every observed path must match one exact manifest entry; staged whitespace, acceptance, push, remote commit equality, and final clean-tree checks must pass.

Observed resolution: `tools/powershell/database/Install-RiverviewPostgreSQL.ps1` was created during the approved native PostgreSQL installation and was added as one exact path in publisher v0.2.1.
'@
    New-Item -ItemType Directory -Path (Split-Path -Parent $ScopeCheckpointPath) -Force | Out-Null
    Set-Content -LiteralPath $ScopeCheckpointPath -Value $ScopeCheckpoint -Encoding utf8NoBOM -NoNewline
    Add-Line 'RIV-PUB-0005 reconciled: approved PostgreSQL installer added as one exact path.' Green
    Add-Line 'Created Cookbook checkpoint RIV-PUB-0005 from observed publication evidence.' Green

    Push-Location $RepositoryPath
    try {
        Add-Section 'GITHUB AND BRANCH SAFETY'
        Invoke-Checked 'GitHub authentication' { gh auth status }
        $Origin = (git remote get-url origin).Trim()
        if ($LASTEXITCODE -ne 0 -or $Origin -ne 'https://github.com/ppow1/Riverview.git') {
            throw "RIV-PUB-0002: Unexpected origin: $Origin"
        }
        Add-Line "Origin validated: $Origin" Green
        $Branch = (git branch --show-current).Trim()
        if ($Branch -ne 'main') { throw "RIV-PUB-0003: Expected main branch; found $Branch" }
        Invoke-Checked 'Fetch origin' { git fetch origin main }
        $LocalBefore = (git rev-parse HEAD).Trim()
        $RemoteBefore = (git rev-parse origin/main).Trim()
        if ($LocalBefore -ne $RemoteBefore) {
            throw "RIV-PUB-0004: Local main ($LocalBefore) does not equal origin/main ($RemoteBefore)."
        }
        Add-Line "Publication base verified: $LocalBefore" Green

        Add-Section 'SCOPE CONFIRMATION'
        $Allowed = @(
            'pyproject.toml',
            'docs/operations/troubleshooting/checkpoints/RIV-BLD-0005_RUFF_RUNTIME_SLICE.md',
            'docs/operations/troubleshooting/checkpoints/RIV-DB-0002_CREDENTIAL_CONFIGURATION.md',
            'docs/operations/troubleshooting/checkpoints/RIV-DB-0003_DPAPI_RECOVERY.md',
            'docs/operations/troubleshooting/checkpoints/RIV-DB-0004_CONNECTION_TRANSACTION.md',
            'docs/operations/troubleshooting/checkpoints/RIV-EVT-0001_EVENT_APPEND.md',
            'docs/operations/troubleshooting/checkpoints/RIV-PUB-0005_UNEXPECTED_SCOPE.md',
            'src/riverview/database/__init__.py',
            'src/riverview/database/connection.py',
            'src/riverview/health.py',
            'src/riverview/river/__init__.py',
            'src/riverview/river/events.py',
            'src/riverview/river/store.py',
            'tests/test_river_event.py',
            'tools/powershell/database/Initialize-RiverviewDatabase.ps1',
            'tools/powershell/database/Install-RiverviewPostgreSQL.ps1',
            'tools/powershell/river/Install-RiverviewRiverSlice.ps1',
            'tools/powershell/river/Repair-RiverviewRiverSlice.ps1',
            'tools/powershell/synchronization/Publish-RiverviewRiverSlice.ps1'
        )
        $Observed = @(git status --porcelain=v1 -uall | ForEach-Object {
            if ($_.Length -lt 4) { return }
            $_.Substring(3).Trim().Replace('\', '/')
        })
        foreach ($Path in $Observed) {
            Add-Line "CHANGE $Path"
            if ($Path -notin $Allowed) { throw "RIV-PUB-0005: Unexpected working-tree path: $Path" }
        }
        foreach ($Required in $Allowed) {
            if (-not (Test-Path -LiteralPath (Join-Path $RepositoryPath $Required))) {
                throw "RIV-PUB-0006: Required publication file missing: $Required"
            }
        }

        Add-Section 'FULL ACCEPTANCE'
        & $Python -m pip install -e '.[dev]'
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
        Invoke-Checked 'Ruff check' { & $Python -m ruff check src tests }
        Invoke-Checked 'Pytest' { & $Python -m pytest }
        Invoke-Checked 'Python compilation' { & $Python -m compileall -q src }
        Invoke-Checked 'Database health' { & $Python -m riverview.health database }
        Invoke-Checked 'River event smoke test' { & $Python -m riverview.health event }

        Add-Section 'STAGE AND VERIFY'
        git add -- $Allowed
        if ($LASTEXITCODE -ne 0) { throw 'Explicit staging failed.' }
        Invoke-Checked 'Staged whitespace validation' { git diff --cached --check }
        $Staged = @(git diff --cached --name-only)
        foreach ($Path in $Staged) {
            Add-Line "STAGED $Path" Green
            if ($Path -notin $Allowed) { throw "RIV-PUB-0007: Unexpected staged path: $Path" }
        }
        if ($Staged.Count -eq 0) { throw 'RIV-PUB-0008: Nothing is staged for publication.' }

        Add-Section 'COMMIT PUSH AND REMOTE VERIFICATION'
        Invoke-Checked 'River runtime commit' { git commit -m $CommitMessage }
        $Commit = (git rev-parse HEAD).Trim()
        Invoke-Checked 'Push main' { git push origin main }
        $RemoteLine = (git ls-remote origin refs/heads/main).Trim()
        $RemoteCommit = ($RemoteLine -split '\s+')[0]
        if ($RemoteCommit -ne $Commit) {
            throw "RIV-PUB-0009: Remote verification mismatch; local=$Commit remote=$RemoteCommit"
        }
        $Remaining = @(git status --porcelain=v1 -uall)
        if ($Remaining.Count -gt 0) {
            foreach ($Line in $Remaining) { Add-Line "REMAINING $Line" Yellow }
            throw 'RIV-PUB-0010: Publication succeeded but the working tree is not clean.'
        }

        Add-Section 'PUBLICATION RESULT'
        Add-Line 'River v0.2 acceptance passed and the exact tested files were published.' Green
        Add-Line "Verified commit: $Commit" Green
        Add-Line 'Published branch: main' Green
        Add-Line "Publisher version: $ToolVersion"
    }
    finally { Pop-Location }
    Save-Report
}
catch {
    Add-Section 'PUBLICATION BLOCKED'
    Add-Line $_.Exception.Message Red
    Add-Line 'No unsupported completion claim was made.' Yellow
    if (Test-Path $RepositoryPath -PathType Container) { Save-Report }
    throw
}
