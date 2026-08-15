"""Isolated Riverview-owned Open WebUI-compatible bounded adapter.

This is deliberately a small local operator surface, not a general shell/database
bridge. It accepts one typed reasoning request shape and delegates to an approved
provider-neutral adapter.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from uuid import UUID

from riverview.reasoning import ReasoningRequest, ReasoningResponse


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
        service = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, status: HTTPStatus, payload: dict[str, object]) -> None:
                body = json.dumps(payload, separators=(",", ":")).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _auth(self) -> bool:
                return self.headers.get("Authorization") == f"Bearer {service.config.bearer_token}"

            def do_GET(self) -> None:
                if self.path == "/health":
                    self._send(HTTPStatus.OK, {"status": True, "service": service.config.service_identity})
                elif self.path == "/api/models" and self._auth():
                    self._send(HTTPStatus.OK, {"data": [{"id": "riverview-provider-neutral"}]})
                elif self.path == "/api/models":
                    self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"})
                else:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

            def do_POST(self) -> None:
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
                    self._send(HTTPStatus.OK, {"service": service.config.service_identity, "response": response.as_typed_payload()})
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
