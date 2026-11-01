"""Local HTTP surface for Riverview Steward status.

Version: 0.8.0
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from riverview.snail.store import DurableStore
from riverview.status.snapshot import status_snapshot

CAMPAIGN_DOCS = {
    "/campaign/requirements": "PROJECT_REQUIREMENTS.md",
    "/campaign/process-map": "PROCESS_MAP.md",
}

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Estate at Riverview — Steward Status</title>
<style>
:root{color-scheme:dark;font-family:Segoe UI,Arial,sans-serif;background:#071713;color:#e7f4ec}body{margin:0;padding:20px}h1{margin:0 0 4px;color:#8fe0bc}.sub{color:#9db8ad;margin-bottom:18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}.card{background:#10251f;border:1px solid #285443;border-radius:10px;padding:14px}.wide{grid-column:1/-1}h2{font-size:16px;margin:0 0 10px;color:#b9edd6}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:7px;border-bottom:1px solid #28483e;vertical-align:top}.ok{color:#71e2a5}.warn{color:#ffd166}.bad{color:#ff7b7b}.target{font-size:18px;font-weight:700;color:#ffd166}.anchors a{margin-right:18px;color:#b7d9ff}code{color:#b7d9ff}#stamp{font-size:12px;color:#93aa9f}</style></head>
<body><h1>The Estate at Riverview</h1><div class="sub">Steward Status · River + SNAIL operational projection · <span id="stamp">loading</span></div><main class="grid" id="view"></main><section class="card wide"><h2>OctoMiner BIOS Campaign Authority</h2><div class="target">TARGET: stable operation with 10+ Tesla P100 16 GB GPUs</div><p>Boot/POST latency is a secondary acceptance and diagnostic metric; it is not the campaign objective.</p><p class="anchors"><a href="/campaign/requirements" target="_blank">PROJECT REQUIREMENTS</a><a href="/campaign/process-map" target="_blank">PROCESS MAP</a></p></section><section class="card wide" id="snail"><h2>SNAIL · OctoMiner BIOS Campaign</h2><div id="snail-view">loading</div></section>
<script>
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const table=(rows,cols)=>`<table><thead><tr>${cols.map(c=>`<th>${esc(c[0])}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(c=>`<td>${esc(r[c[1]] ?? '--')}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
async function refresh(){try{const r=await fetch('/api/status',{cache:'no-store'});if(!r.ok)throw Error(r.status);const d=await r.json();document.getElementById('stamp').textContent=`updated ${new Date(d.generated_at).toLocaleTimeString()}`;const counts=Object.fromEntries(d.work_counts.map(x=>[x.status,x.count]));document.getElementById('view').innerHTML=`<section class="card"><h2>River</h2><div class="ok">${esc(d.status)}</div><p>Migrations: ${d.migrations.length}</p><p>Queued: ${counts.queued||0} · Running: ${counts.running||0}</p></section><section class="card"><h2>Workers</h2>${table(d.workers,[['Worker','worker_id'],['State','state'],['Seen','last_seen_at']])}</section><section class="card wide"><h2>Roadmap</h2>${table(d.roadmap,[['Waypoint','waypoint_id'],['Title','title'],['Status','status'],['Updated','status_changed_at']])}</section><section class="card wide"><h2>Open Steward Escalations</h2>${table(d.escalations,[['Checkpoint','checkpoint_id'],['Reason','reason'],['State','state'],['Created','created_at']])}</section><section class="card wide"><h2>Recent Work</h2>${table(d.recent_work,[['Action','action_type'],['Status','status'],['Checkpoint','error_checkpoint'],['Created','created_at']])}</section><section class="card wide"><h2>Recent Diagnostics</h2>${table(d.diagnostics,[['Checkpoint','checkpoint_id'],['Severity','severity'],['Summary','summary'],['Recovery','recovery_state']])}</section>`}catch(e){document.getElementById('stamp').innerHTML='<span class="bad">RIV-UI-0002 status unavailable</span>'}}
async function snailControl(command,withValue=false){const value=withValue?prompt(`${command} value`) : null;if(withValue&&value===null)return;await fetch('/api/snail/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command,value})});await refreshSnail()}
async function refreshSnail(){const el=document.getElementById('snail-view');try{const r=await fetch('/api/snail/status',{cache:'no-store'});if(r.status===404){el.innerHTML='<span class="warn">SNAIL runtime is not configured on this Steward service.</span>';return}if(!r.ok)throw Error(r.status);const d=await r.json();const w=d.worker||{};const i=d.intervention;const frame=d.frame||{};el.innerHTML=`<p><b>Campaign:</b> ${esc(d.campaign_name)} · <b>Phase:</b> ${esc(d.phase)} · <b>State:</b> <span class="${d.steward_intervention_required?'warn':'ok'}">${esc(d.snail_state)}</span></p><p><b>Task:</b> ${esc(d.task)}</p><p><b>Current event:</b> ${esc(d.current_event_id)} · <b>Worker:</b> ${esc(w.state)} · <b>Boot:</b> ${esc(w.boot_id)} · <b>PID:</b> ${esc(w.pid)}</p><p><b>Pending reasoning:</b> ${esc(JSON.stringify(d.pending_reasoning))}</p><p><b>Pending operation:</b> ${esc(JSON.stringify(d.pending_execution||d.pending_operation))}</p><p><b>Latest evidence:</b> ${esc(d.latest_evidence_id)} · <b>Frame:</b> <span class="${frame.stale?'bad':'ok'}">${frame.stale?'STALE':'CURRENT'} (${esc(frame.age_seconds)}s)</span> <a href="/api/snail/frame">view</a></p><p><b>Hypothesis:</b> ${esc(JSON.stringify(d.hypothesis))}</p><p><b>Last verified:</b> ${esc(JSON.stringify(d.last_verified_machine_state))}</p><p><b>Next:</b> ${esc(d.next_proposed_action)}</p><p><b>Intervention:</b> ${i?esc(`${i.code}: ${i.what_happened} Required: ${i.human_action_required}`):'none'}</p><p>${['START','PAUSE','RESUME','STOP','ABORT','SNAPSHOT'].map(c=>`<button onclick="snailControl('${c}')">${c}</button>`).join(' ')} ${['UPDATE_TASK','UPDATE_DIRECTION','INQUIRY','PHYSICAL_WORK_COMPLETE'].map(c=>`<button onclick="snailControl('${c}',true)">${c.replaceAll('_',' ')}</button>`).join(' ')}</p><details><summary>Recent SNAIL events</summary><pre>${esc((d.recent_events||[]).map(e=>`${e.timestamp} ${e.event_id} ${e.type} [${e.status}]`).join('\n'))}</pre></details>`}catch(e){el.innerHTML=`<span class="bad">SNAIL status unavailable: ${esc(e)}</span>`}}
refresh();refreshSnail();setInterval(refresh,3000);setInterval(refreshSnail,3000);
</script></body></html>"""


class StatusHandler(BaseHTTPRequestHandler):
    server_version = "RiverviewStatus/0.8.0"

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
                return
            if self.path in CAMPAIGN_DOCS:
                repository = getattr(self.server, "repository_path", None)
                if repository is None:
                    self._send(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"campaign document root unavailable")
                    return
                path = repository / "docs" / "operations" / "octominer" / "campaign" / CAMPAIGN_DOCS[self.path]
                if not path.exists():
                    self._send(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"campaign document unavailable")
                    return
                self._send(HTTPStatus.OK, "text/plain; charset=utf-8", path.read_bytes())
                return
            if self.path == "/healthz":
                snapshot = status_snapshot()
                body = json.dumps({"status":snapshot["status"],"authority":snapshot["authority"]}).encode()
                self._send(HTTPStatus.OK, "application/json", body)
                return
            if self.path == "/api/status":
                body = json.dumps(status_snapshot(), default=str, sort_keys=True).encode()
                self._send(HTTPStatus.OK, "application/json", body)
                return
            if self.path == "/api/snail/status":
                root = getattr(self.server, "snail_runtime", None)
                if root is None or not (root / "state.json").exists():
                    self._send(HTTPStatus.NOT_FOUND, "application/json", b'{"status":"not_configured"}')
                    return
                store = DurableStore(root)
                payload = store.load_state()
                payload["recent_events"] = store.events()[-30:]
                frame = _snail_frame(payload, root)
                payload["frame"] = _frame_status(frame)
                body = json.dumps(payload, default=str, sort_keys=True).encode()
                self._send(HTTPStatus.OK, "application/json", body)
                return
            if self.path == "/api/snail/frame":
                root = getattr(self.server, "snail_runtime", None)
                if root is None or not (root / "state.json").exists():
                    self._send(HTTPStatus.NOT_FOUND, "application/json", b'{"status":"not_configured"}')
                    return
                frame = _snail_frame(DurableStore(root).load_state(), root)
                if not frame.exists():
                    self._send(HTTPStatus.NOT_FOUND, "application/json", b'{"status":"frame_unavailable"}')
                    return
                self._send(HTTPStatus.OK, mimetypes.guess_type(frame.name)[0] or "image/jpeg", frame.read_bytes())
                return
            self._send(HTTPStatus.NOT_FOUND, "application/json", b'{"checkpoint_id":"RIV-UI-0001","status":"not_found"}')
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            body = json.dumps({"checkpoint_id":"RIV-UI-0002","status":"failed","summary":str(exc)}).encode()
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, "application/json", body)

    def do_POST(self) -> None:
        try:
            if self.path != "/api/snail/control":
                self._send(HTTPStatus.NOT_FOUND, "application/json", b'{"status":"not_found"}')
                return
            root = getattr(self.server, "snail_runtime", None)
            if root is None or not (root / "state.json").exists():
                self._send(HTTPStatus.NOT_FOUND, "application/json", b'{"status":"not_configured"}')
                return
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length) or b"{}")
            control = DurableStore(root).enqueue_control(request["command"], request.get("value"))
            self._send(HTTPStatus.ACCEPTED, "application/json", json.dumps(control).encode())
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            body = json.dumps({"checkpoint_id":"RIV-UI-SNAIL-0001","status":"failed","summary":str(exc)}).encode()
            self._send(HTTPStatus.BAD_REQUEST, "application/json", body)


def _snail_frame(state: dict[str, Any], root: Path) -> Path:
    configured = state.get("last_observation", {}).get("frame", {}).get("path")
    return Path(configured) if configured else root / "video1" / "latest.jpg"


def _frame_status(frame: Path, freshness_seconds: float = 10.0) -> dict[str, Any]:
    if not frame.exists():
        return {"available": False, "stale": True, "age_seconds": None, "source": str(frame)}
    age = max(0.0, time.time() - frame.stat().st_mtime)
    return {"available": True, "stale": age > freshness_seconds, "age_seconds": round(age, 1), "source": str(frame)}


def build_server(host: str="127.0.0.1",port: int=8770, *, snail_runtime: Path | None=None, repository_path: Path | None=None) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1","localhost"}:
        raise ValueError("RIV-UI-0003: Steward Status must bind to localhost.")
    server = ThreadingHTTPServer((host,port),StatusHandler)
    server.snail_runtime = snail_runtime  # type: ignore[attr-defined]
    server.repository_path = repository_path  # type: ignore[attr-defined]
    return server


def main() -> None:
    parser=argparse.ArgumentParser(description="Riverview Steward Status")
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,default=8770)
    parser.add_argument("--snail-runtime",type=Path,default=os.environ.get("RIVERVIEW_SNAIL_RUNTIME"))
    parser.add_argument("--repository-path",type=Path,default=Path.cwd())
    args=parser.parse_args()
    server=build_server(args.host,args.port,snail_runtime=args.snail_runtime,repository_path=args.repository_path)
    print(f"Riverview Steward Status: http://{args.host}:{server.server_port}/",flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
