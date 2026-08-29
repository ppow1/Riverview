from __future__ import annotations

from uuid import uuid4

from riverview.autonomy.runtime import CMEV1ContinuationPolicy
from riverview.hermes_terminal_outcome import process_terminal_outcome


def test_objective_complete_waits_for_cme_acceptance():
    queued = []
    policy = CMEV1ContinuationPolicy(enqueue=queued.append)
    result = policy.observe({
        "root_task_id": str(uuid4()), "correlation_id": str(uuid4()),
        "request_id": str(uuid4()), "result_id": str(uuid4()),
        "semantic_outcome": "OBJECTIVE_COMPLETE", "result_digest": "candidate",
    })
    assert result["state"] == "AWAITING_ACCEPTANCE"
    assert queued == []


def test_continue_queues_same_root_and_failure_does_not_complete():
    queued = []
    policy = CMEV1ContinuationPolicy(enqueue=queued.append)
    root = str(uuid4()); correlation = str(uuid4())
    result = policy.observe({"root_task_id": root, "correlation_id": correlation, "request_id": str(uuid4()), "result_id": str(uuid4()), "semantic_outcome": "CONTINUE", "result_digest": "step"})
    assert result["state"] == "CONTINUATION_QUEUED"
    assert queued[0]["root_task_id"] == root
    calls = []
    def submit(**kwargs):
        calls.append(kwargs)
        return {"delivery": {"state": "delivered"}}
    attention = '<!-- RIVERVIEW_TERMINAL_OUTCOME {"disposition":"READY_FOR_STEWARD_REVIEW","lane":"test","checkpoint_id":"RIV-HERMES-TEST","evidence_ref":"evidence://test","terminal_transition_id":"t1"} -->'
    assert process_terminal_outcome(attention, session_id="session", submit=submit) == ""
    failure = process_terminal_outcome('<!-- RIVERVIEW_TERMINAL_OUTCOME {"disposition":"TERMINAL_FAILURE"} -->', session_id="session", submit=submit)
    assert "TERMINAL_FAILURE" in failure
    assert len(calls) == 1
