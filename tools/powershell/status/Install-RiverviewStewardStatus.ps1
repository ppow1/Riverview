# Riverview Steward Status View Installer
# Version: 0.7.1
# Purpose: Install a localhost-only, PostgreSQL-backed operational status surface.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ToolVersion='0.7.1'
$ReportLines=[Collections.Generic.List[string]]::new()

function Add-Line {param([Parameter(Mandatory)][AllowEmptyString()][string]$Text,[ConsoleColor]$Color='Gray');$ReportLines.Add($Text);Write-Host $Text -ForegroundColor $Color}
function Add-Section {param([Parameter(Mandatory)][string]$Title);Add-Line '';Add-Line "=== $Title ===" Cyan}
function Write-RepoFile {param([string]$RelativePath,[string]$Content);$Path=Join-Path $RepositoryPath $RelativePath;New-Item -ItemType Directory -Path(Split-Path -Parent $Path)-Force|Out-Null;Set-Content $Path $Content -Encoding utf8NoBOM -NoNewline;Add-Line "WRITTEN   $RelativePath" Green}
function Invoke-Checked {param([string]$Label,[scriptblock]$Command);$global:LASTEXITCODE=0;$Output=@(& $Command 2>&1|ForEach-Object{"$_"});foreach($Line in $Output){Add-Line $Line};if($LASTEXITCODE -ne 0){throw "RIV-BLD-0005: $Label failed with exit code $LASTEXITCODE."};Add-Line "$Label passed." Green}
function Save-Report {$Directory=Join-Path(Split-Path -Parent $RepositoryPath)'runtime\diagnostics\steward-status';New-Item -ItemType Directory -Path $Directory -Force|Out-Null;$Path=Join-Path $Directory "Steward-Status-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt";$Report=($ReportLines-join[Environment]::NewLine)+[Environment]::NewLine;Set-Content $Path $Report -Encoding utf8NoBOM -NoNewline;if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){Set-Clipboard $Report}else{$Report|clip.exe};Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan;Write-Host "Durable report: $Path" -ForegroundColor Green}

try {
 Add-Section 'RIVERVIEW STEWARD STATUS VALIDATION'
 $RepositoryPath=(Resolve-Path $RepositoryPath).Path
 if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){throw 'Riverview Git repository not found.'}
 $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe';if(-not(Test-Path $Python)){throw 'RIV-BLD-0006: Riverview virtual environment not found.'}
 Add-Line "Repository validated: $RepositoryPath" Green

 Add-Section 'SELF-INSTALLATION'
 $Installed=Join-Path $RepositoryPath 'tools\powershell\status\Install-RiverviewStewardStatus.ps1';New-Item -ItemType Directory -Path(Split-Path -Parent $Installed)-Force|Out-Null
 if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Installed)){Copy-Item $PSCommandPath $Installed -Force;Add-Line "Installed reusable tool: $Installed" Green}else{Add-Line "Running repository tool: $Installed" Green}

 Add-Section 'STATUS VIEW FILES'
 $ProjectPath=Join-Path $RepositoryPath 'pyproject.toml';$Project=Get-Content $ProjectPath -Raw;$Project=$Project.Replace('# Version: 0.6.1','# Version: 0.7.1').Replace('version = "0.6.1"','version = "0.7.0"');Write-RepoFile 'pyproject.toml' $Project

 Write-RepoFile 'database\migrations\0006_steward_status.sql' @'
-- Riverview Steward Status View
-- Version: 0.7.1
-- Migration: 0006

BEGIN;
CREATE TABLE service_endpoints (
    service_id text PRIMARY KEY,
    service_name text NOT NULL,
    bind_host text NOT NULL,
    port integer NOT NULL CHECK (port BETWEEN 1 AND 65535),
    health_path text NOT NULL,
    authority text NOT NULL CHECK (authority IN ('read_only','restricted_action','authoritative')),
    enabled boolean NOT NULL DEFAULT true,
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(bind_host,port)
);
INSERT INTO service_endpoints(service_id,service_name,bind_host,port,health_path,authority)
VALUES('steward-status','Riverview Steward Status','127.0.0.1',8770,'/healthz','read_only')
ON CONFLICT(service_id) DO UPDATE SET service_name=EXCLUDED.service_name,bind_host=EXCLUDED.bind_host,port=EXCLUDED.port,health_path=EXCLUDED.health_path,authority=EXCLUDED.authority,enabled=true,updated_at=now();
UPDATE roadmap_items SET status='completed',completed_at=now(),updated_at=now() WHERE waypoint_id='RV-004.3';
INSERT INTO roadmap_transitions(waypoint_id,from_status,to_status,reason,evidence_refs)
VALUES('RV-004.3','pending','completed','Local read-only Steward status acceptance passed.','["migration:0006","service:steward-status"]'::jsonb);
COMMIT;
'@

 Write-RepoFile 'src\riverview\status\__init__.py' @'
"""Read-only Steward status adapter. Version: 0.7.1"""

from .snapshot import status_snapshot

__all__ = ["status_snapshot"]
'@

 Write-RepoFile 'src\riverview\status\snapshot.py' @'
"""PostgreSQL projection for the Steward status surface.

Version: 0.7.1
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from riverview.database import connect


def _rows(cursor: Any) -> list[dict[str, Any]]:
    names = [column.name for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def status_snapshot() -> dict[str, Any]:
    """Return one bounded, read-only operational projection."""

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """SELECT
                   i.waypoint_id,
                   i.parent_waypoint_id,
                   i.sort_order,
                   i.title,
                   i.status,
                   i.steward_checkpoint,
                   COALESCE(
                       t.occurred_at,
                       CASE WHEN i.status='completed' THEN i.completed_at END
                   ) AS status_changed_at
               FROM roadmap_items i
               LEFT JOIN LATERAL (
                   SELECT rt.occurred_at
                   FROM roadmap_transitions rt
                   WHERE rt.waypoint_id=i.waypoint_id
                   ORDER BY rt.occurred_at DESC
                   LIMIT 1
               ) t ON TRUE
               ORDER BY COALESCE(i.parent_waypoint_id,i.waypoint_id),i.sort_order"""
        )
        roadmap = _rows(cursor)
        cursor.execute("SELECT worker_id,state,host_name,process_id,last_seen_at,last_notification_at,completed_orders,failed_orders FROM relay_workers ORDER BY last_seen_at DESC LIMIT 20")
        workers = _rows(cursor)
        cursor.execute("SELECT status,count(*) AS count FROM work_orders GROUP BY status ORDER BY status")
        work_counts = _rows(cursor)
        cursor.execute("SELECT work_order_id,action_type,status,requested_by,error_checkpoint,created_at,finished_at FROM work_orders ORDER BY created_at DESC LIMIT 20")
        recent_work = _rows(cursor)
        cursor.execute("SELECT escalation_id,work_order_id,checkpoint_id,reason,state,created_at FROM steward_escalations WHERE state IN('open','acknowledged') ORDER BY created_at DESC LIMIT 20")
        escalations = _rows(cursor)
        cursor.execute("SELECT event_id,checkpoint_id,component,severity,failure_class,summary,recovery_state,occurred_at FROM diagnostic_events ORDER BY occurred_at DESC LIMIT 20")
        diagnostics = _rows(cursor)
        cursor.execute("SELECT migration_id,version,applied_at FROM schema_migrations ORDER BY migration_id")
        migrations = _rows(cursor)
    return {
        "generated_at": datetime.now(UTC),
        "status": "healthy",
        "authority": "read_only",
        "roadmap": roadmap,
        "workers": workers,
        "work_counts": work_counts,
        "recent_work": recent_work,
        "escalations": escalations,
        "diagnostics": diagnostics,
        "migrations": migrations,
    }
'@

 Write-RepoFile 'src\riverview\status\server.py' @'
"""Local HTTP surface for Riverview Steward status.

Version: 0.7.1
"""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from riverview.status.snapshot import status_snapshot

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Estate at Riverview — Steward Status</title>
<style>
:root{color-scheme:dark;font-family:Segoe UI,Arial,sans-serif;background:#071713;color:#e7f4ec}body{margin:0;padding:20px}h1{margin:0 0 4px;color:#8fe0bc}.sub{color:#9db8ad;margin-bottom:18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}.card{background:#10251f;border:1px solid #285443;border-radius:10px;padding:14px}.wide{grid-column:1/-1}h2{font-size:16px;margin:0 0 10px;color:#b9edd6}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:7px;border-bottom:1px solid #28483e;vertical-align:top}.ok{color:#71e2a5}.warn{color:#ffd166}.bad{color:#ff7b7b}code{color:#b7d9ff}#stamp{font-size:12px;color:#93aa9f}</style></head>
<body><h1>The Estate at Riverview</h1><div class="sub">Steward Status · read-only River projection · <span id="stamp">loading</span></div><main class="grid" id="view"></main>
<script>
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const table=(rows,cols)=>`<table><thead><tr>${cols.map(c=>`<th>${esc(c[0])}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(c=>`<td>${esc(r[c[1]] ?? '--')}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
async function refresh(){try{const r=await fetch('/api/status',{cache:'no-store'});if(!r.ok)throw Error(r.status);const d=await r.json();document.getElementById('stamp').textContent=`updated ${new Date(d.generated_at).toLocaleTimeString()}`;const counts=Object.fromEntries(d.work_counts.map(x=>[x.status,x.count]));document.getElementById('view').innerHTML=`<section class="card"><h2>River</h2><div class="ok">${esc(d.status)}</div><p>Migrations: ${d.migrations.length}</p><p>Queued: ${counts.queued||0} · Running: ${counts.running||0}</p></section><section class="card"><h2>Workers</h2>${table(d.workers,[['Worker','worker_id'],['State','state'],['Seen','last_seen_at']])}</section><section class="card wide"><h2>Roadmap</h2>${table(d.roadmap,[['Waypoint','waypoint_id'],['Title','title'],['Status','status'],['Updated','status_changed_at']])}</section><section class="card wide"><h2>Open Steward Escalations</h2>${table(d.escalations,[['Checkpoint','checkpoint_id'],['Reason','reason'],['State','state'],['Created','created_at']])}</section><section class="card wide"><h2>Recent Work</h2>${table(d.recent_work,[['Action','action_type'],['Status','status'],['Checkpoint','error_checkpoint'],['Created','created_at']])}</section><section class="card wide"><h2>Recent Diagnostics</h2>${table(d.diagnostics,[['Checkpoint','checkpoint_id'],['Severity','severity'],['Summary','summary'],['Recovery','recovery_state']])}</section>`}catch(e){document.getElementById('stamp').innerHTML='<span class="bad">RIV-UI-0002 status unavailable</span>'}}
refresh();setInterval(refresh,3000);
</script></body></html>"""


class StatusHandler(BaseHTTPRequestHandler):
    server_version = "RiverviewStatus/0.7.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        try:
            if self.path == "/":
                self._send(HTTPStatus.OK, "text/html; charset=utf-8", HTML.encode())
            elif self.path == "/healthz":
                snapshot = status_snapshot()
                body = json.dumps({"status":snapshot["status"],"authority":snapshot["authority"]}).encode()
                self._send(HTTPStatus.OK, "application/json", body)
            elif self.path == "/api/status":
                body = json.dumps(status_snapshot(), default=str, sort_keys=True).encode()
                self._send(HTTPStatus.OK, "application/json", body)
            else:
                self._send(HTTPStatus.NOT_FOUND, "application/json", b'{"checkpoint_id":"RIV-UI-0001","status":"not_found"}')
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            body = json.dumps({"checkpoint_id":"RIV-UI-0002","status":"failed","summary":str(exc)}).encode()
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, "application/json", body)


def build_server(host: str="127.0.0.1",port: int=8770) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1","localhost"}:
        raise ValueError("RIV-UI-0003: Steward Status must bind to localhost.")
    return ThreadingHTTPServer((host,port),StatusHandler)


def main() -> None:
    parser=argparse.ArgumentParser(description="Riverview Steward Status")
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,default=8770)
    args=parser.parse_args()
    server=build_server(args.host,args.port)
    print(f"Riverview Steward Status: http://{args.host}:{server.server_port}/",flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
'@

 Write-RepoFile 'src\riverview\status_health.py' @'
"""Live HTTP acceptance for Steward Status. Version: 0.7.1"""

from __future__ import annotations

import json
import threading
from urllib.request import urlopen

from riverview.status.server import build_server


def acceptance() -> dict[str, object]:
    server=build_server(port=0)
    thread=threading.Thread(target=server.serve_forever,kwargs={"poll_interval":0.05},daemon=True)
    thread.start()
    base=f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{base}/healthz",timeout=5) as response:
            health=json.load(response)
        with urlopen(f"{base}/api/status",timeout=5) as response:
            status=json.load(response)
        with urlopen(f"{base}/",timeout=5) as response:
            html=response.read().decode()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    required={"roadmap","workers","work_counts","recent_work","escalations","diagnostics","migrations"}
    if health.get("status")!="healthy" or health.get("authority")!="read_only" or not required.issubset(status) or "The Estate at Riverview" not in html or thread.is_alive():
        raise RuntimeError("RIV-UI-0004: Steward Status HTTP acceptance failed.")
    return {"status":"healthy","localhost_only":True,"read_only":True,"api_projection":True,"auto_refresh":True,"bounded_stop":True}


if __name__ == "__main__":
    print(json.dumps(acceptance(),indent=2,sort_keys=True))
'@

 Write-RepoFile 'tests\test_status_view.py' @'
"""Unit seams for Steward Status. Version: 0.7.1"""

import pytest

from riverview.status.server import HTML, build_server


def test_status_html_has_refresh_and_riverview_identity() -> None:
    assert "setInterval(refresh,3000)" in HTML
    assert "The Estate at Riverview" in HTML


def test_status_server_rejects_nonlocal_bind() -> None:
    with pytest.raises(ValueError,match="RIV-UI-0003"):
        build_server("0.0.0.0",0)
'@

 Write-RepoFile 'tools\powershell\status\Start-RiverviewStewardStatus.ps1' @'
# Riverview Steward Status Launcher
# Version: 0.7.1
# Purpose: Run the localhost-only Steward Status server in the foreground.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone',[int]$Port=8770)

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
if(-not(Test-Path $Python)){throw 'RIV-UI-0005: Riverview Python environment was not found.'}
Set-Location $RepositoryPath
Write-Host "Riverview Steward Status starting at http://127.0.0.1:$Port/" -ForegroundColor Cyan
& $Python -m riverview.status.server --host 127.0.0.1 --port $Port
if($LASTEXITCODE -ne 0){throw "RIV-UI-0006: Steward Status exited with code $LASTEXITCODE."}
'@

 foreach($Pair in @(
  @('RIV-UI-0001_NOT_FOUND.md','RIV-UI-0001 — Unknown status route','Use only `/`, `/healthz`, or `/api/status`. Unknown routes never fall through to filesystem content.'),
  @('RIV-UI-0002_PROJECTION_FAILURE.md','RIV-UI-0002 — Status projection unavailable','Check PostgreSQL health and DPAPI credential ownership. The server returns bounded failure JSON and must not substitute cached authority.'),
  @('RIV-UI-0003_BIND_BOUNDARY.md','RIV-UI-0003 — Nonlocal bind rejected','The initial Steward Status surface is localhost-only. Do not widen the bind address without an authenticated remote-access design.'),
  @('RIV-UI-0004_HTTP_ACCEPTANCE.md','RIV-UI-0004 — HTTP acceptance invariant','Verify `/healthz`, `/api/status`, HTML identity, required projection sections, and bounded server shutdown.'),
  @('RIV-UI-0005_ENVIRONMENT.md','RIV-UI-0005 — Python environment missing','Restore `A:\Riverview\standalone\.venv` using the repository dependency process, then rerun health acceptance.'),
  @('RIV-UI-0006_SERVER_EXIT.md','RIV-UI-0006 — Status server exited','Inspect the exit code, port ownership, database health, and the nearest `RIV-DB-*` or `RIV-UI-*` checkpoint before restart.')
 )){Write-RepoFile ("docs\operations\troubleshooting\checkpoints\"+$Pair[0]) ("<!-- Version: 0.7.1 -->`n# "+$Pair[1]+"`n`n"+$Pair[2]+"`n")}
 $IndexPath=Join-Path $RepositoryPath 'docs\operations\troubleshooting\README.md';$Index=Get-Content $IndexPath -Raw
 if(-not $Index.Contains('RIV-UI-*')){$Index=$Index.Replace('- `RIV-SEC-*` — classification and Undercurrent boundaries','- `RIV-SEC-*` — classification and Undercurrent boundaries'+"`n- ``RIV-UI-*`` — read-only Steward status and operator surfaces");$Index += "`n- ``RIV-UI-0001`` through ``RIV-UI-0006`` — status routing, projection, bind, acceptance, environment, and exit failures`n";Write-RepoFile 'docs\operations\troubleshooting\README.md' $Index}

 Add-Section 'MIGRATION AND ACCEPTANCE'
 Push-Location $RepositoryPath
 try {
  & $Python -m pip install -e '.[dev]';if($LASTEXITCODE -ne 0){throw 'Dependency installation failed.'}
  $Migration=@'
from pathlib import Path
from riverview.database.migrations import apply_migration
changed=apply_migration(Path('database/migrations/0006_steward_status.sql'),'0006','0.7.0')
print('Migration 0006 applied.' if changed else 'Migration 0006 checksum verified.')
'@
  $Migration|& $Python -;if($LASTEXITCODE -ne 0){throw 'RIV-DB-0006: Migration 0006 validation failed.'}
  Invoke-Checked 'Ruff check' {& $Python -m ruff check src tests}
  Invoke-Checked 'Pytest' {& $Python -m pytest}
  Invoke-Checked 'Python compilation' {& $Python -m compileall -q src}
  Invoke-Checked 'Database health' {& $Python -m riverview.health database}
  Invoke-Checked 'Steward Status live acceptance' {& $Python -m riverview.status_health}
  Add-Section 'GIT CHANGE SUMMARY';foreach($Line in @(git status --short)){Add-Line $Line}
 } finally {Pop-Location}
 Add-Section 'STATUS VIEW RESULT';Add-Line 'Local read-only dashboard, live PostgreSQL projection, auto-refresh, health endpoint, and bounded shutdown passed.' Green;Add-Line 'No execution controls, remote bind, Windows service, commit, or push was created.' Yellow;Add-Line "Installer version: $ToolVersion";Save-Report
} catch {Add-Section 'STATUS VIEW BLOCKED';Add-Line $_.Exception.Message Red;Add-Line 'No commit or push was performed.' Yellow;if(Test-Path $RepositoryPath -PathType Container){Save-Report};throw}
