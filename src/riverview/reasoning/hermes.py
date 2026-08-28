"""Provider-neutral Hermes execution adapter for Riverview cognition.

Riverview owns identity, authority, classification, lifecycle, provenance, and
acceptance.  This module owns only bounded loopback transport to a Hermes
OpenAI-compatible API and returns the existing ``ReasoningResponse`` envelope.
It never selects a resident, widens authority, executes actions, or writes
canonical River state.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request as HttpRequest
from urllib.request import urlopen
from uuid import uuid4

from .contracts import ReasoningRequest, ReasoningResponse

DEFAULT_ENDPOINT = "http://127.0.0.1:8642/v1"
DEFAULT_TIMEOUT_SECONDS = 30.0
CODEX_SEATS = {"C1", "C2", "C3"}
MAX_TIMEOUT_SECONDS = 120.0
CAMPAIGN_TIMEOUT_SECONDS = 1800.0
MAX_RESPONSE_BYTES = 128_000
MAX_RESPONSE_CHARS = 12_000


class HermesProviderError(RuntimeError):
    """Base error for truthful, secret-safe Hermes transport failures."""


class HermesAuthenticationError(HermesProviderError):
    """Hermes rejected the supplied authentication."""


class HermesTimeoutError(HermesProviderError, TimeoutError):
    """Hermes did not answer inside the bounded execution window."""


class HermesUnavailableError(HermesProviderError):
    """Hermes could not be reached or returned a transient service error."""


class HermesMalformedResponseError(HermesProviderError):
    """Hermes returned a response outside the bounded protocol shape."""


class HermesPolicyViolationError(HermesProviderError):
    """The request or advisory attempted to cross Riverview's boundary."""


def _validate_loopback(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Hermes endpoint must be an unauthenticated loopback HTTP URL")


def _api_key_from_environment() -> str | None:
    return os.environ.get("HERMES_API_SERVER_KEY") or os.environ.get("API_SERVER_KEY")


class HermesReasoningProvider:
    """Adapt one already-authorized Hermes target to Riverview's provider contract."""

    def __init__(
        self,
        *,
        endpoint: str = DEFAULT_ENDPOINT,
        provider_id: str = "hermes:default",
        resource_class_ref: str = "hermes:local",
        model_ref: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        execution_class: str = "bounded-advisory",
        max_response_chars: int = MAX_RESPONSE_CHARS,
        opener: Callable[..., Any] = urlopen,
        codex_seat_id: str | None = None,
    ) -> None:
        _validate_loopback(endpoint)
        if execution_class not in {"bounded-advisory", "campaign-engineering"}:
            raise ValueError("execution class is unsupported")
        timeout_limit = CAMPAIGN_TIMEOUT_SECONDS if execution_class == "campaign-engineering" else MAX_TIMEOUT_SECONDS
        if not 0.1 <= timeout_seconds <= timeout_limit:
            raise ValueError("timeout is outside its bound")
        if not isinstance(provider_id, str) or not provider_id.startswith("hermes:"):
            raise ValueError("provider_id must identify a Hermes provider")
        if not isinstance(resource_class_ref, str) or not resource_class_ref.strip():
            raise ValueError("resource_class_ref is required")
        if model_ref is not None and (not isinstance(model_ref, str) or not model_ref.strip()):
            raise ValueError("model_ref is invalid")
        if not 256 <= max_response_chars <= MAX_RESPONSE_CHARS:
            raise ValueError("response bound is outside its bound")
        self.endpoint = endpoint.rstrip("/")
        self.provider_id = provider_id
        self.resource_class_ref = resource_class_ref.strip()
        self.model_ref = model_ref.strip() if model_ref else None
        self.timeout_seconds = float(timeout_seconds)
        self.execution_class = execution_class
        self.max_response_chars = max_response_chars
        self._api_key = api_key if api_key is not None else _api_key_from_environment()
        self._opener = opener
        if codex_seat_id is not None and codex_seat_id not in CODEX_SEATS:
            raise ValueError("codex_seat_id must be C1, C2, or C3")
        self.codex_seat_id = codex_seat_id

    def resource_metadata(self) -> dict[str, str | None]:
        """Return dynamic provider/resource identity for registry binding."""
        return {
            "provider_id": self.provider_id,
            "provider_type": "hermes",
            "resource_class_ref": self.resource_class_ref,
            "model_ref": self.model_ref,
            "classification": "provider-declared",
            "execution_class": self.execution_class,
        }

    def for_seat(self, codex_seat_id: str) -> "HermesReasoningProvider":
        """Return an equivalent provider bound to the admitted Codex seat."""
        return HermesReasoningProvider(
            endpoint=self.endpoint, provider_id=self.provider_id,
            resource_class_ref=self.resource_class_ref, model_ref=self.model_ref,
            api_key=self._api_key, timeout_seconds=self.timeout_seconds,
            execution_class=self.execution_class, max_response_chars=self.max_response_chars,
            opener=self._opener, codex_seat_id=codex_seat_id,
        )

    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        """Perform one bounded advisory generation with no action tools."""
        if not isinstance(request, ReasoningRequest):
            raise TypeError("Hermes provider requires a Riverview ReasoningRequest")
        if request.expires_at <= datetime.now(UTC):
            raise HermesPolicyViolationError("Hermes request is expired")
        allowed_returns = {"return:advisory", "return:diagnostic"}
        if not request.allowed_authority or any(
            authority not in allowed_returns for authority in request.allowed_authority
        ):
            raise HermesPolicyViolationError("Hermes request authority exceeds advisory scope")
        body: dict[str, Any] = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Riverview is authoritative. Return advisory reasoning only. "
                        "Do not change resident identity, grant authority, execute actions, "
                        "or treat model prose as canonical state."
                    ),
                },
                {"role": "user", "content": request.instruction},
            ],
            "stream": False,
        }
        if self.model_ref:
            body["model"] = self.model_ref
        if self.codex_seat_id:
            body["model_options"] = {"codex_seat_id": self.codex_seat_id}
        if request.response_format is not None:
            body["response_format"] = request.response_format
        payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            with self._opener(
                HttpRequest(
                    self.endpoint + "/chat/completions",
                    data=payload,
                    headers=headers,
                    method="POST",
                ),
                timeout=self.timeout_seconds,
            ) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            if exc.code in {401, 403}:
                raise HermesAuthenticationError("Hermes authentication was rejected") from exc
            if exc.code in {408, 504}:
                raise HermesTimeoutError("Hermes request timed out") from exc
            raise HermesUnavailableError("Hermes request failed with an HTTP error") from exc
        except TimeoutError as exc:
            raise HermesTimeoutError("Hermes request timed out") from exc
        except (OSError, URLError) as exc:
            raise HermesUnavailableError("Hermes provider is unavailable") from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise HermesMalformedResponseError("Hermes response exceeds the byte bound")
        try:
            data = json.loads(raw.decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            returned_model = data.get("model")
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise HermesMalformedResponseError("Hermes returned a malformed chat completion") from exc
        if not isinstance(content, str) or not content.strip() or len(content) > self.max_response_chars:
            raise HermesMalformedResponseError("Hermes returned content outside the response bound")
        try:
            structured_content = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            structured_content = None
        if isinstance(structured_content, dict):
            forbidden_keys = {
                "resident_id", "occupant_id", "office_id", "implementation_id",
                "canonical_identity", "canonical_state", "acceptance",
            }
            if forbidden_keys.intersection(structured_content):
                raise HermesPolicyViolationError("Hermes advisory attempted an identity override")
            authority_scope = structured_content.get("authority_scope")
            if isinstance(authority_scope, list) and any(
                value not in {"return:advisory", "return:diagnostic"}
                for value in authority_scope
            ):
                raise HermesPolicyViolationError("Hermes advisory attempted an authority override")
        semantic_outcome = structured_content.get("semantic_outcome") if isinstance(structured_content, dict) else None
        model_label = returned_model.strip() if isinstance(returned_model, str) and returned_model.strip() else self.model_ref or "configured"
        response_id = uuid4()
        evidence = (
            f"hermes:request:{request.request_id}",
            f"hermes:response:{response_id}",
            f"hermes:provider:{self.provider_id}",
            f"hermes:model:{model_label}",
            f"hermes:resource:{self.resource_class_ref}",
        )
        return ReasoningResponse(
            response_id=response_id,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            provider_id=self.provider_id,
            response_type={
                "decision_proposal": "decision_proposal",
                "diagnostic": "diagnostic_recommendation",
            }.get(request.request_type, request.request_type),
            summary=content.strip(),
            evidence_refs=evidence,
            classification=request.classification,
            created_at=datetime.now(UTC),
            semantic_outcome=semantic_outcome,
        )


__all__ = [
    "HermesAuthenticationError",
    "HermesMalformedResponseError",
    "HermesPolicyViolationError",
    "HermesProviderError",
    "HermesReasoningProvider",
    "HermesTimeoutError",
    "HermesUnavailableError",
]
