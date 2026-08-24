param(
    [ValidateSet('runtime', 'quest-dev', 'quest-cast')]
    [string]$Control,
    [ValidateSet('single', 'double', 'long')]
    [string]$Gesture = 'single',
    [string]$RepositoryPath = 'A:\Riverview\repo'
)

Clear-Host 2>$null
# Riverview Stream Deck initial operator control layer. Version: 1.0.0. Date: 2026-08-23.
# Purpose: bounded Runtime, Quest Dev, and Quest Cast Stream Deck actions.

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepositoryPath = (Resolve-Path -LiteralPath $RepositoryPath).Path
$ReportRoot = Join-Path $env:LOCALAPPDATA 'Riverview\StreamDeck\reports'
$RuntimeStart = Join-Path $RepositoryPath 'tools\powershell\runtime\Start-RiverviewRuntimeSupervisor.ps1'
$RuntimeStop = Join-Path $RepositoryPath 'tools\powershell\runtime\Stop-RiverviewRuntimeSupervisor.ps1'
$QuestMirror = Join-Path $RepositoryPath 'runtime\quest-observability\Quest-LeftEyeMirror.ps1'
$PowerShell7 = 'C:\Program Files\PowerShell\7\pwsh.exe'
$AdbCandidates = @(
    'C:\Users\wille\Downloads\platform-tools-latest-windows\platform-tools\adb.exe',
    'adb.exe'
)

function Write-Result([hashtable]$Result) {
    New-Item -ItemType Directory -Path $ReportRoot -Force | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $reportPath = Join-Path $ReportRoot ("riverview-stream-deck-{0}-{1}.json" -f $Control, $stamp)
    $Result.timestamp = (Get-Date).ToString('o')
    $Result.control = $Control
    $Result.gesture = $Gesture
    $Result.report_path = $reportPath
    $Result.clipboard = 'unavailable'
    $json = $Result | ConvertTo-Json -Depth 10
    try { Set-Clipboard -Value $json; $Result.clipboard = 'copied' } catch { }
    $json = $Result | ConvertTo-Json -Depth 10
    Set-Content -LiteralPath $reportPath -Value $json -Encoding UTF8
    $Result | ConvertTo-Json -Depth 10
}

function Find-Adb {
    foreach ($candidate in $AdbCandidates) {
        if ($candidate -eq 'adb.exe') {
            $command = Get-Command adb.exe -ErrorAction SilentlyContinue
            if ($command) { return $command.Source }
        } elseif (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    throw 'RIV-ADB-0001: ADB executable/tool discovery failed.'
}

function Get-QuestDevices([string]$AdbPath) {
    foreach ($line in @(& $AdbPath devices -l)) {
        if ($line -match '^\s*(\S+)\s+(device|unauthorized)\s*(.*)$') {
            $serial = $Matches[1]
            $state = $Matches[2]
            $details = $Matches[3]
            if ($details -match 'model:Quest_2|product:hollywood|device:hollywood|Quest') {
                [pscustomobject]@{
                    Serial = $serial
                    State = $state
                    Details = $details
                    Wireless = ($serial -match ':' -or $serial -match '_adb-tls-connect\._tcp')
                }
            }
        }
    }
}

function Test-QuestShell([string]$AdbPath, [string]$Serial) {
    $model = (& $AdbPath -s $Serial shell getprop ro.product.model 2>$null | Out-String).Trim()
    return $model -match 'Quest'
}

function Get-CurrentWirelessQuest([string]$AdbPath) {
    $devices = @(Get-QuestDevices $AdbPath)
    foreach ($device in @($devices | Where-Object { $_.State -eq 'device' -and $_.Wireless })) {
        if (Test-QuestShell $AdbPath $device.Serial) { return $device.Serial }
    }
    foreach ($line in @(& $AdbPath mdns services 2>$null | Where-Object { $_ -match '_adb-tls-connect\._tcp' })) {
        $endpoint = $null
        if ($line -match '(\d{1,3}(?:\.\d{1,3}){3}:\d+)') { $endpoint = $Matches[1] }
        elseif ($line -match '(\d{1,3}(?:\.\d{1,3}){3})\s+(\d{2,5})') { $endpoint = "$($Matches[1]):$($Matches[2])" }
        if ($endpoint) {
            & $AdbPath connect $endpoint | Out-Null
            if ((Test-QuestShell $AdbPath $endpoint)) { return $endpoint }
        }
    }
    return $null
}

function Ensure-QuestTransport {
    $adb = Find-Adb
    & $adb start-server | Out-Null
    $wireless = Get-CurrentWirelessQuest $adb
    if ($wireless) {
        return @{ ok = $true; serial = $wireless; transport = 'wireless'; adb = $adb; failure_class = $null }
    }
    $devices = @(Get-QuestDevices $adb)
    $usb = @($devices | Where-Object { $_.State -eq 'device' -and -not $_.Wireless })
    if ($usb.Count -gt 0) {
        $usbSerial = $usb[0].Serial
        $ip = $null
        foreach ($line in @(& $adb -s $usbSerial shell ip -o -4 addr show wlan0 2>$null)) {
            if ($line -match '\binet\s+(\d{1,3}(?:\.\d{1,3}){3})/') { $ip = $Matches[1]; break }
        }
        if (-not $ip) {
            $route = (& $adb -s $usbSerial shell ip route 2>$null | Out-String)
            if ($route -match 'src\s+(\d{1,3}(?:\.\d{1,3}){3})') { $ip = $Matches[1] }
        }
        if ($ip) {
            & $adb -s $usbSerial tcpip 5555 | Out-Null
            Start-Sleep -Seconds 2
            $endpoint = "$ip`:5555"
            & $adb connect $endpoint | Out-Null
            if (Test-QuestShell $adb $endpoint) {
                return @{ ok = $true; serial = $endpoint; transport = 'wireless-recovered-from-usb'; adb = $adb; failure_class = $null }
            }
        }
        return @{ ok = $true; serial = $usbSerial; transport = 'usb-fallback'; adb = $adb; failure_class = 'RIV-ADB-0003: wireless ADB establishment failed; USB remains authorized.' }
    }
    $unauthorized = @($devices | Where-Object { $_.State -eq 'unauthorized' })
    if ($unauthorized.Count -gt 0) {
        return @{ ok = $false; failure_class = 'RIV-ADB-0002: Quest device is visible but unauthorized; approve debugging in the headset.'; adb = $adb }
    }
    return @{ ok = $false; failure_class = 'RIV-ADB-0004: Quest device discovery failed; wake/connect/authorize the headset.'; adb = $adb }
}

function Invoke-Runtime {
    if (-not (Test-Path -LiteralPath $RuntimeStart -PathType Leaf) -or -not (Test-Path -LiteralPath $RuntimeStop -PathType Leaf)) {
        return Write-Result @{ state = 'blocked'; failure_class = 'RIV-RUN-0001: Riverview Runtime Supervisor launcher is unavailable.' }
    }
    $task = Get-ScheduledTask -TaskName 'Riverview Runtime Supervisor' -ErrorAction SilentlyContinue
    if ($Gesture -eq 'long') {
        & $RuntimeStop -RepositoryPath $RepositoryPath
        return Write-Result @{ state = 'stopped'; owner = 'Riverview Runtime Supervisor' }
    }
    if (-not $task) {
        return Write-Result @{ state = 'blocked'; failure_class = 'RIV-RUN-0002: unified lifecycle task is not installed.' }
    }
    if ($task.State -ne 'Running') { Start-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath; Start-Sleep -Seconds 2 }
    $state = (Get-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath).State.ToString()
    if ($state -ne 'Running') { return Write-Result @{ state = 'degraded'; failure_class = 'RIV-RUN-0003: supervisor did not reach Running state.' } }
    if ($Gesture -eq 'double') { Start-Process 'http://127.0.0.1:18082/' }
    return Write-Result @{ state = 'ready'; owner = 'Riverview Runtime Supervisor'; operator_ui = ($Gesture -eq 'double') }
}

function Invoke-QuestDev {
    $transport = Ensure-QuestTransport
    if (-not $transport.ok) { return Write-Result @{ state = 'blocked'; failure_class = $transport.failure_class } }
    if ($Gesture -eq 'long') {
        $owned = @(Get-Process scrcpy -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq 'Riverview Quest Live View' })
        foreach ($process in $owned) { Stop-Process -Id $process.Id -Force }
        if ($transport.transport -like 'wireless*') { & $transport.adb disconnect $transport.serial | Out-Null }
        return Write-Result @{ state = 'stopped'; transport = $transport.transport; serial = $transport.serial; owned_session = $true }
    }
    if (-not (Test-Path -LiteralPath $QuestMirror -PathType Leaf)) {
        return Write-Result @{ state = 'blocked'; failure_class = 'RIV-LIVEVIEW-0001: Quest live-view launcher is unavailable.' }
    }
    if (-not (Test-Path -LiteralPath $PowerShell7 -PathType Leaf)) {
        return Write-Result @{ state = 'blocked'; failure_class = 'RIV-LIVEVIEW-0002: verified PowerShell 7 executable is unavailable.'; executable = $PowerShell7 }
    }
    $existing = @(Get-Process scrcpy -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq 'Riverview Quest Live View' })
    if ($existing.Count -gt 0) {
        try { $shell = New-Object -ComObject WScript.Shell; [void]$shell.AppActivate($existing[0].Id) } catch { }
        return Write-Result @{ state = 'ready'; transport = $transport.transport; serial = $transport.serial; live_view = 'raised'; process_id = $existing[0].Id; executable = $PowerShell7 }
    }
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $PowerShell7; $psi.UseShellExecute = $true; $psi.WindowStyle = 'Normal'
    foreach ($arg in @('-NoProfile','-ExecutionPolicy','Bypass','-File',$QuestMirror,'-Serial',$transport.serial)) { [void]$psi.ArgumentList.Add($arg) }
    [void][System.Diagnostics.Process]::Start($psi)
    Start-Sleep -Seconds 3
    $started = @(Get-Process scrcpy -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq 'Riverview Quest Live View' })
    if ($started.Count -gt 0) {
        return Write-Result @{ state = 'ready'; transport = $transport.transport; serial = $transport.serial; live_view = 'running'; process_id = $started[0].Id; executable = $PowerShell7 }
    }
    return Write-Result @{ state = 'degraded'; transport = $transport.transport; serial = $transport.serial; live_view = 'launch_requested'; executable = $PowerShell7; failure_class = 'RIV-LIVEVIEW-0003: mirror launch requested but the owned window was not observed.' }
}

function Invoke-QuestCast {
    $metaApp = @(Get-StartApps | Where-Object { $_.Name -eq 'Meta Quest Developer Hub' })
    if ($Gesture -eq 'long') {
        $statePath = Join-Path $ReportRoot 'quest-cast-owned-session.json'
        if (Test-Path -LiteralPath $statePath) {
            $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
            $process = Get-Process -Id $state.pid -ErrorAction SilentlyContinue
            if ($process) { Stop-Process -Id $process.Id -Force }
            Remove-Item -LiteralPath $statePath -Force
            return Write-Result @{ state = 'stopped'; owned_session = $true }
        }
        return Write-Result @{ state = 'not_running'; owned_session = $false }
    }
    if ($metaApp.Count -gt 0) {
        return Write-Result @{ state = 'blocked'; failure_class = 'RIV-CAST-0001: Meta Quest Developer Hub is installed, but no verified local Meta casting executable, URI, or automation command was found; no casting launch was attempted.'; detected = 'Meta Quest Developer Hub' }
    }
    return Write-Result @{ state = 'blocked'; failure_class = 'RIV-CAST-0002: no installed/verifiable Meta Quest casting path was found.' }
}

switch ($Control) {
    'runtime' { Invoke-Runtime }
    'quest-dev' { Invoke-QuestDev }
    'quest-cast' { Invoke-QuestCast }
}
