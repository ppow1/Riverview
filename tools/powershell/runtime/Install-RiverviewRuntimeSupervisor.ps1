Clear-Host 2>$null
# Install/migrate the single Riverview Windows lifecycle owner. Version: 1.0.0

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RepositoryPath = 'A:\Riverview\repo'
$MigratePeerTasks = $false
for ($i = 0; $i -lt $args.Count; $i++) {
    if ($args[$i] -eq '-RepositoryPath' -and $i + 1 -lt $args.Count) { $RepositoryPath = $args[++$i] }
    elseif ($args[$i] -eq '-MigratePeerTasks') { $MigratePeerTasks = $true }
}
$RepositoryPath = (Resolve-Path $RepositoryPath).Path
$StartScript = Join-Path $RepositoryPath 'tools\powershell\runtime\Start-RiverviewRuntimeSupervisor.ps1'
if (-not (Test-Path $StartScript -PathType Leaf)) { throw 'RIV-RUN-0001: supervisor launcher not found.' }

$taskName = 'Riverview Runtime Supervisor'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$StartScript`" -RepositoryPath `"$RepositoryPath`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

$backups = Join-Path $RepositoryPath 'runtime\riverview-supervisor\task-backups'
New-Item -ItemType Directory -Path $backups -Force | Out-Null
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Export-ScheduledTask -TaskName $taskName -TaskPath '\' | Set-Content (Join-Path $backups 'Riverview Runtime Supervisor.xml') -Encoding Unicode
}
Register-ScheduledTask -TaskName $taskName -TaskPath '\' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

if ($MigratePeerTasks) {
    $peerNames = @('Riverview CME Supervisor', 'Riverview Comms5 HTTP Service', 'Riverview Comms5 Reverse Tunnel')
    foreach ($peer in $peerNames) {
        $task = Get-ScheduledTask -TaskName $peer -ErrorAction SilentlyContinue
        if ($null -ne $task) {
            Export-ScheduledTask -TaskName $peer -TaskPath '\' | Set-Content (Join-Path $backups ($peer + '.xml')) -Encoding Unicode
            Disable-ScheduledTask -TaskName $peer -TaskPath '\' | Out-Null
        }
    }
}

Start-ScheduledTask -TaskName $taskName -TaskPath '\'
Start-Sleep -Seconds 2
$state = Get-ScheduledTask -TaskName $taskName -TaskPath '\'
[pscustomobject]@{
    task_name = $taskName
    state = $state.State
    peer_tasks_migrated = [bool]$MigratePeerTasks
    registry = (Join-Path $RepositoryPath 'config\runtime\riverview-runtime-services.json')
    status_path = (Join-Path $RepositoryPath 'runtime\riverview-supervisor\status.json')
} | ConvertTo-Json
