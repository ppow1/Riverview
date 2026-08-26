from riverview.operator.hermes_projection import project_hermes_execution


def test_projection_is_derived_secret_safe_and_keeps_acceptance_separate():
    projected = project_hermes_execution({
        "execution_id": "exec-1",
        "correlation_id": "corr-1",
        "resident_id": "resident-jessica",
        "office": "character-architecture",
        "campaign_package_id": "pkg-1",
        "attempt_id": "attempt-1",
        "hermes_profile": "seat-2",
        "worker_id": "worker-1",
        "provider_id": "hermes:codex",
        "model_ref": "codex-latest",
        "resource_class_ref": "resource:codex",
        "state": "completed",
        "spawned_workers": ["worker-2"],
        "evidence_refs": ["hermes:response:1"],
        "failure": None,
        "repair_state": "not_required",
        "canonical_reconciliation": "pending",
        "acceptance_state": "not_accepted",
        "api_key": "do-not-project",
        "metadata": {"authorization": "do-not-project"},
    })
    assert projected["execution_id"] == "exec-1"
    assert projected["provider"] == "hermes:codex"
    assert projected["model"] == "codex-latest"
    assert projected["acceptance_state"] == "not_accepted"
    assert projected["secrets_redacted"] is True
    assert projected["api_key"] == "[REDACTED]"
    assert projected["metadata"]["authorization"] == "[REDACTED]"
