from __future__ import annotations

from uuid import uuid4

import pytest

from riverview.reasoning.occupational import (
    CapabilityResultStatus,
    ResidentCapabilityBroker,
    ResidentCapabilityDescriptor,
    ResidentCapabilityRequest,
    ResidentOfficeCapabilityPackage,
    ResidentOccupationalReasoner,
)


RESIDENT = uuid4()
OCCUPANT = RESIDENT
OFFICE = uuid4()
IMPLEMENTATION = uuid4()


def package(*capabilities: ResidentCapabilityDescriptor) -> ResidentOfficeCapabilityPackage:
    return ResidentOfficeCapabilityPackage(
        package_id="grace-operations-v1",
        package_version="1.0.0",
        resident_id=RESIDENT,
        occupant_id=OCCUPANT,
        office_id=OFFICE,
        implementation_id=IMPLEMENTATION,
        resident_name="Grace",
        title="Director of Operations",
        office_purpose="Coordinate bounded Riverview operations.",
        responsibilities=("observe current work", "advise on progression"),
        professional_domain_refs=("riverview://office/operations",),
        domain_knowledge_refs=("riverview://bounded-operational-context",),
        capabilities=capabilities,
        authority_boundaries=("read:bounded", "return:advisory"),
        procedure_refs=("cookbook://operations",),
        classification="operational",
        freshness_seconds=300,
        grounding_policy="institutional evidence outranks generic priors",
        privacy_policy="bounded operational metadata only",
        provenance_refs=("architecture://resident-office-capability",),
    )


def test_package_catalog_contains_only_bounded_named_capabilities():
    descriptor = ResidentCapabilityDescriptor(
        capability_id="operations.current-work.read",
        capability_version="1.0.0",
        name="Current work",
        purpose="Read bounded active, ready, blocked, and recent work state.",
        authority_class="READ",
        input_schema={"type": "object", "properties": {"limit": {"type": "integer"}}},
        result_schema={"type": "object"},
        handler=lambda request: {"items": []},
        classification="operational",
        freshness_seconds=60,
        timeout_seconds=5,
        max_result_bytes=8_000,
        evidence_requirements=("authoritative-state",),
    )
    catalog = package(descriptor).catalog()
    assert catalog == [{
        "capability_id": "operations.current-work.read",
        "capability_version": "1.0.0",
        "name": "Current work",
        "purpose": "Read bounded active, ready, blocked, and recent work state.",
        "authority_class": "READ",
        "input_schema": {"type": "object", "properties": {"limit": {"type": "integer"}}},
        "result_type": "object",
        "classification": "operational",
        "freshness_seconds": 60,
        "timeout_seconds": 5,
    }]


def test_broker_executes_authorized_capability_and_attaches_provenance():
    descriptor = ResidentCapabilityDescriptor(
        capability_id="operations.current-work.read",
        capability_version="1.0.0",
        name="Current work",
        purpose="Read current work.",
        authority_class="READ",
        input_schema={"type": "object"},
        result_schema={"type": "object"},
        handler=lambda request: {"items": [{"state": "active"}]},
        classification="operational",
        freshness_seconds=60,
        timeout_seconds=5,
        max_result_bytes=8_000,
        evidence_requirements=("authoritative-state",),
    )
    request = ResidentCapabilityRequest(
        request_id=uuid4(),
        correlation_id=uuid4(),
        resident_id=RESIDENT,
        occupant_id=OCCUPANT,
        office_id=OFFICE,
        implementation_id=IMPLEMENTATION,
        package_id="grace-operations-v1",
        package_version="1.0.0",
        capability_id="operations.current-work.read",
        arguments={},
        classification="operational",
        authority="read:bounded",
        call_index=1,
        call_budget=2,
    )
    result = ResidentCapabilityBroker(package(descriptor)).execute(request)
    assert result.status is CapabilityResultStatus.SUCCESS
    assert result.value == {"items": [{"state": "active"}]}
    assert result.capability_id == request.capability_id
    assert result.evidence_refs == ("authoritative-state",)


def test_broker_denies_capability_not_in_package_without_substitution():
    request = ResidentCapabilityRequest(
        request_id=uuid4(), correlation_id=uuid4(), resident_id=RESIDENT,
        occupant_id=OCCUPANT, office_id=OFFICE, implementation_id=IMPLEMENTATION,
        package_id="grace-operations-v1", package_version="1.0.0",
        capability_id="character.canon.read", arguments={}, classification="operational",
        authority="read:bounded", call_index=1, call_budget=2,
    )
    result = ResidentCapabilityBroker(package()).execute(request)
    assert result.status is CapabilityResultStatus.DENIED
    assert result.capability_id == request.capability_id
    assert "not allowlisted" in (result.reason or "")


def test_broker_rejects_call_budget_exhaustion():
    descriptor = ResidentCapabilityDescriptor(
        capability_id="operations.current-work.read", capability_version="1.0.0",
        name="Current work", purpose="Read current work.", authority_class="READ",
        input_schema={"type": "object"}, result_schema={"type": "object"},
        handler=lambda request: {}, classification="operational", freshness_seconds=60,
        timeout_seconds=5, max_result_bytes=8_000, evidence_requirements=("state",),
    )
    request = ResidentCapabilityRequest(
        request_id=uuid4(), correlation_id=uuid4(), resident_id=RESIDENT,
        occupant_id=OCCUPANT, office_id=OFFICE, implementation_id=IMPLEMENTATION,
        package_id="grace-operations-v1", package_version="1.0.0",
        capability_id=descriptor.capability_id, arguments={}, classification="operational",
        authority="read:bounded", call_index=3, call_budget=2,
    )
    result = ResidentCapabilityBroker(package(descriptor)).execute(request)
    assert result.status is CapabilityResultStatus.DENIED
    assert "budget" in (result.reason or "")


def test_model_selects_capability_and_receives_result_on_second_pass():
    descriptor = ResidentCapabilityDescriptor(
        capability_id="operations.current-work.read", capability_version="1.0.0",
        name="Current work", purpose="Read current work.", authority_class="READ",
        input_schema={"type": "object"}, result_schema={"type": "object"},
        handler=lambda request: {"items": [{"title": "Alpha", "state": "active"}], "evidence_refs": ["work://alpha"]},
        classification="operational", freshness_seconds=60, timeout_seconds=5,
        max_result_bytes=8_000, evidence_requirements=("work://authoritative",),
    )
    pkg = package(descriptor)
    phases = []

    def model(payload):
        phases.append(payload["phase"])
        if payload["phase"] == "first":
            return {"decision": "capability", "capability_id": descriptor.capability_id, "arguments": {}}
        assert payload["tool_result"]["status"] == "SUCCESS"
        assert payload["tool_result"]["value"]["items"][0]["state"] == "active"
        return {"decision": "answer", "answer": "Alpha is active."}

    run = ResidentOccupationalReasoner(pkg, model).run("What is currently moving?", correlation_id=uuid4())
    assert phases == ["first", "second"]
    assert run.tool_result is not None
    assert run.tool_result.status is CapabilityResultStatus.SUCCESS
    assert run.final_answer == "Alpha is active."


def test_model_can_answer_without_selecting_a_tool():
    pkg = package()
    phases = []

    def model(payload):
        phases.append(payload["phase"])
        return {"decision": "answer", "answer": "Good evening, Steward."}

    run = ResidentOccupationalReasoner(pkg, model).run("Good evening, Grace.", correlation_id=uuid4())
    assert phases == ["first"]
    assert run.tool_result is None
    assert run.final_answer == "Good evening, Steward."


def test_unsupported_institutional_assertion_is_repaired_through_model_capability_selection():
    descriptor = ResidentCapabilityDescriptor(
        capability_id="operations.current-work.read", capability_version="1.0.0",
        name="Current work", purpose="Read current work.", authority_class="READ",
        input_schema={"type": "object"}, result_schema={"type": "object"},
        handler=lambda request: {"items": [{"title": "Accepted work", "state": "result_available"}], "evidence_refs": ["work://authoritative"]},
        classification="operational", freshness_seconds=60, timeout_seconds=5,
        max_result_bytes=8_000, evidence_requirements=("work://authoritative",),
    )
    phases = []

    def model(payload):
        phases.append(payload["phase"])
        if payload["phase"] == "first":
            return {"decision": "answer", "answer": "The work is completed and accepted.", "claims": [{"kind": "lifecycle", "value": "accepted"}]}
        if payload["phase"] == "repair":
            return {"decision": "capability", "capability_id": descriptor.capability_id, "arguments": {}}
        return {"decision": "answer", "answer": "The authoritative record shows work is available for review, not accepted."}

    run = ResidentOccupationalReasoner(package(descriptor), model).run("Is the work accepted?", correlation_id=uuid4())
    assert phases == ["first", "repair", "second"]
    assert run.tool_result is not None
    assert run.final_answer.startswith("The authoritative record")
