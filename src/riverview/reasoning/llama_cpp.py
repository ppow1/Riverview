"""Bounded loopback llama.cpp reasoning adapter for explicitly selected GPUs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from http.client import RemoteDisconnected
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from .contracts import ReasoningRequest, ReasoningResponse


class LlamaCppReasoningAdapter:
    """Call a Riverview-approved local llama-server endpoint only."""

    def __init__(self, *, endpoint: str = "http://127.0.0.1:8080", timeout_seconds: int = 90) -> None:
        parsed = urlparse(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or not parsed.port:
            raise ValueError("RIV-REASON-0003: llama.cpp adapter is loopback-only.")
        if not 1 <= timeout_seconds <= 300:
            raise ValueError("RIV-REASON-0003: timeout is outside its bound.")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def complete(self, model: str, request: ReasoningRequest, *, response_id: UUID | None = None) -> ReasoningResponse:
        if not model.strip() or len(model) > 200:
            raise ValueError("RIV-REASON-0003: model identity is invalid.")
        body = json.dumps({"prompt": request.instruction, "n_predict": 256, "temperature": 0}, separators=(",", ":")).encode()
        try:
            with urlopen(Request(self.endpoint + "/completion", data=body, headers={"Content-Type": "application/json"}), timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read(32_000))
        except (OSError, URLError, RemoteDisconnected, TimeoutError) as exc:
            raise RuntimeError("RIV-REASON-0003: local llama.cpp provider unavailable or timed out.") from exc
        summary = payload.get("content")
        if not isinstance(summary, str) or not summary.strip():
            raise RuntimeError("RIV-REASON-0003: local llama.cpp provider returned an invalid response.")
        return ReasoningResponse(
            response_id=response_id or uuid4(), request_id=request.request_id,
            correlation_id=request.correlation_id, provider_id=f"llama-cpp:{model}",
            response_type="analysis" if request.request_type == "analysis" else "advice",
            summary=summary[:8000], evidence_refs=(f"provider://llama-cpp/{model}",),
            classification=request.classification, created_at=datetime.now(UTC),
        )
