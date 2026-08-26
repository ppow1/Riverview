from riverview.operator.hermes_projection import project_campaign_runner_record


def test_campaign_runner_snapshot_record_is_ui_ready_and_separates_acceptance():
    projected = project_campaign_runner_record({
        "work_order_id": "work-1",
        "objective_id": "objective-1",
        "stage_id": "stage-1",
        "role": "repair_writer",
        "status": "succeeded",
        "attempt_id": "attempt-2",
        "lease_generation": 3,
        "worker_instance_id": "worker-2",
        "seat_id": "codex.seat.C2",
        "runner_state": "revalidation_pending",
        "repair_generation": 1,
        "provider_id": "hermes:tranche2-live",
        "model_ref": "gpt-5.6-luna-900k",
        "resource_class_ref": "codex.seat.C2",
        "capacity": {"weekly_left": 82, "freshness": "current"},
        "candidate_identity": "sha256:candidate-v2",
        "validation_state": "pending",
        "attention_required": False,
        "acceptance_state": "awaiting_validation",
        "fencing_token": "must-not-project",
    })
    assert projected["package_id"] == "stage-1"
    assert projected["role"] == "repair_writer"
    assert projected["repair_generation"] == 1
    assert projected["candidate_technically_complete"] is True
    assert projected["institutionally_accepted"] is False
    assert projected["steward_attention_required"] is False
    assert projected["capacity"]["weekly_left"] == 82
    assert "fencing_token" not in projected
