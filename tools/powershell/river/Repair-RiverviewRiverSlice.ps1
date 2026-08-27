# Riverview River Runtime Slice Repair
# Version: 0.2.1
# Purpose: Repair the observed Ruff import and intentional-naive-datetime test failures.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath = 'A:\Riverview\standalone')

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ToolVersion = '0.2.1'
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
    if ($LASTEXITCODE -ne 0) { throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE." }
    Add-Line "$Label passed." Green
}

function Save-Report {
    $Directory = Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\river'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path = Join-Path $Directory "River-Slice-Repair-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    Set-Content -LiteralPath $Path -Value $Report -Encoding utf8NoBOM -NoNewline
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard $Report }
    else { $Report | clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW REPAIR VALIDATION'
    $RepositoryPath = (Resolve-Path $RepositoryPath).Path
    if (-not (Test-Path (Join-Path $RepositoryPath '.git'))) { throw 'Riverview Git repository not found.' }
    $Python = Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    if (-not (Test-Path $Python)) { throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    Add-Line "Repository validated: $RepositoryPath" Green

    Add-Section 'SELF-INSTALLATION'
    if (-not $PSCommandPath) { throw 'Run this repair from a saved .ps1 file.' }
    $InstalledTool = Join-Path $RepositoryPath 'tools\powershell\river\Repair-RiverviewRiverSlice.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $InstalledTool) -Force | Out-Null
    if ([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($InstalledTool)) {
        Copy-Item -LiteralPath $PSCommandPath -Destination $InstalledTool -Force
        Add-Line "Installed reusable repair: $InstalledTool" Green
    }
    else { Add-Line "Running repository repair: $InstalledTool" Green }

    Add-Section 'KNOWN FAILURE RECONCILIATION'
    $ConnectionPath = Join-Path $RepositoryPath 'src\riverview\database\connection.py'
    $TestPath = Join-Path $RepositoryPath 'tests\test_river_event.py'
    foreach ($Required in @($ConnectionPath, $TestPath)) {
        if (-not (Test-Path $Required -PathType Leaf)) { throw "RIV-BLD-0008: Required file missing: $Required" }
    }

    $Connection = Get-Content -LiteralPath $ConnectionPath -Raw
    $OldImports = "from contextlib import contextmanager`nfrom dataclasses import dataclass`nfrom pathlib import Path`nfrom typing import Any, Iterator"
    $NewImports = "from collections.abc import Iterator`nfrom contextlib import contextmanager`nfrom dataclasses import dataclass`nfrom pathlib import Path`nfrom typing import Any"
    if ($Connection.Contains($OldImports)) {
        Copy-Item $ConnectionPath "$ConnectionPath.pre-$ToolVersion.bak" -Force
        $Connection = $Connection.Replace($OldImports, $NewImports).Replace('Version: 0.2.0', 'Version: 0.2.1')
        Set-Content -LiteralPath $ConnectionPath -Value $Connection -Encoding utf8NoBOM -NoNewline
        Add-Line 'RIV-BLD-0005A repaired: Iterator imports from collections.abc.' Green
    }
    elseif ($Connection.Contains('from collections.abc import Iterator')) {
        Add-Line 'RIV-BLD-0005A repair already present.' DarkGray
    }
    else { throw 'RIV-BLD-0008: Expected connection import block was not recognized.' }

    $Tests = Get-Content -LiteralPath $TestPath -Raw
    $OldDatetime = 'occurred_at=datetime(2026, 8, 14),'
    $NewDatetime = 'occurred_at=datetime(2026, 8, 14, tzinfo=UTC).replace(tzinfo=None),'
    if ($Tests.Contains($OldDatetime)) {
        Copy-Item $TestPath "$TestPath.pre-$ToolVersion.bak" -Force
        $Tests = $Tests.Replace($OldDatetime, $NewDatetime).Replace('Version: 0.2.0', 'Version: 0.2.1')
        Set-Content -LiteralPath $TestPath -Value $Tests -Encoding utf8NoBOM -NoNewline
        Add-Line 'RIV-BLD-0005B repaired: the intentional naive datetime is constructed explicitly.' Green
    }
    elseif ($Tests.Contains($NewDatetime)) {
        Add-Line 'RIV-BLD-0005B repair already present.' DarkGray
    }
    else { throw 'RIV-BLD-0008: Expected timezone test expression was not recognized.' }

    $CookbookPath = Join-Path $RepositoryPath 'docs\operations\troubleshooting\checkpoints\RIV-BLD-0005_RUFF_RUNTIME_SLICE.md'
    $Cookbook = @'
<!-- Version: 0.2.1 -->
# RIV-BLD-0005 — Runtime-slice static acceptance failed

Trigger: Ruff rejects River runtime source or tests before live acceptance.

Observed failure classes:

1. `UP035`: an abstract collection type is imported from `typing` instead of `collections.abc`.
2. `DTZ001`: a test constructs a timezone-naive datetime without explicitly showing that intent.
3. Import sorting: a corrected import is placed outside Ruff's standard-library order.
4. Formatting: an automated or manual repair leaves a source file outside repository formatting rules.

Diagnostic procedure: Run `.venv\Scripts\python.exe -m ruff check src tests` and use the exact rule, file, and line. Do not proceed to database acceptance while Ruff fails.

Smallest repair: Move abstract collection imports to `collections.abc`; construct intentional naive test values from a timezone-aware value and remove the timezone explicitly. Change no runtime behavior unrelated to the reported rule.

Verification: Require Ruff, Pytest, Python compilation, database health, and River event smoke acceptance to all pass in that order.

Applicability: Riverview Kernel v0.2.x River runtime slice.
'@
    New-Item -ItemType Directory -Path (Split-Path -Parent $CookbookPath) -Force | Out-Null
    Set-Content -LiteralPath $CookbookPath -Value $Cookbook -Encoding utf8NoBOM -NoNewline
    Add-Line 'Created Cookbook checkpoint RIV-BLD-0005 from observed evidence.' Green

    Add-Section 'FULL ACCEPTANCE REPLAY'
    Push-Location $RepositoryPath
    try {
        Invoke-Checked 'Ruff check' { & $Python -m ruff check src tests }
        Invoke-Checked 'Pytest' { & $Python -m pytest }
        Invoke-Checked 'Python compilation' { & $Python -m compileall -q src }
        Invoke-Checked 'Database health' { & $Python -m riverview.health database }
        Invoke-Checked 'River event smoke test' { & $Python -m riverview.health event }

        Add-Section 'GIT CHANGE SUMMARY'
        $Status = @(git status --short)
        foreach ($Line in $Status) { Add-Line $Line }
        if ($LASTEXITCODE -ne 0) { throw 'Git status failed.' }
    }
    finally { Pop-Location }

    Add-Section 'REPAIR RESULT'
    Add-Line 'Observed static failures repaired; full River acceptance passed.' Green
    Add-Line 'No commit or push was performed.' Yellow
    Add-Line "Repair version: $ToolVersion"
    Save-Report
}
catch {
    Add-Section 'REPAIR BLOCKED'
    Add-Line $_.Exception.Message Red
    Add-Line 'No commit or push was performed.' Yellow
    if (Test-Path $RepositoryPath -PathType Container) { Save-Report }
    throw
}
