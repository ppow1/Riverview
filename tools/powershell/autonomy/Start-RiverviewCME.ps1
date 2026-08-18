# Start the persistent CME recovery supervisor.
# The supervisor owns only the CME child; River/objective authority remains in PostgreSQL.

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\repo')

$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$RepositoryPath=(Resolve-Path $RepositoryPath).Path
$Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
if(-not(Test-Path $Python)){ throw 'RIV-GRC-0008: Riverview virtual environment not found.' }

$existing=Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'riverview.autonomy.supervisor' }
if($existing){ exit 0 }

Push-Location $RepositoryPath
try {
    $env:PYTHONPATH='src'
    & $Python -m riverview.autonomy.supervisor
    if($LASTEXITCODE -ne 0){ throw "RIV-GRC-0008: CME supervisor exited with code $LASTEXITCODE." }
}
finally { Pop-Location }
