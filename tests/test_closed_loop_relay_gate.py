from riverview.relay.store import RelayStore


def test_claim_sql_has_root_scoped_closed_loop_binding_gate():
    sql, params = RelayStore.closed_loop_claim_predicate()
    assert "autonomous_governance_bindings" in sql
    assert "root_task_id" in sql
    assert "correlation_id" in sql
    assert "objective_id" in sql
    assert "stage_id" in sql
    assert "work_order_id" in sql
    assert "EXECUTABLE" in sql
    assert params == ()
