from __future__ import annotations

import json

from riverview.host_resource_health import collect_host_resource_health


def test_collect_host_resource_health_returns_bounded_authoritative_snapshot():
    sample = {
        "Memory": {"PhysicalTotalMB": 65536, "PhysicalFreeMB": 32000, "CommitLimitMB": 193000, "CommitAvailableMB": 19000, "CommitUsedPct": 90},
        "PagefileUsage": [{"Name": "C:\\pagefile.sys", "AllocatedBaseSize": 128000, "CurrentUsage": 1600, "PeakUsage": 21385}],
        "PagefileConfig": [{"Name": "c:\\pagefile.sys", "InitialSize": 50000, "MaximumSize": 128000}],
        "ProcessCount": 861,
        "TotalHandles": 482241,
        "TopProcesses": [{"Name": "llama-server", "PrivateMB": 21400}],
        "Events": [{"Provider": "Resource-Exhaustion-Detector", "Id": 2004, "Message": "low virtual memory"}],
    }

    result = collect_host_resource_health(lambda: json.dumps(sample))

    assert result["status"] == "commit_pressure"
    assert result["memory"]["commit_used_pct"] == 90
    assert result["pagefiles"][0]["maximum_size_mb"] == 128000
    assert len(result["pagefiles"]) == 1
    assert result["top_processes"][0]["name"] == "llama-server"
    assert result["events"][0]["provider"] == "Resource-Exhaustion-Detector"
    assert len(json.dumps(result)) < 12_000


def test_collect_host_resource_health_fails_closed_on_invalid_probe():
    result = collect_host_resource_health(lambda: "not-json")
    assert result["status"] == "unavailable"
    assert result["authoritative"] is False
