Clear-Host 2>$null
# Riverview unified lifecycle owner. Version: 1.0.0

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RepositoryPath = 'A:\Riverview\repo'
for ($i = 0; $i -lt $args.Count; $i++) {
    if ($args[$i] -eq '-RepositoryPath' -and $i + 1 -lt $args.Count) { $RepositoryPath = $args[++$i] }
}
$RepositoryPath = (Resolve-Path $RepositoryPath).Path
$Python = Join-Path $RepositoryPath '.venv\Scripts\python.exe'
$Registry = Join-Path $RepositoryPath 'config\runtime\riverview-runtime-services.json'
if (-not (Test-Path $Python -PathType Leaf)) { throw 'RIV-RUN-0001: Riverview virtual environment not found.' }
if (-not (Test-Path $Registry -PathType Leaf)) { throw 'RIV-RUN-0001: runtime service registry not found.' }

$env:RIVERVIEW_REPOSITORY = $RepositoryPath
$env:RIVERVIEW_RUNTIME_REGISTRY = $Registry
$env:PYTHONPATH = Join-Path $RepositoryPath 'src'
Push-Location $RepositoryPath
try {
    & $Python -m riverview.runtime.supervisor
    if ($LASTEXITCODE -ne 0) { throw "RIV-RUN-0001: unified supervisor exited with code $LASTEXITCODE." }
}
finally {
    Pop-Location
}
