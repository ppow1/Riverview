from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from riverview.closed_loop.tracer import TracerStore, run_tracer


def test_tracer_carries_one_root_task_from_queue_to_grace_projection():
    with TemporaryDirectory() as temporary:
        store = TracerStore.memory(artifact_root=Path(temporary))
        result = run_tracer(store, objective="Verify bounded local transport")

        assert result["state"] == "consumed"
        assert result["root_task_id"]
        assert result["request_id"]
        assert result["result_id"]
        assert result["projection"]["root_task_id"] == result["root_task_id"]
        assert result["projection"]["result_id"] == result["result_id"]
        assert result["projection"]["summary"] == "Bounded Hermes tracer completed."
        assert result["events"] == [
            "root_task.created",
            "roadmap.created",
            "request.formed",
            "request.queued",
            "hermes.claimed",
            "hermes.started",
            "hermes.result.persisted",
            "grace.result.available",
            "grace.result.consumed",
        ]


def test_tracer_claim_is_idempotent_and_duplicate_safe():
    with TemporaryDirectory() as temporary:
        store = TracerStore.memory(artifact_root=Path(temporary))
        first = run_tracer(store, objective="Idempotency proof")
        second = store.claim(first["request_id"], owner="hermes-tracer")

        assert second["run_id"] == first["run_id"]
        assert second["request_id"] == first["request_id"]
        assert len(store.events_for(first["root_task_id"])) == 9


def test_artifacts_are_atomic_and_digest_bound():
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        store = TracerStore.memory(artifact_root=root)
        result = run_tracer(store, objective="Artifact proof")
        request = Path(result["artifacts"]["request"])
        outcome = Path(result["artifacts"]["result"])

        assert request.exists() and outcome.exists()
        assert request.with_suffix(request.suffix + ".tmp").exists() is False
        assert result["request_digest"]
        assert result["result_digest"]


def test_same_root_continuation_creates_one_second_request_and_result():
    with TemporaryDirectory() as temporary:
        store = TracerStore.memory(artifact_root=Path(temporary))
        first = run_tracer(store, objective="Continuation proof")
        second = store.continue_from_result(first["root_task_id"], first["result_id"], objective="Continue the bounded tracer")

        assert second["root_task_id"] == first["root_task_id"]
        assert second["correlation_id"] == first["correlation_id"]
        assert second["request_id"] != first["request_id"]
        assert second["result_id"] != first["result_id"]
        assert second["projection"]["result_id"] == second["result_id"]
        assert [x["event_type"] for x in store.events_for(first["root_task_id"])] == [
            "root_task.created", "roadmap.created", "request.formed", "request.queued",
            "hermes.claimed", "hermes.started", "hermes.result.persisted",
            "grace.result.available", "grace.result.consumed", "continuation.requested",
            "request.formed", "request.queued", "hermes.claimed", "hermes.started",
            "hermes.result.persisted", "grace.result.available", "grace.result.consumed",
        ]
