param(
    [string]$ProfilesRoot = 'C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\ProfilesV3',
    [string]$RingConfig = 'A:\Riverview\repo\config\stream_deck\Riverview-Physical-Profile-Ring.json',
    [string]$BackupRoot = 'C:\Users\wille\AppData\Roaming\Elgato\StreamDeck-Backups'
)

Clear-Host 2>$null
# Repair the native Elgato profile ring only. Version: 1.0.0. Date: 2026-08-24.

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not (Test-Path -LiteralPath $ProfilesRoot -PathType Container)) { throw 'RIV-SD-RING-0001: ProfilesV3 root not found.' }
if (-not (Test-Path -LiteralPath $RingConfig -PathType Leaf)) { throw 'RIV-SD-RING-0001: profile ring configuration not found.' }

$config = Get-Content -LiteralPath $RingConfig -Raw | ConvertFrom-Json
$ordered = @($config.order)
if ($ordered.Count -lt 2) { throw 'RIV-SD-RING-0002: at least two profiles are required.' }

$profileDirs = @{}
foreach ($entry in $ordered) {
    $dir = Join-Path $ProfilesRoot ("{0}.sdProfile" -f $entry.uuid.ToUpperInvariant())
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "RIV-SD-RING-0003: profile directory missing for $($entry.name): $dir" }
    $manifestPath = Join-Path $dir 'manifest.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.Name -ne $entry.name) { throw "RIV-SD-RING-0004: profile name mismatch for $($entry.uuid): $($manifest.Name)" }
    if ($manifest.Device.Model -ne $config.device_model) { throw "RIV-SD-RING-0005: profile is not applicable to $($config.device_model): $($entry.name)" }
    $profileDirs[$entry.uuid.ToLowerInvariant()] = $dir
}

New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
$backup = Join-Path $BackupRoot ("ProfilesV3-profile-ring-{0}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
Copy-Item -LiteralPath $ProfilesRoot -Destination $backup -Recurse -Force

function New-ProfileAction([string]$target, [string]$title) {
    return [ordered]@{
        ActionID = [guid]::NewGuid().ToString()
        LinkedTitle = $true
        Name = 'Switch Profile'
        Plugin = [ordered]@{ Name = 'Switch Profile'; UUID = 'com.elgato.streamdeck.profile.rotate'; Version = '1.0' }
        Resources = $null
        Settings = [ordered]@{ DeviceUUID = ''; PageIndex = 1; ProfileUUID = $target }
        State = 0
        States = @([ordered]@{ FontFamily = ''; FontSize = 14; FontStyle = ''; FontUnderline = $false; OutlineThickness = 2; ShowTitle = $true; Title = $title; TitleAlignment = 'middle'; TitleColor = '#ffffff' })
        UUID = 'com.elgato.streamdeck.profile.rotate'
    }
}

function Set-Action([object]$actions, [string]$position, [object]$action) {
    $actions | Add-Member -MemberType NoteProperty -Name $position -Value $action -Force
}

for ($i = 0; $i -lt $ordered.Count; $i++) {
    $entry = $ordered[$i]
    $currentUuid = $entry.uuid.ToLowerInvariant()
    $previousUuid = $ordered[($i - 1 + $ordered.Count) % $ordered.Count].uuid.ToLowerInvariant()
    $nextUuid = $ordered[($i + 1) % $ordered.Count].uuid.ToLowerInvariant()
    $profileDir = $profileDirs[$currentUuid]
    $profileManifest = Get-Content (Join-Path $profileDir 'manifest.json') -Raw | ConvertFrom-Json
    $activePages = @($profileManifest.Pages.Pages)
    foreach ($pageUuid in $activePages) {
        $pagePath = Join-Path $profileDir ("Profiles\{0}\manifest.json" -f $pageUuid)
        if (-not (Test-Path -LiteralPath $pagePath -PathType Leaf)) { throw "RIV-SD-RING-0006: active page manifest missing: $pagePath" }
        $page = Get-Content -LiteralPath $pagePath -Raw | ConvertFrom-Json
        $actions = $page.Controllers[0].Actions
        $previousPosition = '7,1'
        $nextPosition = '7,2'
        if ($entry.name -eq 'Windows Shutdown Menu XL') {
            $previousPosition = '6,3'
            $nextPosition = '7,3'
            $actions.PSObject.Properties.Remove('0,0')
        }
        Set-Action $actions $previousPosition (New-ProfileAction $previousUuid '◀ PROFILE')
        Set-Action $actions $nextPosition (New-ProfileAction $nextUuid 'PROFILE ▶')
        $page | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $pagePath -Encoding UTF8
    }
}

# Validate the resulting edge graph directly from the installed manifests.
$next = @{}
$previous = @{}
for ($i = 0; $i -lt $ordered.Count; $i++) {
    $entry = $ordered[$i]
    $expectedPrevious = $ordered[($i - 1 + $ordered.Count) % $ordered.Count].uuid.ToLowerInvariant()
    $expectedNext = $ordered[($i + 1) % $ordered.Count].uuid.ToLowerInvariant()
    $dir = $profileDirs[$entry.uuid.ToLowerInvariant()]
    $pageUuid = (Get-Content (Join-Path $dir 'manifest.json') -Raw | ConvertFrom-Json).Pages.Current
    $page = Get-Content (Join-Path $dir ("Profiles\{0}\manifest.json" -f $pageUuid)) -Raw | ConvertFrom-Json
    $actions = $page.Controllers[0].Actions
    if ($entry.name -eq 'Windows Shutdown Menu XL') {
        $previous[$entry.uuid.ToLowerInvariant()] = ([string]$actions.'6,3'.Settings.ProfileUUID).ToLowerInvariant()
        $next[$entry.uuid.ToLowerInvariant()] = ([string]$actions.'7,3'.Settings.ProfileUUID).ToLowerInvariant()
    } else {
        $previous[$entry.uuid.ToLowerInvariant()] = ([string]$actions.'7,1'.Settings.ProfileUUID).ToLowerInvariant()
        $next[$entry.uuid.ToLowerInvariant()] = ([string]$actions.'7,2'.Settings.ProfileUUID).ToLowerInvariant()
    }
    if ($previous[$entry.uuid.ToLowerInvariant()] -ne $expectedPrevious -or $next[$entry.uuid.ToLowerInvariant()] -ne $expectedNext) { throw "RIV-SD-RING-0007: edge validation failed for $($entry.name)." }
}

foreach ($start in $ordered) {
    $seen = @{}
    $cursor = $start.uuid.ToLowerInvariant()
    for ($step = 0; $step -lt $ordered.Count; $step++) {
        if ($seen.ContainsKey($cursor)) { throw 'RIV-SD-RING-0008: NEXT cycle repeats before visiting every profile.' }
        $seen[$cursor] = $true
        $cursor = $next[$cursor]
    }
    if ($cursor -ne $start.uuid.ToLowerInvariant() -or $seen.Count -ne $ordered.Count) { throw 'RIV-SD-RING-0009: NEXT ring validation failed.' }
    $seen.Clear(); $cursor = $start.uuid.ToLowerInvariant()
    for ($step = 0; $step -lt $ordered.Count; $step++) {
        if ($seen.ContainsKey($cursor)) { throw 'RIV-SD-RING-0010: PREVIOUS cycle repeats before visiting every profile.' }
        $seen[$cursor] = $true
        $cursor = $previous[$cursor]
    }
    if ($cursor -ne $start.uuid.ToLowerInvariant() -or $seen.Count -ne $ordered.Count) { throw 'RIV-SD-RING-0011: PREVIOUS ring validation failed.' }
}

[pscustomobject]@{ state = 'ready'; profile_count = $ordered.Count; backup = $backup; next_edges = $next; previous_edges = $previous } | ConvertTo-Json -Depth 10
