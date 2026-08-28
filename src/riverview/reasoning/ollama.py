"""Bounded local Ollama reasoning adapter.

Only loopback Ollama endpoints are accepted. Provider output is converted into the
provider-neutral response envelope and remains advisory data.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from http.client import RemoteDisconnected
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from .contracts import ReasoningRequest, ReasoningResponse


class OllamaReasoningAdapter:
    def __init__(self, *, endpoint: str = "http://127.0.0.1:11434", timeout_seconds: int = 60) -> None:
        parsed = urlparse(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or not parsed.port:
            raise ValueError("RIV-REASON-0002: Ollama adapter is loopback-only.")
        if not 1 <= timeout_seconds <= 300:
            raise ValueError("RIV-REASON-0002: timeout is outside its bound.")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def complete(self, model: str, request: ReasoningRequest, *, response_id: UUID | None = None) -> ReasoningResponse:
        if not model.strip() or len(model) > 200 or any(token in model.lower() for token in ("http://", "https://", "../")):
            raise ValueError("RIV-REASON-0002: model identity is invalid.")
        body_value: dict[str, object] = {"model": model, "prompt": request.instruction, "stream": False}
        if request.response_format is not None:
            body_value["format"] = request.response_format
            body_value["options"] = {"temperature": 0, "seed": 7, "num_predict": 2048}
        body = json.dumps(body_value, separators=(",", ":")).encode()
        try:
            with urlopen(Request(self.endpoint + "/api/generate", data=body, headers={"Content-Type": "application/json"}), timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read(32_000))
        except HTTPError as exc:
            detail = ""
            try:
                error_payload = json.loads(exc.read(4_000))
                detail = str(error_payload.get("error", ""))
            except (OSError, ValueError, TypeError):
                detail = ""
            if any(marker in detail.casefold() for marker in ("cuda", "out-of-memory", "out of memory")):
                raise RuntimeError(f"RIV-REASON-0003: provider resource unavailable: {detail[:240]}") from exc
            raise RuntimeError("RIV-REASON-0002: local reasoning provider unavailable or timed out.") from exc
        except (OSError, URLError, RemoteDisconnected, TimeoutError) as exc:
            raise RuntimeError("RIV-REASON-0002: local reasoning provider unavailable or timed out.") from exc
        summary = payload.get("response")
        if not isinstance(summary, str) or not summary.strip():
            raise RuntimeError("RIV-REASON-0002: local provider returned an invalid response.")
        structured = json.loads(summary) if summary.lstrip().startswith("{") else None
        semantic_outcome = structured.get("semantic_outcome") if isinstance(structured, dict) else None
        return ReasoningResponse(
            response_id=response_id or uuid4(),
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            provider_id=f"ollama:{model}",
            response_type="analysis" if request.request_type == "analysis" else "advice",
            summary=summary[:8000],
            evidence_refs=(f"provider://ollama/{model}",),
            classification=request.classification,
            created_at=datetime.now(UTC),
            semantic_outcome=semantic_outcome,
        )
