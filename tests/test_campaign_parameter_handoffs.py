from __future__ import annotations

from uuid import uuid4

from riverview.campaign import WorkerSlot
from riverview.campaign.one_go import CampaignOneGoRunner
from riverview.relay.store import ClaimedWork
from test_hermes_campaign_executor import fenced


class CaptureLifecycle:
    def __init__(self):
        self.calls = []

    def record_validation(self, work: ClaimedWork, **kwargs):
        self.calls.append(("validation", kwargs))
        return "validation-id"

    def record_repair_completion(self, work: ClaimedWork, **kwargs):
        self.calls.append(("repair", kwargs))
        return "revalidation-id"


def runner(lifecycle):
    return CampaignOneGoRunner(
        workers=(WorkerSlot("w", "s", ("validator", "repair_writer"), uuid4()),),
        executors={"validator": lambda _work: {}, "repair_writer": lambda _work: {}},
        lifecycle=lifecycle,
    )


def test_validator_and_repair_parameters_cross_lifecycle_handoffs():
    lifecycle = CaptureLifecycle()
    instance = runner(lifecycle)
    from riverview.campaign.one_go import _claimed
    validator_work = _claimed(fenced(role="validator"))
    repair_work = _claimed(fenced(role="repair_writer"))
    instance._advance_completed("validator", validator_work, {
        "verdict": "FAIL", "basis_hash": "b", "result_version_hash": "c",
        "evidence_refs": ["e"], "findings_summary": "d", "defects": [],
        "implementation_ref": "candidate://c",
        "repair_parameters": {"hermes_request": {"request_id": "repair"}},
    })
    instance._advance_completed("repair_writer", repair_work, {
        "revalidation_parameters": {"hermes_request": {"request_id": "revalidation"}},
    })
    assert lifecycle.calls[0][1]["repair_parameters"] == {"hermes_request": {"request_id": "repair"}}
    assert lifecycle.calls[1][1]["revalidation_parameters"] == {"hermes_request": {"request_id": "revalidation"}}
