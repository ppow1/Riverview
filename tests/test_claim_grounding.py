import json

from riverview.reasoning.claim_grounding import ground_claims


def material():
    return (json.dumps({"source_ref": "RV-014.1", "value": {"metadata": {"registry": [
        {"name": "Jessica", "resident_id": "j", "responsibility_domains": []},
        {"name": "Marie", "resident_id": "m", "responsibility_domains": ["research"]},
        {"name": "Grace", "resident_id": "g", "responsibility_domains": []},
    ], "capabilities": [{"capability": "codex.engineering.v1", "human_owner_known": False, "suitable_resident_ids": []}]}}}),)


def claim(subject_id, domain):
    return {"subject_type": "resident", "subject_id": subject_id, "domain": domain, "assertion_kind": "authoritative_contact", "evidence_refs": ["RV-014.1"]}


def test_unsupported_resident_claims_are_rejected_generically():
    result = ground_claims([claim("j", "mechanical_engineering"), claim("g", "research")], material())
    assert len(result.unsupported) == 2
    assert not result.supported


def test_supported_role_domain_claim_survives():
    result = ground_claims([claim("m", "research")], material())
    assert [item.subject_id for item in result.supported] == ["m"]


def test_unknown_engineering_owner_remains_unknown():
    result = ground_claims([{"subject_type": "capability", "subject_id": "codex.engineering.v1", "domain": "engineering", "assertion_kind": "suitable_for", "evidence_refs": ["RV-014.1"]}], material())
    assert [item.subject_id for item in result.supported] == ["codex.engineering.v1"]
    assert result.unsupported == ()
