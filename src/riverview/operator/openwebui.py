"""Isolated Riverview-owned Open WebUI-compatible bounded adapter.

This is deliberately a small local operator surface, not a general shell/database
bridge. It accepts one typed reasoning request shape and delegates to an approved
provider-neutral adapter.
"""
from __future__ import annotations

import json
import os
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from uuid import UUID

from riverview.diagnostics import DiagnosticEvent, DiagnosticStore, RecoveryState, Severity
from riverview.operator.snapshot import build_snapshot
from riverview.reasoning import ReasoningRequest, ReasoningResponse
from riverview.residents.gateway import ResidentConversationGateway

UI_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Riverview Operator</title>
<style>body{font:16px sans-serif;max-width:720px;margin:3rem auto;padding:0 1rem}textarea{width:100%;height:8rem}input,button{margin:.4rem 0;padding:.5rem}#result{white-space:pre-wrap;background:#f3f3f3;padding:1rem}</style></head>
<body><h1>Riverview Operator</h1><p id="status">Use the local credential handoff, then enter an instruction and optionally attach a harmless artifact. Attachments are reference-only unless the selected provider explicitly supports content inspection.</p>
<button id="snapshot">Snapshot</button> <button id="local-auth">Use local Riverview credential</button><br>
<label>Resident <select id="resident"><option value="">General Riverview operator</option></select></label><br>
<span id="resident-state">Active resident: General operator · session: none</span><br>
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
  if(window.riverviewRoomId&&residentId){const roomResponse=await fetch('/api/rooms/'+window.riverviewRoomId+'/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:$('message').value,correlation_id:correlation})});const roomBody=await roomResponse.json();$('status').textContent=roomResponse.ok?'Room responses completed':'Room turn rejected';$('result').textContent=JSON.stringify({correlation_id:correlation,room_responses:roomBody.responses||roomBody},null,2);return;}
  const response=await fetch('/api/chat',{method:'POST',headers:{'Authorization':'Bearer '+$('token').value,'Content-Type':'application/json'},body:JSON.stringify({request_id:request,correlation_id:correlation,message:$('message').value,context_refs:refs,resident_id:residentId,session_id:residentSessions[residentId]||'',classification:'operational',model:'qwen3-coder:30b-qwencode-20k'})});
  const body=await response.json(); if(response.ok&&body.resident){$('resident-state').textContent='Active resident: '+body.resident.resident_name+' · session: '+body.resident.session_id+' · character: '+(body.resident.character_version||'unknown');} $('status').textContent=response.ok?(body.artifact_semantics==='reference_only'?'Completed — artifact attached as reference-only; image content was not inspected.':'Completed'):'Rejected';
  if(response.ok&&residentId&&body.session_id)residentSessions[residentId]=body.session_id;
  $('result').textContent=JSON.stringify({correlation_id:correlation,artifact_refs:refs,artifact_semantics:body.artifact_semantics||'none',resident:body.resident||null,session_id:body.session_id||null,response:body.response||body.error},null,2);
}
async function localAuth(){const response=await fetch('/session',{method:'POST'}); if(response.ok){$('status').textContent='Authenticated through local Riverview credential handoff';await loadResidents();}else $('status').textContent='Authentication handoff failed';}
async function loadResidents(){const response=await fetch('/api/residents');if(!response.ok)return;const body=await response.json();for(const resident of body.residents){const option=document.createElement('option');option.value=resident.resident_id;option.textContent=resident.name+' — '+resident.role;$('resident').appendChild(option);}}
async function createRoom(){const response=await fetch('/api/rooms',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({participants:['RES-000001','RES-000002','RES-000003']})});const body=await response.json();if(!response.ok)throw Error(body.error||'room creation failed');$('room-state').textContent='Room '+body.room_id+' ready; use the selected resident to submit a bounded turn.';window.riverviewRoomId=body.room_id;}
async function snapshot(){ $('status').textContent='Creating snapshot…'; try { const clone=document.documentElement.cloneNode(true); clone.querySelector('#token')?.setAttribute('value','[REDACTED]'); clone.querySelector('#token')?.removeAttribute('value'); clone.querySelector('#artifact')?.removeAttribute('value'); clone.querySelectorAll('textarea').forEach(x=>x.textContent=x.value); const file=$('artifact').files[0]; const refs=file?['browser-artifact:'+file.name]:[]; let roomState={}; if(window.riverviewRoomId){const room=await fetch('/api/rooms/'+window.riverviewRoomId);if(room.ok)roomState=await room.json();} const health=await fetch('/health'); const residents=await fetch('/api/residents'); const body={current_dom:'<!doctype html>\n'+clone.outerHTML,page_url:location.href,title:document.title,visible_status:$('status').textContent,selected_resident:$('resident').value,active_resident_display:$('resident-state').textContent,composer:$('message').value,result:$('result').textContent,correlation_ids:($('result').textContent.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/gi)||[]),artifact_refs:refs,room_id:window.riverviewRoomId||null,room_state:roomState,resident_state:{selected_resident:$('resident').value,active_display:$('resident-state').textContent,session_ids:residentSessions},api_state:{health:health.ok?await health.json():{status:false},residents:residents.ok?await residents.json():{available:false}},provider_identities:['ollama:qwen3-coder:30b-qwencode-20k']}; const response=await fetch('/snapshot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); if(!response.ok)throw Error('snapshot failed'); const blob=await response.blob(); const url=URL.createObjectURL(blob), link=document.createElement('a'); link.href=url; link.download=(response.headers.get('Content-Disposition')||'riverview-snapshot.zip').split('filename="')[1]?.split('"')[0]||'riverview-snapshot.zip'; link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000); $('status').textContent='Snapshot downloaded.'; } catch(error) { $('status').textContent='Snapshot failed — RIV-UI-0019'; $('result').textContent=String(error); } }
async function mic(){ $('status').textContent='Listening for up to 8 seconds…'; const response=await fetch('/api/transcribe',{method:'POST'}); const body=await response.json(); if(!response.ok) throw Error(body.error||'transcription failed'); $('message').value=body.text; $('status').textContent='Local transcription ready; review before submitting.'; }
$('local-auth').addEventListener('click',()=>localAuth().catch(error=>{$('status').textContent='Authentication handoff failed';}));
$('mic').addEventListener('click',()=>mic().catch(error=>{$('status').textContent='Local transcription failed: '+error;}));
$('send').addEventListener('click',()=>submit().catch(error=>{$('status').textContent='Failed';$('result').textContent=String(error);}));
 $('resident').addEventListener('change',()=>{const option=$('resident').selectedOptions[0];$('resident-state').textContent=option&&option.value?'Active resident: '+option.textContent+' · session: '+(residentSessions[option.value]||'not started'):'Active resident: General operator · session: none';});
 $('snapshot').addEventListener('click',()=>snapshot());
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
        self.diagnostics = DiagnosticStore()
        service = self

        def diagnostic(checkpoint: str, operation: str, failure_class: str, summary: str) -> None:
            try:
                service.diagnostics.emit(DiagnosticEvent(
                    checkpoint_id=checkpoint, component="riverview.operator.openwebui", operation=operation,
                    severity=Severity.ERROR, failure_class=failure_class, summary=summary[:500],
                    cookbook_entry=f"CB-{checkpoint}", evidence_refs=("operator://bounded-metadata",),
                    recovery_state=RecoveryState.UNVERIFIED,
                ))
            except (OSError, RuntimeError, TypeError, ValueError):
                pass

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

            def _send_zip(self, body: bytes, filename: str) -> None:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

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
                        diagnostic("RIV-UI-0015", "microphone_capture", "microphone_worker_failure", "Bounded local microphone capture failed.")
                        self._send(HTTPStatus.BAD_GATEWAY, {"error": "local_transcription_unavailable", "checkpoint": "RIV-UI-0015"})
                    return
                if self.path == "/snapshot":
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        if length <= 0 or length > 512_000:
                            raise ValueError("bounded_snapshot_payload")
                        payload = json.loads(self.rfile.read(length))
                        if not isinstance(payload, dict):
                            raise TypeError("snapshot_object_required")
                        archive, filename = build_snapshot(payload, service_identity=service.config.service_identity, service_url="http://127.0.0.1:18082/", pid=os.getpid())
                        self._send_zip(archive, filename)
                    except (KeyError, TypeError, ValueError, RuntimeError, OSError) as exc:
                        diagnostic("RIV-UI-0019", "snapshot", "snapshot_generation_failure", f"Bounded snapshot failed: {type(exc).__name__}.")
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "snapshot_failed", "checkpoint": "RIV-UI-0019"})
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
                if self.path.startswith("/api/rooms/") and self.path.endswith("/chat"):
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        room_text = self.path.removeprefix("/api/rooms/").removesuffix("/chat").strip("/")
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        model = str(payload.get("model", "qwen3-coder:30b-qwencode-20k"))
                        responses = service.resident_gateway.room_chat(UUID(room_text), str(payload["message"]), provider=lambda request: service.provider(model, request), interface_id=service.config.service_identity, correlation_id=UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None)
                        self._send(HTTPStatus.OK, {"responses": responses, "no_authority_expansion": True})
                    except (KeyError, TypeError, ValueError, LookupError, PermissionError, RuntimeError) as exc:
                        diagnostic("RIV-RES-0002", "room_chat", "room_provider_or_membership_failure", f"Bounded room request failed: {type(exc).__name__}.")
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_chat_rejected", "checkpoint": "RIV-RES-0002"})
                    return
                if self.path != "/api/chat" or not self._auth():
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                    return
                resident_id = ""
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
                except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as exc:  # bounded protocol error
                    diagnostic("RIV-RES-0002" if resident_id else "RIV-UI-0009", "resident_chat" if resident_id else "operator_chat", "resident_provider_failure" if resident_id else "bounded_request_failure", f"Bounded operator request failed: {type(exc).__name__}.")
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
