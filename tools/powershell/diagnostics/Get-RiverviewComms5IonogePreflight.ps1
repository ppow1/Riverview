[CmdletBinding()]
param([string]$SshHostAlias = 'ionoge-control-01')

Clear-Host
$ErrorActionPreference = 'Continue'
Set-StrictMode -Version Latest

$Ssh = Get-Command ssh.exe -ErrorAction Stop
$RemoteScript = @'
set +e
printf 'hostname='; hostname
printf 'time='; date -Is
printf '\ncaddy_unit_state\n'
sudo -n systemctl show caddy -p ActiveState -p SubState -p MainPID -p FragmentPath -p DropInPaths 2>&1
printf '\nriverview_relevant_units\n'
sudo -n systemctl list-units --type=service --all --no-legend 2>/dev/null | grep -Ei 'caddy|comms|tunnel|riverview' | awk '{print $1, $2, $3, $4}' | head -60
printf '\nsanitized_caddy_route_lines\n'
sudo -n grep -niE 'riverview-comms|comms5|/mcp|reverse_proxy|11825|11826|11827' /etc/caddy/Caddyfile 2>/dev/null | sed -E '/authorization|bearer|secret|password|token|basicauth|basic_auth/Id' | head -100
printf '\nlisteners\n'
sudo -n ss -ltnp 2>/dev/null | awk 'NR == 1 || $4 ~ /:(80|443|11825|11826|11827)$/ {print}'
printf '\nestablished_tunnel_sockets\n'
sudo -n ss -tnp state established 2>/dev/null | awk 'NR == 1 || $4 ~ /:22$/ || $5 ~ /:22$/ {print}' | head -30
printf '\nloopback_upstream_status\n'
curl -sS --max-time 4 -o /dev/null -w 'comms5_loopback_http_status=%{http_code}\n' http://127.0.0.1:11826/mcp 2>&1
curl -sS --max-time 4 -o /dev/null -w 'oauth_loopback_health_status=%{http_code}\n' http://127.0.0.1:11827/healthz 2>&1
printf '\ncaddy_syntax_validation\n'
sudo -n caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile 2>&1 | head -20
'@

$SshArgs = @(
    '-T',
    '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=yes',
    '-o', 'ConnectTimeout=5',
    $SshHostAlias,
    'sudo -n bash -s'
)
$Result = $RemoteScript | & $Ssh.Source @SshArgs 2>&1
$SshExitCode = $LASTEXITCODE
$Report = @"
Riverview Comms5 Ionoge read-only preflight
SSH alias: $SshHostAlias
SSH exit code: $SshExitCode
No secrets, Authorization values, credentials, or request bodies are collected.

$($Result -join [Environment]::NewLine)
"@
$Report | Set-Clipboard
Write-Host $Report
