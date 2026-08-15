"""Authenticated bounded voice/remote request contract.

This module models the local acceptance boundary only. It deliberately does not
open a microphone, execute commands, or persist bearer material.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VoiceResponse:
    correlation_id: UUID
    classification: str
    provider_id: str
    summary: str


class AuthenticatedVoiceChannel:
    """A loopback-safe channel with explicit session and bearer boundaries."""

    def __init__(self, *, expected_bearer: str, provider_id: str = "local:fixture-voice") -> None:
        if not expected_bearer or len(expected_bearer) < 16:
            raise ValueError("RIV-UI-0012: voice channel bearer is outside the bounded policy.")
        if not provider_id.startswith("local:"):
            raise ValueError("RIV-UI-0012: remote voice provider must be local for this acceptance.")
        self._expected_bearer = expected_bearer
        self._provider_id = provider_id

    def request(
        self,
        *,
        bearer: str,
        correlation_id: UUID,
        classification: str,
        text: str,
    ) -> VoiceResponse:
        if bearer != self._expected_bearer:
            raise PermissionError("RIV-UI-0012: unauthenticated voice request rejected.")
        if classification not in {"public", "operational", "private", "sensitive"}:
            raise PermissionError("RIV-UI-0012: voice classification is denied.")
        if not text.strip() or len(text) > 4000:
            raise ValueError("RIV-UI-0012: bounded voice request rejected.")
        return VoiceResponse(correlation_id, classification, self._provider_id, text.strip())
