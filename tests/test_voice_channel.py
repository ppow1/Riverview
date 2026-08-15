from __future__ import annotations

from uuid import uuid4

import pytest

from riverview.operator.voice import AuthenticatedVoiceChannel


def test_authenticated_loopback_voice_preserves_lineage() -> None:
    channel = AuthenticatedVoiceChannel(expected_bearer="local-test-bearer-1234")
    correlation = uuid4()
    response = channel.request(
        bearer="local-test-bearer-1234",
        correlation_id=correlation,
        classification="operational",
        text="bounded voice request",
    )
    assert response.correlation_id == correlation
    assert response.provider_id == "local:fixture-voice"


def test_voice_channel_rejects_ambient_or_unauthenticated_access() -> None:
    channel = AuthenticatedVoiceChannel(expected_bearer="local-test-bearer-1234")
    with pytest.raises(PermissionError, match="unauthenticated"):
        channel.request(
            bearer="wrong",
            correlation_id=uuid4(),
            classification="operational",
            text="should fail",
        )
    with pytest.raises(PermissionError, match="classification"):
        channel.request(
            bearer="local-test-bearer-1234",
            correlation_id=uuid4(),
            classification="credential",
            text="should fail",
        )
