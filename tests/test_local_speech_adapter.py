from __future__ import annotations

import json

import pytest

from riverview.operator import local_speech


def test_local_speech_adapter_uses_bounded_windows_provider(monkeypatch) -> None:
    class Completed:
        stdout = json.dumps({"provider_id": "windows:System.Speech", "text": "say hello", "retention": "discard-after-transcription", "duration_seconds": 8})

    monkeypatch.setattr(local_speech.subprocess, "run", lambda *args, **kwargs: Completed())
    result = local_speech.capture_windows_speech()
    assert result.provider_id == "windows:System.Speech"
    assert result.text == "say hello"
    assert result.retention.startswith("discard")


def test_local_speech_duration_is_bounded() -> None:
    with pytest.raises(ValueError, match="duration"):
        local_speech.capture_windows_speech(duration_seconds=30)
