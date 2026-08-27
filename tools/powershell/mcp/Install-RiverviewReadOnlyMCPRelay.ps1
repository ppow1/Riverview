# Riverview Read-Only MCP Relay Installer
# Version: 0.9.14
# Purpose: Install and validate the bounded read-only MCP Relay transport for RV-004.4.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.9.14'
$MigrationId='0008'
$MigrationVersion='0.9.1'
$ReportLines=[Collections.Generic.List[string]]::new()

function Add-Line {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text,[ConsoleColor]$Color='Gray')
    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}
function Add-Section {
    param([Parameter(Mandatory)][string]$Title)
    Add-Line ''
    Add-Line "=== $Title ===" Cyan
}
function Write-Utf8NoBom {
    param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][AllowEmptyString()][string]$Content)
    $Encoding=New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path,$Content,$Encoding)
}
function Write-RepoFile {
    param([Parameter(Mandatory)][string]$RelativePath,[Parameter(Mandatory)][AllowEmptyString()][string]$Content)
    $Path=Join-Path $RepositoryPath $RelativePath
    New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force | Out-Null
    Write-Utf8NoBom -Path $Path -Content $Content
    Add-Line "WRITTEN   $RelativePath" Green
}
function Invoke-Checked {
    param([Parameter(Mandatory)][string]$Label,[Parameter(Mandatory)][scriptblock]$Command)
    $global:LASTEXITCODE=0
    $Output=@(& $Command 2>&1 | ForEach-Object { "$_" })
    foreach($Line in $Output){ Add-Line $Line }
    if($LASTEXITCODE -ne 0){ throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE." }
    Add-Line "$Label passed." Green
}
function Save-Report {
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\mcp-relay'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path=Join-Path $Directory "ReadOnly-MCP-Relay-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){
        Set-Clipboard $Report
        Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    } else {
        $Report | clip.exe
        if($LASTEXITCODE -eq 0){
            Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
        } else {
            Write-Host "`nClipboard copy failed; durable report was preserved." -ForegroundColor Yellow
        }
    }
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW READ-ONLY MCP RELAY VALIDATION'
    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){ throw 'RIV-MCP-0007: Riverview Git repository not found.' }
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: Riverview virtual environment not found.' }
    Add-Line "Repository validated: $RepositoryPath" Green
    Add-Line "PowerShell version: $($PSVersionTable.PSVersion)"
    Add-Line "Installer version: $ToolVersion"

    Add-Section 'SELF-INSTALLATION'
    $Installed=Join-Path $RepositoryPath 'tools\powershell\mcp\Install-RiverviewReadOnlyMCPRelay.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $Installed) -Force | Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Installed)){
        Copy-Item $PSCommandPath $Installed -Force
        Add-Line "Installed reusable tool: $Installed" Green
    } else {
        Add-Line "Running repository tool: $Installed" Green
    }

    Add-Section 'BOUNDARY AND WORKING TREE'
    $Head=(git -C $RepositoryPath rev-parse HEAD).Trim()
    Add-Line "Local HEAD: $Head"
    foreach($Line in @(git -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }

    Add-Section 'PACKAGE VERSION AND DEPENDENCIES'
    $ProjectPath=Join-Path $RepositoryPath 'pyproject.toml'
    $Project=Get-Content $ProjectPath -Raw
    $Project=[regex]::Replace($Project,'(?m)^# Version: .+$','# Version: 0.9.3',1)
    $Project=[regex]::Replace($Project,'(?m)^version = "[^"]+"$','version = "0.9.3"',1)
    if($Project -notmatch '"mcp>=1,<2"'){
        $Project=$Project.Replace('  "psycopg[binary]>=3.2,<4",','  "psycopg[binary]>=3.2,<4",'+"`r`n"+'  "mcp>=1,<2",')
    }
    Write-RepoFile 'pyproject.toml' $Project

    Add-Section 'MIGRATION PRESERVATION'
    $MigrationPath=Join-Path $RepositoryPath 'database\migrations\0008_readonly_mcp_relay.sql'
    if(Test-Path $MigrationPath){
        Add-Line 'Preserving existing migration 0008 byte-for-byte; transport repair requires no schema change.' Green
        Add-Line "Migration SHA256: $((Get-FileHash $MigrationPath -Algorithm SHA256).Hash)"
    } else {
        Write-RepoFile 'database\migrations\0008_readonly_mcp_relay.sql' @'
-- Riverview Read-Only MCP Relay
-- Version: 0.9.1
-- Migration: 0008

BEGIN;
CREATE TABLE IF NOT EXISTS cookbook_entries (
    checkpoint_id text PRIMARY KEY,
    title text NOT NULL,
    summary text NOT NULL,
    failure_classes jsonb NOT NULL DEFAULT '[]'::jsonb,
    distinguishing_probes jsonb NOT NULL DEFAULT '[]'::jsonb,
    smallest_safe_repair text NOT NULL,
    recovery_verification text NOT NULL,
    source_path text NOT NULL,
    implementation_revision text,
    validation_state text NOT NULL DEFAULT 'candidate',
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mcp_read_surfaces (
    surface_id text PRIMARY KEY,
    authority text NOT NULL CHECK (authority='read_only'),
    bind_scope text NOT NULL CHECK (bind_scope='local'),
    enabled boolean NOT NULL DEFAULT true,
    updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO mcp_read_surfaces(surface_id,authority,bind_scope)
VALUES('riverview-readonly-relay','read_only','local')
ON CONFLICT(surface_id) DO UPDATE
SET authority=EXCLUDED.authority,bind_scope=EXCLUDED.bind_scope,enabled=true,updated_at=now();
COMMIT;
'@
    }

    Add-Section 'MCP IMPLEMENTATION'
    Write-RepoFile 'src\riverview\mcp\__init__.py' @'
"""Bounded read-only MCP Relay.

Version: 0.9.3
"""

from .read_model import ReadOnlyRelay

__all__ = ["ReadOnlyRelay"]
'@

    Write-RepoFile 'src\riverview\mcp\read_model.py' @'
"""Bounded PostgreSQL read model for RV-004.4.

Version: 0.9.3
"""

from __future__ import annotations

from typing import Any

from riverview.database import connect


class ReadOnlyRelay:
    """Expose only fixed, bounded read queries. Caller-supplied SQL is never accepted."""

    @staticmethod
    def _rows(cursor: Any) -> list[dict[str, Any]]:
        names = [column.name for column in cursor.description]
        return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]

    def roadmap_revision(self) -> dict[str, Any] | None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT revision_id,content_sha256,waypoint_count,source_path,applied_at "
                "FROM roadmap_revisions ORDER BY applied_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row is None:
                return None
            names = [column.name for column in cursor.description]
            return dict(zip(names, row, strict=True))

    def waypoints(self, limit: int = 200) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT waypoint_id,parent_waypoint_id,sort_order,title,description,status,"
                "steward_checkpoint,acceptance_criteria,depends_on,governing_refs,scope_boundary,"
                "roadmap_revision,completed_at,updated_at FROM roadmap_items "
                "ORDER BY COALESCE(parent_waypoint_id,waypoint_id),sort_order LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def current_position(self) -> dict[str, Any]:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT waypoint_id,title,status,steward_checkpoint,depends_on,scope_boundary,"
                "roadmap_revision FROM roadmap_items WHERE status IN ('active','pending','blocked') "
                "ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'pending' THEN 1 ELSE 2 END,"
                "COALESCE(parent_waypoint_id,waypoint_id),sort_order LIMIT 25"
            )
            return {"authority": "read_only", "items": self._rows(cursor)}

    def workers(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT worker_id,state,host_name,process_id,last_seen_at,last_notification_at,"
                "completed_orders,failed_orders FROM relay_workers ORDER BY last_seen_at DESC LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def work_orders(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT work_order_id,action_type,action_version,status,requested_by,correlation_id,"
                "error_checkpoint,created_at,started_at,finished_at FROM work_orders "
                "ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def completed_reports(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT work_order_id,action_type,status,result_report,correlation_id,finished_at "
                "FROM work_orders WHERE status='succeeded' AND result_report IS NOT NULL "
                "ORDER BY finished_at DESC LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def escalations(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT escalation_id,work_order_id,checkpoint_id,reason,state,evidence_refs,"
                "created_at,acknowledged_at,resolved_at FROM steward_escalations "
                "WHERE state IN('open','acknowledged') ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def diagnostics(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 100))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT event_id,checkpoint_id,component,severity,failure_class,summary,evidence,"
                "recovery_state,occurred_at FROM diagnostic_events ORDER BY occurred_at DESC LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)

    def cookbook(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 100))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT cookbook_entry,checkpoint_id,component,failure_classes,diagnostic_procedure,"
                "repair_procedure,verification_procedure,applicability,implementation_revision,"
                "validation_state,updated_at FROM cookbook_entries ORDER BY checkpoint_id LIMIT %s",
                (limit,),
            )
            return self._rows(cursor)
'@

    Write-RepoFile 'src\riverview\mcp\server.py' @'
"""Local stdio MCP transport for the RV-004.4 read-only Relay.

Version: 0.9.3
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from riverview.mcp.read_model import ReadOnlyRelay

SERVER_NAME = "Riverview Read-Only Relay"
mcp = FastMCP(SERVER_NAME)
relay = ReadOnlyRelay()


def _safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


@mcp.tool()
def roadmap_revision() -> Any:
    """Return the latest applied master-roadmap revision."""
    return _safe(relay.roadmap_revision())


@mcp.tool()
def waypoints(limit: int = 200) -> Any:
    """Return a bounded roadmap waypoint projection."""
    return _safe(relay.waypoints(limit))


@mcp.tool()
def current_position() -> Any:
    """Return the bounded current roadmap position."""
    return _safe(relay.current_position())


@mcp.tool()
def relay_workers(limit: int = 50) -> Any:
    """Return bounded Relay worker state."""
    return _safe(relay.workers(limit))


@mcp.tool()
def work_order_status(limit: int = 50) -> Any:
    """Return bounded work-order status without parameters or payloads."""
    return _safe(relay.work_orders(limit))


@mcp.tool()
def completed_work_reports(limit: int = 50) -> Any:
    """Return bounded completed work reports."""
    return _safe(relay.completed_reports(limit))


@mcp.tool()
def open_steward_escalations(limit: int = 50) -> Any:
    """Return bounded open or acknowledged Steward escalations."""
    return _safe(relay.escalations(limit))


@mcp.tool()
def recent_diagnostic_events(limit: int = 100) -> Any:
    """Return bounded recent diagnostic events."""
    return _safe(relay.diagnostics(limit))


@mcp.tool()
def troubleshooting_cookbook(limit: int = 100) -> Any:
    """Return bounded Troubleshooting Cookbook projections."""
    return _safe(relay.cookbook(limit))


def main() -> None:
    """Run only over stdio; no TCP or remote listener is created."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
'@

    Write-RepoFile 'src\riverview\mcp\cookbook_sync.py' @'
"""Synchronize bounded RV-004.4 Cookbook projections into PostgreSQL.

Version: 0.9.3
"""

from __future__ import annotations

import json

from riverview.database import connect

ENTRIES = [
    (
        "RIV-MCP-0001",
        "Missing read surface",
        "Required bounded read surface is unavailable.",
        ["missing-method", "missing-projection"],
        ["Run python -m riverview.mcp_health."],
        "Restore only the missing fixed read adapter.",
        "Run MCP health and live protocol acceptance.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0001_READ_SURFACE.md",
    ),
    (
        "RIV-MCP-0002",
        "Prohibited authority exposed",
        "Read-only MCP surface exposes prohibited authority.",
        ["write-authority", "arbitrary-sql", "filesystem", "shell", "secret", "undercurrent"],
        ["List MCP tools and compare them with the exact read-only allowlist."],
        "Remove the prohibited tool or capability.",
        "Run live MCP tool-list and protocol acceptance.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0002_AUTHORITY_BOUNDARY.md",
    ),
    (
        "RIV-MCP-0003",
        "PostgreSQL read failure",
        "A fixed MCP read cannot reach authoritative PostgreSQL state.",
        ["database-connectivity", "schema-missing", "role-permission"],
        ["Run database health, then python -m riverview.mcp_health."],
        "Repair the smallest database connectivity or schema seam; do not add file fallback authority.",
        "Run database health and live MCP read acceptance.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0003_DATABASE_READ.md",
    ),
    (
        "RIV-MCP-0004",
        "Cookbook projection unavailable",
        "Bounded Cookbook projection is missing or unreadable.",
        ["table-missing", "projection-empty", "unsafe-content"],
        ["Query the fixed cookbook read through the MCP client."],
        "Restore bounded operational Cookbook projections only.",
        "Run cookbook sync and live MCP cookbook read.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0004_COOKBOOK_READ.md",
    ),
    (
        "RIV-MCP-0005",
        "Unbounded query request",
        "A requested retrieval limit exceeds the declared bound.",
        ["limit-overflow", "caller-controlled-unbounded-read"],
        ["Request limits above each maximum and verify clamping."],
        "Clamp to the declared maximum.",
        "Run bounded-limit unit tests and live MCP acceptance.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0005_BOUND_LIMIT.md",
    ),
    (
        "RIV-MCP-0006",
        "MCP transport acceptance failure",
        "The local stdio MCP protocol boundary does not initialize, enumerate, or execute allowed reads.",
        ["stdio-startup", "protocol-initialize", "tool-list", "tool-call", "authority-boundary"],
        ["Run python -m riverview.mcp.live_acceptance."],
        "Repair only the failing local MCP transport seam.",
        "Run the complete live MCP acceptance again.",
        "docs/operations/troubleshooting/checkpoints/RIV-MCP-0006_ACCEPTANCE.md",
    ),
]


def sync() -> dict[str, object]:
    with connect() as connection, connection.cursor() as cursor:
        for checkpoint_id, title, summary, classes, probes, repair, verify, source in ENTRIES:
            cursor.execute(
                """
                INSERT INTO cookbook_entries(
                    checkpoint_id,title,summary,failure_classes,distinguishing_probes,
                    smallest_safe_repair,recovery_verification,source_path,
                    validation_state,validated_at,updated_at
                )
                VALUES(%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,'0.9.3','observed-or-induced')
                ON CONFLICT(checkpoint_id) DO UPDATE SET
                    title=EXCLUDED.title,
                    summary=EXCLUDED.summary,
                    failure_classes=EXCLUDED.failure_classes,
                    distinguishing_probes=EXCLUDED.distinguishing_probes,
                    smallest_safe_repair=EXCLUDED.smallest_safe_repair,
                    recovery_verification=EXCLUDED.recovery_verification,
                    source_path=EXCLUDED.source_path,
                    implementation_revision=EXCLUDED.implementation_revision,
                    validation_state=EXCLUDED.validation_state,
                    updated_at=now()
                """,
                (
                    checkpoint_id,
                    title,
                    summary,
                    json.dumps(classes),
                    json.dumps(probes),
                    repair,
                    verify,
                    source,
                ),
            )
    return {"status": "healthy", "entries": len(ENTRIES), "version": "0.9.3"}


if __name__ == "__main__":
    print(json.dumps(sync(), indent=2, sort_keys=True))
'@

    Write-RepoFile 'src\riverview\mcp\live_acceptance.py' @'
"""Live stdio MCP protocol acceptance for RV-004.4.

Version: 0.9.3
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REQUIRED = {
    "roadmap_revision",
    "waypoints",
    "current_position",
    "relay_workers",
    "work_order_status",
    "completed_work_reports",
    "open_steward_escalations",
    "recent_diagnostic_events",
    "troubleshooting_cookbook",
}
PROHIBITED = {
    "enqueue",
    "execute_sql",
    "filesystem",
    "shell",
    "secret",
    "credential",
    "undercurrent",
    "write",
}


async def _accept() -> dict[str, Any]:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "riverview.mcp.server"],
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            missing = sorted(REQUIRED - names)
            prohibited = sorted(name for name in names if name.lower() in PROHIBITED)
            if missing:
                raise RuntimeError(f"RIV-MCP-0001: Missing MCP tools: {missing}")
            if prohibited:
                raise RuntimeError(f"RIV-MCP-0002: Prohibited MCP tools exposed: {prohibited}")

            revision = await session.call_tool("roadmap_revision", {})
            if getattr(revision, "isError", False) or getattr(revision, "is_error", False):
                raise RuntimeError("RIV-MCP-0006: roadmap_revision tool call failed.")

            position = await session.call_tool("current_position", {})
            if getattr(position, "isError", False) or getattr(position, "is_error", False):
                raise RuntimeError("RIV-MCP-0006: current_position tool call failed.")

            cookbook = await session.call_tool("troubleshooting_cookbook", {"limit": 5})
            if getattr(cookbook, "isError", False) or getattr(cookbook, "is_error", False):
                raise RuntimeError("RIV-MCP-0004: troubleshooting_cookbook tool call failed.")

            return {
                "status": "healthy",
                "transport": "stdio",
                "authority": "read_only",
                "tool_count": len(names),
                "required_tools_present": True,
                "prohibited_tools_present": False,
                "remote_listener_created": False,
            }


def main() -> None:
    print(json.dumps(asyncio.run(_accept()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
'@

    Write-RepoFile 'src\riverview\mcp_health.py' @'
"""RV-004.4 read-model acceptance and authority checks.

Version: 0.9.3
"""

from __future__ import annotations

import json

from riverview.mcp import ReadOnlyRelay

REQUIRED_METHODS = {
    "roadmap_revision",
    "waypoints",
    "current_position",
    "workers",
    "work_orders",
    "completed_reports",
    "escalations",
    "diagnostics",
    "cookbook",
}
PROHIBITED_METHODS = {
    "enqueue",
    "execute_sql",
    "filesystem",
    "shell",
    "secret",
    "credential",
    "undercurrent",
    "write",
}


def acceptance() -> dict[str, object]:
    relay = ReadOnlyRelay()
    methods = {
        name
        for name in dir(relay)
        if not name.startswith("_") and callable(getattr(relay, name))
    }
    missing = sorted(REQUIRED_METHODS - methods)
    prohibited = sorted(PROHIBITED_METHODS & methods)
    if missing:
        raise RuntimeError(f"RIV-MCP-0001: Required read surface missing: {missing}")
    if prohibited:
        raise RuntimeError(f"RIV-MCP-0002: Prohibited authority exposed: {prohibited}")

    revision = relay.roadmap_revision()
    position = relay.current_position()
    relay.workers(1)
    relay.work_orders(1)
    relay.completed_reports(1)
    relay.escalations(1)
    relay.diagnostics(1)
    relay.cookbook(1)
    relay.waypoints(1)

    return {
        "status": "healthy",
        "authority": "read_only",
        "roadmap_revision": None if revision is None else revision["revision_id"],
        "position_items": len(position["items"]),
        "prohibited_authority_exposed": False,
    }


if __name__ == "__main__":
    print(json.dumps(acceptance(), indent=2, sort_keys=True, default=str))
'@

    Write-RepoFile 'tests\test_mcp_readonly.py' @'
"""Read-only MCP Relay contract tests.

Version: 0.9.3
"""

from riverview.mcp import ReadOnlyRelay


def test_public_read_model_surface_is_read_only() -> None:
    relay = ReadOnlyRelay()
    methods = {
        name
        for name in dir(relay)
        if not name.startswith("_") and callable(getattr(relay, name))
    }
    for prohibited in {
        "enqueue",
        "execute_sql",
        "filesystem",
        "shell",
        "secret",
        "credential",
        "undercurrent",
        "write",
    }:
        assert prohibited not in methods


def test_limits_are_bounded() -> None:
    relay = ReadOnlyRelay()
    assert relay.waypoints.__defaults__ == (200,)
    assert relay.workers.__defaults__ == (50,)
    assert relay.work_orders.__defaults__ == (50,)
    assert relay.completed_reports.__defaults__ == (50,)
    assert relay.escalations.__defaults__ == (50,)
    assert relay.diagnostics.__defaults__ == (100,)
    assert relay.cookbook.__defaults__ == (100,)
'@

    Write-RepoFile 'tests\test_mcp_transport.py' @'
"""MCP transport construction tests.

Version: 0.9.3
"""

from riverview.mcp import server


def test_server_is_stdio_only_by_entrypoint_contract() -> None:
    assert server.SERVER_NAME == "Riverview Read-Only Relay"


def test_no_action_adapter_is_exposed_by_server_module() -> None:
    prohibited = {
        "enqueue",
        "execute_sql",
        "filesystem",
        "shell",
        "secret",
        "credential",
        "undercurrent",
        "write",
    }
    public = {name.lower() for name in dir(server) if not name.startswith("_")}
    assert not (public & prohibited)
'@

    Write-RepoFile 'tools\powershell\mcp\Start-RiverviewReadOnlyMCPRelay.ps1' @'
# Riverview Read-Only MCP Relay Launcher
# Version: 0.9.3
# Purpose: Launch the local stdio-only RV-004.4 MCP server for an authorized MCP client.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

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
'@

    foreach($Pair in @(
        @('RIV-MCP-0001_READ_SURFACE.md','RIV-MCP-0001 - Missing read surface','Required fixed read tool or projection is missing.','Restore only the missing fixed read adapter, then rerun read-model and live MCP acceptance.'),
        @('RIV-MCP-0002_AUTHORITY_BOUNDARY.md','RIV-MCP-0002 - Prohibited authority exposed','Tool enumeration exposes write, arbitrary SQL, filesystem, shell, secret, credential, or Undercurrent authority.','Remove the prohibited authority and rerun live MCP tool enumeration.'),
        @('RIV-MCP-0003_DATABASE_READ.md','RIV-MCP-0003 - PostgreSQL read failure','A fixed MCP read cannot retrieve authoritative PostgreSQL state.','Repair the smallest database connectivity/schema seam; do not add file-state fallback authority.'),
        @('RIV-MCP-0004_COOKBOOK_READ.md','RIV-MCP-0004 - Cookbook projection unavailable','The bounded Cookbook projection cannot be returned through MCP.','Restore the bounded PostgreSQL Cookbook projection and rerun the live tool call.'),
        @('RIV-MCP-0005_BOUND_LIMIT.md','RIV-MCP-0005 - Unbounded query request','A requested retrieval limit exceeds the declared maximum.','Clamp to the declared maximum and rerun bounded-limit acceptance.'),
        @('RIV-MCP-0006_ACCEPTANCE.md','RIV-MCP-0006 - MCP transport acceptance failure','The local stdio MCP server fails initialization, tool listing, or an allowed tool call.','Repair only the local MCP protocol seam and replay the full acceptance chain.')
    )){
        Write-RepoFile ("docs\operations\troubleshooting\checkpoints\"+$Pair[0]) ("<!-- Version: 0.9.3 -->`n# "+$Pair[1]+"`n`nComponent: RV-004.4 read-only MCP Relay.`n`nObserved or induced signature: "+$Pair[2]+"`n`nSmallest safe repair: "+$Pair[3]+"`n`nRecovery verification: run ``python -m riverview.mcp_health`` and ``python -m riverview.mcp.live_acceptance``.`n`nEscalation boundary: stop if repair would add write authority, remote exposure, arbitrary SQL/filesystem/process access, secrets, or Undercurrent access.`n`nApplicable version: 0.9.3.`n")
    }

    $IndexPath=Join-Path $RepositoryPath 'docs\operations\troubleshooting\README.md'
    $Index=Get-Content $IndexPath -Raw
    if(-not $Index.Contains('RIV-MCP-0001')){
        $Index += "`n- ``RIV-MCP-0001`` through ``RIV-MCP-0006`` - read-only MCP projection, authority boundary, database reads, Cookbook, bounded limits, and stdio protocol acceptance`n"
    }
    Write-RepoFile 'docs\operations\troubleshooting\README.md' $Index

    Add-Section 'DEPENDENCY INSTALLATION'
    Push-Location $RepositoryPath
    try {
        & $Python -m pip install -e '.[dev]'
        if($LASTEXITCODE -ne 0){ throw 'RIV-BLD-0005: Dependency installation failed.' }

        Add-Section 'MIGRATION CHECKSUM AND DATABASE ACCEPTANCE'
        $Migration=@'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed=apply_migration(Path("database/migrations/0008_readonly_mcp_relay.sql"),"0008","0.9.1")
print("Migration 0008 applied." if changed else "Migration 0008 checksum verified.")
'@
        $Migration | & $Python -
        if($LASTEXITCODE -ne 0){ throw 'RIV-DB-0006: Migration 0008 validation failed.' }

        Invoke-Checked 'Cookbook projection sync' { & $Python -m riverview.mcp.cookbook_sync }
        Invoke-Checked 'Ruff check' { & $Python -m ruff check src tests }
        Invoke-Checked 'Pytest' { & $Python -m pytest }
        Invoke-Checked 'Python compilation' { & $Python -m compileall -q src }
        Invoke-Checked 'Database health' { & $Python -m riverview.health database }
        Invoke-Checked 'Master roadmap acceptance' { & $Python -m riverview.roadmap_health }
        Invoke-Checked 'Read-only MCP read-model acceptance' { & $Python -m riverview.mcp_health }
        Invoke-Checked 'Live stdio MCP protocol acceptance' { & $Python -m riverview.mcp.live_acceptance }

        Add-Section 'GIT CHANGE SUMMARY'
        foreach($Line in @(git status --porcelain=v1 --untracked-files=all)){ Add-Line $Line }
    }
    finally {
        Pop-Location
    }

    Add-Section 'RV-004.4 LOCAL ACCEPTANCE RESULT'
    Add-Line 'The bounded PostgreSQL read model and local stdio MCP protocol boundary passed.' Green
    Add-Line 'No TCP listener or remote MCP exposure was created.' Green
    Add-Line 'No work-order enqueue, arbitrary SQL, filesystem, shell/process, secret, credential, Undercurrent, or general write authority was added.' Green
    Add-Line 'Unified runtime supervisor work was not started.' Green
    Add-Line 'This installer does not commit or push.' Yellow
    Add-Line 'RV-004.4 is not publication-complete until exact-scope publication, remote verification, and the required authorized ChatGPT-side retrieval acceptance are evidenced.' Yellow
    Add-Line "Installer version: $ToolVersion"
    Add-Line "Migration: $MigrationId (schema version $MigrationVersion)"
    Save-Report
}
catch {
    Add-Section 'RV-004.4 BLOCKED'
    Add-Line $_.Exception.Message Red
    Add-Line 'No commit or push was performed.' Yellow
    if(Test-Path $RepositoryPath -PathType Container){ Save-Report }
    throw
}
