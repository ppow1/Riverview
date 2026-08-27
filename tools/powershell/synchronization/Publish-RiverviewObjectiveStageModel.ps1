# Riverview RV-005.2 Final Exact-Scope Publisher
# Version: 0.3.4
# Date: 2026-08-14
# Purpose: Publish the LF-normalized, fully accepted RV-005.2 slice with exact-scope staging, Git whitespace validation, remote verification, and non-destructive local reconciliation.

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.3.4'
$ExpectedBase='34b672f2acb7dd60ea2536505ff3bd39b93ce40b'
$RemoteName='origin'
$RemoteBranch='main'
$CommitMessage='Complete RV-005.2 objective and stage model'
$CheckpointId='RIV-GRC-0002'
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
    $Path=Join-Path $Directory "RV-005.2-Final-Publication-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){ Set-Clipboard $Report }
        else { $Report | clip.exe }
        Write-Host "`nComplete publication report copied to the Windows clipboard." -ForegroundColor Cyan
    } catch {}
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
    $Out=Join-Path $Capture "$Label-$Stamp.stdout.txt"
    $Err=Join-Path $Capture "$Label-$Stamp.stderr.txt"
    $P=Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $Out -RedirectStandardError $Err -Wait -PassThru
    if(Test-Path $Out){ foreach($Line in @(Get-Content $Out -Encoding UTF8)){ Add-Line $Line } }
    if(Test-Path $Err){ foreach($Line in @(Get-Content $Err -Encoding UTF8)){ Add-Line $Line $(if($P.ExitCode -eq 0){'Yellow'}else{'Red'}) } }
    if($P.ExitCode -ne 0){ throw "${CheckpointId}: $Label failed with exit code $($P.ExitCode)." }
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
    Add-Section 'RIVERVIEW RV-005.2 FINAL EXACT-SCOPE PUBLICATION'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    $Head=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    $Branch=(git.exe -C $RepositoryPath branch --show-current).Trim()
    $Origin=(git.exe -C $RepositoryPath remote get-url $RemoteName).Trim()

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Branch: $Branch"
    Add-Line "Local HEAD: $Head"
    Add-Line "Publisher version: $ToolVersion"
    Add-Line "Expected remote base: $ExpectedBase"

    if($Branch -ne 'main'){ throw "${CheckpointId}: expected main branch." }
    if($Head -ne $ExpectedBase){ throw "${CheckpointId}: unexpected local HEAD $Head." }
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: virtual environment missing.' }
    if($Origin -ne 'https://github.com/ppow1/Riverview.git' -and $Origin -ne 'git@github.com:ppow1/Riverview.git'){
        throw "${CheckpointId}: unexpected origin URL $Origin"
    }

    Add-Section 'SELF-INSTALLATION'
    $PublisherRelative='tools/powershell/synchronization/Publish-RiverviewObjectiveStageModel.ps1'
    $PublisherCanonical=Join-Path $RepositoryPath ($PublisherRelative -replace '/','\')
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($PublisherCanonical)){
        Copy-Item $PSCommandPath $PublisherCanonical -Force
        Add-Line "Installed publisher: $PublisherCanonical" Green
    }

    $Scope=@(
        'database/migrations/0010_objective_stage_model.sql',
        'docs/operations/troubleshooting/checkpoints/RIV-GRC-0002_OBJECTIVE_STAGE_MODEL.md',
        'src/riverview/grace/objective_acceptance.py',
        'src/riverview/grace/objectives.py',
        'tests/test_objective_stage_model.py',
        'tools/powershell/grace/Install-RiverviewObjectiveStageModel.ps1',
        'tools/powershell/grace/Repair-RiverviewObjectiveStageAcceptance.ps1',
        'tools/powershell/grace/Repair-RiverviewObjectiveStageWhitespace.ps1',
        $PublisherRelative
    )
    $PreserveAllowlist=@(
        'tools/powershell/roadmap/Promote-RiverviewRV0044Completion.ps1',
        'tools/powershell/roadmap/Promote-RiverviewRV0051Completion.ps1',
        'tools/powershell/synchronization/Repair-RiverviewLocalMainReconciliation.ps1',
        'tools/powershell/synchronization/Sync-RiverviewLocalMainPreserveWorktree.ps1'
    )

    Add-Section 'EXACT SCOPE AND DIRTY-STATE CHECK'
    foreach($Path in $Scope){
        if(-not (Test-Path -LiteralPath (Join-Path $RepositoryPath ($Path -replace '/','\')) -PathType Leaf)){
            throw "${CheckpointId}: missing publication file $Path"
        }
        Add-Line $Path
    }

    $Dirty=Get-DirtyPaths -Repo $RepositoryPath
    $Allowed=@($Scope+$PreserveAllowlist)
    foreach($Path in $Dirty){
        if($Allowed -notcontains $Path){ throw "${CheckpointId}: unexpected dirty path outside allowlist: $Path" }
    }
    $ActualPreserved=@($Dirty | Where-Object { $PreserveAllowlist -contains $_ } | Sort-Object -Unique)
    $PreservedBefore=Get-HashMap -Repo $RepositoryPath -Paths $ActualPreserved
    foreach($Path in $ActualPreserved){ Add-Line "PRESERVE  $Path :: $($PreservedBefore[$Path])" Yellow }

    Add-Section 'REMOTE BASE VERIFICATION'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'fetch','--prune',$RemoteName,$RemoteBranch) -WorkingDirectory $RepositoryPath -Label 'fetch_base'
    $RemoteBase=(git.exe -C $RepositoryPath rev-parse "$RemoteName/$RemoteBranch").Trim()
    Add-Line "Observed remote base: $RemoteBase"
    if($RemoteBase -ne $ExpectedBase){ throw "${CheckpointId}: remote main moved." }

    Add-Section 'COMPLETE LOCAL ACCEPTANCE'
    $AcceptanceKey="acceptance.rv0052.publish.$([Guid]::NewGuid().ToString('N'))"
    Add-Line "Acceptance key: $AcceptanceKey"
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','compileall','-q','src\riverview\grace') -WorkingDirectory $RepositoryPath -Label 'compile'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','ruff','check','src\riverview\grace','tests\test_objective_stage_model.py') -WorkingDirectory $RepositoryPath -Label 'ruff'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','pytest','-q','tests\test_objective_stage_model.py') -WorkingDirectory $RepositoryPath -Label 'tests'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','seed',$AcceptanceKey) -WorkingDirectory $RepositoryPath -Label 'seed'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','read',$AcceptanceKey) -WorkingDirectory $RepositoryPath -Label 'read'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.acceptance') -WorkingDirectory $RepositoryPath -Label 'grace'
    Add-Line 'Local acceptance passed.' Green

    Add-Section 'MIGRATION 0010 LEDGER VERIFICATION'
    $MigrationPath=Join-Path $RepositoryPath 'database\migrations\0010_objective_stage_model.sql'
    $Probe=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\verify_0010_publication_032.py'
    $ProbeText=@'
from pathlib import Path
import hashlib
from riverview.database import connect
root=Path(r"__ROOT__")
path=root/"database/migrations/0010_objective_stage_model.sql"
checksum=hashlib.sha256(path.read_bytes()).hexdigest()
with connect() as connection, connection.cursor() as cursor:
    cursor.execute("SELECT version,checksum_sha256 FROM schema_migrations WHERE migration_id='0010'")
    row=cursor.fetchone()
    if row is None or row[0]!="0.2.0" or row[1].lower()!=checksum.lower():
        raise RuntimeError(f"RIV-DB-0006: migration 0010 mismatch: {row!r} local={checksum}")
    print(f"migration_0010=verified version={row[0]} checksum={row[1]}")
    connection.rollback()
'@
    $ProbeText=$ProbeText.Replace('__ROOT__',$RepositoryPath.Replace('\','\\'))
    Write-Utf8NoBom -Path $Probe -Content $ProbeText
    Invoke-Captured -FilePath $Python -ArgumentList @($Probe) -WorkingDirectory $RepositoryPath -Label 'migration_0010'

    Add-Section 'ISOLATED PUBLICATION WORKTREE'
    $Root=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\publication'
    New-Item -ItemType Directory -Path $Root -Force | Out-Null
    $PublicationWorktree=Join-Path $Root "rv0052-final-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'worktree','add','--detach',$PublicationWorktree,$RemoteBase) -WorkingDirectory $RepositoryPath -Label 'worktree'

    foreach($Path in $Scope){
        $Src=Join-Path $RepositoryPath ($Path -replace '/','\')
        $Dst=Join-Path $PublicationWorktree ($Path -replace '/','\')
        New-Item -ItemType Directory -Path (Split-Path -Parent $Dst) -Force | Out-Null
        Copy-Item $Src $Dst -Force
        if((Get-FileHash $Src -Algorithm SHA256).Hash -ne (Get-FileHash $Dst -Algorithm SHA256).Hash){
            throw "${CheckpointId}: copy hash mismatch for $Path"
        }
    }

    Add-Section 'ISOLATED STATIC ACCEPTANCE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','compileall','-q',(Join-Path $PublicationWorktree 'src\riverview\grace')) -WorkingDirectory $PublicationWorktree -Label 'pub_compile'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','ruff','check',(Join-Path $PublicationWorktree 'src\riverview\grace'),(Join-Path $PublicationWorktree 'tests\test_objective_stage_model.py')) -WorkingDirectory $PublicationWorktree -Label 'pub_ruff'

    Add-Section 'STAGE EXACT SCOPE'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList (@('-C',$PublicationWorktree,'add','--')+$Scope) -WorkingDirectory $PublicationWorktree -Label 'git_add'
    $Staged=@(git.exe -C $PublicationWorktree diff --cached --name-only)
    foreach($Path in $Staged){ Add-Line $Path }
    if($Staged.Count -ne $Scope.Count){ throw "${CheckpointId}: staged file count mismatch." }
    foreach($Path in $Staged){ if($Scope -notcontains $Path.Replace('\','/')){ throw "${CheckpointId}: out-of-scope staged file $Path" } }

    Add-Section 'AUTHORITATIVE STAGED WHITESPACE CHECK'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$PublicationWorktree,'diff','--cached','--check') -WorkingDirectory $PublicationWorktree -Label 'git_diff_check'
    Add-Line 'Full staged Git whitespace check passed.' Green

    Add-Section 'COMMIT'
    $MessagePath=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\rv0052-publication-message.txt'
    Write-Utf8NoBom -Path $MessagePath -Content ($CommitMessage+[Environment]::NewLine)
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$PublicationWorktree,'commit','-F',$MessagePath) -WorkingDirectory $PublicationWorktree -Label 'commit'
    $PublicationCommit=(git.exe -C $PublicationWorktree rev-parse HEAD).Trim()
    Add-Line "Publication commit: $PublicationCommit" Green
    if(@(git.exe -C $PublicationWorktree status --porcelain=v1 --untracked-files=all).Count -ne 0){
        throw "${CheckpointId}: publication worktree not clean after commit."
    }

    Add-Section 'REMOTE RACE CHECK'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'fetch','--prune',$RemoteName,$RemoteBranch) -WorkingDirectory $RepositoryPath -Label 'fetch_race'
    $Race=(git.exe -C $RepositoryPath rev-parse "$RemoteName/$RemoteBranch").Trim()
    if($Race -ne $ExpectedBase){ throw "${CheckpointId}: remote main advanced during publication." }

    Add-Section 'PUSH'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$PublicationWorktree,'push',$RemoteName,"HEAD:$RemoteBranch") -WorkingDirectory $PublicationWorktree -Label 'push'

    Add-Section 'REMOTE VERIFICATION'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'fetch','--prune',$RemoteName,$RemoteBranch) -WorkingDirectory $RepositoryPath -Label 'fetch_verify'
    $Verified=(git.exe -C $RepositoryPath rev-parse "$RemoteName/$RemoteBranch").Trim()
    Add-Line "Expected publication commit: $PublicationCommit"
    Add-Line "Observed remote main:       $Verified"
    if($Verified -ne $PublicationCommit){ throw "${CheckpointId}: remote verification mismatch." }
    Add-Line "REMOTE VERIFIED $Verified" Green

    Add-Section 'NON-DESTRUCTIVE LOCAL RECONCILIATION'
    $PreservedBeforeReset=Get-HashMap -Repo $RepositoryPath -Paths $ActualPreserved
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'update-ref','refs/heads/main',$Verified,$ExpectedBase) -WorkingDirectory $RepositoryPath -Label 'update_ref'
    Invoke-Captured -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'read-tree',$Verified) -WorkingDirectory $RepositoryPath -Label 'read_tree'
    if((git.exe -C $RepositoryPath rev-parse HEAD).Trim() -ne $Verified){ throw "${CheckpointId}: local main reconciliation failed." }

    $PreservedAfter=Get-HashMap -Repo $RepositoryPath -Paths $ActualPreserved
    foreach($Path in $ActualPreserved){
        if($PreservedBeforeReset[$Path] -ne $PreservedAfter[$Path]){ throw "${CheckpointId}: preserved utility changed: $Path" }
        Add-Line "PRESERVED  $Path :: $($PreservedAfter[$Path])" Green
    }

    Add-Section 'FINAL CLEANLINESS'
    foreach($Path in $Scope){
        if(@(git.exe -C $RepositoryPath status --porcelain=v1 -- $Path).Count -ne 0){ throw "${CheckpointId}: published path remains dirty: $Path" }
        Add-Line "CLEAN  $Path" Green
    }
    foreach($Path in @(Get-DirtyPaths -Repo $RepositoryPath)){
        if($PreserveAllowlist -notcontains $Path){ throw "${CheckpointId}: unexpected dirty path remains: $Path" }
        Add-Line "PRESERVED UNTRACKED  $Path" Yellow
    }

    $PublicationSucceeded=$true
    Add-Section 'RV-005.2 PUBLICATION RESULT'
    Add-Line "REMOTE VERIFIED $Verified" Green
    Add-Line 'RV-005.2 is published on remote main.' Green
    Add-Line 'The full nine-file slice passed local acceptance, isolated static acceptance, and Git staged whitespace validation.' Green
    Add-Line 'Migration 0010 remains ledger-verified.' Green
    Add-Line 'Local main is reconciled to the exact remote commit.' Green
    Add-Line 'No RV-005.3 behavior or PostgreSQL roadmap mutation occurred.' Green
    Add-Line 'Next stage: authoritative PostgreSQL RV-005.2 completion promotion.' Green
    Save-Report
}
catch {
    Add-Section 'RV-005.2 PUBLICATION BLOCKED'
    Add-Line $_.Exception.Message Red
    Add-Line 'Do not claim publication without REMOTE VERIFIED.' Yellow
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
