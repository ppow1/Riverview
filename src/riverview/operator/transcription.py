"""Bounded local transcription fixture/provider contract."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    correlation_id: UUID
    provider_id: str
    text: str
    classification: str
    audio_retention: str = "discard-after-transcription"

def transcribe_fixture(audio: bytes, *, correlation_id: UUID, classification: str = "operational") -> TranscriptionResult:
    if not audio or len(audio) > 1_000_000:
        raise ValueError("RIV-UI-0010: bounded audio input rejected.")
    return TranscriptionResult(
        correlation_id,
        "local:fixture-transcriber",
        "bounded local transcription",
        classification,
    )
