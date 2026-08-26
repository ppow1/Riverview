from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from riverview.campaign.one_go import _claimed
from riverview.campaign.hermes_executor import HermesCampaignExecutionError, HermesCampaignRoleExecutor
from riverview.relay import AttemptIdentity
from riverview.relay.store import FencedClaimedWork
from riverview.reasoning.contracts import ReasoningResponse



class FakeHermes:
    provider_id = "hermes:test"
    resource_class_ref = "hermes:local-test"

    def __init__(self, summary: str):
        self.summary = summary
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return ReasoningResponse(
            uuid4(), request.request_id, request.correlation_id, self.provider_id,
            "analysis", self.summary, ("hermes:test:evidence",), request.classification,
            datetime.now(UTC),
        )


def fenced(role="writer"):
    work_order_id = uuid4()
    return FencedClaimedWork(
        identity=AttemptIdentity(work_order_id, uuid4(), 1, uuid4(), uuid4()),
        action_type="engineering.inspect",
        action_version="v1",
        parameters={
            "hermes_request": {
                "request_id": str(uuid4()),
                "request_type": "analysis",
                "instruction": "Inspect one bounded repository seam.",
                "context_refs": ["river:bounded"],
                "classification": "operational",
                "required_output_schema": "campaign-hermes-v1",
                "evidence_requirements": ["provider-response"],
                "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
                "allowed_authority": ["return:advisory"],
            },
            "validator_action_type": "relay.noop",
        },
        hard_timeout_seconds=60,
        expected_duration_seconds=30,
        correlation_id=uuid4(),
        seat_id="resource:dynamic",
        role=role,
    )


def test_claimed_work_preserves_correlation_identity():
    source = fenced()
    claimed = _claimed(source)
    assert claimed.correlation_id == source.correlation_id


def test_campaign_executor_preserves_work_correlation_and_returns_evidence():
    hermes = FakeHermes('{"summary":"bounded inspection complete"}')
    work = _claimed(fenced())
    result = HermesCampaignRoleExecutor(hermes).execute(work)
    assert result["status"] == "succeeded"
    assert result["correlation_id"] == str(work.correlation_id)
    assert result["provider_id"] == "hermes:test"
    assert result["resource_class_ref"] == "hermes:local-test"
    assert result["evidence_refs"] == ["hermes:test:evidence"]
    assert hermes.requests[0].correlation_id == work.correlation_id


def test_campaign_validator_output_stays_a_validation_result_not_acceptance():
    hermes = FakeHermes(json.dumps({
        "verdict": "FAIL",
        "basis_hash": "sha256:basis",
        "result_version_hash": "sha256:candidate",
        "evidence_refs": ["hermes:validator:evidence"],
        "findings_summary": "One bounded defect.",
        "implementation_ref": "candidate://bounded",
        "defects": [],
    }))
    result = HermesCampaignRoleExecutor(hermes).execute(_claimed(fenced(role="validator")))
    assert result["status"] == "succeeded"
    assert result["verdict"] == "FAIL"
    assert "accepted" not in result
    assert result["provider_id"] == "hermes:test"


def test_campaign_validator_rejects_mismatched_canonical_basis_or_candidate():
    hermes = FakeHermes(json.dumps({
        "verdict": "PASS",
        "basis_hash": "sha256:wrong-basis",
        "result_version_hash": "sha256:wrong-candidate",
        "evidence_refs": ["hermes:validator:evidence"],
        "findings_summary": "Looks good.",
        "implementation_ref": "candidate://wrong",
        "defects": [],
    }))
    source = fenced(role="validator")
    source.parameters["validation_basis_hash"] = "sha256:basis"
    source.parameters["candidate_identity"] = "sha256:candidate"
    work = _claimed(source)
    with pytest.raises(HermesCampaignExecutionError, match="correspondence"):
        HermesCampaignRoleExecutor(hermes).execute(work)
