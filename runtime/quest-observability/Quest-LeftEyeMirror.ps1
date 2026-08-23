param(
    [string]$Adb = 'C:\Users\wille\Downloads\platform-tools-latest-windows\platform-tools\adb.exe',
    [string]$Scrcpy = 'C:\Users\wille\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1\scrcpy.exe',
    [string]$Serial = '',
    [switch]$Uncropped
)

if (-not (Test-Path -LiteralPath $Adb)) { throw "ADB executable not found: $Adb" }
if (-not (Test-Path -LiteralPath $Scrcpy)) { throw "scrcpy executable not found: $Scrcpy" }

& $Adb start-server | Out-Null

function Get-QuestAdbDevices {
    $lines = @(& $Adb devices -l)
    foreach ($line in $lines) {
        if ($line -match '^\s*(\S+)\s+(device|unauthorized)\s*(.*)$') {
            $serial = $Matches[1]
            $state = $Matches[2]
            $details = $Matches[3]
            if ($details -match 'model:Quest_2|product:hollywood|device:hollywood|Quest') {
                [pscustomobject]@{
                    Serial = $serial
                    State = $state
                    Details = $details
                    Wireless = ($serial -match ':' -or $serial -match '_adb-tls-(connect|pairing)\._tcp')
                }
            }
        }
    }
}

function Test-QuestShell([string]$CandidateSerial) {
    $model = (& $Adb -s $CandidateSerial shell getprop ro.product.model 2>$null | Out-String).Trim()
    return $model -match 'Quest'
}

# First accept an already-authorized current wireless transport. Then use
# current mDNS advertisements to discover a transport created after reboot.
$Serial = ''
$devices = @(Get-QuestAdbDevices)
$wireless = @($devices | Where-Object { $_.State -eq 'device' -and $_.Wireless -and (Test-QuestShell $_.Serial) })
if ($wireless.Count -gt 0) {
    $Serial = $wireless[0].Serial
    Write-Host "Using authorized wireless Quest: $Serial" -ForegroundColor Green
}

if (-not $Serial) {
    $mdns = @(& $Adb mdns services 2>$null)
    foreach ($line in $mdns | Where-Object { $_ -match '_adb-tls-connect\._tcp' }) {
        $endpoint = $null
        if ($line -match '(\d{1,3}(?:\.\d{1,3}){3}:\d+)') {
            $endpoint = $Matches[1]
        }
        elseif ($line -match '(\d{1,3}(?:\.\d{1,3}){3})\s+(\d{2,5})') {
            $endpoint = "$($Matches[1]):$($Matches[2])"
        }
        if ($endpoint) {
            & $Adb connect $endpoint | Out-Null
            $candidate = @(Get-QuestAdbDevices | Where-Object { $_.State -eq 'device' -and $_.Serial -eq $endpoint })
            if ($candidate.Count -gt 0 -and (Test-QuestShell $endpoint)) {
                $Serial = $endpoint
                Write-Host "Using current mDNS wireless Quest: $Serial" -ForegroundColor Green
                break
            }
        }
    }
}

# If only USB is authorized, derive the current headset Wi-Fi address and
# enable the reversible session-level TCP transport. Never use a historical
# TLS serial or port as a fallback.
if (-not $Serial) {
    $usb = @($devices | Where-Object { $_.State -eq 'device' -and -not $_.Wireless -and (Test-QuestShell $_.Serial) })
    if ($usb.Count -gt 0) {
        $usbSerial = $usb[0].Serial
        $ipOutput = @(& $Adb -s $usbSerial shell ip -o -4 addr show wlan0 2>$null)
        $wifiIp = $null
        foreach ($line in $ipOutput) {
            if ($line -match '\binet\s+(\d{1,3}(?:\.\d{1,3}){3})/') {
                $wifiIp = $Matches[1]
                break
            }
        }
        if (-not $wifiIp) {
            $route = (& $Adb -s $usbSerial shell ip route 2>$null | Out-String)
            if ($route -match 'src\s+(\d{1,3}(?:\.\d{1,3}){3})') { $wifiIp = $Matches[1] }
        }
        if ($wifiIp) {
            Write-Host "USB Quest found; current Wi-Fi address: $wifiIp" -ForegroundColor Yellow
            & $Adb -s $usbSerial tcpip 5555 | Out-Null
            Start-Sleep -Seconds 2
            $endpoint = "$wifiIp`:5555"
            & $Adb connect $endpoint | Out-Null
            if ((Test-QuestShell $endpoint)) {
                $Serial = $endpoint
                Write-Host "Recovered authorized wireless Quest: $Serial" -ForegroundColor Green
            }
            else {
                Write-Warning "Wireless recovery failed; using authorized USB Quest: $usbSerial"
                $Serial = $usbSerial
            }
        }
        else {
            Write-Warning "Quest Wi-Fi address was not available; using authorized USB Quest: $usbSerial"
            $Serial = $usbSerial
        }
    }
}

if (-not $Serial) {
    $unauthorized = @(Get-QuestAdbDevices | Where-Object { $_.State -eq 'unauthorized' })
    if ($unauthorized.Count -gt 0) {
        throw 'Quest is visible but unauthorized. Put on the headset and approve the USB/wireless debugging prompt, then rerun this launcher.'
    }
    throw 'No Quest detected. Wake the headset, connect it by USB or to the workstation LAN, authorize debugging, and rerun this launcher.'
}

$scrcpyArgs = @(
    '--serial', $Serial,
    '--display-id=0',
    '--max-size=1920',
    '--video-bit-rate=16M',
    '--no-audio',
    '--keep-active',
    '--disable-screensaver',
    '--screen-off-timeout=86400',
    '--stay-awake',
    '--window-title', 'Riverview Quest Live View'
)
if (-not $Uncropped) {
    $scrcpyArgs = @('--serial', $Serial, '--display-id=0', '--crop=9000:8000:0:0') + $scrcpyArgs[3..($scrcpyArgs.Count - 1)]
}

& $Adb -s $Serial shell input keyevent KEYCODE_WAKEUP | Out-Null
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $Scrcpy
$startInfo.UseShellExecute = $false
foreach ($argument in $scrcpyArgs) {
    [void]$startInfo.ArgumentList.Add($argument)
}
$mirror = [System.Diagnostics.Process]::Start($startInfo)
try {
    while (-not $mirror.HasExited) {
        Start-Sleep -Seconds 5
        if (-not $mirror.HasExited) {
            & $Adb -s $Serial shell input keyevent KEYCODE_WAKEUP | Out-Null
        }
    }
}
finally {
    if (-not $mirror.HasExited) { Stop-Process -Id $mirror.Id -Force }
}
