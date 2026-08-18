"""Pure contract tests for the CME liveness and external recovery boundary."""

from pathlib import Path

import pytest

from riverview.autonomy.supervisor import CMESupervisor


def test_supervisor_requires_a_stale_threshold_longer_than_heartbeat_freshness() -> None:
    with pytest.raises(ValueError, match="timing bounds"):
        CMESupervisor(stale_grace_seconds=5.0)


def test_supervisor_uses_the_persistent_runtime_entrypoint() -> None:
    supervisor = CMESupervisor(repository=Path("A:/Riverview/repo"))
    assert supervisor._command()[-2:] == ["-m", "riverview.autonomy.live_service"]


def test_supervisor_child_environment_points_at_current_source() -> None:
    supervisor = CMESupervisor(repository=Path("A:/Riverview/repo"))
    environment = supervisor._environment()
    assert environment["PYTHONPATH"].split(";")[0].endswith("Riverview\\repo\\src")
