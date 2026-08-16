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
from riverview.residents.gateway import ResidentConversationGateway

UI_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Riverview Operator</title>
<style>body{font:16px sans-serif;max-width:720px;margin:3rem auto;padding:0 1rem}textarea{width:100%;height:8rem}input,button{margin:.4rem 0;padding:.5rem}#result{white-space:pre-wrap;background:#f3f3f3;padding:1rem}</style></head>
<body><h1>Riverview Operator</h1><p id="status">Use the local credential handoff, then enter an instruction and optionally attach a harmless artifact. Attachments are reference-only unless the selected provider explicitly supports content inspection.</p>
<button id="local-auth">Use local Riverview credential</button><br>
<label>Resident <select id="resident"><option value="">General Riverview operator</option></select></label><br>
<button id="create-room">Create Alfred · Ingrid · Helen room</button> <span id="room-state"></span><br>
<label>Manual bearer fallback <input id="token" type="password" autocomplete="off"></label><br>
<button id="mic">Capture bounded local microphone transcription</button><br>
<textarea id="message" placeholder="Enter a bounded operator request"></textarea><br>
<input id="artifact" type="file"><br><button id="send">Submit</button>
<pre id="result"></pre>
<script>
const $=id=>document.getElementById(id);
const residentSessions={};
async function hash(file){const bytes=await file.arrayBuffer();const digest=await crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');}
async function submit(){
  if(!$('message').value.trim()){$('status').textContent='Enter an instruction describing what you want Riverview to do with this artifact.';return;}
  $('status').textContent='Submitting bounded request…'; $('result').textContent='';
  const file=$('artifact').files[0]; const refs=[];
  if(file) refs.push('browser-artifact:'+file.name+':'+await hash(file));
  const correlation=crypto.randomUUID(), request=crypto.randomUUID();
  const residentId=$('resident').value;
  if(window.riverviewRoomId&&residentId){const roomResponse=await fetch('/api/rooms/'+window.riverviewRoomId+'/turn',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({speaker:residentId,text:$('message').value,correlation_id:correlation})});const roomBody=await roomResponse.json();$('status').textContent=roomResponse.ok?'Room turn recorded':'Room turn rejected';$('result').textContent=JSON.stringify({correlation_id:correlation,room_turn:roomBody},null,2);return;}
  const response=await fetch('/api/chat',{method:'POST',headers:{'Authorization':'Bearer '+$('token').value,'Content-Type':'application/json'},body:JSON.stringify({request_id:request,correlation_id:correlation,message:$('message').value,context_refs:refs,resident_id:residentId,session_id:residentSessions[residentId]||'',classification:'operational',model:'qwen3-coder:30b-qwencode-20k'})});
  const body=await response.json(); $('status').textContent=response.ok?(body.artifact_semantics==='reference_only'?'Completed — artifact attached as reference-only; image content was not inspected.':'Completed'):'Rejected';
  if(response.ok&&residentId&&body.session_id)residentSessions[residentId]=body.session_id;
  $('result').textContent=JSON.stringify({correlation_id:correlation,artifact_refs:refs,artifact_semantics:body.artifact_semantics||'none',response:body.response||body.error},null,2);
}
async function localAuth(){const response=await fetch('/session',{method:'POST'}); $('status').textContent=response.ok?'Authenticated through local Riverview credential handoff':'Authentication handoff failed';}
async function loadResidents(){const response=await fetch('/api/residents');if(!response.ok)return;const body=await response.json();for(const resident of body.residents){const option=document.createElement('option');option.value=resident.resident_id;option.textContent=resident.name+' — '+resident.role;$('resident').appendChild(option);}}
async function createRoom(){const response=await fetch('/api/rooms',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({participants:['RES-000001','RES-000002','RES-000003']})});const body=await response.json();if(!response.ok)throw Error(body.error||'room creation failed');$('room-state').textContent='Room '+body.room_id+' ready; use the selected resident to submit a bounded turn.';window.riverviewRoomId=body.room_id;}
async function mic(){ $('status').textContent='Listening for up to 8 seconds…'; const response=await fetch('/api/transcribe',{method:'POST'}); const body=await response.json(); if(!response.ok) throw Error(body.error||'transcription failed'); $('message').value=body.text; $('status').textContent='Local transcription ready; review before submitting.'; }
$('local-auth').addEventListener('click',()=>localAuth().catch(error=>{$('status').textContent='Authentication handoff failed';}));
$('mic').addEventListener('click',()=>mic().catch(error=>{$('status').textContent='Local transcription failed: '+error;}));
$('send').addEventListener('click',()=>submit().catch(error=>{$('status').textContent='Failed';$('result').textContent=String(error);}));
 $('create-room').addEventListener('click',()=>createRoom().catch(error=>{$('room-state').textContent='Room unavailable';}));
loadResidents().catch(()=>{});
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
    def __init__(self, config: OpenWebUIConfig, provider: Callable[[str, ReasoningRequest], ReasoningResponse], resident_gateway: ResidentConversationGateway | None = None) -> None:
        self.config = config
        self.provider = provider
        self.resident_gateway = resident_gateway or ResidentConversationGateway.from_evidence()
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
                elif self.path == "/spatial":
                    from riverview.spatial.prototype import prototype_html
                    self._send_html(prototype_html())
                elif self.path == "/health":
                    self._send(HTTPStatus.OK, {"status": True, "service": service.config.service_identity})
                elif self.path == "/api/models" and self._auth():
                    self._send(HTTPStatus.OK, {"data": [{"id": "riverview-provider-neutral"}]})
                elif self.path == "/api/models":
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                elif self.path == "/api/residents" and self._auth():
                    self._send(HTTPStatus.OK, {"residents": service.resident_gateway.residents()})
                elif self.path == "/api/residents":
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                elif self.path.startswith("/api/rooms/") and self._auth():
                    try:
                        room = service.resident_gateway.room_snapshot(UUID(self.path.rsplit("/", 1)[1]))
                        self._send(HTTPStatus.OK, room)
                    except (ValueError, LookupError):
                        self._send(HTTPStatus.NOT_FOUND, {"error": "room_not_found", "checkpoint": "RIV-RES-0002"})
                else:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

            def do_POST(self) -> None:
                if self.path == "/session":
                    self._session()
                    return
                if self.path == "/api/transcribe":
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        from riverview.operator.local_speech import capture_windows_speech
                        result = capture_windows_speech()
                        self._send(HTTPStatus.OK, {"provider_id": result.provider_id, "text": result.text, "retention": result.retention})
                    except (RuntimeError, ValueError):
                        self._send(HTTPStatus.BAD_GATEWAY, {"error": "local_transcription_unavailable", "checkpoint": "RIV-UI-0015"})
                    return
                if self.path == "/api/rooms":
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        participants = tuple(str(item) for item in payload.get("participants", ()))
                        room_id = service.resident_gateway.create_room(participants, classification=str(payload.get("classification", "operational")))
                        self._send(HTTPStatus.OK, service.resident_gateway.room_snapshot(room_id))
                    except (TypeError, ValueError, LookupError, PermissionError):
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_request_rejected", "checkpoint": "RIV-RES-0002"})
                    return
                if self.path.startswith("/api/rooms/") and self.path.endswith("/turn"):
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        room_text = self.path.removeprefix("/api/rooms/").removesuffix("/turn").strip("/")
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        turn = service.resident_gateway.add_room_turn(UUID(room_text), speaker=str(payload["speaker"]), text=str(payload["text"]), correlation_id=UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None)
                        self._send(HTTPStatus.OK, turn)
                    except (KeyError, TypeError, ValueError, LookupError, PermissionError):
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_turn_rejected", "checkpoint": "RIV-RES-0002"})
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
                    resident_id = str(payload.get("resident_id") or "").strip()
                    if resident_id:
                        session, response, resident_metadata = service.resident_gateway.chat(
                            resident_id,
                            request.instruction,
                            provider=lambda resident_request: service.provider(str(payload.get("model", "approved")), resident_request),
                            interface_id=service.config.service_identity,
                            classification=request.classification,
                            session_id=UUID(str(payload["session_id"])) if payload.get("session_id") else None,
                            correlation_id=request.correlation_id,
                        )
                        body = {"service": service.config.service_identity, "context_refs": list(request.context_refs), "artifact_semantics": "reference_only" if request.context_refs else "none", "resident": resident_metadata, "session_id": str(session.session_id), "response": response.as_typed_payload()}
                    else:
                        response = service.provider(str(payload.get("model", "approved")), request)
                        body = {"service": service.config.service_identity, "context_refs": list(request.context_refs), "artifact_semantics": "reference_only" if request.context_refs else "none", "response": response.as_typed_payload()}
                    self._send(HTTPStatus.OK, body)
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
