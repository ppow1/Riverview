param(
    [ValidateSet('cme-supervisor', 'relay-worker', 'operator', 'comms5-http', 'comms5-transport')]
    [string]$ServiceId = 'cme-supervisor',
    [string]$RepositoryPath = 'A:\Riverview\repo',
    [int]$TimeoutSeconds = 30
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path $RepositoryPath).Path
$requestDir = Join-Path $root 'runtime\riverview-supervisor\requests'
$resultDir = Join-Path $requestDir 'results'
New-Item -ItemType Directory -Force -Path $requestDir,$resultDir | Out-Null
$id = [guid]::NewGuid().ToString()
$name = "$id.json"
$requestPath = Join-Path $requestDir $name
$resultPath = Join-Path $resultDir $name
$json = @{ operation = 'reload_service'; service_id = $ServiceId; request_id = $id } | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText($requestPath, $json, [System.Text.UTF8Encoding]::new($false))
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath $resultPath) {
        $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
        Remove-Item -LiteralPath $resultPath -Force
        $result | ConvertTo-Json -Compress
        if (-not $result.ok) { exit 1 }
        exit 0
    }
    Start-Sleep -Milliseconds 250
}
throw 'RIV-RUN-0001: supervisor recycle request timed out.'
