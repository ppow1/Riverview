# Riverview Restricted Runner Repair
# Version: 0.5.2
# Purpose: Remove the observed unused Ruff suppression and replay complete runner acceptance.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ToolVersion='0.5.2'
$ReportLines=[Collections.Generic.List[string]]::new()

function Add-Line { param([Parameter(Mandatory)][AllowEmptyString()][string]$Text,[ConsoleColor]$Color='Gray');$ReportLines.Add($Text);Write-Host $Text -ForegroundColor $Color }
function Add-Section { param([Parameter(Mandatory)][string]$Title);Add-Line '';Add-Line "=== $Title ===" Cyan }
function Invoke-Checked { param([Parameter(Mandatory)][string]$Label,[Parameter(Mandatory)][scriptblock]$Command);$Output=@(& $Command 2>&1|ForEach-Object{"$_"});foreach($Line in $Output){Add-Line $Line};if($LASTEXITCODE -ne 0){throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE."};Add-Line "$Label passed." Green }
function Save-Report {$Directory=Join-Path(Split-Path -Parent $RepositoryPath)'runtime\diagnostics\runner';New-Item -ItemType Directory -Path $Directory -Force|Out-Null;$Path=Join-Path $Directory "Restricted-Runner-Repair-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt";$Report=($ReportLines-join[Environment]::NewLine)+[Environment]::NewLine;Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline;if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){Set-Clipboard $Report}else{$Report|clip.exe};Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan;Write-Host "Durable report: $Path" -ForegroundColor Green}

try {
    Add-Section 'RIVERVIEW RUNNER REPAIR VALIDATION'
    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){throw 'Riverview Git repository not found.'}
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    if(-not(Test-Path $Python)){throw 'RIV-BLD-0006: Riverview virtual environment not found.'}
    Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    $InstalledRepair=Join-Path $RepositoryPath 'tools\powershell\relay\Repair-RiverviewRestrictedRunner.ps1'
    New-Item -ItemType Directory -Path(Split-Path -Parent $InstalledRepair)-Force|Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($InstalledRepair)){Copy-Item $PSCommandPath $InstalledRepair -Force;Add-Line "Installed reusable repair: $InstalledRepair" Green}else{Add-Line "Running repository repair: $InstalledRepair" Green}

    Add-Section 'KNOWN FAILURE RECONCILIATION'
    $Old='subprocess.Popen(  # noqa: S603 - command is constructed only by fixed adapters.'
    $New='subprocess.Popen('
    foreach($Target in @((Join-Path $RepositoryPath 'src\riverview\runner.py'),(Join-Path $RepositoryPath 'tools\powershell\relay\Install-RiverviewRestrictedRunner.ps1'))){
        if(-not(Test-Path $Target)){throw "RIV-BLD-0008: Required repair target missing: $Target"}
        $Content=Get-Content $Target -Raw
        if($Content.Contains($Old)){$Content=$Content.Replace($Old,$New);if($Target.EndsWith('runner.py')){$Content=$Content.Replace('Version: 0.5.0','Version: 0.5.2')}else{$Content=$Content.Replace('# Version: 0.5.1','# Version: 0.5.2').Replace("`$ToolVersion = '0.5.1'","`$ToolVersion = '0.5.2'")};Set-Content $Target $Content -Encoding utf8NoBOM -NoNewline;Add-Line "REPAIRED  $Target" Green}elseif($Content.Contains($New)){Add-Line "CURRENT   $Target" DarkGray}else{throw "RIV-BLD-0008: Expected Ruff suppression seam not recognized: $Target"}
    }
    $ProjectPath=Join-Path $RepositoryPath 'pyproject.toml';$Project=Get-Content $ProjectPath -Raw
    if($Project.Contains('version = "0.5.0"')){$Project=$Project.Replace('# Version: 0.5.0','# Version: 0.5.2').Replace('version = "0.5.0"','version = "0.5.2"');Set-Content $ProjectPath $Project -Encoding utf8NoBOM -NoNewline;Add-Line 'UPDATED   pyproject.toml' Green}
    $CookbookPath=Join-Path $RepositoryPath 'docs\operations\troubleshooting\checkpoints\RIV-BLD-0005_RUFF_RUNTIME_SLICE.md';$Cookbook=Get-Content $CookbookPath -Raw
    if (-not $Cookbook.Contains('`RUF100`')) {$Cookbook=$Cookbook.Replace('<!-- Version: 0.3.2 -->','<!-- Version: 0.5.2 -->');$Cookbook += "`n`nObserved runner seam: ``RUF100`` rejects an unused ``noqa`` suppression when its named rule is not enabled. Remove the suppression instead of weakening unused-directive checking.`n";Set-Content $CookbookPath $Cookbook -Encoding utf8NoBOM -NoNewline;Add-Line 'Updated RIV-BLD-0005 with observed RUF100 evidence.' Green}

    Add-Section 'MIGRATION AND FULL ACCEPTANCE'
    Push-Location $RepositoryPath
    try {
        & $Python -m pip install -e '.[dev]';if($LASTEXITCODE -ne 0){throw 'Dependency installation failed.'}
        $Migration=@'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed=apply_migration(Path('database/migrations/0004_restricted_runner.sql'),'0004','0.5.0')
print('Migration 0004 applied.' if changed else 'Migration 0004 checksum verified.')
'@
        $Migration|& $Python -
        if($LASTEXITCODE -ne 0){throw 'RIV-DB-0006: Migration 0004 validation failed.'}
        Invoke-Checked 'Ruff check' {& $Python -m ruff check src tests}
        Invoke-Checked 'Pytest' {& $Python -m pytest}
        Invoke-Checked 'Python compilation' {& $Python -m compileall -q src}
        Invoke-Checked 'Database health' {& $Python -m riverview.health database}
        Invoke-Checked 'Restricted runner live acceptance' {& $Python -m riverview.runner_health}
        Add-Section 'GIT CHANGE SUMMARY'
        foreach($Line in @(git status --short)){Add-Line $Line}
    } finally {Pop-Location}
    Add-Section 'REPAIR RESULT';Add-Line 'Unused suppression removed and the complete restricted-runner acceptance passed.' Green;Add-Line 'No commit or push was performed.' Yellow;Add-Line "Repair version: $ToolVersion";Save-Report
} catch {Add-Section 'REPAIR BLOCKED';Add-Line $_.Exception.Message Red;Add-Line 'No commit or push was performed.' Yellow;if(Test-Path $RepositoryPath -PathType Container){Save-Report};throw}
