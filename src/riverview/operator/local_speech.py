"""Bounded Windows local microphone transcription adapter."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LocalSpeechResult:
    provider_id: str
    text: str
    retention: str
    duration_seconds: int
    culture: str = "en-US"
    confidence: float | None = None


def capture_windows_speech(*, duration_seconds: int = 8) -> LocalSpeechResult:
    if not 1 <= duration_seconds <= 15:
        raise ValueError("RIV-UI-0015: microphone capture duration is outside the bound.")
    script = Path(__file__).parents[3] / "tools" / "powershell" / "operator" / "Invoke-RiverviewLocalTranscription.ps1"
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(script), "-DurationSeconds", str(duration_seconds), "-Culture", "en-US"],
            capture_output=True,
            text=True,
            timeout=duration_seconds + 10,
            check=True,
        )
        payload = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise RuntimeError("RIV-UI-0015: bounded Windows local transcription failed.") from exc
    if not isinstance(payload, dict) or not payload.get("text"):
        raise RuntimeError("RIV-UI-0015: local transcription returned no text.")
    return LocalSpeechResult(
        str(payload["provider_id"]), str(payload["text"]), str(payload["retention"]), int(payload["duration_seconds"]), str(payload.get("culture", "en-US")), float(payload["confidence"]) if payload.get("confidence") is not None else None
    )
