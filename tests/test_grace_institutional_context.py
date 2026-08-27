from riverview.reasoning.grace_state import PostgresAuthoritativeGraceStateSource


def test_institutional_projection_is_bounded_read_only_and_authoritative(monkeypatch):
    class Store:
        def accepted_operator_residents(self):
            return [{"name": "Grace", "role": "Director of Operations", "resident_id": "durable-grace"}]

        def health(self):
            return {"status": "healthy"}

    class CME:
        def read(self):
            return {"effective_state": "EVENT_OBSERVED", "heartbeat_health": "HEALTHY", "last_river_sequence_seen": 42}

    monkeypatch.setattr("riverview.reasoning.grace_state.CMEStatusStore", CME)
    projection = PostgresAuthoritativeGraceStateSource(Store())._add_institutional_projection({"state_records": []})
    item = projection["state_records"][0]
    material = item["bounded_metadata"]
    grace = next(row for row in material["registry"] if row["name"] == "Grace")
    assert grace == {"name": "Grace", "role": "Director of Operations", "resident_id": "durable-grace"}
    assert {row["name"] for row in material["registry"]} >= {"Alfred", "Grace", "Marie"}
    assert material["subsystems"][0]["meaning"] == "Continuous Momentum Engine"
    engineering = next(item for item in material["capabilities"] if item["capability"] == "codex.engineering.v1")
    assert engineering["mode"] == "advisory proposal only"
    assert engineering["execution"].startswith("requires separate Steward")
    assert engineering["human_owner_known"] is False
    assert engineering["suitable_resident_ids"] == []
    assert material["capability_assignment_policy"].startswith("Assign a resident only")
    assert material["authority_boundary"] == "Reading institutional context does not grant mutation or execution authority."


def test_grace_source_projection_keeps_institutional_state_in_context(monkeypatch):
    class Store:
        def accepted_operator_residents(self):
            return []

        def health(self):
            return {"status": "healthy"}

    class CME:
        def read(self):
            return {"effective_state": "EVENT_OBSERVED", "heartbeat_health": "HEALTHY"}

    monkeypatch.setattr("riverview.reasoning.grace_state.CMEStatusStore", CME)
    source = PostgresAuthoritativeGraceStateSource(Store())
    projection = source._add_institutional_projection({"state_records": []})
    assert projection["state_records"][0]["value_ref"] == "riverview:bounded-institutional-context:v1"
    assert projection["state_records"][0]["status"] == "active"
