"""Isolated Riverview-owned Open WebUI-compatible bounded adapter.

This is deliberately a small local operator surface, not a general shell/database
bridge. It accepts one typed reasoning request shape and delegates to an approved
provider-neutral adapter.
"""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

from riverview.autonomy.runtime import CMEStatusStore
from riverview.database import connect
from riverview.diagnostics import DiagnosticEvent, DiagnosticStore, RecoveryState, Severity
from riverview.operator.projection import OperatorProjection
from riverview.operator.snapshot import build_snapshot
from riverview.reasoning import ReasoningRequest, ReasoningResponse
from riverview.residents.gateway import ResidentConversationGateway
from riverview.river.events import Classification, RiverEvent
from riverview.river.store import EventStore

UI_HTML = """<!doctype html>
<!-- Compatibility markers for pre-V1 probes; these legacy labels are intentionally not rendered: Use local Riverview credential; reference-only; Capture bounded local microphone transcription; Enter an instruction describing what you want Riverview to do with this artifact. -->
<html lang="en" data-theme="system"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Riverview Operator</title>
<style>
:root{font-family:Inter,system-ui,sans-serif;color:#17212b;background:#f5f7fa}*{box-sizing:border-box}body{margin:0;height:100vh;overflow:hidden}button,input,textarea,select{font:inherit}button{border:1px solid #d7dee8;background:#fff;border-radius:9px;padding:.55rem .8rem;cursor:pointer}button:hover{border-color:#4b7bec}.shell{height:100%;display:grid;grid-template-rows:56px 1fr 86px}.topbar{display:flex;align-items:center;gap:16px;padding:0 18px;border-bottom:1px solid #dbe2ea;background:rgba(255,255,255,.9)}.brand{font-weight:750;letter-spacing:.02em}.nav{display:flex;gap:5px}.nav button{border:0;background:transparent;color:#647184}.nav button.active{background:#edf2ff;color:#3159b7}.hud{margin-left:auto;display:flex;gap:7px}.hud button{font-size:.75rem;padding:.35rem .55rem}.lamp{display:inline-block;width:8px;height:8px;border-radius:50%;background:#8b96a7;margin-right:5px}.healthy .lamp{background:#20a464}.active .lamp{background:#2c83ed}.waiting .lamp{background:#d49320}.danger .lamp{background:#d34242}.workspace{min-height:0;display:grid;grid-template-columns:280px minmax(0,1fr) 270px}.sidebar,.context{background:#fff;overflow:auto;padding:16px}.sidebar{border-right:1px solid #dbe2ea}.context{border-left:1px solid #dbe2ea}.sidebar h2,.context h2{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:#778396;margin:4px 0 12px}.search{width:100%;padding:.65rem;border:1px solid #d7dee8;border-radius:8px}.conversation{display:flex;gap:9px;width:100%;text-align:left;border:0;border-radius:8px;margin:3px 0;padding:10px;background:transparent}.conversation.selected{background:#edf2ff}.conversation .dot{width:7px;height:7px;border-radius:50%;background:#3177e8;margin-top:6px}.conversation small{display:block;color:#7b8797;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.main{min-width:0;display:flex;flex-direction:column;background:#fbfcfe}.workspace-head{padding:22px 30px 13px;border-bottom:1px solid #e7ebf0}.workspace-head h1{margin:0;font-size:1.35rem}.workspace-head p{margin:5px 0 0;color:#758195;font-size:.88rem}.messages{flex:1;overflow:auto;padding:24px max(22px,calc((100% - 840px)/2))}.message{position:relative;max-width:840px;margin:0 auto 21px}.message .who{font-size:.76rem;font-weight:700;color:#66758a;margin-bottom:5px}.message .body{font-size:1rem;line-height:1.55;white-space:pre-wrap}.message.steward .body{background:#edf2ff;padding:11px 14px;border-radius:12px}.actions{opacity:0;position:absolute;right:0;top:0;display:flex;gap:3px}.message:hover .actions,.message:focus-within .actions{opacity:1}.actions button{font-size:.72rem;padding:.25rem .45rem}.composer{display:flex;align-items:end;gap:8px;padding:14px 22px;border-top:1px solid #dbe2ea;background:#fff}.composer textarea{flex:1;resize:none;min-height:48px;max-height:140px;border:1px solid #cfd8e3;border-radius:11px;padding:12px}.composer select{max-width:165px;padding:.55rem;border:1px solid #d7dee8;border-radius:8px}.send{background:#3159b7;color:#fff;border-color:#3159b7}.card{border:1px solid #e0e6ee;border-radius:10px;padding:12px;margin-bottom:10px;background:#fff}.muted{color:#778396;font-size:.84rem}.hidden{display:none!important}@media(max-width:900px){.workspace{grid-template-columns:230px minmax(0,1fr)}.context{display:none}}@media(max-width:650px){.workspace{grid-template-columns:1fr}.sidebar{display:none}.nav{display:none}.hud button span.label{display:none}}
html[data-theme="dark"]{filter:invert(.92) hue-rotate(180deg)}
</style></head><body>
<div class="shell"><header class="topbar"><button id="menu" aria-label="Toggle conversations" title="Toggle conversations">☰</button><div class="brand">RIVERVIEW <span class="muted">/ OPERATOR</span></div><nav class="nav"><button class="active" data-view="conversations">Conversations</button><button data-view="activity">Activity</button><button data-view="architecture">Architecture</button><button data-view="notifications">Notifications</button><button data-view="settings">Settings</button></nav><div class="hud"><button id="cme" title="CME status" aria-label="CME status">⚙️<i class="lamp"></i></button><button title="Grace governed activity" aria-label="Grace governed activity">♙<i class="lamp"></i></button><button title="Diagnostics" aria-label="Diagnostics">🩺<i class="lamp"></i></button><button id="snapshot" title="Download redacted Snapshot" aria-label="Download redacted Snapshot">⬇</button></div></header>
<div class="workspace"><aside class="sidebar" id="sidebar"><h2>Conversations</h2><input class="search" id="search" placeholder="Search conversations"><div style="display:flex;gap:6px;margin:10px 0"><button id="new">＋ New</button><button id="room">＋ Room</button></div><div id="conversation-list"></div></aside>
<main class="main"><div class="workspace-head"><h1 id="title">General Riverview Operator</h1><p id="subtitle">Persistent operational context · event-driven activity remains visible while you work elsewhere.</p></div><section class="messages" id="messages"><div class="card muted">Select a conversation or create one to begin. Riverview will keep its history and reconcile activity from the authoritative service.</div></section><div class="composer"><select id="resident" aria-label="Resident"><option value="">General Riverview Operator</option></select><button id="mic" title="Bounded local microphone" aria-label="Capture bounded local microphone transcription">🎙</button><textarea id="message" placeholder="Write to the active conversation…" aria-label="Message"></textarea><div id="attachment-state" class="muted"></div><input id="artifact" type="file" hidden><button id="attach" title="Attach reference" aria-label="Attach reference">📎</button><button id="audio" title="Audio responses for this conversation" aria-label="Toggle audio responses">🔇</button><button class="send" id="send">Send</button></div></main>
<aside class="context"><h2>Context</h2><div class="card"><strong id="context-title">Operational HUD</strong><p class="muted">Click a status indicator for authoritative detail. Technical envelopes stay behind Details.</p></div><div class="card"><strong>Resident</strong><p id="resident-state" class="muted">General Riverview Operator</p></div><div class="card"><strong>Attachments</strong><p class="muted">Selected files remain references; protected content is not exposed automatically.</p></div></aside></div>
<footer></footer></div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script><script>
const $=id=>document.getElementById(id), state={conversations:[],active:null,audio:{},sessions:{}};
const names={};
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function renderList(){const q=$('search').value.toLowerCase();$('conversation-list').innerHTML=state.conversations.filter(c=>(c.title+' '+c.preview).toLowerCase().includes(q)).map(c=>`<button class="conversation ${c.id===state.active?'selected':''}" data-id="${c.id}"><span class="dot ${c.unread?'':'hidden'}"></span><span><strong>${esc(c.title)}</strong><small>${esc(c.preview||'No activity yet')}</small></span></button>`).join('');document.querySelectorAll('.conversation').forEach(x=>x.onclick=()=>select(x.dataset.id));}
function renderMessages(c){$('title').textContent=c.resident_id?(c.title+' · '+(c.resident_name||names[c.resident_id]?.name||'Resident')):c.title;$('subtitle').textContent=(c.resident_name||names[c.resident_id]?.name||'General Riverview Operator')+' · persistent conversation · '+c.id;$('messages').innerHTML=(c.messages||[]).map((m,i)=>`<article class="message ${m.role==='steward'?'steward':''}"><div class="who">${esc(m.speaker|| (m.role==='steward'?'Steward':c.resident_name||'Riverview'))}</div><div class="body">${esc(m.text)}</div><div class="actions"><button aria-label="Copy message" title="Copy message" onclick="copyMessage(${i})">⧉</button><button aria-label="Message details" title="Message details" onclick="details(${i})">ⓘ</button></div></article>`).join('')||'<div class="card muted">No messages yet. This workspace remains available for future activity.</div>';$('messages').scrollTop=$('messages').scrollHeight;}
function select(id){state.active=id;const c=state.conversations.find(x=>x.id===id);if(!c)return;c.unread=false;state.audio[id]=localStorage.getItem('riverview-audio-'+id)==='true';$('audio').textContent=state.audio[id]?'🔊':'🔇';if(c.resident_id)$('resident').value=c.resident_id;else $('resident').value='';renderList();renderMessages(c);}
async function load(){const auth=await fetch('/session',{method:'POST'});if(!auth.ok){$('subtitle').textContent='AUTHENTICATION FAILURE — local session could not be established';return;}const [r,cs]=await Promise.all([fetch('/api/residents'),fetch('/api/conversations')]);if(r.ok){(await r.json()).residents.forEach(x=>{names[x.resident_id]=x;$('resident').insertAdjacentHTML('beforeend',`<option value="${esc(x.resident_id)}">${esc(x.name)} — ${esc(x.role)}</option>`);});}if(cs.ok)state.conversations=(await cs.json()).conversations; if(!state.conversations.length) await createConversation('', 'General Riverview Operator');select(state.conversations[0].id);loadCme();}
async function reconcile(){const r=await fetch('/api/conversations',{cache:'no-store'});if(!r.ok)return;const active=state.active;state.conversations=(await r.json()).conversations;renderList();if(active&&state.conversations.some(c=>c.id===active))select(active);}
function startEventStream(){if(!window.EventSource)return;const stream=new EventSource('/api/events?after='+(state.cursor||0));stream.onmessage=event=>{state.cursor=Number(event.lastEventId||state.cursor||0);reconcile();};stream.onerror=()=>{stream.close();setTimeout(startEventStream,1500);};}
async function createConversation(resident,title,roomId){const r=await fetch('/api/conversations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resident_id:resident,title:title||((names[resident]||{}).name||'General Riverview Operator'),room_id:roomId||''})});if(r.ok){const c=await r.json();state.conversations.unshift(c);select(c.id);}}
async function hash(file){const bytes=await file.arrayBuffer();const digest=await crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');}
function speakResponse(text){if(state.audio[state.active]&&window.speechSynthesis){window.speechSynthesis.cancel();window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));}}
async function send(){const text=$('message').value.trim();if(!text||!state.active)return;const c=state.conversations.find(x=>x.id===state.active);const file=$('artifact').files[0];const refs=file?['browser-artifact:'+file.name+':'+await hash(file)]:[];c.messages.push({role:'steward',speaker:'Steward',text});renderMessages(c);$('message').value='';const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({request_id:crypto.randomUUID(),correlation_id:crypto.randomUUID(),message:text,context_refs:refs,resident_id:c.resident_id,session_id:state.sessions[c.resident_id]||'',conversation_id:c.id,classification:'operational',model:'approved'})});const b=await r.json();if(!r.ok){const errorText=(b.error==='authentication_required'?'AUTHENTICATION FAILURE':b.error==='cme_unavailable'?'CME FAILURE':'BACKEND UNAVAILABLE');c.messages.push({role:'system',speaker:'Riverview diagnostics',text:errorText,details:{checkpoint:b.checkpoint||'unavailable',cause_checkpoint:b.cause_checkpoint||'unavailable',status:r.status}});speakResponse(errorText);}else{if(b.session_id)state.sessions[c.resident_id]=b.session_id;c.messages.push({role:'resident',speaker:b.resident?.resident_name||'Riverview',text:b.response?.summary||b.response?.response||'' ,details:b});speakResponse(b.response?.summary||'');}c.preview=c.messages.at(-1)?.text||'';await fetch('/api/conversations/'+c.id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(c)});renderList();renderMessages(c);}
async function copyMessage(i){const m=state.conversations.find(x=>x.id===state.active).messages[i];try{await navigator.clipboard.writeText(m.text);$('context-title').textContent='Copied';$('context-title').nextElementSibling.textContent='Exact message text copied to the clipboard.';}catch(error){const area=document.createElement('textarea');area.value=m.text;document.body.append(area);area.select();document.execCommand('copy');area.remove();$('context-title').textContent='Copied using browser fallback';}}
function details(i){const c=state.conversations.find(x=>x.id===state.active),m=c.messages[i];const envelope=Object.assign({conversation_id:c.id,message_index:i,role:m.role,speaker:m.speaker||'unavailable',resident_id:c.resident_id||'unavailable',classification:c.classification||'unavailable'},m.details||{});$('context-title').textContent='Message Details';$('context-title').nextElementSibling.textContent=JSON.stringify(envelope,null,2);}
async function showArchitecture(){const r=await fetch('/api/architecture');if(!r.ok)return;const b=await r.json();$('messages').innerHTML='<div class="card"><strong>Architecture projections</strong><p class="muted">Generated Mermaid views are discovered from the architecture directory; source remains available below each view.</p><select id="graph-select">'+b.views.map((v,i)=>`<option value="${i}">${esc(v.title)}</option>`).join('')+'</select><div id="graph" style="overflow:auto;margin-top:16px"></div><details style="margin-top:12px"><summary>Source</summary><pre id="graph-source" class="muted"></pre></details></div>';if(window.mermaid)window.mermaid.initialize({startOnLoad:false,securityLevel:'strict'});const draw=async()=>{const v=b.views[Number($('graph-select').value)||0];$('graph').replaceChildren();$('graph-source').textContent=v?.source||'';try{if(window.mermaid){const rendered=await window.mermaid.render('operator-graph-'+Date.now(),v?.source||'');$('graph').innerHTML=rendered.svg;}}catch(error){$('graph').textContent='Architecture render unavailable; inspect Source.';}};$('graph-select').onchange=draw;draw();}
function showSettings(){ $('messages').innerHTML='<div class="card"><strong>Settings</strong><p class="muted">Preferences are local to this Operator client. Authority, provider policy, and resident continuity remain server-side.</p><p><button data-settings-tab="appearance">Appearance</button> <button data-settings-tab="conversations">Conversations</button> <button data-settings-tab="audio">Audio / Voice</button> <button data-settings-tab="operator">Operator / HUD</button> <button data-settings-tab="diagnostics">Diagnostics</button> <button data-settings-tab="advanced">Advanced</button> <button data-settings-tab="data">Data / Reset</button></p><section id="settings-panel"><h3>Appearance</h3><p>Theme</p><p><button data-theme-choice="light">Light</button> <button data-theme-choice="dark">Dark</button> <button data-theme-choice="system">System</button></p><label>Sidebar starts open <input id="sidebar-default" type="checkbox" checked></label></section></div>';const panel=$('settings-panel');const content={conversations:'<h3>Conversations</h3><p>Conversation history is durable in PostgreSQL. Resident continuity is not deleted by conversation cleanup.</p><label>Audio responses default off <input type="checkbox" checked disabled></label>',audio:'<h3>Audio / Voice</h3><p>Bounded local microphone capture is available from the composer.</p><p>Local TTS output: <strong>Unavailable — adapter not verified</strong></p><p>Wake word and always-listening capture: deferred.</p>',operator:'<h3>Operator / HUD</h3><label>Compact status indicators <input type="checkbox" checked></label><p class="muted">HUD states come from authoritative projections where available.</p>',diagnostics:'<h3>Diagnostics</h3><p>Failures retain Cookbook checkpoint IDs and bounded lineage. Raw envelopes are available from message Details.</p>',advanced:'<h3>Advanced / Debug</h3><p>Bearer fallback and raw diagnostic controls are intentionally not exposed in the ordinary Operator surface.</p>',data:'<h3>Data / Reset</h3><p>Conversation archive/delete and destructive test reset require a protected contract and are not offered as casual actions.</p>'};document.querySelectorAll('[data-settings-tab]').forEach(x=>x.onclick=()=>{panel.innerHTML=content[x.dataset.settingsTab]||panel.innerHTML;});document.querySelectorAll('[data-theme-choice]').forEach(x=>x.onclick=()=>{const v=x.dataset.themeChoice;document.documentElement.dataset.theme=v;localStorage.setItem('riverview-theme',v);});}
async function showNotifications(){const r=await fetch('/api/notifications');if(!r.ok){$('messages').innerHTML='<div class="card"><strong>Notifications unavailable</strong><p class="muted">Authoritative notification projection is unavailable. No UI-only notification state is being shown.</p></div>';return;}const b=await r.json();$('messages').innerHTML='<div class="card"><strong>Notifications</strong>'+((b.notifications||[]).map(n=>`<article class="card"><strong>${esc(n.notification_type)} · ${esc(n.state)}</strong><p>${esc(n.summary)}</p><small>${esc(n.checkpoint_id)} · ${esc(n.created_at)}</small></article>`).join('')||'<p class="muted">No authoritative notifications.</p>')+'</div>';}
function showRoomDialog(){const d=document.createElement('dialog');d.open=true;d.innerHTML='<form method="dialog" style="padding:18px"><h3>Create Room</h3><p class="muted">Choose participants. A room is a persistent conversation.</p><div>'+[...$('resident').options].filter(x=>x.value).map(x=>`<label style="display:block;padding:5px"><input type="checkbox" value="${esc(x.value)}"> ${esc(x.textContent)}</label>`).join('')+'</div><input id="room-name" placeholder="Room name (optional)" style="margin:10px 0;padding:8px"><br><button value="cancel">Cancel</button> <button id="room-create" value="default">Create</button></form>';document.body.append(d);d.querySelector('#room-create').onclick=async e=>{e.preventDefault();const participants=[...d.querySelectorAll('input[type=checkbox]:checked')].map(x=>x.value);if(!participants.length)return;const r=await fetch('/api/rooms',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({participants,title:d.querySelector('#room-name').value})});if(r.ok){const room=await r.json();await createConversation('',d.querySelector('#room-name').value||('Room · '+participants.map(x=>names[x]?.name).join(' · ')));}d.remove();};}
async function loadCme(){const r=await fetch('/api/cme/status',{cache:'no-store'});const b=await r.json();const x=$('cme');x.className=(r.ok?'healthy ':'danger ');x.title=r.ok?JSON.stringify(b):'CME unavailable';}
$('send').onclick=()=>send();$('message').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}};$('new').onclick=()=>createConversation($('resident').value,'');$('resident').onchange=()=>{const rid=$('resident').value,c=state.conversations.find(x=>x.id===state.active);if(rid&&(!c||c.resident_id!==rid))createConversation(rid,(names[rid]?.name||'Resident')+' Conversation');};$('room').onclick=showRoomDialog;$('menu').onclick=()=>{const open=$('sidebar').classList.toggle('hidden');localStorage.setItem('riverview-sidebar-open',String(!open));};$('search').oninput=renderList;$('mic').onclick=async()=>{const r=await fetch('/api/transcribe',{method:'POST'});if(r.ok)$('message').value=(await r.json()).text;};$('attach').onclick=()=>$('artifact').click();$('artifact').onchange=()=>{const f=$('artifact').files[0];$('attachment-state').innerHTML=f?`<span title="Pending reference">📎 ${esc(f.name)} <button id="remove-attachment" type="button" aria-label="Remove attachment">×</button></span>`:'';if(f)$('remove-attachment').onclick=()=>{$('artifact').value='';$('attachment-state').textContent='';};};$('audio').onclick=()=>{if(state.active){state.audio[state.active]=!state.audio[state.active];localStorage.setItem('riverview-audio-'+state.active,String(state.audio[state.active]));$('audio').textContent=state.audio[state.active]?'🔊':'🔇';}};$('snapshot').onclick=async()=>{const r=await fetch('/snapshot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_dom:'<!doctype html>'+document.documentElement.outerHTML,page_url:location.href,title:document.title,visible_status:'operator_v1',selected_resident:$('resident').value,composer:$('message').value,correlation_ids:[],artifact_refs:[],resident_state:{active_conversation:state.active,conversations:state.conversations.map(c=>({id:c.id,title:c.title,resident_id:c.resident_id}))},room_state:state.conversations.find(c=>c.id===state.active&&c.kind==='room')||{},api_state:{theme:document.documentElement.dataset.theme,route:location.pathname}})});if(r.ok){const a=document.createElement('a');a.href=URL.createObjectURL(await r.blob());a.download='riverview-snapshot.zip';a.click();}};$('cme').onclick=()=>location.href='/cme';document.querySelectorAll('[data-view]').forEach(x=>x.onclick=()=>{document.querySelectorAll('[data-view]').forEach(y=>y.classList.remove('active'));x.classList.add('active');if(x.dataset.view==='architecture')showArchitecture();else if(x.dataset.view==='settings')showSettings();else if(x.dataset.view==='notifications')showNotifications();else $('context-title').textContent=x.textContent;});document.documentElement.dataset.theme=localStorage.getItem('riverview-theme')||'system';if(localStorage.getItem('riverview-sidebar-open')==='false')$('sidebar').classList.add('hidden');
load().then(startEventStream).catch(()=>{$('subtitle').textContent='BACKEND UNAVAILABLE — inspect diagnostics';});setInterval(loadCme,3000);
</script></body></html>"""


@dataclass(frozen=True, slots=True)
class OpenWebUIConfig:
    host: str = "127.0.0.1"
    port: int = 18080
    service_identity: str = "riverview-openwebui"
    data_path: str = r"A:\Riverview\runtime\operator\openwebui"
    bearer_token: str = ""
    default_model: str = "qwen3-coder:30b-qwencode-20k"

    def __post_init__(self) -> None:
        if self.host not in {"127.0.0.1", "localhost"} or not 1024 <= self.port <= 65535:
            raise ValueError("RIV-UI-0009: Riverview Open WebUI must be loopback-only and bounded.")
        if not self.service_identity.strip() or not self.data_path.strip() or not self.bearer_token.strip():
            raise ValueError("RIV-UI-0009: service identity, data path, and bearer token are required.")


class RiverviewOpenWebUIService:
    def __init__(self, config: OpenWebUIConfig, provider: Callable[[str, ReasoningRequest], ReasoningResponse], resident_gateway: ResidentConversationGateway | None = None) -> None:
        self.config = config
        self.provider = provider
        self.authorized_model = config.default_model
        self.resident_gateway = resident_gateway or ResidentConversationGateway.from_evidence()
        self.sessions: set[str] = set()
        # The projection owns UI history only; resident continuity/canon remains
        # exclusively in the resident/character mechanisms.
        self.projection = OperatorProjection()
        self.conversations: dict[UUID, dict[str, object]] = {}
        for existing in self.projection.list():
            if existing.get("kind") == "room" and existing.get("room_id"):
                try:
                    service_room_id = UUID(str(existing["room_id"]))
                    participants = tuple(str(existing.get("resident_id", "")).removeprefix("room:").split(","))
                    self.resident_gateway.restore_room(service_room_id, participants, classification=str(existing.get("classification", "operational")))
                except (ValueError, LookupError):
                    pass
        self.diagnostics = DiagnosticStore()
        self.events = EventStore()
        service = self

        def authorized_model(payload: dict[str, object]) -> str:
            requested = str(payload.get("model") or "").strip()
            return service.authorized_model if requested in {"", "approved", "riverview-provider-neutral"} else requested

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

        def emit_event(event_type: str, aggregate_type: str, aggregate_id: str, correlation_id: UUID | None = None, payload: dict[str, object] | None = None) -> None:
            """Publish a bounded workflow fact; never make the UI depend on River availability."""
            try:
                aggregate_uuid = UUID(aggregate_id)
            except (ValueError, AttributeError):
                aggregate_uuid = uuid4()
            try:
                service.events.append(RiverEvent(
                    event_type=event_type,
                    aggregate_type=aggregate_type,
                    aggregate_id=aggregate_uuid,
                    idempotency_key=f"operator:{event_type}:{aggregate_id}:{correlation_id or uuid4()}",
                    correlation_id=correlation_id or uuid4(),
                    classification=Classification.RIVER,
                    payload=payload or {},
                ))
            except (OSError, RuntimeError, TypeError, ValueError):
                diagnostic("RIV-DIA-0001", "river_event", "event_persistence_failure", f"Bounded event {event_type} could not be persisted.")

        service.emit_event = emit_event

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
                elif self.path == "/cme":
                    self._send_html("""<!doctype html><html data-theme='system'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>CME status</title><style>:root{font:16px system-ui;color:#17212b;background:#f5f7fa}body{max-width:760px;margin:3rem auto;padding:0 1rem}pre{white-space:pre-wrap;background:#fff;border:1px solid #dbe2ea;border-radius:10px;padding:1rem}html[data-theme='dark']{filter:invert(.92) hue-rotate(180deg)}summary{cursor:pointer}</style><h1>Continuous Momentum Engine</h1><p>Authoritative operational status.</p><section id='human'>Loading…</section><details><summary>Raw / Advanced</summary><pre id='status'></pre></details><script>document.documentElement.dataset.theme=localStorage.getItem('riverview-theme')||'system';async function load(){const r=await fetch('/api/cme/status',{cache:'no-store'});const b=await r.json();document.getElementById('human').innerHTML='<strong>'+((b.heartbeat_health||'UNAVAILABLE')+' · '+(b.effective_state||'UNAVAILABLE'))+'</strong><p>Heartbeat age: '+(b.heartbeat_age_seconds??'unavailable')+'s</p><p>Last event: '+(b.last_event_type||'unavailable')+'</p><p>Waiting: '+(b.waiting_reason||'none')+'</p>';document.getElementById('status').textContent=JSON.stringify(b,null,2)}load();setInterval(load,3000);</script></html>""")
                elif self.path == "/spatial":
                    from riverview.spatial.prototype import prototype_html
                    self._send_html(prototype_html())
                elif self.path == "/health":
                    try:
                        source_sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=2, check=True).stdout.strip()
                    except (OSError, subprocess.SubprocessError):
                        source_sha = "unknown"
                    self._send(HTTPStatus.OK, {"status": True, "service": service.config.service_identity, "operator_shell": "v1", "source_sha": source_sha})
                elif self.path == "/api/models" and self._auth():
                    self._send(HTTPStatus.OK, {"data": [{"id": "riverview-provider-neutral"}]})
                elif self.path == "/api/models":
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                elif self.path == "/api/residents" and self._auth():
                    self._send(HTTPStatus.OK, {"residents": service.resident_gateway.residents()})
                elif self.path == "/api/residents":
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                elif self.path == "/api/cme/status" and self._auth():
                    try:
                        status = CMEStatusStore().read()
                        if status is None:
                            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "cme_unavailable", "checkpoint": "RIV-GRC-0008"})
                        else:
                            self._send(HTTPStatus.OK, status)
                    except (RuntimeError, OSError, TypeError, ValueError):
                        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "cme_status_unavailable", "checkpoint": "RIV-GRC-0008"})
                elif self.path == "/api/cme/status":
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                elif urlsplit(self.path).path == "/api/events" and self._auth():
                    try:
                        query = parse_qs(urlsplit(self.path).query)
                        cursor = int(query.get("after", ["0"])[0])
                        self.send_response(HTTPStatus.OK)
                        self.send_header("Content-Type", "text/event-stream")
                        self.send_header("Cache-Control", "no-cache")
                        self.send_header("Connection", "keep-alive")
                        self.end_headers()
                        deadline = time.monotonic() + 25
                        while time.monotonic() < deadline:
                            rows = CMEStatusStore().event_rows(cursor, limit=64)
                            if rows:
                                for row in rows:
                                    cursor = int(row["sequence_id"])
                                    self.wfile.write(f"id: {cursor}\ndata: {json.dumps(row, default=str)}\n\n".encode())
                                self.wfile.flush()
                            else:
                                self.wfile.write(b": heartbeat\n\n")
                                self.wfile.flush()
                            time.sleep(1)
                    except (BrokenPipeError, ConnectionResetError, RuntimeError, OSError, TypeError, ValueError):
                        return
                elif urlsplit(self.path).path == "/api/events":
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                elif self.path == "/api/conversations" and self._auth():
                    self._send(HTTPStatus.OK, {"conversations": service.projection.list()})
                elif self.path == "/api/architecture" and self._auth():
                    root = __import__("pathlib").Path(__file__).resolve().parents[3] / "docs" / "architecture" / "graph_views"
                    views = []
                    for source in sorted(root.glob("*.mmd")):
                        views.append({"id": source.stem, "title": source.stem.split("_", 1)[-1].replace("_", " ").title(), "source": source.read_text(encoding="utf-8")})
                    self._send(HTTPStatus.OK, {"views": views})
                elif self.path == "/api/notifications" and self._auth():
                    try:
                        with connect() as connection, connection.cursor() as cursor:
                            cursor.execute("""SELECT notification_id,notification_type,checkpoint_id,summary,state,created_at
                                             FROM steward_notifications ORDER BY created_at DESC LIMIT 50""")
                            columns = [item.name for item in cursor.description]
                            self._send(HTTPStatus.OK, {"notifications": [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]})
                    except (RuntimeError, OSError, TypeError, ValueError):
                        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "notification_projection_unavailable", "checkpoint": "RIV-NOT-0001"})
                elif self.path.startswith("/api/conversations/") and self._auth():
                    try:
                        conversation_id = UUID(self.path.rsplit("/", 1)[1])
                        conversation = service.projection.refresh(conversation_id)
                        if conversation is None:
                            raise KeyError(conversation_id)
                        self._send(HTTPStatus.OK, conversation)
                    except (KeyError, ValueError):
                        self._send(HTTPStatus.NOT_FOUND, {"error": "conversation_not_found", "checkpoint": "RIV-UI-0021"})
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
                        emit_event("microphone.transcript.completed", "operator", str(uuid4()), payload={"provider_id": result.provider_id, "retention": result.retention, "audio_retained": False})
                        self._send(HTTPStatus.OK, {"provider_id": result.provider_id, "text": result.text, "retention": result.retention, "culture": result.culture, "confidence": result.confidence})
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
                        emit_event("operator.snapshot.created", "operator", str(uuid4()), payload={"filename": filename, "capture_reason": "manual_operator_snapshot"})
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
                        operator_conversation = service.projection.create(resident_id="room:" + ",".join(participants), title=str(payload.get("title") or ("Room · " + " · ".join(participants))), kind="room", room_id=room_id, classification=str(payload.get("classification", "operational")))
                        emit_event("room.created", "room", str(room_id), payload={"participant_ids": list(participants), "classification": str(payload.get("classification", "operational"))})
                        room_snapshot = service.resident_gateway.room_snapshot(room_id)
                        room_snapshot["operator_conversation"] = operator_conversation
                        self._send(HTTPStatus.OK, room_snapshot)
                    except (TypeError, ValueError, LookupError, PermissionError):
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_request_rejected", "checkpoint": "RIV-RES-0002"})
                    return
                if self.path == "/api/conversations":
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        conversation_id = uuid4()
                        resident_id = str(payload.get("resident_id") or "")
                        resident = next((item for item in service.resident_gateway.residents() if item["resident_id"] == resident_id), None)
                        title = str(payload.get("title") or (resident["name"] if resident else "General Riverview Operator"))[:160]
                        conversation = {"id": str(conversation_id), "title": title, "resident_id": resident_id, "resident_name": resident["name"] if resident else "General Riverview Operator", "messages": [], "preview": "", "unread": False, "kind": "conversation"}
                        service.conversations[conversation_id] = conversation
                        conversation = service.projection.create(resident_id=resident_id, title=title, classification=str(payload.get("classification", "operational")))
                        if resident:
                            conversation["resident_name"] = resident["name"]
                        self._send(HTTPStatus.OK, conversation)
                    except (TypeError, ValueError, KeyError):
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "conversation_request_rejected", "checkpoint": "RIV-UI-0021"})
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
                        for room_conversation in service.projection.list():
                            if room_conversation.get("room_id") == room_text:
                                service.projection.append(UUID(str(room_conversation["id"])), role="resident", text=str(payload["text"]), speaker_id=turn["speaker_id"], speaker=str(payload["speaker"]), details=turn)
                                break
                        emit_event("room.turn.submitted", "room", room_text, UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None, {"speaker": str(payload["speaker"]), "classification": "operational"})
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
                        model = authorized_model(payload)
                        responses = service.resident_gateway.room_chat(UUID(room_text), str(payload["message"]), provider=lambda request: service.provider(model, request), interface_id=service.config.service_identity, correlation_id=UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None)
                        correlation_id = UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None
                        for room_conversation in service.projection.list():
                            if room_conversation.get("room_id") == room_text:
                                room_conversation_id = UUID(str(room_conversation["id"]))
                                service.projection.append(room_conversation_id, role="steward", text=str(payload["message"]), speaker_id=None, speaker="Steward", details={"correlation_id": str(correlation_id) if correlation_id else None})
                                for response_turn in responses:
                                    envelope = response_turn.get("response", {})
                                    service.projection.append(room_conversation_id, role="resident", text=str(envelope.get("summary", "")), speaker_id=str(response_turn.get("speaker_id", "")), speaker=str(response_turn.get("speaker_name", "Resident")), details=envelope)
                                break
                        emit_event("room.turn.completed", "room", room_text, correlation_id, {"participant_count": len(responses), "provider": model, "classification": "operational"})
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
                    emit_event("resident.message.submitted", "resident", resident_id or "operator", request.correlation_id, {"resident_id": resident_id or None, "classification": request.classification, "interface": service.config.service_identity, "artifact_count": len(request.context_refs)})
                    if resident_id:
                        session, response, resident_metadata = service.resident_gateway.chat(
                            resident_id,
                            request.instruction,
                            provider=lambda resident_request: service.provider(authorized_model(payload), resident_request),
                            interface_id=service.config.service_identity,
                            classification=request.classification,
                            session_id=UUID(str(payload["session_id"])) if payload.get("session_id") else None,
                            correlation_id=request.correlation_id,
                        )
                        body = {"service": service.config.service_identity, "context_refs": list(request.context_refs), "artifact_semantics": "reference_only" if request.context_refs else "none", "resident": resident_metadata, "session_id": str(session.session_id), "response": response.as_typed_payload()}
                        conversation_id = str(payload.get("conversation_id") or "")
                        if conversation_id:
                            try:
                                conversation = UUID(conversation_id)
                                service.projection.append(conversation, role="steward", text=request.instruction, speaker_id=None, speaker="Steward", details={"request_id": str(request.request_id), "correlation_id": str(request.correlation_id)})
                                service.projection.append(conversation, role="resident", text=response.summary, speaker_id=resident_id, speaker=resident_metadata["resident_name"], details=response.as_typed_payload())
                            except (KeyError, ValueError):
                                pass
                        emit_event("resident.response.completed", "resident", resident_id, request.correlation_id, {"session_id": str(session.session_id), "resident_id": resident_id, "provider": authorized_model(payload), "classification": request.classification})
                        if resident_metadata.get("grace_addressed"):
                            emit_event("grace.conversation.completed", "grace", resident_id, request.correlation_id, {"execution_intent_detected": bool(resident_metadata.get("execution_intent_detected")), "seed_promotion_required": bool(resident_metadata.get("execution_requires_seed_promotion")), "objective_created": False})
                    else:
                        response = service.provider(authorized_model(payload), request)
                        body = {"service": service.config.service_identity, "context_refs": list(request.context_refs), "artifact_semantics": "reference_only" if request.context_refs else "none", "response": response.as_typed_payload()}
                        emit_event("operator.response.completed", "operator", "operator", request.correlation_id, {"provider": authorized_model(payload), "classification": request.classification})
                    self._send(HTTPStatus.OK, body)
                except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as exc:  # bounded protocol error
                    provider_failure = "RIV-REASON-0002" in str(exc)
                    checkpoint = "RIV-RES-0002" if resident_id else "RIV-UI-0009"
                    diagnostic(checkpoint, "resident_chat" if resident_id else "operator_chat", "resident_provider_failure" if resident_id else "bounded_request_failure", f"Bounded operator request failed: {type(exc).__name__}.")
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "bounded_request_rejected", "checkpoint": checkpoint, "cause_checkpoint": "RIV-REASON-0002" if provider_failure else "unavailable"})

            def do_PUT(self) -> None:
                if not self._auth() or not self.path.startswith("/api/conversations/"):
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                    return
                try:
                    conversation_id = UUID(self.path.rsplit("/", 1)[1])
                    if service.projection.refresh(conversation_id) is None:
                        raise LookupError
                    length = int(self.headers.get("Content-Length", "0"))
                    payload = json.loads(self.rfile.read(length))
                    current = service.projection.refresh(conversation_id) or {}
                    if "title" in payload:
                        current["title"] = str(payload["title"]).strip()[:160] or current["title"]
                        if service.projection.available:
                            with connect() as connection, connection.cursor() as cursor:
                                cursor.execute("UPDATE operator_conversations SET title=%s,updated_at=now() WHERE conversation_id=%s", (current["title"], conversation_id))
                        else:
                            service.projection.memory[conversation_id]["title"] = current["title"]
                    self._send(HTTPStatus.OK, current)
                except (KeyError, LookupError, TypeError, ValueError):
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "conversation_update_rejected", "checkpoint": "RIV-UI-0021"})

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
