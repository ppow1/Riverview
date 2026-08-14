"""Deterministic RV-008.3 preparation tests; no live browser is used.

Version: 0.1.0
"""

from riverview.doorbell.contract import LocalAcceptanceDoorbell, acceptance_request


def test_doorbell_harness_preserves_correlation_without_live_acceptance() -> None:
    request = acceptance_request()
    result = LocalAcceptanceDoorbell().ring(request)
    assert result.state == "prepared"
    assert result.request_id == request.request_id
    assert result.correlation_id == request.correlation_id
    assert result.evidence_ref == "acceptance://doorbell/prepared-only"


def test_doorbell_harness_models_bounded_timeout() -> None:
    request = acceptance_request()
    result = LocalAcceptanceDoorbell(induced_failure=True).ring(request)
    assert result.state == "failed"
    assert result.failure_class == "bounded-timeout"
