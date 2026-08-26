# RUN-005A package-level self-repair entrypoint.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][guid]$ObjectiveId,
    [Parameter(Mandatory=$true)][guid]$StageId,
    [Parameter(Mandatory=$true)][string]$Worktree,
    [Parameter(Mandatory=$true)][string]$Adapter,
    [ValidateRange(1,10)][int]$MaxRepairsPerRoot = 3
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$env:PYTHONPATH = Join-Path $repoRoot 'src'
python -m riverview.campaign.package_runner `
    --objective-id $ObjectiveId `
    --stage-id $StageId `
    --worktree $Worktree `
    --adapter $Adapter `
    --max-repairs-per-root $MaxRepairsPerRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
