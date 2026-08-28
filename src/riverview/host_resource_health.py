"""Read-only Windows host commit/resource evidence for operator diagnostics."""
from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from typing import Any


_PROBE = r'''$os=Get-CimInstance Win32_OperatingSystem; $all=Get-Process; $pfu=Get-CimInstance Win32_PageFileUsage | Select-Object Name,AllocatedBaseSize,CurrentUsage,PeakUsage,TempPageFile; $pfs=Get-CimInstance Win32_PageFileSetting | Select-Object Name,InitialSize,MaximumSize; $top=$all | ForEach-Object { try {[pscustomobject]@{Name=$_.ProcessName;Id=$_.Id;PrivateMB=[math]::Round($_.PrivateMemorySize64/1MB,1);WorkingSetMB=[math]::Round($_.WorkingSet64/1MB,1);Handles=$_.Handles}} catch {}} | Sort-Object PrivateMB -Descending | Select-Object -First 20; $events=Get-WinEvent -FilterHashtable @{LogName=@("System","Application");StartTime=(Get-Date).AddHours(-6)} -ErrorAction SilentlyContinue | Where-Object {$_.ProviderName -match "Resource-Exhaustion-Detector|Application Error|Windows Error Reporting|Application Popup" -or $_.Message -match "0xc000012d|Out of Virtual Memory|low virtual memory"} | Sort-Object TimeCreated | Select-Object -Last 20 | ForEach-Object {[pscustomobject]@{Time=$_.TimeCreated.ToString("o");Log=$_.LogName;Provider=$_.ProviderName;Id=$_.Id;Message=(($_.Message -replace "\r?\n"," ") -replace "\s+"," ").Substring(0,[math]::Min(500,(($_.Message -replace "\r?\n"," ") -replace "\s+"," ").Length))}}; [pscustomobject]@{Memory=[pscustomobject]@{PhysicalTotalMB=[math]::Round($os.TotalVisibleMemorySize/1024,1);PhysicalFreeMB=[math]::Round($os.FreePhysicalMemory/1024,1);CommitLimitMB=[math]::Round($os.TotalVirtualMemorySize/1024,1);CommitAvailableMB=[math]::Round($os.FreeVirtualMemory/1024,1);CommitUsedMB=[math]::Round(($os.TotalVirtualMemorySize-$os.FreeVirtualMemory)/1024,1);CommitUsedPct=[math]::Round(100*(1-$os.FreeVirtualMemory/$os.TotalVirtualMemorySize),2)};PagefileUsage=$pfu;PagefileConfig=$pfs;TopProcesses=$top;ProcessCount=$all.Count;TotalHandles=(($all|Measure-Object Handles -Sum).Sum);Events=$events} | ConvertTo-Json -Depth 5'''


def _items(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _clean_items(value: Any, mapping: dict[str, str]) -> list[dict[str, Any]]:
    return [{target: item[source] for source, target in mapping.items() if source in item and item[source] is not None} for item in _items(value)]


def collect_host_resource_health(command_runner: Callable[[], str] | None = None) -> dict[str, Any]:
    """Return bounded host evidence; never changes host state."""
    try:
        raw = command_runner() if command_runner else subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", _PROBE],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout
        value = json.loads(raw)
        memory = value["Memory"]
        used_pct = float(memory["CommitUsedPct"])
        status = "critical_commit_pressure" if used_pct >= 95 else "commit_pressure" if used_pct >= 85 else "healthy"
        usage = _clean_items(value.get("PagefileUsage"), {"Name": "name", "AllocatedBaseSize": "allocated_base_size_mb", "CurrentUsage": "current_usage_mb", "PeakUsage": "peak_usage_mb", "TempPageFile": "temporary"})
        config = _clean_items(value.get("PagefileConfig"), {"Name": "name", "InitialSize": "initial_size_mb", "MaximumSize": "maximum_size_mb"})
        pagefiles = {item["name"].casefold(): item for item in usage if "name" in item}
        for item in config:
            pagefiles.setdefault(item.get("name", "").casefold(), {}).update(item)
        return {
            "status": status,
            "authoritative": True,
            "memory": {"physical_total_mb": memory.get("PhysicalTotalMB"), "physical_free_mb": memory.get("PhysicalFreeMB"), "commit_limit_mb": memory.get("CommitLimitMB"), "commit_available_mb": memory.get("CommitAvailableMB"), "commit_used_mb": memory.get("CommitUsedMB"), "commit_used_pct": used_pct},
            "pagefiles": list(pagefiles.values()),
            "top_processes": _clean_items(value.get("TopProcesses"), {"Name": "name", "Id": "pid", "PrivateMB": "private_mb", "WorkingSetMB": "working_set_mb", "Handles": "handles"}),
            "process_count": value.get("ProcessCount"),
            "total_handles": value.get("TotalHandles"),
            "events": _clean_items(value.get("Events"), {"Time": "time", "Log": "log", "Provider": "provider", "Id": "event_id", "Message": "message"}),
        }
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {"status": "unavailable", "authoritative": False, "reason": "host resource probe failed or returned invalid evidence"}
