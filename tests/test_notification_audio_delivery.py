from uuid import uuid4

from riverview.notifications import NotificationStore
from riverview.notifications_audio import deliver_steward_notification


class FakePresenter:
    def __init__(self):
        self.calls = []

    def ding(self):
        self.calls.append("ding")
        return {"api": "fake-ding"}

    def speak(self, text):
        self.calls.append(("speak", text))
        return {"api": "fake-speech"}

    def announce(self, item):
        self.ding()
        self.speak(item["summary"])


def test_existing_estate_presenter_delivery_marks_notification_delivered():
    key = f"test:audio-delivery:{uuid4()}"
    notification_id = NotificationStore().emit(
        idempotency_key=key,
        notification_type="blocked_requires_steward",
        checkpoint_id="RIV-HERMES-TRANCHE2-BLOCKED-AUDIO-TEST",
        summary="Riverview Hermes needs your assistance.",
        evidence_refs=("test:audio-delivery",),
    )
    presenter = FakePresenter()
    result = deliver_steward_notification(notification_id, presenter=presenter)
    assert result["delivered"] is True
    assert presenter.calls == ["ding", ("speak", "Riverview Hermes needs your assistance.")]


def test_unavailable_annunciation_capability_leaves_notification_queued(monkeypatch):
    import riverview.notifications_audio as audio

    key = f"test:audio-capability:{uuid4()}"
    notification_id = NotificationStore().emit(
        idempotency_key=key,
        notification_type="blocked_requires_steward",
        checkpoint_id="RIV-HERMES-AUDIO-CAPABILITY",
        summary="Riverview Hermes needs your assistance.",
        evidence_refs=("test:audio-capability",),
    )
    monkeypatch.setattr(audio, "check_annunciation_capability", lambda: {"available": False, "reason": "test unavailable", "estate_process_required": False})
    presenter = FakePresenter()
    result = deliver_steward_notification(notification_id, presenter=presenter)
    assert result["delivered"] is False
    assert result["reason"] == "audio_delivery_unavailable"
    assert result["state"] == "queued"
    assert presenter.calls == []
