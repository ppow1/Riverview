from __future__ import annotations

import json
import urllib.request
from typing import Any

from .validator import validate_reasoning


class WorkerResponseError(ValueError):
    """The worker replied, but not with the mandatory structured contract."""


class ReasoningWorker:
    """One-shot OpenAI-compatible worker; no conversational state is retained."""

    def __init__(self, endpoint: str, timeout: float = 600):
        self.endpoint = endpoint
        self.timeout = timeout

    def reason(self, packet: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps({
                "model": "Qwen3-Next-80B-A3B-Instruct-Q4_K_M",
                "messages": [
                    {"role": "system", "content": "Return exactly one JSON object satisfying response_contract. Use only supplied durable evidence."},
                    {"role": "user", "content": json.dumps(packet, sort_keys=True)},
                ],
                "temperature": 0.1,
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.load(response)
        try:
            content = payload["choices"][0]["message"]["content"]
            result = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise WorkerResponseError("response was not a single JSON contract object") from exc
        validation = validate_reasoning(result)
        if not validation.accepted:
            raise WorkerResponseError(f"{validation.code}: {validation.reason}")
        return result
