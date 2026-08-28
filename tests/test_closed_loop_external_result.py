from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
import pytest
from riverview.closed_loop.tracer import TracerStore


def test_external_campaign_result_is_root_scoped_and_correspondence_checked():
    with TemporaryDirectory() as directory:
        store = TracerStore.memory(artifact_root=Path(directory))
        request = store.dispatch("governed result")
        result = store.record_external_result({"root_task_id": request["root_task_id"], "correlation_id": request["correlation_id"], "request_id": request["request_id"], "run_id": str(uuid4()), "work_order_id": str(uuid4()), "attempt_id": str(uuid4()), "semantic_outcome": "RESULT_AVAILABLE", "summary": "bounded governed result", "evidence": ["campaign-runner"], "adapter_id": "hermes.campaign_runner.v1"})
        assert result["root_task_id"] == request["root_task_id"]
        assert store.read_projection(request["root_task_id"])["summary"] == "bounded governed result"
        with pytest.raises(ValueError, match="correspondence"):
            store.record_external_result({**result, "root_task_id": str(uuid4()), "result_id": str(uuid4())})
