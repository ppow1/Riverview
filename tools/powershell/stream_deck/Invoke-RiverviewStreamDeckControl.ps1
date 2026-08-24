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
$OperatorUrl = 'http://127.0.0.1:18082/'
$OperatorHealthUrl = 'http://127.0.0.1:18082/health'
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
    foreach ($line in @(& $AdbPath mdns services 2>$null | Where-Object { $_ -match '(_adb\._tcp|_adb-tls-connect\._tcp)' })) {
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

function Test-OperatorHealth {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $OperatorHealthUrl -TimeoutSec 3
        return ($response.StatusCode -eq 200)
    } catch { return $false }
}

function Wait-OperatorHealth([int]$TimeoutSeconds = 60) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-OperatorHealth) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Invoke-OperatorSupervisorRequest([string]$Operation, [int]$TimeoutSeconds = 30) {
    $requestDir = Join-Path $RepositoryPath 'runtime\riverview-supervisor\requests'
    $resultDir = Join-Path $requestDir 'results'
    New-Item -ItemType Directory -Path $requestDir,$resultDir -Force | Out-Null
    $id = [guid]::NewGuid().ToString()
    $name = "$id.json"
    $requestPath = Join-Path $requestDir $name
    $resultPath = Join-Path $resultDir $name
    $payload = @{ operation = $Operation; service_id = 'operator'; request_id = $id } | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($requestPath, $payload, [System.Text.UTF8Encoding]::new($false))
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath $resultPath) {
            $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
            Remove-Item -LiteralPath $resultPath -Force
            return $result
        }
        Start-Sleep -Milliseconds 250
    }
    throw 'RIV-RUN-0004: Operator supervisor request timed out.'
}

function Get-OperatorProcess {
    $listener = @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 18082 -State Listen -ErrorAction SilentlyContinue)
    foreach ($connection in $listener) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($connection.OwningProcess)" -ErrorAction SilentlyContinue
        if ($process -and $process.CommandLine -match '-m\s+riverview\.operator\.live_service(?:\s|$)') { return $process }
    }
    return $null
}

function Ensure-Operator {
    if (Test-OperatorHealth) { return @{ state = 'running'; started = $false; process = (Get-OperatorProcess) } }
    $task = Get-ScheduledTask -TaskName 'Riverview Runtime Supervisor' -ErrorAction SilentlyContinue
    if (-not $task) { return @{ state = 'blocked'; failure_class = 'RIV-RUN-0002: canonical Operator lifecycle task is not installed.' } }
    if ($task.State -ne 'Running') { Start-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath }
    if (Wait-OperatorHealth) { return @{ state = 'running'; started = $true; process = (Get-OperatorProcess) } }
    return @{ state = 'starting'; started = $true; failure_class = 'RIV-RUN-0003: Operator HTTP health did not converge on port 18082.' }
}

function Invoke-Runtime {
    if (-not (Test-Path -LiteralPath $RuntimeStart -PathType Leaf)) {
        return Write-Result @{ state = 'blocked'; failure_class = 'RIV-RUN-0001: canonical Operator lifecycle launcher is unavailable.' }
    }
    if ($Gesture -eq 'long') {
        if (-not (Test-OperatorHealth)) { return Write-Result @{ state = 'stopped'; owner = 'Riverview Operator HTTP server'; port = 18082 } }
        $task = Get-ScheduledTask -TaskName 'Riverview Runtime Supervisor' -ErrorAction SilentlyContinue
        if ($task -and $task.State -eq 'Running') {
            $result = Invoke-OperatorSupervisorRequest -Operation 'stop_service'
            if (-not $result.ok) { return Write-Result @{ state = 'degraded'; failure_class = [string]$result.error } }
        } else {
            $process = Get-OperatorProcess
            if ($process) { Stop-Process -Id $process.ProcessId -Force }
        }
        if (Wait-OperatorHealth 5) { return Write-Result @{ state = 'degraded'; failure_class = 'RIV-RUN-0005: Operator HTTP server did not stop.' } }
        return Write-Result @{ state = 'stopped'; owner = 'Riverview Operator HTTP server'; port = 18082 }
    }
    $result = Ensure-Operator
    if ($result.state -ne 'running') { return Write-Result $result }
    if ($Gesture -eq 'double') { Start-Process $OperatorUrl }
    return Write-Result @{ state = 'ready'; owner = 'Riverview Operator HTTP server'; port = 18082; health_url = $OperatorHealthUrl; process_id = $result.process.ProcessId; operator_ui = ($Gesture -eq 'double') }
}

function Invoke-QuestDev {
    $transport = Ensure-QuestTransport
    if (-not $transport.ok) { return Write-Result @{ state = 'blocked'; failure_class = $transport.failure_class } }
    if ($Gesture -eq 'long') {
        $owned = @(Get-Process scrcpy -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq 'Riverview Quest Live View' })
        foreach ($process in $owned) { Stop-Process -Id $process.Id -Force }
        return Write-Result @{ state = 'stopped'; transport = $transport.transport; serial = $transport.serial; owned_session = $true; adb_preserved = ($transport.transport -like 'wireless*') }
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
    $psi.FileName = $PowerShell7; $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    foreach ($arg in @('-NoProfile','-ExecutionPolicy','Bypass','-File',$QuestMirror,'-Serial',$transport.serial)) { [void]$psi.ArgumentList.Add($arg) }
    [void][System.Diagnostics.Process]::Start($psi)
    $started = @()
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline) {
        $started = @(Get-Process scrcpy -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq 'Riverview Quest Live View' })
        if ($started.Count -gt 0) { break }
        Start-Sleep -Milliseconds 250
    }
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
