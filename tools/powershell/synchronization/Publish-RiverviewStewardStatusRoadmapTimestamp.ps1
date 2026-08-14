# Riverview Steward Status Roadmap Timestamp Publisher
# Version: 0.7.4
# Purpose: Repair publisher native-stderr handling and publish only RIV-UI-0007 through an isolated worktree.
# Updated: 2026-08-14

[CmdletBinding()]
param(
    [string]$RepositoryPath='A:\Riverview\repo',
    [string]$RemoteName='origin',
    [string]$RemoteBranch='main'
)

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.7.4'
$CheckpointId='RIV-UI-0007'
$CommitMessage='Fix Steward Status roadmap timestamp semantics'
$ExpectedRemoteBase='f4bc47857f382cb59d324653b7cdf6bdb88d5794'
$ReportLines=[Collections.Generic.List[string]]::new()
$WorktreePath=$null
$WorktreeCreated=$false

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
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\steward-status'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path=Join-Path $Directory "Steward-Status-Roadmap-Timestamp-Publish-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){ Set-Clipboard $Report }
        else { $Report | clip.exe; if($LASTEXITCODE -ne 0){ throw "clip.exe exited with code $LASTEXITCODE." } }
        Write-Host "`nComplete publication report copied to the Windows clipboard." -ForegroundColor Cyan
    } catch {
        Write-Host "`nClipboard copy failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host "Durable report: $Path" -ForegroundColor Green
}
function Invoke-ProcessCapture {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$Label,
        [switch]$AllowFailure
    )
    $CaptureRoot=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\steward-status\publisher-capture'
    New-Item -ItemType Directory -Path $CaptureRoot -Force | Out-Null
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmssfff'
    $SafeLabel=($Label -replace '[^A-Za-z0-9_-]','_')
    $Stdout=Join-Path $CaptureRoot "$SafeLabel-$Stamp.stdout.txt"
    $Stderr=Join-Path $CaptureRoot "$SafeLabel-$Stamp.stderr.txt"
    $Process=Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -Wait -PassThru
    $Out=@()
    if(Test-Path $Stdout){ $Out += @(Get-Content $Stdout) }
    if(Test-Path $Stderr){ $Out += @(Get-Content $Stderr) }
    foreach($Line in $Out){ Add-Line $Line }
    if(-not $AllowFailure -and $Process.ExitCode -ne 0){
        throw "${CheckpointId}: $Label failed with exit code $($Process.ExitCode)."
    }
    return [pscustomobject]@{ ExitCode=$Process.ExitCode; Output=$Out }
}
function Invoke-GitCapture {
    param(
        [Parameter(Mandatory)][string[]]$Arguments,
        [string]$WorkingDirectory=$RepositoryPath,
        [Parameter(Mandatory)][string]$Label,
        [switch]$AllowFailure
    )
    return Invoke-ProcessCapture -FilePath 'git.exe' -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -Label $Label -AllowFailure:$AllowFailure
}
function Get-GitText {
    param([string[]]$Arguments,[string]$WorkingDirectory=$RepositoryPath,[string]$Label='git_query')
    $Result=Invoke-GitCapture -Arguments $Arguments -WorkingDirectory $WorkingDirectory -Label $Label
    return (($Result.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) | Select-Object -Last 1).Trim()
}
function Get-GitBlob {
    param([string]$Revision,[string]$Path)
    $Result=Invoke-GitCapture -Arguments @('rev-parse',"$Revision`:$Path") -WorkingDirectory $RepositoryPath -Label 'rev_parse_blob' -AllowFailure
    if($Result.ExitCode -ne 0){ return $null }
    return (($Result.Output | Where-Object { $_ -match '^[0-9a-f]{40}$' }) | Select-Object -First 1)
}

try {
    Add-Section 'RIVERVIEW STEWARD STATUS EXACT-SCOPE PUBLICATION'
    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){ throw "${CheckpointId}: Riverview Git repository not found." }

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Local HEAD: $((git -C $RepositoryPath rev-parse HEAD).Trim())"
    Add-Line "Branch: $((git -C $RepositoryPath branch --show-current).Trim())"
    Add-Line "Publisher version: $ToolVersion"
    Add-Line "Expected remote base: $ExpectedRemoteBase"

    Add-Section 'CHARTER AND SCOPE ANCHOR'
    Add-Line 'Current dependency-ready waypoint remains RV-004.4 - Read-only MCP Relay.'
    Add-Line 'This stage publishes only the live-verified RIV-UI-0007 Steward Status repair.'
    Add-Line 'No PostgreSQL mutation, roadmap mutation, migration, MCP authority change, supervisor implementation, or Undercurrent exposure.'
    Add-Line 'Unrelated local RV-004.4 work must remain untouched.'

    Add-Section 'SELF-INSTALLATION'
    $CanonicalPublisher=Join-Path $RepositoryPath 'tools\powershell\synchronization\Publish-RiverviewStewardStatusRoadmapTimestamp.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $CanonicalPublisher) -Force | Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($CanonicalPublisher)){
        Copy-Item $PSCommandPath $CanonicalPublisher -Force
        Add-Line "Installed publisher: $CanonicalPublisher" Green
    }

    $ExactFiles=@(
        'src/riverview/status/server.py',
        'src/riverview/status/snapshot.py',
        'tools/powershell/status/Install-RiverviewStewardStatus.ps1',
        'tools/powershell/status/Repair-RiverviewStewardStatusRoadmapTimestamp.ps1',
        'tools/powershell/status/Restart-RiverviewStewardStatus.ps1',
        'tools/powershell/synchronization/Publish-RiverviewStewardStatusRoadmapTimestamp.ps1',
        'docs/operations/troubleshooting/checkpoints/RIV-UI-0007_ROADMAP_TIMESTAMP_SEMANTICS.md'
    )

    Add-Section 'LOCAL WORKING TREE SNAPSHOT'
    $BeforeStatus=@(git -C $RepositoryPath status --porcelain=v1 --untracked-files=all)
    foreach($Line in $BeforeStatus){ Add-Line $Line Yellow }

    Add-Section 'FETCH REMOTE MAIN'
    Invoke-GitCapture -Arguments @('fetch','--prune',$RemoteName,$RemoteBranch) -WorkingDirectory $RepositoryPath -Label 'git_fetch' | Out-Null
    $RemoteBase=Get-GitText -Arguments @('rev-parse',"$RemoteName/$RemoteBranch") -WorkingDirectory $RepositoryPath -Label 'remote_base'
    Add-Line "Observed remote base: $RemoteBase"
    if($RemoteBase -ne $ExpectedRemoteBase){
        throw "${CheckpointId}: Remote main differs from expected base $ExpectedRemoteBase. Stop for reinspection."
    }
    Add-Line 'Remote base verified.' Green

    $LocalBase=(git -C $RepositoryPath rev-parse HEAD).Trim()

    Add-Section 'TARGET COLLISION CHECK'
    foreach($Relative in $ExactFiles){
        $LocalBlob=Get-GitBlob -Revision $LocalBase -Path $Relative
        $RemoteBlob=Get-GitBlob -Revision "$RemoteName/$RemoteBranch" -Path $Relative
        if($null -ne $LocalBlob){
            if($null -eq $RemoteBlob -or $LocalBlob -ne $RemoteBlob){
                throw "${CheckpointId}: Remote target changed since local base: $Relative"
            }
            Add-Line "UNCHANGED REMOTE TARGET  $Relative"
        } else {
            if($null -ne $RemoteBlob){
                throw "${CheckpointId}: New local repair file already exists on remote main: $Relative"
            }
            Add-Line "NEW TARGET CLEAR         $Relative"
        }
    }

    Add-Section 'ISOLATED WORKTREE'
    $RuntimeRoot=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\publication'
    New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
    $WorktreePath=Join-Path $RuntimeRoot "steward-status-$((Get-Date).ToString('yyyyMMdd-HHmmss'))"
    Invoke-GitCapture -Arguments @('worktree','add','--detach',$WorktreePath,"$RemoteName/$RemoteBranch") -WorkingDirectory $RepositoryPath -Label 'worktree_add' | Out-Null
    $WorktreeCreated=$true
    Add-Line "Publication worktree: $WorktreePath" Green

    Add-Section 'COPY EXACT FILES'
    foreach($Relative in $ExactFiles){
        $Source=Join-Path $RepositoryPath ($Relative -replace '/','\')
        $Destination=Join-Path $WorktreePath ($Relative -replace '/','\')
        if(-not(Test-Path $Source)){ throw "${CheckpointId}: Missing source file: $Relative" }
        New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
        Copy-Item $Source $Destination -Force
        Add-Line "COPIED  $Relative"
    }

    Add-Section 'EXACT DIFF CHECK'
    $StatusResult=Invoke-GitCapture -Arguments @('status','--porcelain=v1','--untracked-files=all') -WorkingDirectory $WorktreePath -Label 'worktree_status'
    $Changed=@()
    foreach($Line in $StatusResult.Output){
        if($Line.Length -ge 4){ $Changed += (($Line.Substring(3).Trim()) -replace '\\','/') }
    }
    $Expected=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($File in $ExactFiles){ [void]$Expected.Add($File) }
    foreach($File in $Changed){
        if(-not $Expected.Contains($File)){ throw "${CheckpointId}: Out-of-scope worktree change: $File" }
    }
    foreach($File in $ExactFiles){
        if($Changed -notcontains $File){ throw "${CheckpointId}: Expected file produced no diff: $File" }
    }
    Add-Line 'Exact-scope diff check passed.' Green

    Add-Section 'PUBLICATION ACCEPTANCE'
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    Invoke-ProcessCapture -FilePath $Python -ArgumentList @('-m','compileall','-q',(Join-Path $WorktreePath 'src\riverview\status')) -WorkingDirectory $WorktreePath -Label 'compileall' | Out-Null
    Invoke-ProcessCapture -FilePath $Python -ArgumentList @('-m','ruff','check',(Join-Path $WorktreePath 'src\riverview\status\server.py'),(Join-Path $WorktreePath 'src\riverview\status\snapshot.py')) -WorkingDirectory $WorktreePath -Label 'ruff' | Out-Null
    Add-Line 'Publication static acceptance passed.' Green

    Add-Section 'STAGE AND COMMIT'
    foreach($Relative in $ExactFiles){
        Invoke-GitCapture -Arguments @('add','--',$Relative) -WorkingDirectory $WorktreePath -Label 'git_add' | Out-Null
    }
    $Staged=Invoke-GitCapture -Arguments @('diff','--cached','--name-only') -WorkingDirectory $WorktreePath -Label 'staged_names'
    $StagedNames=@($Staged.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_ -replace '\\','/' })
    if($StagedNames.Count -ne $ExactFiles.Count){ throw "${CheckpointId}: Staged file count mismatch." }
    foreach($Name in $StagedNames){ if(-not $Expected.Contains($Name)){ throw "${CheckpointId}: Out-of-scope staged file: $Name" } }
    $CommitMessagePath=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\steward-status\publisher-commit-message.txt'
    Write-Utf8NoBom -Path $CommitMessagePath -Content ($CommitMessage+[Environment]::NewLine)
    Invoke-GitCapture -Arguments @('commit','-F',$CommitMessagePath) -WorkingDirectory $WorktreePath -Label 'git_commit' | Out-Null
    $CommitId=Get-GitText -Arguments @('rev-parse','HEAD') -WorkingDirectory $WorktreePath -Label 'commit_id'
    Add-Line "Created commit: $CommitId" Green

    Add-Section 'REMOTE RACE CHECK'
    Invoke-GitCapture -Arguments @('fetch',$RemoteName,$RemoteBranch) -WorkingDirectory $RepositoryPath -Label 'git_refetch' | Out-Null
    $RemoteBeforePush=Get-GitText -Arguments @('rev-parse',"$RemoteName/$RemoteBranch") -WorkingDirectory $RepositoryPath -Label 'remote_before_push'
    if($RemoteBeforePush -ne $ExpectedRemoteBase){
        throw "${CheckpointId}: Remote main advanced during publication. Commit $CommitId was not pushed."
    }
    Add-Line 'Remote main remained stable.' Green

    Add-Section 'PUSH'
    Invoke-GitCapture -Arguments @('push',$RemoteName,"HEAD:$RemoteBranch") -WorkingDirectory $WorktreePath -Label 'git_push' | Out-Null

    Add-Section 'REMOTE VERIFICATION'
    $Ls=Invoke-GitCapture -Arguments @('ls-remote',$RemoteName,"refs/heads/$RemoteBranch") -WorkingDirectory $RepositoryPath -Label 'ls_remote'
    $RemoteVerified=$null
    foreach($Line in $Ls.Output){
        if($Line -match '^([0-9a-f]{40})\s+refs/heads/'){
            $RemoteVerified=$Matches[1]
            break
        }
    }
    if($null -eq $RemoteVerified){ throw "${CheckpointId}: Could not parse remote main SHA." }
    Add-Line "Expected remote commit: $CommitId"
    Add-Line "Observed remote commit: $RemoteVerified"
    if($RemoteVerified -ne $CommitId){ throw "${CheckpointId}: Remote verification mismatch." }
    Add-Line "REMOTE VERIFIED  $CommitId" Green

    Add-Section 'LOCAL PRESERVATION CHECK'
    $AfterStatus=@(git -C $RepositoryPath status --porcelain=v1 --untracked-files=all)
    foreach($Line in $AfterStatus){ Add-Line $Line }
    $Unexpected=@()
    foreach($Line in $AfterStatus){
        if($BeforeStatus -notcontains $Line -and $Line -notmatch 'Publish-RiverviewStewardStatusRoadmapTimestamp\.ps1$'){
            $Unexpected += $Line
        }
    }
    if($Unexpected.Count -gt 0){ throw "${CheckpointId}: Unexpected local working-tree change after publication." }
    Add-Line 'Active local RV-004.4 working tree preserved.' Green

    Add-Section 'PUBLICATION RESULT'
    Add-Line 'RIV-UI-0007 publication complete.' Green
    Add-Line "Verified remote commit: $CommitId" Green
    Add-Line "Commit message: $CommitMessage"
    Add-Line 'Local main intentionally remains at its prior commit because it contains active uncommitted RV-004.4 work.' Yellow
    Save-Report
}
catch {
    Add-Section 'STEWARD STATUS PUBLICATION BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'Do not claim GitHub publication unless REMOTE VERIFIED appears with the exact commit.' Yellow
    Save-Report
    throw
}
finally {
    if($WorktreeCreated -and $null -ne $WorktreePath){
        try {
            Start-Process -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'worktree','remove','--force',$WorktreePath) -Wait -WindowStyle Hidden
            Start-Process -FilePath 'git.exe' -ArgumentList @('-C',$RepositoryPath,'worktree','prune') -Wait -WindowStyle Hidden
        } catch {
            Write-Host "Warning: publication worktree cleanup may require manual review: $WorktreePath" -ForegroundColor Yellow
        }
    }
}
