from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic, sleep

import pytest

from riverview.closed_loop.tracer import TracerStore, run_tracer


def test_three_roots_are_isolated_and_unknown_claim_fails_closed():
    with TemporaryDirectory() as temporary:
        store = TracerStore.memory(artifact_root=Path(temporary))
        a = store.dispatch("Task A")
        b = store.dispatch("Task B")
        c = store.dispatch("Task C")

        assert len({a["root_task_id"], b["root_task_id"], c["root_task_id"]}) == 3
        assert len({a["correlation_id"], b["correlation_id"], c["correlation_id"]}) == 3
        with pytest.raises(LookupError, match="unknown request"):
            store.claim("not-a-real-request", owner="worker")

        release_c = Event()
        started = []
        completed = []

        class Executor:
            def execute(self, request, *, run_id):
                started.append(request["request_id"])
                if request["request_id"] == a["request_id"]:
                    sleep(0.08)
                    raise RuntimeError("bounded executor failure")
                if request["request_id"] == b["request_id"]:
                    sleep(0.01)
                    completed.append(request["request_id"])
                    return {"adapter_id": "test.executor", "run_id": run_id, "summary": "B succeeded", "evidence": ["B-evidence"], "semantic_outcome": "COMPLETED_NO_ATTENTION"}
                release_c.wait(2)
                return {"adapter_id": "test.executor", "run_id": run_id, "summary": "C succeeded", "evidence": ["C-evidence"], "semantic_outcome": "COMPLETED_NO_ATTENTION"}

        worker = store.worker(executor=Executor())
        futures = [worker.submit(item["request_id"]) for item in (a, b, c)]
        deadline = monotonic() + 2
        while len(started) < 3 and monotonic() < deadline:
            sleep(0.01)
        assert len(started) == 3
        assert futures[1].result()["request_id"] == b["request_id"]
        assert b["request_id"] in completed
        assert worker.read_state(a["root_task_id"])["state"] == "running"
        assert worker.read_projection(b["root_task_id"])["request_id"] == b["request_id"]
        assert worker.read_projection(a["root_task_id"])["result_id"] is None
        assert futures[0].result()["state"] == "failed"
        assert worker.read_state(a["root_task_id"])["state"] == "failed"
        assert worker.read_state(b["root_task_id"])["state"] == "completed"
        assert worker.read_state(c["root_task_id"])["state"] == "running"
        release_c.set()
        assert futures[2].result()["request_id"] == c["request_id"]
        continuation = worker.continue_from_result(b["root_task_id"], futures[1].result()["result_id"], objective="Continue B")
        assert continuation["root_task_id"] == b["root_task_id"]
        assert continuation["correlation_id"] == b["correlation_id"]
        assert continuation["request_id"] != b["request_id"]
        assert worker.read_projection(a["root_task_id"])["request_id"] is None
