# Riverview Steward Status Publisher
# Version: 0.7.1
# Purpose: Revalidate and publish the exact read-only Steward Status slice.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ToolVersion='0.7.1'
$ExpectedBase='05fce2686f207734a689bec84f21898086ac6fdf'
$ReportLines=[Collections.Generic.List[string]]::new()

function Add-Line {param([Parameter(Mandatory)][AllowEmptyString()][string]$Text,[ConsoleColor]$Color='Gray');$ReportLines.Add($Text);Write-Host $Text -ForegroundColor $Color}
function Add-Section {param([Parameter(Mandatory)][string]$Title);Add-Line '';Add-Line "=== $Title ===" Cyan}
function Invoke-Checked {param([string]$Label,[scriptblock]$Command);$global:LASTEXITCODE=0;$Output=@(& $Command 2>&1|ForEach-Object{"$_"});foreach($Line in $Output){Add-Line $Line};if($LASTEXITCODE -ne 0){throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE."};Add-Line "$Label passed." Green}
function Save-Report {$Directory=Join-Path(Split-Path -Parent $RepositoryPath)'runtime\diagnostics\publication';New-Item -ItemType Directory -Path $Directory -Force|Out-Null;$Path=Join-Path $Directory "Riverview-Steward-Status-Publication-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt";$Report=($ReportLines-join[Environment]::NewLine)+[Environment]::NewLine;Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline;if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){Set-Clipboard $Report}else{$Report|clip.exe};Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan;Write-Host "Durable report: $Path" -ForegroundColor Green}

$AllowedPaths=@(
 'database/migrations/0006_steward_status.sql',
 'docs/operations/troubleshooting/README.md',
 'docs/operations/troubleshooting/checkpoints/RIV-UI-0001_NOT_FOUND.md',
 'docs/operations/troubleshooting/checkpoints/RIV-UI-0002_PROJECTION_FAILURE.md',
 'docs/operations/troubleshooting/checkpoints/RIV-UI-0003_BIND_BOUNDARY.md',
 'docs/operations/troubleshooting/checkpoints/RIV-UI-0004_HTTP_ACCEPTANCE.md',
 'docs/operations/troubleshooting/checkpoints/RIV-UI-0005_ENVIRONMENT.md',
 'docs/operations/troubleshooting/checkpoints/RIV-UI-0006_SERVER_EXIT.md',
 'docs/operations/troubleshooting/checkpoints/RIV-PUB-0005_UNEXPECTED_SCOPE.md',
 'pyproject.toml',
 'src/riverview/status/__init__.py',
 'src/riverview/status/server.py',
 'src/riverview/status/snapshot.py',
 'src/riverview/status_health.py',
 'tests/test_status_view.py',
 'tools/powershell/status/Install-RiverviewStewardStatus.ps1',
 'tools/powershell/status/Start-RiverviewStewardStatus.ps1',
 'tools/powershell/synchronization/Publish-RiverviewStewardStatus.ps1'
)

try {
 Add-Section 'RIVERVIEW STEWARD STATUS PUBLICATION VALIDATION'
 foreach($Command in @('git','gh')){if(-not(Get-Command $Command -ErrorAction SilentlyContinue)){throw "Required command not found: $Command"};Add-Line "Found prerequisite: $Command" Green}
 $RepositoryPath=(Resolve-Path $RepositoryPath).Path
 if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){throw 'Riverview Git repository not found.'}
 $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe';if(-not(Test-Path $Python)){throw 'RIV-BLD-0006: Riverview virtual environment not found.'}
 Add-Line "Repository validated: $RepositoryPath" Green

 Add-Section 'SELF-INSTALLATION'
 $Installed=Join-Path $RepositoryPath 'tools\powershell\synchronization\Publish-RiverviewStewardStatus.ps1';New-Item -ItemType Directory -Path(Split-Path -Parent $Installed)-Force|Out-Null
 if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Installed)){Copy-Item $PSCommandPath $Installed -Force;Add-Line "Updated publisher: $Installed" Green}else{Add-Line "Running repository publisher: $Installed" Green}

 Add-Section 'KNOWN FAILURE RECONCILIATION'
 $ScopeCheckpoint=Join-Path $RepositoryPath 'docs\operations\troubleshooting\checkpoints\RIV-PUB-0005_UNEXPECTED_SCOPE.md'
 $ScopeText=Get-Content $ScopeCheckpoint -Raw
 if(-not $ScopeText.Contains('untracked directory summary')){$ScopeText += "`nObserved status-view manifestation: default porcelain output condensed an untracked package to an untracked directory summary. Publication scope must use ``--untracked-files=all`` so every file is independently allowlisted.`n";Set-Content $ScopeCheckpoint $ScopeText -Encoding utf8NoBOM -NoNewline;Add-Line 'RIV-PUB-0005 reconciled: untracked directories now expand to individual files.' Green}else{Add-Line 'RIV-PUB-0005 untracked-directory reconciliation already present.' DarkGray}

 Push-Location $RepositoryPath
 try {
  Add-Section 'GITHUB AND BRANCH SAFETY'
  Invoke-Checked 'GitHub authentication' {gh auth status}
  $Origin=(git remote get-url origin).Trim();if($Origin -notin @('https://github.com/ppow1/Riverview.git','git@github.com:ppow1/Riverview.git')){throw "RIV-PUB-0002: Unexpected origin: $Origin"};Add-Line "Origin validated: $Origin" Green
  if((git branch --show-current).Trim() -ne 'main'){throw 'RIV-PUB-0003: Publication requires branch main.'}
  Invoke-Checked 'Fetch origin' {git fetch origin main}
  $Head=(git rev-parse HEAD).Trim();$Remote=(git rev-parse origin/main).Trim();if($Head -ne $ExpectedBase -or $Remote -ne $ExpectedBase){throw "RIV-PUB-0004: Expected synchronized base $ExpectedBase; local=$Head remote=$Remote"};Add-Line "Publication base verified: $ExpectedBase" Green

  Add-Section 'SCOPE CONFIRMATION'
  $Changed=@(git status --porcelain=v1 --untracked-files=all|ForEach-Object{$Path=$_.Substring(3).Trim();if($Path.Contains(' -> ')){$Path=($Path-split ' -> ')[-1]};$Path.Replace('\','/')}|Sort-Object -Unique)
  if($Changed.Count -eq 0){throw 'RIV-PUB-0001: No Steward Status changes were found.'}
  foreach($Path in $Changed){Add-Line "CHANGE $Path";if($Path -notin $AllowedPaths){throw "RIV-PUB-0005: Unexpected working-tree path: $Path"}}
  foreach($Required in $AllowedPaths){if($Required -notin $Changed){throw "RIV-PUB-0006: Required publication path is absent: $Required"}}

  Add-Section 'MIGRATION AND FULL ACCEPTANCE'
  & $Python -m pip install -e '.[dev]';if($LASTEXITCODE -ne 0){throw 'Dependency installation failed.'}
  $Migration=@'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed=apply_migration(Path('database/migrations/0006_steward_status.sql'),'0006','0.7.0')
print('Migration 0006 applied.' if changed else 'Migration 0006 checksum verified.')
'@
  $Migration|& $Python -;if($LASTEXITCODE -ne 0){throw 'RIV-DB-0006: Migration 0006 validation failed.'}
  Invoke-Checked 'Ruff check' {& $Python -m ruff check src tests}
  Invoke-Checked 'Pytest' {& $Python -m pytest}
  Invoke-Checked 'Python compilation' {& $Python -m compileall -q src}
  Invoke-Checked 'Database health' {& $Python -m riverview.health database}
  Invoke-Checked 'Steward Status live acceptance' {& $Python -m riverview.status_health}

  Add-Section 'STAGE AND VERIFY'
  git reset|Out-Null;foreach($Path in $AllowedPaths){git add -- $Path}
  Invoke-Checked 'Staged whitespace validation' {git diff --cached --check}
  $Staged=@(git diff --cached --name-only|ForEach-Object{$_.Replace('\','/')})
  foreach($Path in $Staged){Add-Line "STAGED $Path";if($Path -notin $AllowedPaths){throw "RIV-PUB-0007: Unexpected staged path: $Path"}}
  foreach($Required in $AllowedPaths){if($Required -notin $Staged){throw "RIV-PUB-0008: Required staged path is absent: $Required"}}

  Add-Section 'COMMIT PUSH AND REMOTE VERIFICATION'
  Invoke-Checked 'Steward Status commit' {git commit -m 'Implement read-only Steward status view'}
  $Commit=(git rev-parse HEAD).Trim();Invoke-Checked 'Push main' {git push origin main};Invoke-Checked 'Remote refresh' {git fetch origin main}
  $Verified=(git rev-parse origin/main).Trim();if($Verified -ne $Commit){throw "RIV-PUB-0009: Remote commit mismatch; local=$Commit remote=$Verified"}
  if(@(git status --porcelain=v1 --untracked-files=all).Count -ne 0){throw 'RIV-PUB-0010: Working tree is not clean after publication.'}
  Add-Section 'PUBLICATION RESULT';Add-Line 'Steward Status v0.7.0 passed and the exact tested files were published.' Green;Add-Line "Verified commit: $Commit" Green;Add-Line 'Published branch: main' Green;Add-Line "Publisher version: $ToolVersion"
 } finally {Pop-Location}
 Save-Report
} catch {Add-Section 'PUBLICATION BLOCKED';Add-Line $_.Exception.Message Red;Add-Line 'No unsupported completion claim was made.' Yellow;if(Test-Path $RepositoryPath -PathType Container){Save-Report};throw}
