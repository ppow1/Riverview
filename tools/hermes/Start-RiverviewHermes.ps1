<#
.SYNOPSIS
    Launch a Riverview-bound Hermes engineering session with automatic attention routing.
.VERSION
    1.0.0
.DATE
    2026-08-27
#>
CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$PluginName = 'riverview-steward-attention'
$PluginPath = Join-Path $RepositoryRoot '.hermes\plugins\riverview-steward-attention\plugin.yaml'

if (-not (Test-Path -LiteralPath (Join-Path $RepositoryRoot 'AI_HINTS.md'))) {
    throw "RIV-HERMES-LAUNCH-0001: repository root is not Riverview: $RepositoryRoot"
}
if (-not (Test-Path -LiteralPath $PluginPath)) {
    throw "RIV-HERMES-LAUNCH-0002: required project plugin is missing: $PluginPath"
}

$env:HERMES_ENABLE_PROJECT_PLUGINS = '1'
$env:RIVERVIEW_HERMES_ENGINEERING = '1'

Push-Location $RepositoryRoot
try {
    # Project plugins are discovered only when opted in, and the generic
    # plugins enable command intentionally does not install project plugins.
    # Extend the existing supported config list without replacing its entries.
    $configured = @()
    try {
        $configured = @(& hermes config get plugins.enabled 2>&1 | ForEach-Object {
            if ($_ -match '^\s*-\s+(.+)$') {
                $Matches[1].Trim()
            }
        })
    }
    catch {
        $configured = @()
    }
    if ($configured -notcontains $PluginName) {
        $configured += $PluginName
        $encoded = $configured | ConvertTo-Json -Compress
        & hermes config set plugins.enabled $encoded
        if ($LASTEXITCODE -ne 0) {
            throw "RIV-HERMES-LAUNCH-0003: Hermes project-plugin enablement failed ($LASTEXITCODE)."
        }
    }

    & hermes @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
