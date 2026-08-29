from uuid import uuid4
from riverview.autonomy.runtime import CMEV1ContinuationPolicy


def test_cme_v1_requeues_continue_same_root_and_parks_external_outcomes():
    queued = []
    policy = CMEV1ContinuationPolicy(enqueue=queued.append, max_no_progress=2)
    root, correlation = str(uuid4()), str(uuid4())
    assert policy.observe({"root_task_id": root, "correlation_id": correlation, "request_id": str(uuid4()), "result_id": str(uuid4()), "semantic_outcome": "CONTINUE", "result_digest": "a"})["state"] == "CONTINUATION_QUEUED"
    assert queued[0]["root_task_id"] == root and queued[0]["correlation_id"] == correlation
    assert policy.observe({"root_task_id": root, "correlation_id": correlation, "request_id": str(uuid4()), "result_id": str(uuid4()), "semantic_outcome": "STEWARD_DECISION_REQUIRED", "result_digest": "b"})["state"] == "PARKED"


def test_cme_v1_anti_spin_is_root_scoped():
    queued = []
    policy = CMEV1ContinuationPolicy(enqueue=queued.append, max_no_progress=2)
    a, b = str(uuid4()), str(uuid4())
    event = lambda root: {"root_task_id": root, "correlation_id": str(uuid4()), "request_id": str(uuid4()), "result_id": str(uuid4()), "semantic_outcome": "CONTINUE", "result_digest": "same"}
    policy.observe(event(a)); policy.observe(event(a)); anomaly = policy.observe(event(a))
    assert anomaly["state"] == "MOMENTUM_ANOMALY"
    assert policy.observe(event(b))["state"] == "CONTINUATION_QUEUED"


def test_cme_does_not_advance_authority_from_objective_complete_report():
    queued = []
    policy = CMEV1ContinuationPolicy(enqueue=queued.append)
    result = policy.observe({
        "root_task_id": str(uuid4()), "correlation_id": str(uuid4()),
        "request_id": str(uuid4()), "result_id": str(uuid4()),
        "semantic_outcome": "OBJECTIVE_COMPLETE", "result_digest": "accepted-candidate",
    })
    assert result["state"] == "AWAITING_ACCEPTANCE"
    assert queued == []
