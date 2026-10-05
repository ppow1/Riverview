# Riverview Steward Status Launcher
# Version: 0.7.0
# Purpose: Run the localhost-only Steward Status server in the foreground.
# Updated: 2026-08-14

[CmdletBinding()]
param(
    [string]$RepositoryPath='A:\Riverview\standalone',
    [int]$Port=8770,
    [string]$SnailRuntime=''
)

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
if(-not(Test-Path $Python)){throw 'RIV-UI-0005: Riverview Python environment was not found.'}
if([string]::IsNullOrWhiteSpace($SnailRuntime)){$SnailRuntime=Join-Path $RepositoryPath 'var\snail'}
Set-Location $RepositoryPath
Write-Host "Riverview Steward Status starting at http://127.0.0.1:$Port/" -ForegroundColor Cyan
& $Python -m riverview.status.server --host 127.0.0.1 --port $Port --snail-runtime $SnailRuntime
if($LASTEXITCODE -ne 0){throw "RIV-UI-0006: Steward Status exited with code $LASTEXITCODE."}
