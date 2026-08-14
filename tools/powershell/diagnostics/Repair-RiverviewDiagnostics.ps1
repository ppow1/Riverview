# Riverview Diagnostic Persistence Repair
# Version: 0.3.2
# Purpose: Correct the Python 3.14 context-manager type import and preserve the reusable installer.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath = 'A:\Riverview\repo')

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ToolVersion = '0.3.2'
$ReportLines = [Collections.Generic.List[string]]::new()

function Add-Line {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text, [ConsoleColor]$Color = 'Gray')
    $ReportLines.Add($Text); Write-Host $Text -ForegroundColor $Color
}
function Add-Section { param([Parameter(Mandatory)][string]$Title); Add-Line ''; Add-Line "=== $Title ===" Cyan }
function Invoke-Checked {
    param([Parameter(Mandatory)][string]$Label, [Parameter(Mandatory)][scriptblock]$Command)
    $Output = @(& $Command 2>&1 | ForEach-Object { "$_" }); foreach ($Line in $Output) { Add-Line $Line }
    if ($LASTEXITCODE -ne 0) { throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE." }
    Add-Line "$Label passed." Green
}
function Save-Report {
    $Directory = Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\diagnostic-engine'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path = Join-Path $Directory "Diagnostic-Repair-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard $Report } else { $Report | clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW DIAGNOSTIC REPAIR VALIDATION'
    $RepositoryPath = (Resolve-Path $RepositoryPath).Path
    if (-not (Test-Path (Join-Path $RepositoryPath '.git'))) { throw 'Riverview Git repository not found.' }
    $Python = Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    if (-not (Test-Path $Python)) { throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    $InstalledRepair = Join-Path $RepositoryPath 'tools\powershell\diagnostics\Repair-RiverviewDiagnostics.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $InstalledRepair) -Force | Out-Null
    if ([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($InstalledRepair)) {
        Copy-Item $PSCommandPath $InstalledRepair -Force; Add-Line "Updated reusable repair: $InstalledRepair" Green
    } else { Add-Line "Running repository repair: $InstalledRepair" Green }

    Add-Section 'KNOWN FAILURE RECONCILIATION'
    $OldImport = 'from collections.abc import Callable, ContextManager'
    $NewImports = "from collections.abc import Callable`nfrom contextlib import AbstractContextManager"
    $OldType = 'Callable[..., ContextManager[Any]]'
    $NewType = 'Callable[..., AbstractContextManager[Any]]'
    $Targets = @(
        (Join-Path $RepositoryPath 'src\riverview\diagnostics\store.py'),
        (Join-Path $RepositoryPath 'tools\powershell\diagnostics\Install-RiverviewDiagnostics.ps1')
    )
    foreach ($Target in $Targets) {
        if (-not (Test-Path $Target)) { throw "RIV-BLD-0008: Required repair target missing: $Target" }
        $Content = Get-Content $Target -Raw
        if ($Content.Contains($OldImport) -and $Content.Contains($OldType)) {
            Copy-Item $Target "$Target.pre-$ToolVersion.bak" -Force
            $Content = $Content.Replace($OldImport, $NewImports).Replace($OldType, $NewType)
            if ($Target.EndsWith('store.py')) { $Content = $Content.Replace('Version: 0.3.1', 'Version: 0.3.2') }
            if ($Target.EndsWith('Install-RiverviewDiagnostics.ps1')) {
                $Content = $Content.Replace('# Version: 0.3.1', '# Version: 0.3.2').Replace("`$ToolVersion = '0.3.1'", "`$ToolVersion = '0.3.2'")
            }
            Set-Content $Target $Content -Encoding utf8NoBOM -NoNewline
            Add-Line "REPAIRED  $Target" Green
        }
        elseif ($Content.Contains('from contextlib import AbstractContextManager') -and $Content.Contains($NewType)) {
            Add-Line "CURRENT   $Target" DarkGray
        }
        else { throw "RIV-BLD-0008: Expected context-manager type boundary not recognized in $Target" }
    }

    $ProjectPath = Join-Path $RepositoryPath 'pyproject.toml'
    $Project = Get-Content $ProjectPath -Raw
    if ($Project.Contains('version = "0.3.1"')) {
        $Project = $Project.Replace('# Version: 0.3.1', '# Version: 0.3.2').Replace('version = "0.3.1"', 'version = "0.3.2"')
        Set-Content $ProjectPath $Project -Encoding utf8NoBOM -NoNewline
        Add-Line 'UPDATED   pyproject.toml' Green
    }

    $CookbookPath = Join-Path $RepositoryPath 'docs\operations\troubleshooting\checkpoints\RIV-BLD-0005_RUFF_RUNTIME_SLICE.md'
    $Cookbook = Get-Content $CookbookPath -Raw
    if (-not $Cookbook.Contains('Python 3.14 does not expose `ContextManager`')) {
        $Cookbook = $Cookbook.Replace('<!-- Version: 0.3.1 -->', '<!-- Version: 0.3.2 -->')
        $Cookbook += "`n`nObserved compatibility seam: Python 3.14 does not expose ``ContextManager`` from ``collections.abc``. Use ``contextlib.AbstractContextManager`` for the runtime annotation and retain ``Callable`` from ``collections.abc``.`n"
        Set-Content $CookbookPath $Cookbook -Encoding utf8NoBOM -NoNewline
        Add-Line 'Updated RIV-BLD-0005 with the Python 3.14 collection-time failure.' Green
    }

    Add-Section 'FULL ACCEPTANCE REPLAY'
    Push-Location $RepositoryPath
    try {
        & $Python -m pip install -e '.[dev]'; if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
        Invoke-Checked 'Ruff check' { & $Python -m ruff check src tests }
        Invoke-Checked 'Pytest' { & $Python -m pytest }
        Invoke-Checked 'Python compilation' { & $Python -m compileall -q src }
        Invoke-Checked 'Database health' { & $Python -m riverview.health database }
        Invoke-Checked 'Diagnostic database persistence' { & $Python -m riverview.diagnostic_health database }
        Invoke-Checked 'Induced diagnostic fallback' { & $Python -m riverview.diagnostic_health fallback }
        Add-Section 'GIT CHANGE SUMMARY'; foreach ($Line in @(git status --short)) { Add-Line $Line }
    } finally { Pop-Location }

    Add-Section 'REPAIR RESULT'
    Add-Line 'Python 3.14 import compatibility and the complete diagnostic acceptance chain passed.' Green
    Add-Line 'No commit or push was performed.' Yellow
    Add-Line "Repair version: $ToolVersion"; Save-Report
}
catch {
    Add-Section 'REPAIR BLOCKED'; Add-Line $_.Exception.Message Red
    Add-Line 'No commit or push was performed.' Yellow
    if (Test-Path $RepositoryPath -PathType Container) { Save-Report }; throw
}
