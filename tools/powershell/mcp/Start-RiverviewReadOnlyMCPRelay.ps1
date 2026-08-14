# Riverview Read-Only MCP Relay Launcher
# Version: 0.9.3
# Purpose: Launch the local stdio-only RV-004.4 MCP server for an authorized MCP client.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\repo')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$RepositoryPath=(Resolve-Path $RepositoryPath).Path
$Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: Riverview virtual environment not found.' }

Push-Location $RepositoryPath
try {
    & $Python -m riverview.mcp.server
    if($LASTEXITCODE -ne 0){ throw "RIV-MCP-0006: MCP stdio server exited with code $LASTEXITCODE." }
}
finally {
    Pop-Location
}