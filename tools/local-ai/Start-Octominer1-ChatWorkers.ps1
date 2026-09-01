# Recover/start both provisional OCTOMINER1 local AI workers.
# This is a recovery/operator convenience template, not the final Riverview UI integration.

param(
    [string]$HostIp = '192.168.1.160',
    [string]$User = 'root',
    [string]$Password = 'test',
    [switch]$SkipWake
)

Clear-Host
$ErrorActionPreference = 'Stop'

$OctoMac = '00:e0:4c:6b:05:a9'
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$QwenScript = Join-Path $RepoRoot 'tools\local-ai\Start-Octominer1-Qwen3060Chat.ps1'
$GemmaScript = Join-Path $RepoRoot 'tools\local-ai\Start-Octominer1-GemmaP100VL.ps1'

function Test-SshPort {
    param([string]$Ip)
    try {
        $tcp = [System.Net.Sockets.TcpClient]::new()
        $iar = $tcp.BeginConnect($Ip,22,$null,$null)
        $ok = $iar.AsyncWaitHandle.WaitOne(1000) -and $tcp.Connected
        if ($ok) { $tcp.EndConnect($iar) }
        $tcp.Dispose()
        return $ok
    } catch { return $false }
}

function Send-WakeOnLan {
    param([string]$Mac)
    $clean = $Mac -replace '[:-]',''
    $macBytes = for ($i=0; $i -lt 12; $i+=2) { [Convert]::ToByte($clean.Substring($i,2),16) }
    [byte[]]$packet = (,[byte]0xFF * 6) + ($macBytes * 16)
    $udp = [System.Net.Sockets.UdpClient]::new()
    $udp.EnableBroadcast = $true
    [void]$udp.Send($packet,$packet.Length,'255.255.255.255',9)
    $udp.Dispose()
}

if (-not (Test-SshPort $HostIp)) {
    if ($SkipWake) { throw "OCTOMINER1 SSH is down and -SkipWake was supplied." }
    Write-Host "OCTOMINER1 is not reachable; sending WOL to $OctoMac..." -ForegroundColor Yellow
    Send-WakeOnLan $OctoMac
    $deadline = (Get-Date).AddMinutes(5)
    while ((Get-Date) -lt $deadline -and -not (Test-SshPort $HostIp)) {
        Start-Sleep -Seconds 5
    }
    if (-not (Test-SshPort $HostIp)) { throw 'OCTOMINER1 did not expose SSH within five minutes.' }
}

Write-Host 'OCTOMINER1 SSH reachable.' -ForegroundColor Green

& $QwenScript -HostIp $HostIp -User $User -Password $Password
& $GemmaScript -HostIp $HostIp -User $User -Password $Password

Write-Host ''
Write-Host '=== PROVISIONAL LOCAL AI WORKERS READY ===' -ForegroundColor Green
Write-Host "Qwen 3060 chat : http://$HostIp`:8094/v1/chat/completions"
Write-Host "Gemma P100 VLM : http://$HostIp`:8095/v1/chat/completions"
Write-Host ''
Write-Host 'Recovery/report: docs/operations/LOCAL_AI_CHAT_WORKER_TESTING_AND_STARTUP.md'
