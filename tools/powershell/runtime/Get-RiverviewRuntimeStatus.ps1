Clear-Host 2>$null
# Read the bounded unified Riverview lifecycle projection. Version: 1.0.0

$ErrorActionPreference = 'Stop'
$RepositoryPath = 'A:\Riverview\repo'
for ($i = 0; $i -lt $args.Count; $i++) {
    if ($args[$i] -eq '-RepositoryPath' -and $i + 1 -lt $args.Count) { $RepositoryPath = $args[++$i] }
}
$path = Join-Path (Resolve-Path $RepositoryPath).Path 'runtime\riverview-supervisor\status.json'
if (-not (Test-Path $path)) { throw 'RIV-RUN-0001: unified runtime status is unavailable.' }
Get-Content -LiteralPath $path -Raw
