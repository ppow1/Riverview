# Riverview Read-Only MCP Relay Exact-Scope Publisher
# Version: 0.9.15
# Purpose: Publish the locally accepted RV-004.4 read-only MCP Relay, verify the exact remote commit, and reconcile local main.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\repo')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.9.15'
$ExpectedBase='c496b01f86ccdf21b3b1a0914c5e48d9bf300043'
$RemoteName='origin'
$RemoteBranch='main'
$CommitMessage='Complete RV-004.4 read-only MCP Relay'
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
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\mcp-relay'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path=Join-Path $Directory "ReadOnly-MCP-Relay-Publication-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
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
    $Capture=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\mcp-relay\publication-capture'
    New-Item -ItemType Directory -Path $Capture -Force | Out-Null
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmssfff'
    $Safe=($Label -replace '[^A-Za-z0-9_-]','_')
    $Out=Join-Path $Capture "$Safe-$Stamp.stdout.txt"
    $Err=Join-Path $Capture "$Safe-$Stamp.stderr.txt"

    $Process=Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $Out `
        -RedirectStandardError $Err `
        -Wait `
        -PassThru

    if(Test-Path $Out){
        foreach($Line in @(Get-Content $Out -Encoding UTF8)){ Add-Line $Line }
    }
    if(Test-Path $Err){
        foreach($Line in @(Get-Content $Err -Encoding UTF8)){
            Add-Line $Line $(if($Process.ExitCode -eq 0){'Yellow'}else{'Red'})
        }
    }

    if($Process.ExitCode -ne 0){
        throw "RIV-MCP-0006: $Label failed with exit code $($Process.ExitCode)."
    }
}

function Get-RelativeDirtyPaths {
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
    param(
        [Parameter(Mandatory)][string]$Repo,
        [Parameter(Mandatory)][string[]]$Paths
    )
    $Map=@{}
    foreach($Relative in $Paths){
        $Full=Join-Path $Repo ($Relative -replace '/','\')
        if(Test-Path $Full -PathType Leaf){
            $Map[$Relative]=(Get-FileHash $Full -Algorithm SHA256).Hash
        } else {
            $Map[$Relative]='<MISSING>'
        }
    }
    return $Map
}

try {
    Add-Section 'RIVERVIEW RV-004.4 EXACT-SCOPE PUBLICATION'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){
        throw 'RIV-MCP-0006: Riverview Git repository not found.'
    }

    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    $LocalHead=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    $Branch=(git.exe -C $RepositoryPath branch --show-current).Trim()
    $Origin=(git.exe -C $RepositoryPath remote get-url $RemoteName).Trim()

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Branch: $Branch"
    Add-Line "Local HEAD: $LocalHead"
    Add-Line "Expected remote base: $ExpectedBase"
    Add-Line "Publisher version: $ToolVersion"
    Add-Line "Migration: 0008 (schema version 0.9.1)"

    Add-Section 'CHARTER AND RV-004.4 SCOPE ANCHOR'
    Add-Line 'Mission: preserve and extend the Estate while making Riverview smaller, explicit, diagnosable, resumable, and self-documenting.'
    Add-Line 'Waypoint: RV-004.4 - Read-only MCP Relay.'
    Add-Line 'Exact action: publish only the fully accepted read-only MCP slice, verify the exact remote SHA, then align local main to that verified commit.'
    Add-Line 'Prohibited: enqueue authority, arbitrary SQL, filesystem/process authority through MCP, credentials, secrets, Undercurrent access, remote listener exposure, unified-supervisor work, unrelated reconciliation-tool publication.'
    Add-Line 'This publisher does not change roadmap status in PostgreSQL.'

    if($Branch -ne 'main'){ throw "RIV-MCP-0006: Expected branch main, observed $Branch." }
    if($LocalHead -ne $ExpectedBase){ throw "RIV-MCP-0006: Local HEAD changed from expected base $ExpectedBase." }
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    if($Origin -ne 'https://github.com/ppow1/Riverview.git' -and $Origin -ne 'git@github.com:ppow1/Riverview.git'){
        throw "RIV-MCP-0006: Unexpected origin URL: $Origin"
    }

    Add-Section 'SELF-INSTALLATION'
    $PublisherRelative='tools/powershell/synchronization/Publish-RiverviewReadOnlyMCPRelay.ps1'
    $PublisherCanonical=Join-Path $RepositoryPath ($PublisherRelative -replace '/','\')
    New-Item -ItemType Directory -Path (Split-Path -Parent $PublisherCanonical) -Force | Out-Null
    if([System.IO.Path]::GetFullPath($PSCommandPath) -ne [System.IO.Path]::GetFullPath($PublisherCanonical)){
        Copy-Item $PSCommandPath $PublisherCanonical -Force
        Add-Line "Installed publisher: $PublisherCanonical" Green
    }

    $Scope=@(
        'pyproject.toml',
        'database/migrations/0008_readonly_mcp_relay.sql',
        'docs/operations/troubleshooting/README.md',
        'docs/operations/troubleshooting/checkpoints/RIV-BLD-0010_POWERSHELL_UTF8_NOBOM.md',
        'docs/operations/troubleshooting/checkpoints/RIV-MCP-0001_READ_SURFACE.md',
        'docs/operations/troubleshooting/checkpoints/RIV-MCP-0002_AUTHORITY_BOUNDARY.md',
        'docs/operations/troubleshooting/checkpoints/RIV-MCP-0003_DATABASE_READ.md',
        'docs/operations/troubleshooting/checkpoints/RIV-MCP-0004_COOKBOOK_READ.md',
        'docs/operations/troubleshooting/checkpoints/RIV-MCP-0005_BOUND_LIMIT.md',
        'docs/operations/troubleshooting/checkpoints/RIV-MCP-0006_ACCEPTANCE.md',
        'src/riverview/mcp/__init__.py',
        'src/riverview/mcp/cookbook_sync.py',
        'src/riverview/mcp/live_acceptance.py',
        'src/riverview/mcp/read_model.py',
        'src/riverview/mcp/server.py',
        'src/riverview/mcp_health.py',
        'tests/test_mcp_readonly.py',
        'tests/test_mcp_transport.py',
        'tools/powershell/mcp/Get-RiverviewMCPCookbookSchemaDiagnostic.ps1',
        'tools/powershell/mcp/Install-RiverviewReadOnlyMCPRelay.ps1',
        'tools/powershell/mcp/Repair-RiverviewReadOnlyMCPRelay.ps1',
        'tools/powershell/mcp/Start-RiverviewReadOnlyMCPRelay.ps1',
        $PublisherRelative
    )

    Add-Section 'EXACT PUBLICATION SCOPE'
    foreach($Path in $Scope){
        $Full=Join-Path $RepositoryPath ($Path -replace '/','\')
        if(-not(Test-Path $Full -PathType Leaf)){
            throw "RIV-MCP-0006: Publication target missing: $Path"
        }
        Add-Line $Path
    }

    Add-Section 'UNRELATED LOCAL WORK PRESERVATION'
    $DirtyBefore=Get-RelativeDirtyPaths -Repo $RepositoryPath
    $Excluded=@($DirtyBefore | Where-Object { $Scope -notcontains $_ } | Sort-Object -Unique)
    $ExcludedBefore=Get-HashMap -Repo $RepositoryPath -Paths $Excluded
    if($Excluded.Count -eq 0){
        Add-Line 'No unrelated dirty paths present.' Green
    } else {
        foreach($Path in $Excluded){
            Add-Line "PRESERVE  $Path :: $($ExcludedBefore[$Path])" Yellow
        }
    }

    Add-Section 'FETCH AND VERIFY REMOTE BASE'
    Invoke-Captured `
        -FilePath 'git.exe' `
        -ArgumentList @('-C',$RepositoryPath,'fetch','--prune',$RemoteName,$RemoteBranch) `
        -WorkingDirectory $RepositoryPath `
        -Label 'git_fetch_base'

    $RemoteBase=(git.exe -C $RepositoryPath rev-parse "$RemoteName/$RemoteBranch").Trim()
    Add-Line "Observed remote base: $RemoteBase"
    if($RemoteBase -ne $ExpectedBase){
        throw "RIV-MCP-0006: Remote main changed from expected base $ExpectedBase."
    }
    Add-Line 'Remote base verified.' Green

    Add-Section 'LOCAL PUBLICATION ACCEPTANCE REPLAY'
    Invoke-Captured `
        -FilePath $Python `
        -ArgumentList @('-m','compileall','-q','src\riverview\mcp','src\riverview\mcp_health.py') `
        -WorkingDirectory $RepositoryPath `
        -Label 'local_compile'
    Invoke-Captured `
        -FilePath $Python `
        -ArgumentList @('-m','ruff','check','src\riverview\mcp','src\riverview\mcp_health.py','tests\test_mcp_readonly.py','tests\test_mcp_transport.py') `
        -WorkingDirectory $RepositoryPath `
        -Label 'local_ruff'
    Invoke-Captured `
        -FilePath $Python `
        -ArgumentList @('-m','riverview.mcp.cookbook_sync') `
        -WorkingDirectory $RepositoryPath `
        -Label 'local_cookbook_sync'
    Invoke-Captured `
        -FilePath $Python `
        -ArgumentList @('-m','riverview.mcp_health') `
        -WorkingDirectory $RepositoryPath `
        -Label 'local_mcp_health'
    Invoke-Captured `
        -FilePath $Python `
        -ArgumentList @('-m','pytest','-q','tests\test_mcp_readonly.py','tests\test_mcp_transport.py') `
        -WorkingDirectory $RepositoryPath `
        -Label 'local_mcp_tests'
    Invoke-Captured `
        -FilePath $Python `
        -ArgumentList @('-m','riverview.mcp.live_acceptance') `
        -WorkingDirectory $RepositoryPath `
        -Label 'local_live_stdio'
    Add-Line 'Local publication acceptance replay passed.' Green

    Add-Section 'ISOLATED PUBLICATION WORKTREE'
    $PublicationRoot=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\publication'
    New-Item -ItemType Directory -Path $PublicationRoot -Force | Out-Null
    $PublicationWorktree=Join-Path $PublicationRoot "rv0044-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

    Invoke-Captured `
        -FilePath 'git.exe' `
        -ArgumentList @('-C',$RepositoryPath,'worktree','add','--detach',$PublicationWorktree,$RemoteBase) `
        -WorkingDirectory $RepositoryPath `
        -Label 'git_worktree_add'
    Add-Line "Publication worktree: $PublicationWorktree" Green

    Add-Section 'COPY EXACT ACCEPTED FILES'
    foreach($Path in $Scope){
        $Source=Join-Path $RepositoryPath ($Path -replace '/','\')
        $Destination=Join-Path $PublicationWorktree ($Path -replace '/','\')
        New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
        Copy-Item $Source $Destination -Force

        $SourceHash=(Get-FileHash $Source -Algorithm SHA256).Hash
        $DestinationHash=(Get-FileHash $Destination -Algorithm SHA256).Hash
        if($SourceHash -ne $DestinationHash){
            throw "RIV-MCP-0006: Copy verification failed for $Path."
        }
        Add-Line "COPIED  $Path :: $SourceHash" Green
    }

    Add-Section 'EXACT DIFF CHECK'
    $WorktreeStatus=@(git.exe -C $PublicationWorktree status --porcelain=v1 --untracked-files=all)
    foreach($Line in $WorktreeStatus){ Add-Line $Line Yellow }

    $ActualChanged=@()
    foreach($Line in $WorktreeStatus){
        if($Line.Length -ge 4){
            $Path=($Line.Substring(3).Trim() -replace '\\','/')
            if($Path -match ' -> '){ $Path=($Path -split ' -> ')[-1] }
            $ActualChanged += $Path
        }
    }

    foreach($Path in $ActualChanged){
        if($Scope -notcontains $Path){
            throw "RIV-MCP-0006: Out-of-scope publication diff detected: $Path"
        }
    }
    foreach($Path in $Scope){
        if($ActualChanged -notcontains $Path){
            # Existing files may be byte-identical to base only if already published, which is unexpected for RV-004.4.
            Add-Line "NO DIFF  $Path" Yellow
        }
    }
    Add-Line 'Exact-scope diff check passed.' Green

    Add-Section 'ISOLATED STATIC ACCEPTANCE'
    Invoke-Captured `
        -FilePath $Python `
        -ArgumentList @('-m','compileall','-q',(Join-Path $PublicationWorktree 'src\riverview\mcp'),(Join-Path $PublicationWorktree 'src\riverview\mcp_health.py')) `
        -WorkingDirectory $PublicationWorktree `
        -Label 'publication_compile'
    Invoke-Captured `
        -FilePath $Python `
        -ArgumentList @('-m','ruff','check',(Join-Path $PublicationWorktree 'src\riverview\mcp'),(Join-Path $PublicationWorktree 'src\riverview\mcp_health.py'),(Join-Path $PublicationWorktree 'tests\test_mcp_readonly.py'),(Join-Path $PublicationWorktree 'tests\test_mcp_transport.py')) `
        -WorkingDirectory $PublicationWorktree `
        -Label 'publication_ruff'
    Add-Line 'Isolated static acceptance passed.' Green

    Add-Section 'STAGE EXACT SCOPE'
    $AddArgs=@('-C',$PublicationWorktree,'add','--') + $Scope
    Invoke-Captured `
        -FilePath 'git.exe' `
        -ArgumentList $AddArgs `
        -WorkingDirectory $PublicationWorktree `
        -Label 'git_add_exact'

    $Staged=@(git.exe -C $PublicationWorktree diff --cached --name-only)
    foreach($Path in $Staged){ Add-Line $Path }
    foreach($Path in $Staged){
        if($Scope -notcontains ($Path -replace '\\','/')){
            throw "RIV-MCP-0006: Out-of-scope staged file: $Path"
        }
    }
    if($Staged.Count -eq 0){
        throw 'RIV-MCP-0006: Nothing staged for RV-004.4 publication.'
    }

    Add-Section 'COMMIT'
    $CommitMessagePath=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\mcp-relay\publication-commit-message.txt'
    Write-Utf8NoBom -Path $CommitMessagePath -Content ($CommitMessage+[Environment]::NewLine)
    Invoke-Captured `
        -FilePath 'git.exe' `
        -ArgumentList @('-C',$PublicationWorktree,'commit','-F',$CommitMessagePath) `
        -WorkingDirectory $PublicationWorktree `
        -Label 'git_commit'

    $PublicationCommit=(git.exe -C $PublicationWorktree rev-parse HEAD).Trim()
    Add-Line "Publication commit: $PublicationCommit" Green

    Add-Section 'REMOTE RACE CHECK'
    Invoke-Captured `
        -FilePath 'git.exe' `
        -ArgumentList @('-C',$RepositoryPath,'fetch','--prune',$RemoteName,$RemoteBranch) `
        -WorkingDirectory $RepositoryPath `
        -Label 'git_fetch_race'

    $RaceBase=(git.exe -C $RepositoryPath rev-parse "$RemoteName/$RemoteBranch").Trim()
    Add-Line "Remote main before push: $RaceBase"
    if($RaceBase -ne $ExpectedBase){
        throw "RIV-MCP-0006: Remote main advanced during publication; push aborted."
    }
    Add-Line 'Remote race check passed.' Green

    Add-Section 'PUSH EXACT PUBLICATION'
    Invoke-Captured `
        -FilePath 'git.exe' `
        -ArgumentList @('-C',$PublicationWorktree,'push',$RemoteName,"HEAD:$RemoteBranch") `
        -WorkingDirectory $PublicationWorktree `
        -Label 'git_push'

    Add-Section 'REMOTE COMMIT VERIFICATION'
    Invoke-Captured `
        -FilePath 'git.exe' `
        -ArgumentList @('-C',$RepositoryPath,'fetch','--prune',$RemoteName,$RemoteBranch) `
        -WorkingDirectory $RepositoryPath `
        -Label 'git_fetch_verify'

    $VerifiedRemote=(git.exe -C $RepositoryPath rev-parse "$RemoteName/$RemoteBranch").Trim()
    Add-Line "Expected publication commit: $PublicationCommit"
    Add-Line "Observed remote main:       $VerifiedRemote"
    if($VerifiedRemote -ne $PublicationCommit){
        throw "RIV-MCP-0006: Remote verification failed. Expected $PublicationCommit, observed $VerifiedRemote."
    }
    Add-Line "REMOTE VERIFIED $VerifiedRemote" Green

    Add-Section 'POST-PUBLICATION LOCAL MAIN RECONCILIATION'
    $ExcludedBeforeReset=Get-HashMap -Repo $RepositoryPath -Paths $Excluded
    Invoke-Captured `
        -FilePath 'git.exe' `
        -ArgumentList @('-C',$RepositoryPath,'reset','--mixed',$VerifiedRemote) `
        -WorkingDirectory $RepositoryPath `
        -Label 'git_reset_local_main'

    $LocalAfter=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    Add-Line "Local HEAD after reconciliation: $LocalAfter"
    if($LocalAfter -ne $VerifiedRemote){
        throw 'RIV-MCP-0006: Local main did not align to verified publication commit.'
    }

    $ExcludedAfterReset=Get-HashMap -Repo $RepositoryPath -Paths $Excluded
    foreach($Path in $Excluded){
        if($ExcludedBeforeReset[$Path] -ne $ExcludedAfterReset[$Path]){
            throw "RIV-MCP-0006: Unrelated local work changed during post-publication reconciliation: $Path"
        }
        Add-Line "PRESERVED  $Path :: $($ExcludedAfterReset[$Path])" Green
    }

    Add-Section 'PUBLISHED-SCOPE CLEANLINESS'
    foreach($Path in $Scope){
        $PathStatus=@(git.exe -C $RepositoryPath status --porcelain=v1 -- $Path)
        if($PathStatus.Count -ne 0){
            foreach($Line in $PathStatus){ Add-Line $Line Red }
            throw "RIV-MCP-0006: Published path remains dirty after reconciliation: $Path"
        }
        Add-Line "CLEAN  $Path" Green
    }

    Add-Section 'FINAL LOCAL WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){
        Add-Line $Line Yellow
    }

    $PublicationSucceeded=$true

    Add-Section 'RV-004.4 PUBLICATION RESULT'
    Add-Line "REMOTE VERIFIED $VerifiedRemote" Green
    Add-Line 'RV-004.4 source, migration, diagnostics, tests, installer, repair, launcher, and publisher are published on remote main.' Green
    Add-Line 'Local main is reconciled to the verified remote publication commit.' Green
    Add-Line 'Unrelated local reconciliation utilities were preserved and were not published.' Green
    Add-Line 'No MCP write authority, remote listener exposure, Undercurrent access, or unified-supervisor work was introduced.' Green
    Add-Line 'PostgreSQL roadmap status was intentionally not changed by this publisher.' Yellow
    Add-Line 'Next stage: record the verified RV-004.4 completion in authoritative roadmap state, then advance only to the dependency-ready successor.' Green

    Save-Report
}
catch {
    Add-Section 'RV-004.4 PUBLICATION BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'Do not claim GitHub publication unless this report contains REMOTE VERIFIED with the exact commit.' Yellow
    if($PublicationWorktree){
        Add-Line "Publication worktree retained for evidence: $PublicationWorktree" Yellow
    }
    Save-Report
    throw
}
finally {
    if($PublicationSucceeded -and $PublicationWorktree -and (Test-Path $PublicationWorktree)){
        try {
            & git.exe -C $RepositoryPath worktree remove --force $PublicationWorktree 2>$null | Out-Null
            & git.exe -C $RepositoryPath worktree prune 2>$null | Out-Null
        } catch {
            # Cleanup failure is non-authoritative after verified publication; leave runtime path for later cleanup.
        }
    }
}
