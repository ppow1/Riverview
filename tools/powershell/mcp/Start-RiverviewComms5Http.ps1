# Start the loopback Comms5 Streamable HTTP backend.
# The approved Caddy ingress must proxy /comms5/mcp to 127.0.0.1:11826.

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\repo')

$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$RepositoryPath=(Resolve-Path $RepositoryPath).Path
$Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
if(-not(Test-Path $Python)){ throw 'RIV-COMMS5-0015: Riverview virtual environment not found.' }

$listener=Get-NetTCPConnection -State Listen -LocalAddress '127.0.0.1' -LocalPort 11826 -ErrorAction SilentlyContinue
if($listener){ throw "RIV-COMMS5-0015: port 11826 is already owned by PID $($listener.OwningProcess). Stop and diagnose that owner; do not kill it automatically." }

Push-Location $RepositoryPath
try {
    $env:PYTHONPATH='src'
    $env:RIVERVIEW_COMMS5_HOST='127.0.0.1'
    $env:RIVERVIEW_COMMS5_PORT='11826'
    & $Python -m riverview.mcp.comms5_http_server
    if($LASTEXITCODE -ne 0){ throw "RIV-COMMS5-0015: Comms5 HTTP service exited with code $LASTEXITCODE." }
}
finally { Pop-Location }
