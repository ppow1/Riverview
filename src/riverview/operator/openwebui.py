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

from psycopg import Error as PostgresError

from riverview.autonomy.runtime import CMEStatusStore
from riverview.database import connect
from riverview.diagnostics import DiagnosticEvent, DiagnosticStore, RecoveryState, Severity
from riverview.operator.activity import ActivityProjection
from riverview.operator.projection import OperatorProjection
from riverview.operator.room_admin import RoomAdministration
from riverview.operator.snapshot import build_snapshot
from riverview.operator.ui import UI_HTML as CLEAN_UI_HTML
from riverview.reasoning import ReasoningRequest, ReasoningResponse
from riverview.residents.gateway import ResidentConversationGateway, RoomTurnPartialFailure
from riverview.river.events import Classification, RiverEvent
from riverview.river.store import EventStore


class RoomProjectionError(ValueError):
    """Bounded room integrity failure with a stable diagnostic class."""

    def __init__(self, failure_class: str, reason: str) -> None:
        super().__init__(reason)
        self.failure_class = failure_class


def _canonical_room_title(profiles: list[dict[str, str]], fallback: str = "") -> str:
    names = [str(item.get("name", "")).strip() for item in profiles if str(item.get("name", "")).strip()]
    if len(names) == 2:
        return " & ".join(names)
    if len(names) > 2:
        return ", ".join(names[:-1]) + " & " + names[-1]
    return fallback


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
        self.room_administration = RoomAdministration()
        self.activity = ActivityProjection()
        self.conversations: dict[UUID, dict[str, object]] = {}
        for existing in self.projection.list():
            if existing.get("kind") == "room" and existing.get("room_id"):
                try:
                    service_room_id = UUID(str(existing["room_id"]))
                    legacy = tuple(item for item in str(existing.get("resident_id", "")).removeprefix("room:").split(",") if item)
                    # Only an old room with no membership history is eligible
                    # for deterministic migration.  Removed/left history is
                    # never revived from a title or transcript.
                    if legacy and all(self.resident_gateway.resolve(item) for item in legacy):
                        membership_state = self.room_administration.reconcile_legacy(service_room_id, legacy)
                    else:
                        membership_state = self.room_administration.snapshot(service_room_id)
                    participants = tuple(membership_state["participants"])
                    if participants:
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

        def room_projection(room_id: UUID) -> dict[str, object]:
            """Reconcile derived gateway state from durable room membership."""
            membership = service.room_administration.snapshot(room_id)
            canonical = tuple(str(item) for item in membership.get("participants", ()))
            errors: list[str] = []
            if not membership.get("membership_projection_consistent", True):
                errors.append("duplicate_active_membership")
            profiles: list[dict[str, str]] = []
            for resident_id in canonical:
                try:
                    profile = service.resident_gateway.resolve(resident_id)
                except LookupError:
                    errors.append("participant_profile_resolution_failed")
                    continue
                profiles.append({"resident_id": resident_id, "name": profile.name, "role": profile.role})
            try:
                gateway = service.resident_gateway.room_snapshot(room_id)
                gateway_participants = tuple(str(item) for item in gateway.get("participants", ()))
            except LookupError:
                gateway = None
                gateway_participants = ()
            if canonical:
                try:
                    if gateway is None:
                        service.resident_gateway.restore_room(room_id, canonical)
                    elif gateway_participants != canonical:
                        service.resident_gateway.set_room_participants(room_id, canonical)
                    gateway_participants = tuple(str(item) for item in service.resident_gateway.room_snapshot(room_id).get("participants", ()))
                except (LookupError, ValueError):
                    errors.append("gateway_membership_reconciliation_failed")
            elif gateway_participants:
                errors.append("gateway_membership_without_durable_membership")
            if gateway_participants != canonical:
                errors.append("gateway_membership_mismatch")
            return {
                "room_id": str(room_id),
                "membership_state": membership,
                "participants": list(canonical),
                "participant_profiles": profiles,
                "participant_count": len(canonical),
                "gateway_participant_ids": list(gateway_participants),
                "room_projection_consistent": not errors and len(profiles) == len(canonical),
                "inconsistency_classes": sorted(set(errors)),
                "administrator_ids": [row.get("administrator_id") for row in membership.get("administrators", ())],
                "primary_administrator": next((row.get("administrator_id") for row in membership.get("administrators", ()) if row.get("primary_administrator")), None),
            }

        def enrich_room_conversation(conversation: dict[str, object]) -> dict[str, object]:
            """Attach the canonical room projection to every conversation read."""
            if conversation.get("kind") != "room" or not conversation.get("room_id"):
                return conversation
            room = room_projection(UUID(str(conversation["room_id"])))
            conversation.update({
                "participants": room["participants"],
                "participant_profiles": room["participant_profiles"],
                "participant_count": room["participant_count"],
                "gateway_participant_ids": room["gateway_participant_ids"],
                "membership_state": room["membership_state"],
                "room_projection_consistent": room["room_projection_consistent"],
                "inconsistency_classes": room["inconsistency_classes"],
                "administrator_ids": room["administrator_ids"],
                "primary_administrator": room["primary_administrator"],
            })
            return conversation

        service.room_projection = room_projection

        class Handler(BaseHTTPRequestHandler):
            def _send(self, status: HTTPStatus, payload: dict[str, object]) -> None:
                body = json.dumps(payload, separators=(",", ":"), default=str).encode()
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
                    self._send_html(CLEAN_UI_HTML)
                elif self.path == "/cme":
                    self._send_html("""<!doctype html><html data-theme='system'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>CME status</title><style>:root{font:16px system-ui;color:#17212b;background:#f5f7fa;--panel:#fff;--border:#dbe2ea}body{max-width:760px;margin:3rem auto;padding:0 1rem}body,pre{background:var(--panel)}pre{white-space:pre-wrap;border:1px solid var(--border);border-radius:10px;padding:1rem}a{display:inline-block;margin-bottom:1rem}html[data-theme='dark']{color-scheme:dark;--panel:#182231;--border:#344257;color:#e8edf5;background:#111722}summary{cursor:pointer}</style><a href='/'>← Back to Operator</a><h1>Continuous Momentum Engine</h1><p>Authoritative operational status.</p><section id='human'>Loading…</section><details><summary>Raw / Advanced</summary><pre id='status'></pre></details><script>document.documentElement.dataset.theme=localStorage.getItem('riverview-theme')||'system';async function load(){const r=await fetch('/api/cme/status',{cache:'no-store'});const b=await r.json();document.getElementById('human').innerHTML='<strong>'+((b.heartbeat_health||'UNAVAILABLE')+' · '+(b.effective_state||'UNAVAILABLE'))+'</strong><p>Heartbeat age: '+(b.heartbeat_age_seconds??'unavailable')+'s</p><p>Last event: '+(b.last_event_type||'unavailable')+'</p><p>Waiting: '+(b.waiting_reason||'none')+'</p>';document.getElementById('status').textContent=JSON.stringify(b,null,2)}load();setInterval(load,3000);</script></html>""")
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
                elif urlsplit(self.path).path == "/api/activity" and self._auth():
                    try:
                        query = parse_qs(urlsplit(self.path).query)
                        after = int(query.get("after", ["0"])[0])
                        limit = int(query.get("limit", ["50"])[0])
                        category = str(query.get("category", [""])[0]).strip().lower()
                        if category not in {"", "all", "comms", "grace", "cme", "objectives", "work", "notifications", "river"}:
                            raise ValueError("activity_category_invalid")
                        self._send(HTTPStatus.OK, service.activity.list(after=after, limit=limit, category="" if category == "all" else category))
                    except (PostgresError, RuntimeError, TypeError, ValueError):
                        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "activity_projection_unavailable", "checkpoint": "RIV-UI-0028"})
                elif urlsplit(self.path).path == "/api/conversations" and self._auth():
                    query = parse_qs(urlsplit(self.path).query)
                    include_archived = query.get("archived", ["active"])[0] in {"all", "true", "archived"}
                    conversations = service.projection.list(include_archived=include_archived)
                    for item in conversations:
                        if item.get("kind") == "room" and item.get("title", "").startswith("Room · RES-"):
                            ids = [part for part in item.get("resident_id", "").removeprefix("room:").split(",") if part]
                            try:
                                labels = [service.resident_gateway.resolve(part).name for part in ids]
                                item["title"] = ", ".join(labels) if labels else "Conference Room"
                            except LookupError:
                                pass
                        item["archived"] = bool(include_archived and item.get("archived"))
                    self._send(HTTPStatus.OK, {"conversations": conversations})
                elif urlsplit(self.path).path == "/api/conversations/search" and self._auth():
                    query = parse_qs(urlsplit(self.path).query)
                    term = query.get("q", [""])[0]
                    try:
                        limit = int(query.get("limit", ["25"])[0])
                    except ValueError:
                        limit = 25
                    try:
                        results = service.projection.search(term, limit=limit)
                    except (PostgresError, RuntimeError, OSError, TypeError, ValueError) as exc:
                        diagnostic("RIV-UI-0025", "conversation_search", "durable_search_failure", f"Bounded durable search failed: {type(exc).__name__}.")
                        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "conversation_search_unavailable", "checkpoint": "RIV-UI-0025"})
                    else:
                        self._send(HTTPStatus.OK, {"query": term, "results": results})
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
                        path = urlsplit(self.path)
                        conversation_id = UUID(path.path.rsplit("/", 1)[1])
                        conversation = service.projection.refresh(conversation_id, include_archived=parse_qs(path.query).get("archived", [""])[0] == "true")
                        if conversation is None:
                            raise KeyError(conversation_id)
                        self._send(HTTPStatus.OK, enrich_room_conversation(conversation))
                    except (KeyError, ValueError):
                        self._send(HTTPStatus.NOT_FOUND, {"error": "conversation_not_found", "checkpoint": "RIV-UI-0021"})
                elif urlsplit(self.path).path.startswith("/api/rooms/") and urlsplit(self.path).path.endswith("/members") and self._auth():
                    try:
                        room_id = UUID(urlsplit(self.path).path.split("/")[3])
                        room = service.room_projection(room_id)
                        self._send(HTTPStatus.OK, room)
                    except (ValueError, LookupError):
                        self._send(HTTPStatus.NOT_FOUND, {"error": "room_membership_not_found", "checkpoint": "RIV-UI-0030"})
                elif self.path.startswith("/api/rooms/") and self._auth():
                    try:
                        room_id = UUID(self.path.rsplit("/", 1)[1])
                        room = service.room_projection(room_id)
                        projection = next((item for item in service.projection.list(include_archived=True) if item.get("room_id") == str(room_id)), None)
                        if projection:
                            room["conversation_id"] = projection.get("id", "")
                            room["declared_title"] = projection.get("title", "")
                            room["title"] = _canonical_room_title(room["participant_profiles"], "Room membership inconsistent" if not room["room_projection_consistent"] else projection.get("title", ""))
                            room["messages"] = projection.get("messages", [])
                            for key in ("source_conversation_id", "inherited_context_window", "inherited_message_count", "participants_added"):
                                room[key] = projection.get(key, "" if key != "inherited_message_count" else 0)
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
                if self.path.startswith("/api/conversations/") and self.path.endswith("/members"):
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        source_id = UUID(self.path.removeprefix("/api/conversations/").removesuffix("/members").strip("/"))
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        source = service.projection.refresh(source_id, include_archived=True)
                        resident_id = str(payload["resident_id"])
                        if source is None or source.get("kind") != "conversation" or not source.get("resident_id"):
                            raise ValueError("source must be an established resident conversation")
                        context_window = str(payload.get("context_window", "from_this_point"))
                        source_messages = list(source.get("messages", []))
                        inherited = source_messages[-100:] if context_window == "all" else source_messages[-100:] if context_window == "last_100" else source_messages[-20:] if context_window == "last_20" else []
                        participants = (str(source["resident_id"]), resident_id)
                        room_id = service.resident_gateway.create_room(participants, classification=str(source.get("classification", "operational")))
                        service.room_administration.initialize(room_id, participants, actor="steward")
                        labels = [service.resident_gateway.resolve(item).name for item in participants]
                        title = ", ".join(labels[:-1]) + " & " + labels[-1]
                        operator_conversation = service.projection.create(resident_id="room:" + ",".join(participants), title=title, kind="room", room_id=room_id, classification=str(source.get("classification", "operational")), source_conversation_id=source_id, inherited_context_window=context_window, inherited_message_count=len(inherited), participants_added=[resident_id])
                        for message in inherited:
                            service.projection.append(UUID(operator_conversation["id"]), role=str(message.get("role", "resident")), text=str(message.get("text", "")), speaker_id=message.get("speaker_id"), speaker=str(message.get("speaker", "Inherited context")), details={"inherited_from": str(source_id), "context_window": context_window})
                        operator_conversation = service.projection.refresh(UUID(operator_conversation["id"]), include_archived=True) or operator_conversation
                        emit_event("room.derived", "room", str(room_id), None, {"source_conversation_id": str(source_id), "resident_id": resident_id, "context_window": context_window, "inherited_message_count": len(inherited)})
                        self._send(HTTPStatus.OK, {"operator_conversation": operator_conversation, "room_id": str(room_id), "participants": list(participants), "source_conversation_id": str(source_id), "inherited_context_window": context_window, "inherited_message_count": len(inherited)})
                    except (KeyError, TypeError, ValueError, LookupError, PermissionError) as exc:
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "conversation_participant_add_rejected", "checkpoint": "RIV-UI-0030", "reason": str(exc)})
                    return
                if self.path.startswith("/api/rooms/") and self.path.endswith("/members"):
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        room_id = UUID(self.path.removeprefix("/api/rooms/").removesuffix("/members").strip("/"))
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        resident_id = str(payload["resident_id"])
                        context_window = str(payload.get("context_window", "from_this_point"))
                        source_id = UUID(str(payload["source_conversation_id"])) if payload.get("source_conversation_id") else None
                        correlation_id = UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else uuid4()
                        membership = service.room_administration.add(room_id, resident_id, actor="steward", context_window=context_window, source_conversation_id=source_id, correlation_id=correlation_id)
                        state = service.room_administration.snapshot(room_id)
                        service.resident_gateway.set_room_participants(room_id, tuple(state["participants"]))
                        conversation = next((item for item in service.projection.list(include_archived=True) if item.get("room_id") == str(room_id)), None)
                        if conversation:
                            conversation_id = UUID(str(conversation["id"]))
                            service.projection.append(conversation_id, role="system", text=f"{service.resident_gateway.resolve(resident_id).name} was added to the room.", speaker_id=None, speaker="Room membership", details={"event_type": "room_participant_added", "actor": "steward", "target": resident_id, "context_window": context_window, "correlation_id": str(correlation_id)})
                        emit_event("room.participant.added", "room", str(room_id), correlation_id, {"actor": "steward", "resident_id": resident_id, "context_window": context_window})
                        self._send(HTTPStatus.OK, {"membership": membership, "room": state})
                    except (KeyError, TypeError, ValueError, LookupError, PermissionError) as exc:
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_participant_add_rejected", "checkpoint": "RIV-UI-0030", "reason": str(exc)})
                    return
                if self.path.startswith("/api/rooms/") and self.path.endswith("/leave"):
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        room_id = UUID(self.path.removeprefix("/api/rooms/").removesuffix("/leave").strip("/"))
                        administration = service.room_administration.leave(room_id, actor="steward")
                        emit_event("room.administrator.left", "room", str(room_id), None, {"actor": "steward"})
                        self._send(HTTPStatus.OK, {"administrator": administration, "room": service.room_administration.snapshot(room_id)})
                    except (KeyError, TypeError, ValueError, LookupError, PermissionError) as exc:
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_leave_rejected", "checkpoint": "RIV-UI-0030", "reason": str(exc)})
                    return
                if self.path.startswith("/api/rooms/") and self.path.endswith("/admins"):
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        room_id = UUID(self.path.removeprefix("/api/rooms/").removesuffix("/admins").strip("/"))
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        admin = service.room_administration.grant_admin(room_id, str(payload["administrator_id"]), actor="steward", primary=bool(payload.get("primary", False)))
                        conversation = next((item for item in service.projection.list(include_archived=True) if item.get("room_id") == str(room_id)), None)
                        if conversation and admin["administrator_id"] != "steward":
                            profile = service.resident_gateway.resolve(admin["administrator_id"])
                            service.projection.append(UUID(str(conversation["id"])), role="system", text=f"{profile.name} was granted Room Administrator status.", speaker_id=None, speaker="Room membership", details={"event_type": "room_administrator_granted", "actor": "steward", "target": admin["administrator_id"]})
                        emit_event("room.administrator.granted", "room", str(room_id), UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None, {"actor": "steward", "administrator_id": admin["administrator_id"], "primary": admin["primary_administrator"]})
                        self._send(HTTPStatus.OK, {"administrator": admin, "room": service.room_administration.snapshot(room_id)})
                    except (KeyError, TypeError, ValueError, LookupError, PermissionError) as exc:
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_administrator_grant_rejected", "checkpoint": "RIV-UI-0030", "reason": str(exc)})
                    return
                if self.path == "/api/rooms":
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        participants = tuple(str(item) for item in payload.get("participants", ()))
                        source_conversation_id = UUID(str(payload["source_conversation_id"])) if payload.get("source_conversation_id") else None
                        context_window = str(payload.get("context_window", "from_this_point"))
                        inherited = []
                        if source_conversation_id:
                            source = service.projection.refresh(source_conversation_id, include_archived=True)
                            if source is None or source.get("kind") == "room":
                                raise LookupError("RIV-UI-0027: source conversation is unavailable for room derivation.")
                            source_messages = list(source.get("messages", []))
                            inherited = source_messages[-200:] if context_window == "all" else source_messages[-100:] if context_window == "last_100" else source_messages[-20:] if context_window == "last_20" else []
                        room_id = service.resident_gateway.create_room(participants, classification=str(payload.get("classification", "operational")))
                        service.room_administration.initialize(room_id, participants, actor="steward")
                        labels = [service.resident_gateway.resolve(participant).name for participant in participants]
                        default_title = ", ".join(labels[:-1]) + (" & " + labels[-1] if len(labels) > 1 else "") if labels else "Conference Room"
                        operator_conversation = service.projection.create(resident_id="room:" + ",".join(participants), title=str(payload.get("title") or default_title), kind="room", room_id=room_id, classification=str(payload.get("classification", "operational")), source_conversation_id=source_conversation_id, inherited_context_window=context_window if source_conversation_id else "", inherited_message_count=len(inherited), participants_added=list(participants))
                        for inherited_message in inherited:
                            service.projection.append(UUID(str(operator_conversation["id"])), role=str(inherited_message.get("role", "resident")), text=str(inherited_message.get("text", "")), speaker_id=inherited_message.get("speaker_id"), speaker=str(inherited_message.get("speaker", "Inherited context")), details={"inherited_from": str(source_conversation_id), "context_window": context_window})
                        operator_conversation = service.projection.refresh(UUID(str(operator_conversation["id"])), include_archived=True) or operator_conversation
                        emit_event("room.created", "room", str(room_id), payload={"participant_ids": list(participants), "classification": str(payload.get("classification", "operational"))})
                        room_snapshot = service.resident_gateway.room_snapshot(room_id)
                        room_snapshot["participant_profiles"] = [{"resident_id": p, "name": service.resident_gateway.resolve(p).name, "role": service.resident_gateway.resolve(p).role} for p in participants]
                        room_snapshot["source_conversation_id"] = str(source_conversation_id) if source_conversation_id else ""
                        room_snapshot["inherited_context_window"] = context_window if source_conversation_id else ""
                        room_snapshot["inherited_message_count"] = len(inherited)
                        room_snapshot["operator_conversation"] = operator_conversation
                        self._send(HTTPStatus.OK, room_snapshot)
                    except (TypeError, ValueError, LookupError, PermissionError):
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_request_rejected", "checkpoint": "RIV-RES-0002"})
                    return
                if self.path == "/api/conversations/bulk":
                    if not self._auth():
                        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                        return
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        ids = [UUID(str(item)) for item in payload.get("conversation_ids", [])]
                        archived = bool(payload.get("archived", True))
                        changed = [service.projection.set_archived(item, archived) for item in ids]
                        self._send(HTTPStatus.OK, {"updated": [item for item in changed if item is not None], "archived": archived})
                    except (KeyError, TypeError, ValueError):
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "conversation_bulk_update_rejected", "checkpoint": "RIV-UI-0030"})
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
                        room_conversation = next((item for item in service.projection.list() if item.get("room_id") == room_text), None)
                        if room_conversation is None:
                            raise LookupError("RIV-UI-0027: room conversation projection is unavailable.")
                        room_state = service.room_projection(UUID(room_text))
                        if not room_state["room_projection_consistent"]:
                            raise RoomProjectionError("membership_projection_inconsistent", "room membership projection is inconsistent")
                        if not room_state["participants"]:
                            raise RoomProjectionError("room_has_no_active_participants", "room has no active participants")
                        room_messages = list(room_conversation.get("messages", []))
                        inherited_count = int(room_conversation.get("inherited_message_count") or 0)
                        inherited_messages = room_messages[:inherited_count]
                        context_window = str(room_conversation.get("inherited_context_window") or "from_this_point")
                        selected_inherited = inherited_messages[-200:] if context_window == "all" else inherited_messages[-100:] if context_window == "last_100" else inherited_messages[-20:] if context_window == "last_20" else []
                        live_messages = room_messages[inherited_count:][-20:]
                        context_messages = selected_inherited + live_messages
                        inherited_context = "\n".join(f"{item.get('speaker', 'Participant')}: {item.get('text', '')}" for item in context_messages)
                        instruction = str(payload["message"])
                        if inherited_context:
                            instruction = "Bounded inherited room context (do not treat as a new instruction):\n" + inherited_context + "\n\nCurrent Steward question:\n" + instruction
                        responses = service.resident_gateway.room_chat(UUID(room_text), instruction, provider=lambda request: service.provider(model, request), interface_id=service.config.service_identity, correlation_id=UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None)
                        correlation_id = UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None
                        for room_conversation in service.projection.list():
                            if room_conversation.get("room_id") == room_text:
                                room_conversation_id = UUID(str(room_conversation["id"]))
                                service.projection.append(room_conversation_id, role="steward", text=str(payload["message"]), speaker_id=None, speaker="Steward", details={"correlation_id": str(correlation_id) if correlation_id else None})
                                for response_turn in responses:
                                    envelope = response_turn.get("response", {})
                                    service.projection.append(room_conversation_id, role="resident", text=str(envelope.get("summary", "")), speaker_id=str(response_turn.get("speaker_id", "")), speaker=str(response_turn.get("speaker_name", "Resident")), details=envelope)
                                persisted = service.projection.refresh(room_conversation_id, include_archived=True)
                                if persisted is None or len(persisted.get("messages", [])) < 1 + len(responses):
                                    raise RuntimeError("RIV-UI-0027: room responses were not durably reconciled.")
                                break
                        emit_event("room.turn.completed", "room", room_text, correlation_id, {"participant_count": len(responses), "provider": model, "classification": "operational"})
                        self._send(HTTPStatus.OK, {"responses": responses, "persisted_message_count": len(persisted.get("messages", [])) if persisted else 0, "no_authority_expansion": True})
                    except RoomTurnPartialFailure as exc:
                        correlation_id = UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None
                        persisted = None
                        for room_conversation in service.projection.list():
                            if room_conversation.get("room_id") == room_text:
                                room_conversation_id = UUID(str(room_conversation["id"]))
                                service.projection.append(room_conversation_id, role="steward", text=str(payload["message"]), speaker_id=None, speaker="Steward", details={"correlation_id": str(correlation_id) if correlation_id else None, "status": "partial_failure"})
                                for response_turn in exc.completed:
                                    envelope = response_turn.get("response", {})
                                    service.projection.append(room_conversation_id, role="resident", text=str(envelope.get("summary", "")), speaker_id=str(response_turn.get("speaker_id", "")), speaker=str(response_turn.get("speaker_name", "Resident")), details={**envelope, "status": "completed", "correlation_id": str(correlation_id) if correlation_id else None})
                                persisted = service.projection.refresh(room_conversation_id, include_archived=True)
                                break
                        failure_class = getattr(exc, "failure_class", "provider_partial_failure")
                        diagnostic("RIV-RES-0002", "room_chat", failure_class, f"Room turn partially completed; failed resident {exc.failed_resident_id}; completed={len(exc.completed)}; cause={exc.cause_type}.")
                        emit_event("room.turn.partial_failure", "room", room_text, correlation_id, {"failed_participant": exc.failed_resident_id, "completed_participants": [item.get("speaker_id") for item in exc.completed], "failure_class": failure_class, "cause_type": exc.cause_type, "classification": "operational"})
                        self._send(HTTPStatus.BAD_GATEWAY, {"error": "room_chat_partial_failure", "checkpoint": "RIV-RES-0002", "failure_class": failure_class, "failed_participant": exc.failed_resident_id, "completed_participants": [item.get("speaker_id") for item in exc.completed], "persisted_message_count": len(persisted.get("messages", [])) if persisted else 0, "correlation_id": str(correlation_id) if correlation_id else None})
                    except (KeyError, TypeError, ValueError, LookupError, PermissionError, RuntimeError) as exc:
                        failure_class = getattr(exc, "failure_class", "room_provider_failure")
                        if isinstance(exc, LookupError):
                            failure_class = "room_missing" if "projection" in str(exc) else "participant_profile_resolution_failed"
                        elif isinstance(exc, PermissionError):
                            failure_class = "room_membership_inconsistent"
                        elif "RIV-REASON-0002" in str(exc):
                            failure_class = "provider_unavailable"
                        elif "durably reconciled" in str(exc):
                            failure_class = "persistence_failure"
                        reason = str(exc)[:240]
                        diagnostic("RIV-RES-0002", "room_chat", failure_class, f"Bounded room request failed: {failure_class}; reason={reason}.")
                        emit_event("room.turn.failed", "room", room_text, UUID(str(payload["correlation_id"])) if payload.get("correlation_id") else None, {"failure_class": failure_class, "reason": reason, "classification": "operational"})
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_chat_rejected", "checkpoint": "RIV-RES-0002", "failure_class": failure_class, "reason": reason})
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

            def do_PATCH(self) -> None:
                if self._auth() and self.path.startswith("/api/rooms/"):
                    try:
                        room_id = UUID(self.path.removeprefix("/api/rooms/").strip("/"))
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length))
                        title = str(payload.get("title", "")).strip()[:160]
                        if not title:
                            raise ValueError("room title is required")
                        conversation = next((item for item in service.projection.list(include_archived=True) if item.get("room_id") == str(room_id)), None)
                        if conversation is None:
                            raise LookupError
                        with connect() as connection, connection.cursor() as cursor:
                            cursor.execute("UPDATE operator_conversations SET title=%s,updated_at=now() WHERE conversation_id=%s", (title, UUID(str(conversation["id"]))))
                        emit_event("room.renamed", "room", str(room_id), None, {"actor": "steward", "title": title})
                        self._send(HTTPStatus.OK, {"room_id": str(room_id), "title": title})
                    except (KeyError, LookupError, TypeError, ValueError):
                        self._send(HTTPStatus.BAD_REQUEST, {"error": "room_update_rejected", "checkpoint": "RIV-UI-0030"})
                    return
                if not self._auth() or not self.path.startswith("/api/conversations/"):
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                    return
                try:
                    conversation_id = UUID(self.path.rsplit("/", 1)[1])
                    length = int(self.headers.get("Content-Length", "0"))
                    payload = json.loads(self.rfile.read(length))
                    result = service.projection.set_archived(conversation_id, bool(payload.get("archived", True)))
                    if result is None:
                        raise LookupError
                    self._send(HTTPStatus.OK, result)
                except (KeyError, LookupError, TypeError, ValueError):
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "conversation_archive_rejected", "checkpoint": "RIV-UI-0024"})

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
                    if "resident_id" in payload:
                        resident_id = str(payload.get("resident_id") or "").strip()
                        if not resident_id or current.get("kind") == "room" or current.get("resident_id"):
                            raise ValueError("initial resident assignment is only valid for an unassigned conversation")
                        profile = next((item for item in service.resident_gateway.residents() if item["resident_id"] == resident_id), None)
                        if profile is None:
                            raise ValueError("resident is not admitted")
                        assigned = service.projection.assign_resident(conversation_id, resident_id, str(payload.get("title") or f"{profile['name']} Conversation"))
                        if assigned is None:
                            raise ValueError("conversation resident assignment was not accepted")
                        current = assigned
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

            def do_DELETE(self) -> None:
                if not self._auth() or not self.path.startswith("/api/rooms/"):
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                    return
                try:
                    parts = self.path.removeprefix("/api/rooms/").strip("/").split("/")
                    room_id = UUID(parts[0])
                    if len(parts) != 3 or parts[1] not in {"members", "admins"}:
                        raise ValueError("room membership or administrator path required")
                    resident_id = parts[2]
                    if parts[1] == "admins":
                        admin = service.room_administration.revoke_admin(room_id, resident_id, actor="steward")
                        emit_event("room.administrator.revoked", "room", str(room_id), None, {"actor": "steward", "administrator_id": resident_id})
                        self._send(HTTPStatus.OK, {"administrator": admin, "room": service.room_administration.snapshot(room_id)})
                        return
                    membership = service.room_administration.remove(room_id, resident_id, actor="steward")
                    state = service.room_administration.snapshot(room_id)
                    service.resident_gateway.set_room_participants(room_id, tuple(state["participants"]))
                    conversation = next((item for item in service.projection.list(include_archived=True) if item.get("room_id") == str(room_id)), None)
                    if conversation:
                        service.projection.append(UUID(str(conversation["id"])), role="system", text=f"{service.resident_gateway.resolve(resident_id).name} was removed from the room.", speaker_id=None, speaker="Room membership", details={"event_type": "room_participant_removed", "actor": "steward", "target": resident_id, "correlation_id": membership.get("correlation_id")})
                    emit_event("room.participant.removed", "room", str(room_id), None, {"actor": "steward", "resident_id": resident_id})
                    self._send(HTTPStatus.OK, {"membership": membership, "room": state})
                except (KeyError, TypeError, ValueError, LookupError, PermissionError) as exc:
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "room_participant_remove_rejected", "checkpoint": "RIV-UI-0030", "reason": str(exc)})

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
