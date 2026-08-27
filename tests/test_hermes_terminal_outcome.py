from __future__ import annotations

import json
from uuid import UUID, uuid4

from riverview.hermes_attention import submit_hermes_attention
from riverview.hermes_terminal_outcome import (
    attention_speech,
    first_window_word,
    process_terminal_outcome,
)


class FakeStore:
    def __init__(self) -> None:
        self.rows: dict[str, UUID] = {}
        self.calls: list[dict[str, object]] = []

    def emit(self, **payload):
        self.calls.append(payload)
        return self.rows.setdefault(str(payload["idempotency_key"]), uuid4())


class QueuedDelivery:
    def __init__(self) -> None:
        self.queued: set[UUID] = set()
        self.presenter_calls: list[UUID] = []

    def __call__(self, notification_id: UUID) -> dict[str, object]:
        if notification_id not in self.queued:
            self.queued.add(notification_id)
            self.presenter_calls.append(notification_id)
            return {"delivered": True, "acknowledged": False, "state": "delivered"}
        return {"delivered": False, "reason": "notification_not_queued", "state": "delivered"}


def _submit(store, deliver, **overrides):
    values = {
        "lane": "Runtime repair",
        "boundary": "READY_FOR_STEWARD_REVIEW",
        "checkpoint_id": "RIV-HERMES-ATTN-TEST",
        "evidence_ref": "evidence://runtime-repair/1",
        "session_id": "hermes-session-1",
        "transition_id": "transition-1",
        "store": store,
        "deliver": deliver,
    }
    values.update(overrides)
    return submit_hermes_attention(**values)


def _marker(**values: object) -> str:
    return "<!-- RIVERVIEW_TERMINAL_OUTCOME " + json.dumps(values, sort_keys=True) + " -->"


def _attention_marker(outcome: str = "READY_FOR_STEWARD_REVIEW", **values: object) -> str:
    payload = {
        "outcome": outcome,
        "lane": "Runtime repair",
        "checkpoint_id": "RIV-HERMES-AUTO-TEST",
        "evidence_ref": "evidence://runtime-repair/auto",
        "terminal_transition_id": "auto-transition-1",
        "summary": "Bounded report is ready for Steward attention.",
    }
    payload.update(values)
    return _marker(**payload)


def test_ready_boundary_is_one_idempotent_delivery_and_not_acceptance():
    store = FakeStore()
    delivery = QueuedDelivery()

    first = _submit(store, delivery)
    second = _submit(store, delivery)

    assert first["notification_id"] == second["notification_id"]
    assert len(store.calls) == 2
    assert delivery.presenter_calls == [UUID(first["notification_id"])]
    assert first["notification_type"] == "ready_for_steward_review"
    assert first["acknowledged"] is False
    assert first["institutionally_accepted"] is False


def test_blocked_boundary_is_attributed_per_independent_lane():
    store = FakeStore()
    delivery = QueuedDelivery()

    first = _submit(
        store,
        delivery,
        lane="C1 C2 C3",
        boundary="BLOCKED_REQUIRES_STEWARD",
        checkpoint_id="RIV-HERMES-C123-BLOCKED",
        session_id="hermes-c123",
        transition_id="blocked-1",
    )
    second = _submit(
        store,
        delivery,
        lane="Operator",
        boundary="STEWARD_DECISION_REQUIRED",
        checkpoint_id="RIV-HERMES-OPERATOR-DECISION",
        session_id="hermes-operator",
        transition_id="decision-1",
    )

    assert first["notification_type"] == "blocked_requires_steward"
    assert second["notification_type"] == "blocked_requires_steward"
    assert first["lane"] == "C1 C2 C3"
    assert second["lane"] == "Operator"
    assert len(delivery.presenter_calls) == 2
    assert first["notification_id"] != second["notification_id"]


def test_non_terminal_or_retryable_work_does_not_enter_attention_boundary():
    store = FakeStore()
    delivery = QueuedDelivery()
    assert store.calls == []
    assert delivery.presenter_calls == []


def test_invalid_boundary_fails_closed():
    store = FakeStore()
    delivery = QueuedDelivery()

    try:
        _submit(store, delivery, boundary="TEST_PASS")
    except ValueError as exc:
        assert "attention boundary" in str(exc)
    else:
        raise AssertionError("non-terminal boundary was accepted")
    assert store.calls == []
    assert delivery.presenter_calls == []


def test_semantic_outcome_automatically_submits_without_notifier_tool_call():
    calls: list[dict[str, object]] = []

    def submit(**kwargs):
        calls.append(kwargs)
        return {"delivery": {"delivered": True, "state": "delivered"}}

    response = "Full technical report\n\n" + _attention_marker()
    cleaned = process_terminal_outcome(response, session_id="hermes-session-1", submit=submit)

    assert cleaned == "Full technical report"
    assert len(calls) == 1
    assert calls[0]["boundary"] == "READY_FOR_STEWARD_REVIEW"
    assert calls[0]["session_id"] == "hermes-session-1"
    assert calls[0]["transition_id"] == "auto-transition-1"


def test_all_attention_outcomes_are_automatically_routed():
    for outcome in (
        "READY_FOR_STEWARD_REVIEW",
        "BLOCKED_REQUIRES_STEWARD",
        "STEWARD_DECISION_REQUIRED",
    ):
        calls: list[dict[str, object]] = []
        response = _attention_marker(outcome, terminal_transition_id=f"transition-{outcome}")
        def submit_for_outcome(_calls=calls, **kwargs):
            _calls.append(kwargs)
            return {"delivery": {"state": "delivered"}}

        cleaned = process_terminal_outcome(
            response,
            session_id="session-1",
            submit=submit_for_outcome,
        )
        assert cleaned == ""
        assert len(calls) == 1
        assert calls[0]["boundary"] == outcome


def test_continue_completed_step_retryable_failure_and_ordinary_turn_stay_silent():
    calls: list[dict[str, object]] = []
    submit = lambda **kwargs: calls.append(kwargs) or {"delivery": {"state": "delivered"}}

    for outcome in ("CONTINUE", "COMPLETED_NO_ATTENTION"):
        assert process_terminal_outcome(_marker(outcome=outcome), session_id="session-1", submit=submit) == ""
    assert process_terminal_outcome("ordinary completed Hermes response", session_id="session-1", submit=submit) == "ordinary completed Hermes response"
    assert process_terminal_outcome("retryable failure; retrying", session_id="session-1", submit=submit) == "retryable failure; retrying"
    assert calls == []


def test_unknown_or_malformed_outcome_is_visible_and_does_not_notify():
    calls: list[dict[str, object]] = []
    submit = lambda **kwargs: calls.append(kwargs) or {"delivery": {"state": "delivered"}}

    unknown = process_terminal_outcome(
        _marker(outcome="SURPRISE"), session_id="session-1", submit=submit
    )
    malformed = process_terminal_outcome(
        "report <!-- RIVERVIEW_TERMINAL_OUTCOME {bad} -->",
        session_id="session-1",
        submit=submit,
    )
    assert "RIV-HERMES-OUTCOME-0005" in unknown
    assert "RIV-HERMES-OUTCOME-0003" in malformed
    assert calls == []


def test_duplicate_semantic_transition_reuses_existing_notification_and_presenter_once():
    store = FakeStore()
    delivery = QueuedDelivery()
    response = _attention_marker()
    submit = lambda **kwargs: _submit(store, delivery, **kwargs)

    first = process_terminal_outcome(response, session_id="hermes-session-1", submit=submit)
    second = process_terminal_outcome(response, session_id="hermes-session-1", submit=submit)

    assert first == second == ""
    assert len(store.calls) == 2
    assert len(delivery.presenter_calls) == 1


def test_notification_and_delivery_failures_are_visible():
    response = _attention_marker()
    persistence_failure = process_terminal_outcome(
        response,
        session_id="session-1",
        submit=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("database unavailable")),
    )
    delivery_failure = process_terminal_outcome(
        response,
        session_id="session-1",
        submit=lambda **kwargs: {"delivery": {"state": "failed", "error": "presenter unavailable"}},
    )
    assert "database unavailable" in persistence_failure
    assert "RIV-HERMES-OUTCOME-0008" in delivery_failure


def test_session_mismatch_fails_closed():
    response = _attention_marker(hermes_session_id="wrong-session")
    result = process_terminal_outcome(response, session_id="actual-session", submit=lambda **kwargs: {})
    assert "RIV-HERMES-OUTCOME-0006" in result


def test_project_plugin_transform_is_disabled_for_non_riverview_sessions(monkeypatch):
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parents[1] / ".hermes/plugins/riverview-steward-attention/__init__.py"
    spec = importlib.util.spec_from_file_location("riverview_project_plugin", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    monkeypatch.delenv("RIVERVIEW_HERMES_ENGINEERING", raising=False)
    response = _attention_marker()
    assert module._transform_riverview_outcome(response, session_id="session-1") == response


def test_first_window_word_uses_visible_title_and_skips_articles_and_punctuation():
    assert first_window_word("Audit C1 C2 C3 Codex fuel...") == "Audit"
    assert first_window_word("  ... Restore Grace reasoning...  ") == "Restore"
    assert first_window_word("\u2026Audit\tC1 fuel") == "Audit"
    assert first_window_word("The Reconcile and publish Steward notification") == "Reconcile"
    assert first_window_word("Document Riverview Operator...") == "Document"


def test_attention_speech_maps_each_terminal_state_to_short_window_identifier():
    assert attention_speech("READY_FOR_STEWARD_REVIEW", window_description="Audit C1") == "Audit needs your review."
    assert attention_speech("BLOCKED_REQUIRES_STEWARD", window_description="Restore Grace") == "Restore needs your assistance."
    assert attention_speech("STEWARD_DECISION_REQUIRED", window_description="Reconcile and publish") == "Reconcile needs your decision."


def test_window_identifier_fallback_rejects_uuid_sha_and_checkpoint():
    assert first_window_word(None, "Runtime repair") == "Runtime"
    assert first_window_word("550e8400-e29b-41d4-a716-446655440000", "Runtime repair") == "Runtime"
    assert first_window_word("deadbeefcafebabe", "Runtime repair") == "Runtime"
    assert first_window_word("RIV-HERMES-AUTO-ATTN", "Runtime repair") == "Runtime"
    assert first_window_word(None, None) == "Hermes"


def test_automatic_outcome_uses_window_description_for_persisted_speech_and_replay_is_silent():
    store = FakeStore()
    delivery = QueuedDelivery()
    response = _attention_marker(summary="ignored by the audible projection")
    submit = lambda **kwargs: _submit(store, delivery, **kwargs)

    first = process_terminal_outcome(
        response,
        session_id="hermes-session-1",
        window_description="Audit C1 C2 C3 Codex fuel...",
        submit=submit,
    )
    second = process_terminal_outcome(
        response,
        session_id="hermes-session-1",
        window_description="Audit C1 C2 C3 Codex fuel...",
        submit=submit,
    )

    assert first == second == ""
    assert len(delivery.presenter_calls) == 1
    assert store.calls[0]["summary"] == "Audit needs your review."
