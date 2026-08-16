"""Isolated Riverview-owned Open WebUI-compatible bounded adapter.

This is deliberately a small local operator surface, not a general shell/database
bridge. It accepts one typed reasoning request shape and delegates to an approved
provider-neutral adapter.
"""
from __future__ import annotations

import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from uuid import UUID

from riverview.reasoning import ReasoningRequest, ReasoningResponse

UI_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Riverview Operator</title>
<style>body{font:16px sans-serif;max-width:720px;margin:3rem auto;padding:0 1rem}textarea{width:100%;height:8rem}input,button{margin:.4rem 0;padding:.5rem}#result{white-space:pre-wrap;background:#f3f3f3;padding:1rem}</style></head>
<body><h1>Riverview Operator</h1><p id="status">Use the local credential handoff, then enter text and optionally select a harmless artifact.</p>
<button id="local-auth">Use local Riverview credential</button><br>
<label>Manual bearer fallback <input id="token" type="password" autocomplete="off"></label><br>
<textarea id="message" placeholder="Enter a bounded operator request"></textarea><br>
<input id="artifact" type="file"><br><button id="send">Submit</button>
<pre id="result"></pre>
<script>
const $=id=>document.getElementById(id);
async function hash(file){const bytes=await file.arrayBuffer();const digest=await crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');}
async function submit(){
  $('status').textContent='Submitting bounded request…'; $('result').textContent='';
  const file=$('artifact').files[0]; const refs=[];
  if(file) refs.push('browser-artifact:'+file.name+':'+await hash(file));
  const correlation=crypto.randomUUID(), request=crypto.randomUUID();
  const response=await fetch('/api/chat',{method:'POST',headers:{'Authorization':'Bearer '+$('token').value,'Content-Type':'application/json'},body:JSON.stringify({request_id:request,correlation_id:correlation,message:$('message').value,context_refs:refs,classification:'operational',model:'qwen3-coder:30b-qwencode-20k'})});
  const body=await response.json(); $('status').textContent=response.ok?'Completed':'Rejected';
  $('result').textContent=JSON.stringify({correlation_id:correlation,artifact_refs:refs,response:body.response||body.error},null,2);
}
async function localAuth(){const response=await fetch('/session',{method:'POST'}); $('status').textContent=response.ok?'Authenticated through local Riverview credential handoff':'Authentication handoff failed';}
$('local-auth').addEventListener('click',()=>localAuth().catch(error=>{$('status').textContent='Authentication handoff failed';}));
$('send').addEventListener('click',()=>submit().catch(error=>{$('status').textContent='Failed';$('result').textContent=String(error);}));
</script></body></html>"""


@dataclass(frozen=True, slots=True)
class OpenWebUIConfig:
    host: str = "127.0.0.1"
    port: int = 18080
    service_identity: str = "riverview-openwebui"
    data_path: str = r"A:\Riverview\runtime\operator\openwebui"
    bearer_token: str = ""

    def __post_init__(self) -> None:
        if self.host not in {"127.0.0.1", "localhost"} or not 1024 <= self.port <= 65535:
            raise ValueError("RIV-UI-0009: Riverview Open WebUI must be loopback-only and bounded.")
        if not self.service_identity.strip() or not self.data_path.strip() or not self.bearer_token.strip():
            raise ValueError("RIV-UI-0009: service identity, data path, and bearer token are required.")


class RiverviewOpenWebUIService:
    def __init__(self, config: OpenWebUIConfig, provider: Callable[[str, ReasoningRequest], ReasoningResponse]) -> None:
        self.config = config
        self.provider = provider
        self.sessions: set[str] = set()
        service = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, status: HTTPStatus, payload: dict[str, object]) -> None:
                body = json.dumps(payload, separators=(",", ":")).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_html(self, body: str) -> None:
                encoded = body.encode()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def _auth(self) -> bool:
                bearer = self.headers.get("Authorization")
                cookie = self.headers.get("Cookie", "")
                session = next((part.split("=", 1)[1] for part in cookie.split("; ") if part.startswith("rv_session=")), "")
                return bearer == f"Bearer {service.config.bearer_token}" or session in service.sessions

            def _session(self) -> None:
                session = secrets.token_urlsafe(32)
                service.sessions.add(session)
                self.send_response(HTTPStatus.OK)
                self.send_header("Set-Cookie", f"rv_session={session}; HttpOnly; SameSite=Strict; Path=/")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"authenticated":true}')

            def do_GET(self) -> None:
                if self.path == "/":
                    self._send_html(UI_HTML)
                elif self.path == "/health":
                    self._send(HTTPStatus.OK, {"status": True, "service": service.config.service_identity})
                elif self.path == "/api/models" and self._auth():
                    self._send(HTTPStatus.OK, {"data": [{"id": "riverview-provider-neutral"}]})
                elif self.path == "/api/models":
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                else:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

            def do_POST(self) -> None:
                if self.path == "/session":
                    self._session()
                    return
                if self.path != "/api/chat" or not self._auth():
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0 or length > 16_384:
                        raise ValueError("bounded_payload")
                    payload = json.loads(self.rfile.read(length))
                    request = ReasoningRequest(
                        request_id=UUID(str(payload["request_id"])), correlation_id=UUID(str(payload["correlation_id"])),
                        request_type=str(payload.get("request_type", "advice")), instruction=str(payload["message"]),
                        context_refs=tuple(payload.get("context_refs", ())), classification=str(payload.get("classification", "operational")),
                        required_output_schema="advice-v1", evidence_requirements=("provider", "correlation"),
                        expires_at=__import__("datetime").datetime.now(__import__("datetime").UTC), allowed_authority=("read:bounded", "return:advisory"),
                    )
                    response = service.provider(str(payload.get("model", "approved")), request)
                    self._send(HTTPStatus.OK, {"service": service.config.service_identity, "context_refs": list(request.context_refs), "response": response.as_typed_payload()})
                except (AttributeError, KeyError, TypeError, ValueError, RuntimeError):  # bounded protocol error
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "bounded_request_rejected", "checkpoint": "RIV-UI-0009"})

            def log_message(self, *_args: object) -> None:
                return

        self.server = ThreadingHTTPServer((config.host, config.port), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
