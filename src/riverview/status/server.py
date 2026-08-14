"""Local HTTP surface for Riverview Steward status.

Version: 0.7.0
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
const table=(rows,cols)=>`<table><thead><tr>${cols.map(c=>`<th>${esc(c[0])}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(c=>`<td>${esc(r[c[1]])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
async function refresh(){try{const r=await fetch('/api/status',{cache:'no-store'});if(!r.ok)throw Error(r.status);const d=await r.json();document.getElementById('stamp').textContent=`updated ${new Date(d.generated_at).toLocaleTimeString()}`;const counts=Object.fromEntries(d.work_counts.map(x=>[x.status,x.count]));document.getElementById('view').innerHTML=`<section class="card"><h2>River</h2><div class="ok">${esc(d.status)}</div><p>Migrations: ${d.migrations.length}</p><p>Queued: ${counts.queued||0} · Running: ${counts.running||0}</p></section><section class="card"><h2>Workers</h2>${table(d.workers,[['Worker','worker_id'],['State','state'],['Seen','last_seen_at']])}</section><section class="card wide"><h2>Roadmap</h2>${table(d.roadmap,[['Waypoint','waypoint_id'],['Title','title'],['Status','status'],['Updated','updated_at']])}</section><section class="card wide"><h2>Open Steward Escalations</h2>${table(d.escalations,[['Checkpoint','checkpoint_id'],['Reason','reason'],['State','state'],['Created','created_at']])}</section><section class="card wide"><h2>Recent Work</h2>${table(d.recent_work,[['Action','action_type'],['Status','status'],['Checkpoint','error_checkpoint'],['Created','created_at']])}</section><section class="card wide"><h2>Recent Diagnostics</h2>${table(d.diagnostics,[['Checkpoint','checkpoint_id'],['Severity','severity'],['Summary','summary'],['Recovery','recovery_state']])}</section>`}catch(e){document.getElementById('stamp').innerHTML='<span class="bad">RIV-UI-0002 status unavailable</span>'}}
refresh();setInterval(refresh,3000);
</script></body></html>"""


class StatusHandler(BaseHTTPRequestHandler):
    server_version = "RiverviewStatus/0.7.0"

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