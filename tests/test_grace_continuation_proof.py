from unittest.mock import Mock

from riverview.autonomy.control import ContinuousMomentumEngine


def test_provider_return_can_drive_multiple_ready_cycles_without_recursion() -> None:
    engine = ContinuousMomentumEngine()
    first = [{"objective_key": "one", "stage_key": "build"}]
    second = [{"objective_key": "one", "stage_key": "verify"}]
    engine.frontier = Mock(side_effect=[first, second, second, [], []])  # type: ignore[method-assign]
    engine.cycle = Mock(side_effect=[
        {"evaluated": [{"objective_key": "one", "stage_key": "build", "decision": "ready"}]},
        {"evaluated": [{"objective_key": "one", "stage_key": "verify", "decision": "ready"}]},
    ])  # type: ignore[method-assign]
    redispatch = Mock()

    result = engine.cycle_until_quiescent(redispatch=redispatch)

    assert result["cycle_count"] == 2
    assert result["redispatched"] == 2
    assert result["remaining_frontier"] == []
    assert result["stop_reason"] == "frontier_empty"
    assert redispatch.call_count == 2


def test_continuation_stops_at_no_progress_boundary() -> None:
    engine = ContinuousMomentumEngine()
    frontier = [{"objective_key": "one", "stage_key": "needs-approval"}]
    engine.frontier = Mock(side_effect=[frontier, frontier, frontier])  # type: ignore[method-assign]
    engine.cycle = Mock(return_value={"evaluated": [{"objective_key": "one", "stage_key": "needs-approval", "decision": "blocked"}]})  # type: ignore[method-assign]

    result = engine.cycle_until_quiescent()

    assert result["cycle_count"] == 1
    assert result["redispatched"] == 0
    assert result["stop_reason"] == "no_progress_or_external_boundary"


def test_continuation_cycle_bound_is_validated() -> None:
    try:
        ContinuousMomentumEngine().cycle_until_quiescent(max_cycles=0)
    except ValueError as exc:
        assert "cycle bound" in str(exc)
    else:
        raise AssertionError("invalid cycle bound was accepted")
