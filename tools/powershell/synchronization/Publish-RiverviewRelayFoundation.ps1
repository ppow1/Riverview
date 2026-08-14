# Riverview Relay Foundation Publisher
# Version: 0.4.0
# Purpose: Validate, publish, and remotely verify the Relay data-and-lifecycle foundation.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath = 'A:\Riverview\repo')

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ToolVersion = '0.4.0'
$CommitMessage = 'Implement Relay waypoint and work-order foundation'
$ReportLines = [Collections.Generic.List[string]]::new()

function Add-Line { param([Parameter(Mandatory)][AllowEmptyString()][string]$Text, [ConsoleColor]$Color = 'Gray'); $ReportLines.Add($Text); Write-Host $Text -ForegroundColor $Color }
function Add-Section { param([Parameter(Mandatory)][string]$Title); Add-Line ''; Add-Line "=== $Title ===" Cyan }
function Invoke-Checked {
    param([Parameter(Mandatory)][string]$Label, [Parameter(Mandatory)][scriptblock]$Command)
    $Output = @(& $Command 2>&1 | ForEach-Object { "$_" }); foreach ($Line in $Output) { Add-Line $Line }
    if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE." }; Add-Line "$Label passed." Green
}
function Save-Report {
    $Directory = Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\publication'; New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path = Join-Path $Directory "Riverview-Relay-Foundation-Publication-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"; $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline; if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard $Report } else { $Report | clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan; Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW RELAY PUBLICATION VALIDATION'
    foreach ($Name in @('git','gh')) { if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { throw "RIV-PUB-0001: Missing prerequisite: $Name" }; Add-Line "Found prerequisite: $Name" Green }
    $RepositoryPath = (Resolve-Path $RepositoryPath).Path; if (-not (Test-Path (Join-Path $RepositoryPath '.git'))) { throw 'Riverview Git repository not found.' }
    $Python = Join-Path $RepositoryPath '.venv\Scripts\python.exe'; if (-not (Test-Path $Python)) { throw 'RIV-BLD-0006: Riverview virtual environment not found.' }; Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    $InstalledTool = Join-Path $RepositoryPath 'tools\powershell\synchronization\Publish-RiverviewRelayFoundation.ps1'; New-Item -ItemType Directory -Path (Split-Path -Parent $InstalledTool) -Force | Out-Null
    if ([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($InstalledTool)) { Copy-Item $PSCommandPath $InstalledTool -Force; Add-Line "Installed publisher: $InstalledTool" Green } else { Add-Line "Running repository publisher: $InstalledTool" Green }

    Push-Location $RepositoryPath
    try {
        Add-Section 'GITHUB AND BRANCH SAFETY'; Invoke-Checked 'GitHub authentication' { gh auth status }
        $Origin = (git remote get-url origin).Trim(); if ($Origin -ne 'https://github.com/ppow1/Riverview.git') { throw "RIV-PUB-0002: Unexpected origin: $Origin" }; Add-Line "Origin validated: $Origin" Green
        if ((git branch --show-current).Trim() -ne 'main') { throw 'RIV-PUB-0003: Publication requires main.' }
        Invoke-Checked 'Fetch origin' { git fetch origin main }; $LocalBefore = (git rev-parse HEAD).Trim(); $RemoteBefore = (git rev-parse origin/main).Trim()
        if ($LocalBefore -ne $RemoteBefore) { throw 'RIV-PUB-0004: Local and remote main differ.' }; Add-Line "Publication base verified: $LocalBefore" Green

        Add-Section 'SCOPE CONFIRMATION'
        $Allowed = @(
            'database/migrations/0003_relay_foundation.sql',
            'docs/operations/troubleshooting/checkpoints/RIV-WRK-0001_ACTION_POLICY.md',
            'docs/operations/troubleshooting/checkpoints/RIV-WRK-0002_LEASE_OWNERSHIP.md',
            'docs/operations/troubleshooting/checkpoints/RIV-WRK-0004_LEASE_TIMEOUT.md',
            'pyproject.toml',
            'src/riverview/relay/__init__.py',
            'src/riverview/relay/store.py',
            'src/riverview/relay_health.py',
            'tests/test_relay_contract.py',
            'tools/powershell/relay/Install-RiverviewRelayFoundation.ps1',
            'tools/powershell/synchronization/Publish-RiverviewRelayFoundation.ps1'
        )
        $Observed = @(git status --porcelain=v1 -uall | ForEach-Object { if ($_.Length -ge 4) { $_.Substring(3).Trim().Replace('\','/') } })
        foreach ($Path in $Observed) { Add-Line "CHANGE $Path"; if ($Path -notin $Allowed) { throw "RIV-PUB-0005: Unexpected working-tree path: $Path" } }
        foreach ($Path in $Allowed) { if (-not (Test-Path (Join-Path $RepositoryPath $Path))) { throw "RIV-PUB-0006: Required file missing: $Path" } }

        Add-Section 'MIGRATION AND FULL ACCEPTANCE'
        & $Python -m pip install -e '.[dev]'; if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
        $Migration = @'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed = apply_migration(Path('database/migrations/0003_relay_foundation.sql'), '0003', '0.4.0')
print('Migration 0003 applied.' if changed else 'Migration 0003 checksum verified.')
'@
        $Migration | & $Python -; if ($LASTEXITCODE -ne 0) { throw 'RIV-DB-0006: Migration 0003 validation failed.' }
        Invoke-Checked 'Ruff check' { & $Python -m ruff check src tests }; Invoke-Checked 'Pytest' { & $Python -m pytest }
        Invoke-Checked 'Python compilation' { & $Python -m compileall -q src }; Invoke-Checked 'Database health' { & $Python -m riverview.health database }
        Invoke-Checked 'Relay lifecycle acceptance' { & $Python -m riverview.relay_health }

        Add-Section 'STAGE AND VERIFY'; git add -- $Allowed; if ($LASTEXITCODE -ne 0) { throw 'Explicit staging failed.' }
        Invoke-Checked 'Staged whitespace validation' { git diff --cached --check }; $Staged = @(git diff --cached --name-only)
        foreach ($Path in $Staged) { Add-Line "STAGED $Path" Green; if ($Path -notin $Allowed) { throw "RIV-PUB-0007: Unexpected staged path: $Path" } }
        if ($Staged.Count -eq 0) { throw 'RIV-PUB-0008: Nothing staged.' }

        Add-Section 'COMMIT PUSH AND REMOTE VERIFICATION'; Invoke-Checked 'Relay foundation commit' { git commit -m $CommitMessage }; $Commit = (git rev-parse HEAD).Trim()
        Invoke-Checked 'Push main' { git push origin main }; $RemoteCommit = (((git ls-remote origin refs/heads/main).Trim()) -split '\s+')[0]
        if ($RemoteCommit -ne $Commit) { throw 'RIV-PUB-0009: Remote verification mismatch.' }
        $Remaining = @(git status --porcelain=v1 -uall); if ($Remaining.Count -gt 0) { foreach ($Line in $Remaining) { Add-Line "REMAINING $Line" Yellow }; throw 'RIV-PUB-0010: Working tree is not clean.' }

        Add-Section 'PUBLICATION RESULT'; Add-Line 'Relay foundation v0.4.0 passed and was published.' Green; Add-Line "Verified commit: $Commit" Green
        Add-Line 'Published branch: main' Green; Add-Line "Publisher version: $ToolVersion"
    } finally { Pop-Location }
    Save-Report
}
catch { Add-Section 'PUBLICATION BLOCKED'; Add-Line $_.Exception.Message Red; Add-Line 'No unsupported completion claim was made.' Yellow; if (Test-Path $RepositoryPath -PathType Container) { Save-Report }; throw }
