# Riverview Foundation Acceptance and Publication Tool
# Version: 0.1.4
# Purpose: Validate, commit, push, and remotely verify the initial Riverview foundation.
# Updated: 2026-08-14

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$RepositoryPath = 'A:\Riverview\repo'
)

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ToolVersion = [version]'0.1.4'
$CanonicalToolName = 'Publish-RiverviewFoundation.ps1'
$CanonicalToolDirectory = 'tools\powershell\synchronization'
$CommitMessage = 'Initialize Riverview Kernel v0.1 diagnostics-first foundation'
$ReportLines = [System.Collections.Generic.List[string]]::new()

function Add-ReportLine {
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$Text,
        [ConsoleColor]$Color = [ConsoleColor]::Gray
    )

    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}

function Add-Section {
    param([Parameter(Mandatory)][string]$Title)
    Add-ReportLine -Text ''
    Add-ReportLine -Text "=== $Title ===" -Color Cyan
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][scriptblock]$Command
    )

    $Started = Get-Date
    $Output = @(& $Command 2>&1 | ForEach-Object { "$_" })
    $ExitCode = $LASTEXITCODE
    $Elapsed = (Get-Date) - $Started

    foreach ($Line in $Output) {
        Add-ReportLine -Text $Line
    }
    Add-ReportLine -Text "$Label exit=$ExitCode elapsed=$([math]::Round($Elapsed.TotalSeconds, 2))s"

    if ($ExitCode -ne 0) {
        throw "$Label failed with exit code $ExitCode."
    }

    return $Output
}

function Get-HeaderVersion {
    param([Parameter(Mandatory)][string]$Path)

    $Line = Get-Content -LiteralPath $Path -TotalCount 12 |
        Where-Object { $_ -match '^#\s*Version:\s*(?<Version>\d+\.\d+\.\d+)' } |
        Select-Object -First 1
    if (-not $Line) {
        throw "No PowerShell version header was found in: $Path"
    }
    return [version]([regex]::Match($Line, 'Version:\s*(?<Version>\d+\.\d+\.\d+)').Groups['Version'].Value)
}

function Install-Self {
    param([Parameter(Mandatory)][string]$Root)

    if (-not $PSCommandPath) {
        throw 'Run this publisher from a saved .ps1 file.'
    }

    $Source = (Resolve-Path -LiteralPath $PSCommandPath).Path
    $Directory = Join-Path $Root $CanonicalToolDirectory
    $Destination = Join-Path $Directory $CanonicalToolName
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null

    $SourceVersion = Get-HeaderVersion -Path $Source
    if ($SourceVersion -ne $ToolVersion) {
        throw "Publisher version mismatch: header=$SourceVersion runtime=$ToolVersion"
    }

    if ($Source -ieq $Destination) {
        Add-ReportLine -Text "Running installed publisher: $Destination" -Color Green
        return $Destination
    }

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $InstalledVersion = Get-HeaderVersion -Path $Destination
        $SourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
        $InstalledHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash
        if ($InstalledVersion -gt $SourceVersion) {
            throw "A newer publisher is installed: $Destination"
        }
        if (($InstalledVersion -eq $SourceVersion) -and ($SourceHash -ne $InstalledHash)) {
            throw "Publisher content differs at the same version: $Destination"
        }
        if ($SourceHash -eq $InstalledHash) {
            Add-ReportLine -Text "Publisher already current: $Destination" -Color Green
            return $Destination
        }
        $Backup = "$Destination.pre-$SourceVersion.bak"
        Copy-Item -LiteralPath $Destination -Destination $Backup -Force
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
        Add-ReportLine -Text "Updated publisher: $Destination" -Color Green
        return $Destination
    }

    Copy-Item -LiteralPath $Source -Destination $Destination
    Add-ReportLine -Text "Installed publisher: $Destination" -Color Green
    return $Destination
}

function Publish-Report {
    param([Parameter(Mandatory)][string]$Root)

    $WorkspaceRoot = Split-Path -Parent $Root
    $Directory = Join-Path $WorkspaceRoot 'runtime\diagnostics\publication'
    $Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $Path = Join-Path $Directory "Riverview-Publication-$Timestamp.txt"
    $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine

    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    Set-Content -LiteralPath $Path -Value $Report -Encoding utf8NoBOM -NoNewline

    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
        Set-Clipboard -Value $Report
    }
    elseif (Get-Command clip.exe -ErrorAction SilentlyContinue) {
        $Report | & clip.exe
    }

    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

function Apply-KnownFoundationRepair {
    param([Parameter(Mandatory)][string]$Root)

    $PyprojectPath = Join-Path $Root 'pyproject.toml'
    $CookbookIndexPath = Join-Path $Root 'docs\operations\troubleshooting\README.md'
    $CheckpointDirectory = Join-Path $Root 'docs\operations\troubleshooting\checkpoints'
    $CheckpointPath = Join-Path $CheckpointDirectory 'RIV-BLD-0001_HATCH_PACKAGE_SELECTION.md'
    $ImportCheckpointPath = Join-Path $CheckpointDirectory 'RIV-BLD-0002_RUFF_MAPPING_IMPORT.md'
    $ImportOrderCheckpointPath = Join-Path $CheckpointDirectory 'RIV-BLD-0003_RUFF_IMPORT_ORDER.md'
    $WhitespaceCheckpointPath = Join-Path $CheckpointDirectory 'RIV-BLD-0004_STAGED_WHITESPACE.md'
    $DiagnosticModelPath = Join-Path $Root 'src\riverview\diagnostics\models.py'

    if (-not (Test-Path -LiteralPath $PyprojectPath -PathType Leaf)) {
        throw "RIV-BLD-0001: pyproject.toml was not found: $PyprojectPath"
    }

    $Pyproject = Get-Content -LiteralPath $PyprojectPath -Raw
    if ($Pyproject -notmatch '(?m)^\[tool\.hatch\.build\.targets\.wheel\]\s*$') {
        if ($Pyproject -notmatch '(?m)^# Version: 0\.1\.0\s*$') {
            throw 'RIV-BLD-0001: pyproject.toml has an unexpected version or shape; refusing automatic repair.'
        }

        $Pyproject = $Pyproject -replace '(?m)^# Version: 0\.1\.0\s*$', '# Version: 0.1.1'
        $Pyproject = $Pyproject.TrimEnd() + @'


[tool.hatch.build.targets.wheel]
packages = ["src/riverview"]
'@
        Set-Content -LiteralPath $PyprojectPath -Value ($Pyproject + "`n") -Encoding utf8NoBOM -NoNewline
        Add-ReportLine -Text 'RIV-BLD-0001 repaired: declared src/riverview as the Hatch wheel package.' -Color Green
    }
    elseif ($Pyproject -notmatch '(?m)^packages\s*=\s*\["src/riverview"\]\s*$') {
        throw 'RIV-BLD-0001: Hatch wheel configuration exists but does not match the approved package path.'
    }
    else {
        Add-ReportLine -Text 'RIV-BLD-0001 repair already present in pyproject.toml.' -Color Green
    }

    if (-not (Test-Path -LiteralPath $CookbookIndexPath -PathType Leaf)) {
        throw "RIV-BLD-0001: Cookbook index was not found: $CookbookIndexPath"
    }

    $CookbookIndex = Get-Content -LiteralPath $CookbookIndexPath -Raw
    if ($CookbookIndex -notmatch '(?m)^- `RIV-BLD-\*`') {
        $CookbookIndex = $CookbookIndex -replace '<!-- Version: 0\.1\.0 -->', '<!-- Version: 0.1.1 -->'
        $BuildNamespaceLine = '- `RIV-BLD-*` — build, packaging, and dependency-environment failures' + [Environment]::NewLine
        $CookbookIndex = $CookbookIndex -replace '(?m)(^- `RIV-DB-\*`[^\r\n]*\r?\n)', ('${1}' + $BuildNamespaceLine)
        Set-Content -LiteralPath $CookbookIndexPath -Value $CookbookIndex -Encoding utf8NoBOM -NoNewline
        Add-ReportLine -Text 'Added the RIV-BLD checkpoint namespace to the Cookbook index.' -Color Green
    }

    $CheckpointContent = @'
<!-- Version: 0.1.0 -->
# RIV-BLD-0001: Hatch Cannot Select the Riverview Package

Status: Validated from the initial foundation publication attempt on 2026-08-14.

## Detection

Editable installation fails during Hatch metadata generation with a message stating that no directory matches `riverview_kernel` or that Hatch cannot determine which files to ship.

## Cause

The distribution is named `riverview-kernel`, while the import package is `src/riverview`. Hatch's default package-selection heuristic cannot safely infer that mapping.

## Distinguishing probe

Inspect `pyproject.toml` for:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/riverview"]
```

If the table is absent and `src/riverview/__init__.py` exists, this failure class applies. If the table exists with another path, stop rather than replacing it automatically.

## Smallest safe repair

Add the exact wheel package-selection table above. Do not rename the Python package or distribution merely to satisfy inference.

## Verification

1. Run editable development dependency installation.
2. Run `python -m ruff check src tests`.
3. Run `python -m pytest`.
4. Run `python -m compileall -q src`.

## Escalation

Escalate if Hatch still fails after the explicit package declaration, if another build backend is active, or if more than one distributable package is introduced.
'@

    New-Item -ItemType Directory -Path $CheckpointDirectory -Force | Out-Null
    if (Test-Path -LiteralPath $CheckpointPath -PathType Leaf) {
        $ExistingCheckpoint = (Get-Content -LiteralPath $CheckpointPath -Raw) -replace "`r`n", "`n"
        $ExpectedCheckpoint = ($CheckpointContent.TrimStart("`r", "`n") + "`n") -replace "`r`n", "`n"
        if ($ExistingCheckpoint -ne $ExpectedCheckpoint) {
            throw "RIV-BLD-0001: Existing Cookbook checkpoint differs: $CheckpointPath"
        }
    }
    else {
        Set-Content -LiteralPath $CheckpointPath -Value ($CheckpointContent.TrimStart("`r", "`n") + "`n") -Encoding utf8NoBOM -NoNewline
        Add-ReportLine -Text 'Created Cookbook checkpoint RIV-BLD-0001 from the observed failure.' -Color Green
    }

    if (-not (Test-Path -LiteralPath $DiagnosticModelPath -PathType Leaf)) {
        throw "RIV-BLD-0002: Diagnostic model was not found: $DiagnosticModelPath"
    }

    $DiagnosticModel = Get-Content -LiteralPath $DiagnosticModelPath -Raw
    $OldImports = "from types import MappingProxyType`r`nfrom typing import Any, Mapping"
    $OldImportsLf = "from types import MappingProxyType`nfrom typing import Any, Mapping"
    $NewImports = "from collections.abc import Mapping`r`nfrom types import MappingProxyType`r`nfrom typing import Any"

    if ($DiagnosticModel -match '(?m)^from typing import Any, Mapping\s*$') {
        if ($DiagnosticModel.Contains($OldImports)) {
            $DiagnosticModel = $DiagnosticModel.Replace($OldImports, $NewImports)
        }
        elseif ($DiagnosticModel.Contains($OldImportsLf)) {
            $DiagnosticModel = $DiagnosticModel.Replace($OldImportsLf, ($NewImports -replace "`r`n", "`n"))
        }
        else {
            throw 'RIV-BLD-0002: Mapping import has an unexpected surrounding shape; refusing automatic repair.'
        }
        $DiagnosticModel = $DiagnosticModel -replace 'Version: 0\.1\.0', 'Version: 0.1.1'
        Set-Content -LiteralPath $DiagnosticModelPath -Value $DiagnosticModel -Encoding utf8NoBOM -NoNewline
        Add-ReportLine -Text 'RIV-BLD-0002 repaired: Mapping now imports from collections.abc.' -Color Green
    }
    elseif ($DiagnosticModel -match '(?m)^from collections\.abc import Mapping\s*$') {
        Add-ReportLine -Text 'RIV-BLD-0002 repair already present in the diagnostic model.' -Color Green
    }
    else {
        throw 'RIV-BLD-0002: Neither the expected old nor repaired Mapping import was found.'
    }

    $ImportCheckpointContent = @'
<!-- Version: 0.1.0 -->
# RIV-BLD-0002: Ruff Rejects Mapping Imported from typing

Status: Validated from the second initial-foundation publication attempt on 2026-08-14.

## Detection

Ruff reports `UP035` in `src/riverview/diagnostics/models.py` and directs that `Mapping` be imported from `collections.abc`.

## Cause

The diagnostic model imported `Mapping` from `typing`. Under the configured Python 3.12 target, Ruff requires the modern runtime collection interface from `collections.abc`.

## Distinguishing probe

Run:

```text
python -m ruff check src tests
```

This failure applies only when `UP035` identifies `Mapping` on the diagnostic model import line.

## Smallest safe repair

Import `Mapping` from `collections.abc` while retaining `Any` from `typing`. Do not run an unrestricted repository-wide automatic rewrite.

## Verification

1. Run Ruff against `src` and `tests`.
2. Run pytest.
3. Compile `src`.

## Escalation

Escalate if Ruff reports another rule, another file, or additional import restructuring after this bounded change.
'@

    if (Test-Path -LiteralPath $ImportCheckpointPath -PathType Leaf) {
        $ExistingImportCheckpoint = (Get-Content -LiteralPath $ImportCheckpointPath -Raw) -replace "`r`n", "`n"
        $ExpectedImportCheckpoint = ($ImportCheckpointContent.TrimStart("`r", "`n") + "`n") -replace "`r`n", "`n"
        if ($ExistingImportCheckpoint -ne $ExpectedImportCheckpoint) {
            throw "RIV-BLD-0002: Existing Cookbook checkpoint differs: $ImportCheckpointPath"
        }
    }
    else {
        Set-Content -LiteralPath $ImportCheckpointPath -Value ($ImportCheckpointContent.TrimStart("`r", "`n") + "`n") -Encoding utf8NoBOM -NoNewline
        Add-ReportLine -Text 'Created Cookbook checkpoint RIV-BLD-0002 from the observed Ruff failure.' -Color Green
    }

    $DiagnosticModel = Get-Content -LiteralPath $DiagnosticModelPath -Raw
    $UnsortedImportsPattern = '(?ms)^from __future__ import annotations\r?\n\r?\nfrom dataclasses import dataclass, field\r?\nfrom datetime import UTC, datetime\r?\nfrom enum import StrEnum\r?\nfrom collections\.abc import Mapping\r?\nfrom types import MappingProxyType\r?\nfrom typing import Any\r?\nfrom uuid import UUID, uuid4'
    $SortedImports = @'
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4
'@

    if ($DiagnosticModel -match $UnsortedImportsPattern) {
        $DiagnosticModel = [regex]::Replace(
            $DiagnosticModel,
            $UnsortedImportsPattern,
            $SortedImports.TrimEnd(),
            [System.Text.RegularExpressions.RegexOptions]::Multiline
        )
        $DiagnosticModel = $DiagnosticModel -replace 'Version: 0\.1\.1', 'Version: 0.1.2'
        Set-Content -LiteralPath $DiagnosticModelPath -Value $DiagnosticModel -Encoding utf8NoBOM -NoNewline
        Add-ReportLine -Text 'RIV-BLD-0003 repaired: standard-library imports are in Ruff order.' -Color Green
    }
    elseif ($DiagnosticModel -match '(?ms)^from __future__ import annotations\r?\n\r?\nfrom collections\.abc import Mapping\r?\nfrom dataclasses import dataclass, field') {
        Add-ReportLine -Text 'RIV-BLD-0003 repair already present in the diagnostic model.' -Color Green
    }
    else {
        throw 'RIV-BLD-0003: Diagnostic import block has an unexpected shape; refusing automatic repair.'
    }

    $ImportOrderCheckpointContent = @'
<!-- Version: 0.1.0 -->
# RIV-BLD-0003: Ruff Rejects Diagnostic Import Order

Status: Validated from the third initial-foundation publication attempt on 2026-08-14.

## Detection

Ruff reports `I001` for the import block in `src/riverview/diagnostics/models.py` after `Mapping` has been moved to `collections.abc`.

## Cause

The bounded `RIV-BLD-0002` repair placed the new import after other standard-library imports rather than in Ruff's deterministic sorted order.

## Distinguishing probe

Run `python -m ruff check src tests`. This checkpoint applies when `I001` identifies the diagnostic model import block and no unrelated file.

## Smallest safe repair

Move `from collections.abc import Mapping` to the beginning of the standard-library import group immediately after the future import separator.

## Verification

1. Run Ruff against `src` and `tests`.
2. Run pytest.
3. Compile `src`.

## Escalation

Escalate if another file or another formatting rule remains after the exact reorder.
'@

    if (Test-Path -LiteralPath $ImportOrderCheckpointPath -PathType Leaf) {
        $ExistingOrderCheckpoint = (Get-Content -LiteralPath $ImportOrderCheckpointPath -Raw) -replace "`r`n", "`n"
        $ExpectedOrderCheckpoint = ($ImportOrderCheckpointContent.TrimStart("`r", "`n") + "`n") -replace "`r`n", "`n"
        if ($ExistingOrderCheckpoint -ne $ExpectedOrderCheckpoint) {
            throw "RIV-BLD-0003: Existing Cookbook checkpoint differs: $ImportOrderCheckpointPath"
        }
    }
    else {
        Set-Content -LiteralPath $ImportOrderCheckpointPath -Value ($ImportOrderCheckpointContent.TrimStart("`r", "`n") + "`n") -Encoding utf8NoBOM -NoNewline
        Add-ReportLine -Text 'Created Cookbook checkpoint RIV-BLD-0003 from the observed import-order failure.' -Color Green
    }

    $CookbookIndex = Get-Content -LiteralPath $CookbookIndexPath -Raw
    $CookbookLines = @($CookbookIndex -split "`n" | ForEach-Object { $_.TrimEnd() })
    $NormalizedCookbookIndex = ($CookbookLines -join "`n").TrimEnd() + "`n"
    if ($NormalizedCookbookIndex -ne $CookbookIndex) {
        $NormalizedCookbookIndex = $NormalizedCookbookIndex -replace '<!-- Version: 0\.1\.1 -->', '<!-- Version: 0.1.2 -->'
        Set-Content -LiteralPath $CookbookIndexPath -Value $NormalizedCookbookIndex -Encoding utf8NoBOM -NoNewline
        Add-ReportLine -Text 'RIV-BLD-0004 repaired: removed trailing whitespace from the Cookbook index.' -Color Green
    }
    else {
        Add-ReportLine -Text 'RIV-BLD-0004 repair already present in the Cookbook index.' -Color Green
    }

    $WhitespaceCheckpointContent = @'
<!-- Version: 0.1.0 -->
# RIV-BLD-0004: Staged Cookbook Whitespace Rejected

Status: Validated from the fourth initial-foundation publication attempt on 2026-08-14.

## Detection

`git diff --cached --check` reports trailing whitespace in `docs/operations/troubleshooting/README.md` and returns a nonzero exit code.

## Cause

The programmatic insertion of the `RIV-BLD-*` namespace preserved an unwanted whitespace character at the line boundary.

## Distinguishing probe

Run `git diff --cached --check`. This checkpoint applies when the only reported defect is trailing whitespace in the Cookbook index.

## Smallest safe repair

Remove trailing spaces and tabs from the Cookbook index without changing its substantive text, then restage the exact publication paths.

## Verification

1. Rerun `git diff --cached --check`.
2. Confirm the command exits successfully with no output.
3. Continue commit and remote verification gates.

## Escalation

Escalate when whitespace errors affect other files or when normalization would alter substantive content.
'@

    if (Test-Path -LiteralPath $WhitespaceCheckpointPath -PathType Leaf) {
        $ExistingWhitespaceCheckpoint = (Get-Content -LiteralPath $WhitespaceCheckpointPath -Raw) -replace "`r`n", "`n"
        $ExpectedWhitespaceCheckpoint = ($WhitespaceCheckpointContent.TrimStart("`r", "`n") + "`n") -replace "`r`n", "`n"
        if ($ExistingWhitespaceCheckpoint -ne $ExpectedWhitespaceCheckpoint) {
            throw "RIV-BLD-0004: Existing Cookbook checkpoint differs: $WhitespaceCheckpointPath"
        }
    }
    else {
        Set-Content -LiteralPath $WhitespaceCheckpointPath -Value ($WhitespaceCheckpointContent.TrimStart("`r", "`n") + "`n") -Encoding utf8NoBOM -NoNewline
        Add-ReportLine -Text 'Created Cookbook checkpoint RIV-BLD-0004 from the staged-whitespace failure.' -Color Green
    }
}

try {
    Add-Section -Title 'PUBLICATION VALIDATION'

    foreach ($CommandName in @('git', 'gh', 'python')) {
        if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
            throw "$CommandName was not found on PATH."
        }
        Add-ReportLine -Text "Found prerequisite: $CommandName" -Color Green
    }

    if (-not (Test-Path -LiteralPath $RepositoryPath -PathType Container)) {
        throw "Repository not found: $RepositoryPath"
    }
    $RepositoryPath = (Resolve-Path -LiteralPath $RepositoryPath).Path
    if (-not (Test-Path -LiteralPath (Join-Path $RepositoryPath '.git') -PathType Container)) {
        throw "Git metadata not found: $RepositoryPath"
    }
    Set-Location -LiteralPath $RepositoryPath
    Add-ReportLine -Text "Repository validated: $RepositoryPath" -Color Green

    Add-Section -Title 'SELF-INSTALLATION'
    $InstalledTool = Install-Self -Root $RepositoryPath

    Add-Section -Title 'GITHUB AUTHENTICATION'
    Invoke-CheckedCommand -Label 'GitHub CLI version' -Command { gh --version } | Out-Null
    Invoke-CheckedCommand -Label 'GitHub authentication' -Command { gh auth status } | Out-Null
    Invoke-CheckedCommand -Label 'GitHub Git credential configuration' -Command { gh auth setup-git } | Out-Null

    $RemoteUrl = (& git remote get-url origin).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to resolve the origin remote.'
    }
    if ($RemoteUrl -notmatch 'github\.com[/:]ppow1/Riverview(?:\.git)?$') {
        throw "Unexpected origin remote: $RemoteUrl"
    }
    Add-ReportLine -Text "Origin validated: $RemoteUrl" -Color Green

    & git rev-parse --verify HEAD *> $null
    if ($LASTEXITCODE -eq 0) {
        throw 'The repository already has a commit. This initial-foundation publisher will not run again.'
    }

    $GitUserName = ("$(& git config user.name)").Trim()
    $GitUserEmail = ("$(& git config user.email)").Trim()
    if (-not $GitUserName -or -not $GitUserEmail) {
        throw 'Git user.name and user.email must be configured before the initial commit.'
    }
    Add-ReportLine -Text "Git author identity validated: $GitUserName <$GitUserEmail>" -Color Green

    Add-Section -Title 'KNOWN FAILURE RECONCILIATION'
    Apply-KnownFoundationRepair -Root $RepositoryPath

    Add-Section -Title 'DEPENDENCY ENVIRONMENT'
    $VirtualEnvironment = Join-Path $RepositoryPath '.venv'
    $PythonExecutable = Join-Path $VirtualEnvironment 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
        Invoke-CheckedCommand -Label 'Virtual environment creation' -Command {
            python -m venv $VirtualEnvironment
        } | Out-Null
    }
    else {
        Add-ReportLine -Text "Using existing virtual environment: $VirtualEnvironment" -Color Green
    }

    Invoke-CheckedCommand -Label 'Development dependency installation' -Command {
        & $PythonExecutable -m pip install --disable-pip-version-check -e '.[dev]'
    } | Out-Null

    Add-Section -Title 'ACCEPTANCE CHECKS'
    Invoke-CheckedCommand -Label 'Ruff check' -Command {
        & $PythonExecutable -m ruff check src tests
    } | Out-Null
    Invoke-CheckedCommand -Label 'Pytest' -Command {
        & $PythonExecutable -m pytest
    } | Out-Null
    Invoke-CheckedCommand -Label 'Python compilation' -Command {
        & $PythonExecutable -m compileall -q src
    } | Out-Null

    Add-Section -Title 'SCOPE CONFIRMATION'
    $ExpectedRoots = @(
        '.gitignore',
        'AI_HINTS.md',
        'README.md',
        'database/',
        'docs/',
        'pyproject.toml',
        'src/',
        'tests/',
        'tools/'
    )
    $StatusBeforeStage = @(& git status --short 2>&1 | ForEach-Object { "$_" })
    foreach ($Line in $StatusBeforeStage) {
        Add-ReportLine -Text $Line
    }

    $Unexpected = @(
        foreach ($Line in $StatusBeforeStage) {
            $Path = $Line.Substring(3).Trim('"') -replace '\\', '/'
            $MatchesExpected = $false
            foreach ($Expected in $ExpectedRoots) {
                if (($Expected.EndsWith('/') -and $Path.StartsWith($Expected)) -or ($Path -eq $Expected.TrimEnd('/'))) {
                    $MatchesExpected = $true
                    break
                }
            }
            if (-not $MatchesExpected) { $Path }
        }
    )
    if ($Unexpected.Count -gt 0) {
        throw "Unexpected worktree paths detected: $($Unexpected -join ', ')"
    }

    Add-Section -Title 'STAGE AND VERIFY'
    & git add -- .gitignore AI_HINTS.md README.md database docs pyproject.toml src tests tools
    if ($LASTEXITCODE -ne 0) {
        throw 'Git staging failed.'
    }
    Invoke-CheckedCommand -Label 'Staged whitespace validation' -Command {
        git diff --cached --check
    } | Out-Null

    $StagedFiles = @(& git diff --cached --name-only | ForEach-Object { "$_" })
    if ($StagedFiles.Count -eq 0) {
        throw 'No staged foundation files were found.'
    }
    foreach ($Path in $StagedFiles) {
        Add-ReportLine -Text "STAGED $Path" -Color Green
    }

    Add-Section -Title 'COMMIT AND PUSH'
    Invoke-CheckedCommand -Label 'Foundation commit' -Command {
        git commit -m $CommitMessage
    } | Out-Null
    $LocalSha = (& git rev-parse HEAD).Trim()
    Add-ReportLine -Text "Local commit: $LocalSha" -Color Green

    Invoke-CheckedCommand -Label 'Push main' -Command {
        git push -u origin main
    } | Out-Null

    $RemoteLine = (& git ls-remote origin refs/heads/main).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $RemoteLine) {
        throw 'Remote main verification returned no commit.'
    }
    $RemoteSha = ($RemoteLine -split '\s+')[0]
    if ($RemoteSha -ne $LocalSha) {
        throw "Remote verification mismatch: local=$LocalSha remote=$RemoteSha"
    }

    Add-Section -Title 'PUBLICATION RESULT'
    Add-ReportLine -Text 'Foundation acceptance passed.' -Color Green
    Add-ReportLine -Text "Published branch: main" -Color Green
    Add-ReportLine -Text "Verified commit: $RemoteSha" -Color Green
    Add-ReportLine -Text "Publisher: $InstalledTool"
    Add-ReportLine -Text "Publisher version: $ToolVersion"
    Add-ReportLine -Text 'No pull request was created because this is the repository initial commit.'

    Publish-Report -Root $RepositoryPath
}
catch {
    Add-Section -Title 'PUBLICATION BLOCKED'
    Add-ReportLine -Text $_.Exception.Message -Color Red
    Add-ReportLine -Text 'No unsupported completion claim was made. Inspect the report before retrying.' -Color Yellow
    if (Test-Path -LiteralPath $RepositoryPath -PathType Container) {
        Publish-Report -Root $RepositoryPath
    }
    throw
}
