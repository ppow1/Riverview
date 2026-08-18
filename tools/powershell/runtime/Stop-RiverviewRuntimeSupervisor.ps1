Clear-Host 2>$null
# Stop the unified Riverview lifecycle owner. Version: 1.0.0

$ErrorActionPreference = 'Stop'
$taskName = 'Riverview Runtime Supervisor'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $taskName -TaskPath '\'
}
