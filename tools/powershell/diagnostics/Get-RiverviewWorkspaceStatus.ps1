# Riverview Workspace Status Tool
# Version: 1.2.0
# Purpose: Install this reusable diagnostic tool, inspect the local Riverview Git workspace, and preserve a clean report.
# Updated: 2026-08-14

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$RepositoryPath = 'A:\Riverview\standalone'
)

Clear-Host
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ToolVersion = [version]'1.2.0'
$ToolFileName = 'Get-RiverviewWorkspaceStatus.ps1'
$InstalledRelativePath = 'tools\powershell\diagnostics'
$TranscriptPath = Join-Path ([System.IO.Path]::GetTempPath()) "Riverview-WorkspaceStatus-$([guid]::NewGuid().ToString('N')).txt"
$TranscriptStarted = $false

function Get-CleanTranscriptReport {
    param([Parameter(Mandatory)][string]$TranscriptFile)

    if (-not (Test-Path -LiteralPath $TranscriptFile -PathType Leaf)) {
        throw "The diagnostic transcript was not created: $TranscriptFile"
    }

    $Lines = @(Get-Content -LiteralPath $TranscriptFile)
    $DelimiterIndexes = @(
        for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
            if ($Lines[$Index] -match '^\*{20,}$') {
                $Index
            }
        }
    )

    if ($DelimiterIndexes.Count -lt 4) {
        throw 'The PowerShell transcript did not contain the expected report boundaries.'
    }

    $FirstReportLine = $DelimiterIndexes[1] + 1
    $LastReportLine = $DelimiterIndexes[$DelimiterIndexes.Count - 2] - 1

    if ($LastReportLine -lt $FirstReportLine) {
        throw 'The PowerShell transcript contained no diagnostic report body.'
    }

    return (($Lines[$FirstReportLine..$LastReportLine] -join [Environment]::NewLine).Trim() + [Environment]::NewLine)
}

function Copy-ReportToClipboard {
    param([Parameter(Mandatory)][string]$Report)

    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
        Set-Clipboard -Value $Report
        return
    }

    if (Get-Command clip.exe -ErrorAction SilentlyContinue) {
        $Report | & clip.exe
        if ($LASTEXITCODE -ne 0) {
            throw "clip.exe failed with exit code $LASTEXITCODE."
        }
        return
    }

    throw 'Neither Set-Clipboard nor clip.exe is available.'
}

function Write-Section {
    param([Parameter(Mandatory)][string]$Title)

    Write-Host "`n=== $Title ===" -ForegroundColor Cyan
}

function Invoke-Git {
    param(
        [Parameter(Mandatory)][string[]]$Arguments,
        [switch]$AllowFailure
    )

    $Output = & git @Arguments 2>&1
    $ExitCode = $LASTEXITCODE

    if (($ExitCode -ne 0) -and (-not $AllowFailure)) {
        throw "Git command failed (exit $ExitCode): git $($Arguments -join ' ')`n$($Output -join "`n")"
    }

    return [pscustomobject]@{
        ExitCode = $ExitCode
        Output   = @($Output | ForEach-Object { "$_" })
    }
}

function Get-ScriptVersion {
    param([Parameter(Mandatory)][string]$Path)

    $VersionLine = Get-Content -LiteralPath $Path -TotalCount 12 |
        Where-Object { $_ -match '^# Version:\s*(?<Version>\d+\.\d+\.\d+)\s*$' } |
        Select-Object -First 1

    if (-not $VersionLine) {
        throw "No semantic '# Version:' header was found in: $Path"
    }

    [version]([regex]::Match($VersionLine, '^# Version:\s*(?<Version>\d+\.\d+\.\d+)\s*$').Groups['Version'].Value)
}

Start-Transcript -LiteralPath $TranscriptPath -Force | Out-Null
$TranscriptStarted = $true

Write-Section -Title 'RIVERVIEW WORKSPACE VALIDATION'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git was not found on PATH.'
}

if (-not (Test-Path -LiteralPath $RepositoryPath -PathType Container)) {
    throw "Riverview repository was not found at: $RepositoryPath"
}

$ResolvedRepositoryPath = (Resolve-Path -LiteralPath $RepositoryPath).Path
$GitDirectory = Join-Path $ResolvedRepositoryPath '.git'

if (-not (Test-Path -LiteralPath $GitDirectory -PathType Container)) {
    throw "The directory is not a Git repository: $ResolvedRepositoryPath"
}

Set-Location -LiteralPath $ResolvedRepositoryPath

$InsideWorkTree = Invoke-Git -Arguments @('rev-parse', '--is-inside-work-tree')
if (($InsideWorkTree.Output -join '').Trim() -ne 'true') {
    throw "Git did not recognize the repository work tree: $ResolvedRepositoryPath"
}

Write-Host "Repository validated: $ResolvedRepositoryPath" -ForegroundColor Green

Write-Section -Title 'SELF-INSTALLATION'

if (-not $PSCommandPath) {
    throw 'The script must be executed from a saved .ps1 file so it can install a reusable repository copy.'
}

$SourcePath = (Resolve-Path -LiteralPath $PSCommandPath).Path
$InstallDirectory = Join-Path $ResolvedRepositoryPath $InstalledRelativePath
$InstalledPath = Join-Path $InstallDirectory $ToolFileName

New-Item -ItemType Directory -Path $InstallDirectory -Force | Out-Null

$SourceVersion = Get-ScriptVersion -Path $SourcePath
if ($SourceVersion -ne $ToolVersion) {
    throw "Internal version mismatch: header=$SourceVersion runtime=$ToolVersion"
}

if ($SourcePath -ieq $InstalledPath) {
    Write-Host "Running installed repository tool: $InstalledPath" -ForegroundColor Green
}
elseif (Test-Path -LiteralPath $InstalledPath -PathType Leaf) {
    $InstalledVersion = Get-ScriptVersion -Path $InstalledPath
    $SourceHash = (Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash
    $InstalledHash = (Get-FileHash -LiteralPath $InstalledPath -Algorithm SHA256).Hash

    if ($InstalledVersion -gt $SourceVersion) {
        throw "A newer repository copy already exists: $InstalledPath (installed $InstalledVersion; downloaded $SourceVersion)"
    }

    if (($InstalledVersion -eq $SourceVersion) -and ($InstalledHash -ne $SourceHash)) {
        throw "The repository contains different content with the same version. Refusing to overwrite: $InstalledPath"
    }

    if ($InstalledHash -eq $SourceHash) {
        Write-Host "Repository tool is already current: $InstalledPath" -ForegroundColor Green
    }
    else {
        $BackupPath = "$InstalledPath.pre-$SourceVersion.bak"
        Copy-Item -LiteralPath $InstalledPath -Destination $BackupPath -Force
        Copy-Item -LiteralPath $SourcePath -Destination $InstalledPath -Force
        Write-Host "Updated repository tool: $InstalledPath" -ForegroundColor Green
        Write-Host "Previous copy preserved: $BackupPath" -ForegroundColor Yellow
    }
}
else {
    Copy-Item -LiteralPath $SourcePath -Destination $InstalledPath
    Write-Host "Installed repository tool: $InstalledPath" -ForegroundColor Green
}

$InstalledHashAfter = (Get-FileHash -LiteralPath $InstalledPath -Algorithm SHA256).Hash
$SourceHashAfter = (Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash
if ($InstalledHashAfter -ne $SourceHashAfter) {
    throw "Self-installation verification failed: $InstalledPath"
}

Write-Section -Title 'GIT STATUS'
$Status = Invoke-Git -Arguments @('status', '--short', '--branch')
$Status.Output | ForEach-Object { Write-Host $_ }

Write-Section -Title 'CONFIGURED REMOTES'
$Remotes = Invoke-Git -Arguments @('remote', '-v')
if ($Remotes.Output.Count -eq 0) {
    Write-Host 'No Git remotes are configured.' -ForegroundColor Yellow
}
else {
    $Remotes.Output | ForEach-Object { Write-Host $_ }
}

Write-Section -Title 'LOCAL CHANGE SUMMARY'
$ChangedFiles = Invoke-Git -Arguments @('status', '--short')
if ($ChangedFiles.Output.Count -eq 0) {
    Write-Host 'No local changes detected.' -ForegroundColor Green
}
else {
    $ChangedFiles.Output | ForEach-Object { Write-Host $_ }
}

Write-Section -Title 'TRACKED CHANGE STATISTICS'
$DiffStat = Invoke-Git -Arguments @('diff', '--stat')
if ($DiffStat.Output.Count -eq 0) {
    Write-Host 'No unstaged tracked-file differences detected.'
}
else {
    $DiffStat.Output | ForEach-Object { Write-Host $_ }
}

$CachedDiffStat = Invoke-Git -Arguments @('diff', '--cached', '--stat')
if ($CachedDiffStat.Output.Count -gt 0) {
    Write-Host "`nStaged differences:" -ForegroundColor Yellow
    $CachedDiffStat.Output | ForEach-Object { Write-Host $_ }
}

Write-Section -Title 'RECENT LOCAL COMMITS'
$Commits = Invoke-Git -Arguments @('log', '-n', '5', '--date=iso-strict', '--pretty=format:%h %ad %s') -AllowFailure
if ($Commits.ExitCode -eq 0) {
    $Commits.Output | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host 'No local commits exist yet.' -ForegroundColor Yellow
}

Write-Section -Title 'RESULT'
Write-Host 'Inspection completed without committing or pushing.' -ForegroundColor Green
Write-Host "Reusable tool: $InstalledPath" -ForegroundColor Green
Write-Host "Tool version:   $ToolVersion" -ForegroundColor Green

if ($TranscriptStarted) {
    Stop-Transcript | Out-Null
    $TranscriptStarted = $false
}

$CleanReport = Get-CleanTranscriptReport -TranscriptFile $TranscriptPath
$WorkspaceRoot = Split-Path -Parent $ResolvedRepositoryPath
$ReportDirectory = Join-Path $WorkspaceRoot 'runtime\diagnostics\workspace-status'
$ReportTimestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$DurableReportPath = Join-Path $ReportDirectory "Riverview-WorkspaceStatus-$ReportTimestamp.txt"

New-Item -ItemType Directory -Path $ReportDirectory -Force | Out-Null
Set-Content -LiteralPath $DurableReportPath -Value $CleanReport -Encoding utf8
Copy-ReportToClipboard -Report $CleanReport
Remove-Item -LiteralPath $TranscriptPath -Force

Write-Host "`nThe complete report is now on the Windows clipboard." -ForegroundColor Cyan
Write-Host "Durable report: $DurableReportPath" -ForegroundColor Green
Write-Host 'Paste it directly into the Riverview conversation.' -ForegroundColor Cyan
