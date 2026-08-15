from __future__ import annotations

from uuid import uuid4

import pytest

from riverview.classification import Classification
from riverview.operator.artifacts import intake_artifact
from riverview.operator.transcription import transcribe_fixture
from riverview.security.adult_local import route_adult_local


def test_transcription_and_artifact_preserve_correlation(tmp_path):
    correlation = uuid4()
    result = transcribe_fixture(b"RIFF-safe-fixture", correlation_id=correlation)
    assert result.correlation_id == correlation
    assert result.provider_id == "local:fixture-transcriber"
    assert result.audio_retention.startswith("discard")
    artifact = tmp_path / "safe.txt"
    artifact.write_text("safe artifact", encoding="utf-8")
    record = intake_artifact(artifact, correlation_id=correlation, classification="operational")
    assert artifact.exists()
    assert record.byte_size > 0
    assert record.classification == "operational"
    assert record.provenance["correlation_id"] == str(correlation)


def test_transcription_and_artifact_fail_closed():
    with pytest.raises(ValueError, match="RIV-UI-0010"):
        transcribe_fixture(b"", correlation_id=uuid4())
    with pytest.raises(ValueError, match="RIV-UI-0011"):
        intake_artifact(__file__, correlation_id=uuid4(), classification="credential")

def test_adult_local_is_fail_closed_and_synthetic_only():
    assert route_adult_local(Classification.ADULT_LOCAL,'local:llama',synthetic=True).allowed
    assert not route_adult_local(Classification.ADULT_LOCAL,'cloud:provider',synthetic=True).allowed
    assert not route_adult_local(Classification.ADULT_LOCAL,'local:llama',synthetic=False).allowed
