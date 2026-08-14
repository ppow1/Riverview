# Riverview RV-005.1 Grace Authority Exact-Scope Publisher
# Version: 0.1.1
# Purpose: Publish the locally accepted Grace identity and authority contract, verify the exact remote commit, and reconcile local main.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\repo')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.1.1'
$ExpectedBase='ff565726f87c9034b50853d643e9428b0333f4d3'
$RemoteName='origin'
$RemoteBranch='main'
$CommitMessage='Complete RV-005.1 Grace authority contract'
$ReportLines=[Collections.Generic.List[string]]::new()
$PublicationWorktree=$null
$PublicationSucceeded=$false

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
    $Path=Join-Path $Directory "RV-005.1-Grace-Authority-Publication-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){ Set-Clipboard $Report }
        else { $Report | clip.exe }
        Write-Host "`nComplete publication report copied to the Windows clipboard." -ForegroundColor Cyan
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
    $Capture=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\publication-capture'
    New-Item -ItemType Directory -Path $Capture -Force | Out-Null
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmssfff'
    $Safe=($Label -replace '[^A-Za-z0-9_-]','_')
    $Out=Join-Path $Capture "$Safe-$Stamp.stdout.txt"
    $Err=Join-Path $Capture "$Safe-$Stamp.stderr.txt"
    $Process=Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $Out -RedirectStandardError $Err -Wait -PassThru
    if(Test-Path $Out){ foreach($Line in @(Get-Content $Out -Encoding UTF8)){ Add-Line $Line } }
    if(Test-Path $Err){ foreach($Line in @(Get-Content $Err -Encoding UTF8)){ Add-Line $Line $(if($Process.ExitCode -eq 0){'Yellow'}else{'Red'}) } }
    if($Process.ExitCode -ne 0){ throw "RIV-GRC-0001: $Label failed with exit code $($Process.ExitCode)." }
}
function Get-DirtyPaths {
    param([Parameter(Mandatory)][string]$Repo)
    $Result=[Collections.Generic.List[string]]::new()
    foreach($Line in @(git.exe -C $Repo status --porcelain=v1 --untracked-files=all)){
        if($Line.Length -ge 4){
            $Path=($Line.Substring(3).Trim() -replace '\\','/')
            if($Path -match ' -> '){ $Path=($Path -split ' -> ')[-1] }
            $Result.Add($Path)
        }
    }
    return @($Result)
}
function Get-HashMap {
    param([Parameter(Mandatory)][string]$Repo,[Parameter(Mandatory)][string[]]$Paths)
    $Map=@{}
    foreach($Relative in $Paths){
        $Full=Join-Path $Repo ($Relative -replace '/','\')
        if(Test-Path $Full -PathType Leaf){ $Map[$Relative]=(Get-FileHash $Full -Algorithm SHA256).Hash }
        else { $Map[$Relative]='<MISSING>' }
    }
    return $Map
}

try {
    Add-Section 'RIVERVIEW RV-005.1 EXACT-SCOPE PUBLICATION'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){ throw 'RIV-GRC-0001: Riverview Git repository not found.' }

    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    $LocalHead=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    $Branch=(git.exe -C $RepositoryPath branch --show-current).Trim()

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Branch: $Branch"
    Add-Line "Local HEAD: $LocalHead"
    Add-Line "Expected remote base: $ExpectedBase"
    Add-Line "Publisher version: $ToolVersion"
    Add-Line "Migration: 0009 (schema version 0.1.0)"

    Add-Section 'CHARTER AND RV-005.1 SCOPE ANCHOR'
    Add-Line 'Current waypoint: RV-005.1 - Grace identity and authority contract.'
    Add-Line 'Exact action: publish only the accepted Grace identity/authority vertical slice, verify exact remote SHA, and reconcile local main.'
    Add-Line 'Grace remains an operational coordinator, not universal authority.'
    Add-Line 'Prohibited: RV-005.2 objective/stage work, automatic enqueue, provider dispatch, authority widening, Undercurrent access, unrelated roadmap/reconciliation utility publication.'
    Add-Line 'This publisher does not mutate roadmap status in PostgreSQL.'

    if($Branch -ne 'main'){ throw "RIV-GRC-0001: Expected main branch, observed $Branch." }
    if($LocalHead -ne $ExpectedBase){ throw "RIV-GRC-0001: Local HEAD differs from expected publication base." }
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: Riverview virtual environment not found.' }

    Add-Section 'SELF-INSTALLATION'
    $PublisherRelative='tools/powershell/synchronization/Publish-RiverviewGraceAuthority.ps1'
    $PublisherCanonical=Join-Path $RepositoryPath ($PublisherRelative -replace '/','\')
    New-Item -ItemType Directory -Path (Split-Path -Parent $PublisherCanonical) -Force | Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($PublisherCanonical)){
        Copy-Item $PSCommandPath $PublisherCanonical -Force
        Add-Line "Installed publisher: $PublisherCanonical" Green
    }

    $Scope=@(
        'database/migrations/0009_grace_authority.sql',
        'docs/operations/troubleshooting/checkpoints/RIV-GRC-0001_GRACE_AUTHORITY.md',
        'src/riverview/grace/__init__.py',
        'src/riverview/grace/acceptance.py',
        'src/riverview/grace/authority.py',
        'tests/test_grace_authority.py',
        'tools/powershell/grace/Install-RiverviewGraceAuthority.ps1',
        $PublisherRelative
    )

    Add-Section 'EXACT PUBLICATION SCOPE'
    foreach($Path in $Scope){
        $Full=Join-Path $RepositoryPath ($Path -replace '/','\')
        if(-not(Test-Path $Full -PathType Leaf)){ throw "RIV-GRC-0001: Publication target missing: $Path" }
        Add-Line $Path
    }

    Add-Section 'UNRELATED LOCAL WORK PRESERVATION'
    $DirtyBefore=Get-DirtyPaths -Repo $RepositoryPath
    $Excluded=@($DirtyBefore | Where-Object { $Scope -notcontains $_ } | Sort-Object -Unique)
    $ExcludedBefore=Get-HashMap -Repo $RepositoryPath -Paths $Excluded
    if($Excluded.Count -eq 0){ Add-Line 'No unrelated dirty paths present.' Green }
    else {
        foreach($Path in $Excluded){ Add-Line "PRESERVE  $Path :: $($ExcludedBefore[$Path])" Yellow }
    }

    Add-Section 'FETCH AND VERIFY REMOTE BASE'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'fetch','--prune',$RemoteName,$RemoteBranch) -WorkingDirectory $RepositoryPath -Label 'git_fetch_base'
    $RemoteBase=(git.exe -C $RepositoryPath rev-parse "$RemoteName/$RemoteBranch").Trim()
    Add-Line "Observed remote base: $RemoteBase"
    if($RemoteBase -ne $ExpectedBase){ throw "RIV-GRC-0001: Remote main changed from expected base $ExpectedBase." }
    Add-Line 'Remote base verified.' Green

    Add-Section 'LOCAL ACCEPTANCE REPLAY'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','compileall','-q','src\riverview\grace') -WorkingDirectory $RepositoryPath -Label 'local_compile'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','ruff','check','src\riverview\grace','tests\test_grace_authority.py') -WorkingDirectory $RepositoryPath -Label 'local_ruff'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','pytest','-q','tests\test_grace_authority.py') -WorkingDirectory $RepositoryPath -Label 'local_tests'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.acceptance') -WorkingDirectory $RepositoryPath -Label 'local_live_acceptance'
    Add-Line 'Local RV-005.1 acceptance replay passed.' Green

    Add-Section 'MIGRATION LEDGER VERIFICATION'
    $LedgerProbe=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\verify_0009.py'
    $LedgerText=@'
from pathlib import Path
import hashlib
from riverview.database import connect

root = Path(r"__ROOT__")
migration = root / "database/migrations/0009_grace_authority.sql"
checksum = hashlib.sha256(migration.read_bytes()).hexdigest()

with connect() as connection, connection.cursor() as cursor:
    cursor.execute("SELECT version,checksum_sha256 FROM schema_migrations WHERE migration_id='0009'")
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError("RIV-DB-0006: migration 0009 is not applied")
    if row[0] != "0.1.0" or row[1].lower() != checksum.lower():
        raise RuntimeError(f"RIV-DB-0006: migration 0009 ledger mismatch: {row!r} local={checksum}")
    print(f"migration_0009=verified version={row[0]} checksum={row[1]}")
    connection.rollback()
'@
    $LedgerText=$LedgerText.Replace('__ROOT__',$RepositoryPath.Replace('\','\\'))
    Write-Utf8NoBom -Path $LedgerProbe -Content $LedgerText
    Invoke-Captured -FilePath $Python -ArgumentList @($LedgerProbe) -WorkingDirectory $RepositoryPath -Label 'migration_ledger'
    Add-Line 'Migration 0009 ledger verification passed.' Green

    Add-Section 'ISOLATED PUBLICATION WORKTREE'
    $PublicationRoot=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\publication'
    New-Item -ItemType Directory -Path $PublicationRoot -Force | Out-Null
    $PublicationWorktree=Join-Path $PublicationRoot "rv0051-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'worktree','add','--detach',$PublicationWorktree,$RemoteBase) -WorkingDirectory $RepositoryPath -Label 'git_worktree_add'
    Add-Line "Publication worktree: $PublicationWorktree" Green

    Add-Section 'COPY EXACT ACCEPTED FILES'
    foreach($Path in $Scope){
        $Source=Join-Path $RepositoryPath ($Path -replace '/','\')
        $Destination=Join-Path $PublicationWorktree ($Path -replace '/','\')
        New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
        Copy-Item $Source $Destination -Force
        $SourceHash=(Get-FileHash $Source -Algorithm SHA256).Hash
        $DestinationHash=(Get-FileHash $Destination -Algorithm SHA256).Hash
        if($SourceHash -ne $DestinationHash){ throw "RIV-GRC-0001: Copy verification failed for $Path." }
        Add-Line "COPIED  $Path :: $SourceHash" Green
    }

    Add-Section 'EXACT DIFF CHECK'
    $Status=@(git.exe -C $PublicationWorktree status --porcelain=v1 --untracked-files=all)
    foreach($Line in $Status){ Add-Line $Line Yellow }
    $Actual=@()
    foreach($Line in $Status){
        if($Line.Length -ge 4){
            $Path=($Line.Substring(3).Trim() -replace '\\','/')
            if($Path -match ' -> '){ $Path=($Path -split ' -> ')[-1] }
            $Actual += $Path
        }
    }
    foreach($Path in $Actual){
        if($Scope -notcontains $Path){ throw "RIV-GRC-0001: Out-of-scope publication diff: $Path" }
    }
    if($Actual.Count -eq 0){ throw 'RIV-GRC-0001: Nothing changed in isolated publication worktree.' }
    Add-Line 'Exact-scope diff check passed.' Green

    Add-Section 'ISOLATED STATIC ACCEPTANCE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','compileall','-q',(Join-Path $PublicationWorktree 'src\riverview\grace')) -WorkingDirectory $PublicationWorktree -Label 'publication_compile'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','ruff','check',(Join-Path $PublicationWorktree 'src\riverview\grace'),(Join-Path $PublicationWorktree 'tests\test_grace_authority.py')) -WorkingDirectory $PublicationWorktree -Label 'publication_ruff'
    Add-Line 'Isolated static acceptance passed.' Green

    Add-Section 'STAGE AND COMMIT'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList (@('-C',$PublicationWorktree,'add','--') + $Scope) -WorkingDirectory $PublicationWorktree -Label 'git_add_exact'
    $Staged=@(git.exe -C $PublicationWorktree diff --cached --name-only)
    foreach($Path in $Staged){ Add-Line $Path }
    foreach($Path in $Staged){
        if($Scope -notcontains ($Path -replace '\\','/')){ throw "RIV-GRC-0001: Out-of-scope staged file: $Path" }
    }
    if($Staged.Count -eq 0){ throw 'RIV-GRC-0001: Nothing staged for publication.' }

    $MessagePath=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\publication-commit-message.txt'
    Write-Utf8NoBom -Path $MessagePath -Content ($CommitMessage+[Environment]::NewLine)
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$PublicationWorktree,'commit','-F',$MessagePath) -WorkingDirectory $PublicationWorktree -Label 'git_commit'
    $PublicationCommit=(git.exe -C $PublicationWorktree rev-parse HEAD).Trim()
    Add-Line "Publication commit: $PublicationCommit" Green

    Add-Section 'REMOTE RACE CHECK'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'fetch','--prune',$RemoteName,$RemoteBranch) -WorkingDirectory $RepositoryPath -Label 'git_fetch_race'
    $RaceBase=(git.exe -C $RepositoryPath rev-parse "$RemoteName/$RemoteBranch").Trim()
    Add-Line "Remote main before push: $RaceBase"
    if($RaceBase -ne $ExpectedBase){ throw 'RIV-GRC-0001: Remote main advanced during publication; push aborted.' }
    Add-Line 'Remote race check passed.' Green

    Add-Section 'PUSH EXACT PUBLICATION'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$PublicationWorktree,'push',$RemoteName,"HEAD:$RemoteBranch") -WorkingDirectory $PublicationWorktree -Label 'git_push'

    Add-Section 'REMOTE COMMIT VERIFICATION'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'fetch','--prune',$RemoteName,$RemoteBranch) -WorkingDirectory $RepositoryPath -Label 'git_fetch_verify'
    $VerifiedRemote=(git.exe -C $RepositoryPath rev-parse "$RemoteName/$RemoteBranch").Trim()
    Add-Line "Expected publication commit: $PublicationCommit"
    Add-Line "Observed remote main:       $VerifiedRemote"
    if($VerifiedRemote -ne $PublicationCommit){ throw "RIV-GRC-0001: Remote verification failed: expected $PublicationCommit observed $VerifiedRemote." }
    Add-Line "REMOTE VERIFIED $VerifiedRemote" Green

    Add-Section 'POST-PUBLICATION LOCAL MAIN RECONCILIATION'
    $ExcludedBeforeReset=Get-HashMap -Repo $RepositoryPath -Paths $Excluded
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'reset','--mixed',$VerifiedRemote) -WorkingDirectory $RepositoryPath -Label 'git_reset_local_main'
    $LocalAfter=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    if($LocalAfter -ne $VerifiedRemote){ throw 'RIV-GRC-0001: Local main did not align to verified remote commit.' }
    Add-Line "Local HEAD after reconciliation: $LocalAfter" Green

    $ExcludedAfterReset=Get-HashMap -Repo $RepositoryPath -Paths $Excluded
    foreach($Path in $Excluded){
        if($ExcludedBeforeReset[$Path] -ne $ExcludedAfterReset[$Path]){ throw "RIV-GRC-0001: Unrelated work changed during reconciliation: $Path" }
        Add-Line "PRESERVED  $Path :: $($ExcludedAfterReset[$Path])" Green
    }

    Add-Section 'PUBLISHED-SCOPE CLEANLINESS'
    foreach($Path in $Scope){
        $PathStatus=@(git.exe -C $RepositoryPath status --porcelain=v1 -- $Path)
        if($PathStatus.Count -ne 0){
            foreach($Line in $PathStatus){ Add-Line $Line Red }
            throw "RIV-GRC-0001: Published path remains dirty: $Path"
        }
        Add-Line "CLEAN  $Path" Green
    }

    Add-Section 'FINAL LOCAL WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }

    $PublicationSucceeded=$true

    Add-Section 'RV-005.1 PUBLICATION RESULT'
    Add-Line "REMOTE VERIFIED $VerifiedRemote" Green
    Add-Line 'RV-005.1 Grace identity and authority contract is published on remote main.' Green
    Add-Line 'Migration 0009, tests, acceptance, diagnostics checkpoint, installer, and publisher are included.' Green
    Add-Line 'Local main is reconciled to the verified remote publication commit.' Green
    Add-Line 'Prior roadmap-promotion and reconciliation utilities were preserved and not published.' Green
    Add-Line 'No RV-005.2 implementation or roadmap-state mutation was performed.' Green
    Add-Line 'Next stage: record RV-005.1 completion in authoritative PostgreSQL state and advance to the dependency-ready RV-005.2 objective and stage model.' Green

    Save-Report
}
catch {
    Add-Section 'RV-005.1 PUBLICATION BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'Do not claim GitHub publication unless this report contains REMOTE VERIFIED with the exact commit.' Yellow
    if($PublicationWorktree){ Add-Line "Publication worktree retained for evidence: $PublicationWorktree" Yellow }
    Save-Report
    throw
}
finally {
    if($PublicationSucceeded -and $PublicationWorktree -and (Test-Path $PublicationWorktree)){
        try {
            & git.exe -C $RepositoryPath worktree remove --force $PublicationWorktree 2>$null | Out-Null
            & git.exe -C $RepositoryPath worktree prune 2>$null | Out-Null
        } catch {}
    }
}
