from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

from riverview.reasoning.occupational import (
    CapabilityResultStatus,
    CapabilityStaleError,
    CapabilityUnavailableError,
    ResidentCapabilityBroker,
    ResidentCapabilityDescriptor,
    ResidentCapabilityRequest,
    ResidentOccupationalReasoner,
    ResidentOfficeCapabilityPackage,
)


def _package(handler: Callable[[ResidentCapabilityRequest], dict[str, Any]], model: str = "model-a") -> ResidentOfficeCapabilityPackage:
    resident = uuid4()
    descriptor = ResidentCapabilityDescriptor(
        capability_id="office.read", capability_version="1.0.0", name="Office read",
        purpose="Read bounded office state.", authority_class="READ", input_schema={"type": "object"},
        result_schema={"type": "object"}, handler=handler, classification="internal",
        freshness_seconds=60, timeout_seconds=5, max_result_bytes=8_000,
        evidence_requirements=("test://authoritative",),
    )
    return ResidentOfficeCapabilityPackage(
        package_id=f"package-{resident}", package_version="1.0.0", resident_id=resident,
        occupant_id=resident, office_id=uuid4(), implementation_id=uuid4(), resident_name="Resident",
        title="Test Office", office_purpose="Test", responsibilities=("read",),
        professional_domain_refs=("test://office",), domain_knowledge_refs=(f"test://{model}",),
        capabilities=(descriptor,), authority_boundaries=("read:bounded", "return:advisory"),
        procedure_refs=("test://procedure",), classification="internal", freshness_seconds=60,
        grounding_policy="authoritative", privacy_policy="bounded", provenance_refs=("test://package",),
    )


def _request(package: ResidentOfficeCapabilityPackage) -> ResidentCapabilityRequest:
    return ResidentCapabilityRequest(
        request_id=uuid4(), correlation_id=uuid4(), resident_id=package.resident_id,
        occupant_id=package.occupant_id, office_id=package.office_id, implementation_id=package.implementation_id,
        package_id=package.package_id, package_version=package.package_version, capability_id="office.read",
        arguments={}, classification="internal", authority="read:bounded", call_index=1, call_budget=2,
    )


def test_model_binding_does_not_define_package_or_identity():
    first = _package(lambda request: {"items": [{"ok": True}]}, "model-a")
    second = _package(lambda request: {"items": [{"ok": True}]}, "model-b")
    assert first.package_id != second.package_id
    assert first.title == second.title
    assert first.capabilities[0].capability_id == second.capabilities[0].capability_id
    assert ResidentCapabilityBroker(first).execute(_request(first)).status is CapabilityResultStatus.SUCCESS
    assert ResidentCapabilityBroker(second).execute(_request(second)).status is CapabilityResultStatus.SUCCESS


def test_empty_and_backend_failure_are_distinct():
    empty = _package(lambda request: {"items": []})
    failed = _package(lambda request: (_ for _ in ()).throw(RuntimeError("backend")))
    assert ResidentCapabilityBroker(empty).execute(_request(empty)).status is CapabilityResultStatus.EMPTY_AUTHORITATIVE_RESULT
    assert ResidentCapabilityBroker(failed).execute(_request(failed)).status is CapabilityResultStatus.BACKEND_FAILURE


def test_broker_exposes_unavailable_and_stale_without_substitution():
    unavailable = _package(lambda request: (_ for _ in ()).throw(CapabilityUnavailableError("provider offline")))
    stale = _package(lambda request: (_ for _ in ()).throw(CapabilityStaleError("observation expired")))
    assert ResidentCapabilityBroker(unavailable).execute(_request(unavailable)).status is CapabilityResultStatus.UNAVAILABLE
    assert ResidentCapabilityBroker(stale).execute(_request(stale)).status is CapabilityResultStatus.STALE


def test_typed_capability_request_wins_over_contradictory_prose_decision():
    package = _package(lambda request: {"items": [{"formed": True}]})
    calls = []

    def model(payload: dict[str, Any]) -> dict[str, Any]:
        calls.append(payload)
        if payload["phase"] == "first":
            return {"decision": "answer", "answer": "I will perform the bounded action.", "capability_id": "office.read", "arguments": {}}
        return {"decision": "answer", "answer": "The bounded action completed with authoritative evidence.", "capability_id": None, "arguments": {}}

    run = ResidentOccupationalReasoner(package, model).run("Proceed with the bounded action.", correlation_id=uuid4())
    assert run.tool_result is not None
    assert run.tool_result.status is CapabilityResultStatus.SUCCESS
    assert run.model_passes == 2
    assert len(calls) == 2


def test_engineering_prepare_catalog_exposes_authoritative_contract_shape():
    from riverview.residents.occupational_packages import build_grace_operations_package

    class Profile:
        resident_id = str(uuid4())
        name = "Grace"
        role = "Director of Operations"
        classification = "operational"

    package = build_grace_operations_package(Profile(), uuid4(), uuid4(), (Profile(),))
    descriptor = next(item for item in package.catalog() if item["capability_id"] == "operations.engineering-request.prepare")
    contract = descriptor["input_schema"]["properties"]["proposal"]["properties"]["formation_contract"]
    assert set(contract["required"]) == {"repository_identity", "repository_root", "expected_base_sha", "bounded_instruction", "allowed_paths", "acceptance_criteria", "evidence_requirements", "capability_name", "action_type", "timeout_seconds", "write_policy"}
