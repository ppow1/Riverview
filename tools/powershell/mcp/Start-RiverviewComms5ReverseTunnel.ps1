# Maintain the documented Windows-to-VPS Comms5 reverse tunnel.
# VPS 127.0.0.1:11826 -> Windows 127.0.0.1:11826.

[CmdletBinding()]
param([string]$SshKeyPath=(Join-Path $env:USERPROFILE '.ssh\id_ed25519'))

$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if(-not(Test-Path $SshKeyPath)){ throw 'RIV-COMMS5-0015: SSH identity file not found.' }

$existing=Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'ssh.exe' -and $_.CommandLine -match 'root@64\.227\.21\.54' -and
    $_.CommandLine -match '127\.0\.0\.1:11826:127\.0\.0\.1:11826'
}
if($existing){ exit 0 }

& ssh.exe -N -T `
    -o ExitOnForwardFailure=yes `
    -o ServerAliveInterval=30 `
    -o ServerAliveCountMax=3 `
    -o ConnectTimeout=10 `
    -i $SshKeyPath `
    -o IdentitiesOnly=yes `
    -R '127.0.0.1:11826:127.0.0.1:11826' `
    'root@64.227.21.54'
if($LASTEXITCODE -ne 0){ throw "RIV-COMMS5-0015: reverse tunnel exited with code $LASTEXITCODE." }
