"""Pure contract tests for the bounded autonomous control plane."""

from pathlib import Path
from uuid import uuid4

import pytest

from riverview.autonomy.control import (
    CodexCliAdapter,
    ContinuousMomentumEngine,
    ExecutionEnvelope,
    RetryPolicy,
)


def envelope(**overrides: object) -> ExecutionEnvelope:
    values: dict[str, object] = {
        "execution_id": uuid4(),
        "correlation_id": uuid4(),
        "capability_name": "codex.engineering.v1",
        "repository_identity": "ppow1/Riverview",
        "repository_root": Path("A:/Riverview/repo"),
        "expected_base_sha": "a" * 40,
        "bounded_instruction": "Run the bounded acceptance fixture and report evidence.",
        "allowed_paths": ("tests/fixtures/autonomy",),
        "acceptance_criteria": ("fixture passes",),
        "evidence_requirements": ("test result",),
        "timeout_seconds": 60,
        "retry_key": f"test:{uuid4()}",
    }
    values.update(overrides)
    return ExecutionEnvelope(**values)


def test_envelope_rejects_absolute_allowed_path() -> None:
    with pytest.raises(ValueError, match="allowed paths"):
        envelope(allowed_paths=("A:/outside",))


def test_envelope_rejects_bad_base_sha() -> None:
    with pytest.raises(ValueError, match="base SHA"):
        envelope(expected_base_sha="not-a-sha")


def test_envelope_allows_only_the_two_governed_policies() -> None:
    assert envelope(write_policy="bounded_write").write_policy == "bounded_write"
    with pytest.raises(ValueError, match="unsupported"):
        envelope(write_policy="unrestricted").__post_init__()


def test_codex_adapter_selects_write_sandbox_only_for_bounded_write(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repository = tmp_path
    (repository / ".git").mkdir()
    commands: list[list[str]] = []

    class Completed:
        returncode = 0

        def communicate(self, timeout: int) -> tuple[str, str]:
            return "provider evidence", ""

    monkeypatch.setattr("riverview.autonomy.control.subprocess.check_output", lambda *args, **kwargs: "a" * 40)
    monkeypatch.setattr("riverview.autonomy.control.subprocess.Popen", lambda command, **kwargs: commands.append(command) or Completed())
    result = CodexCliAdapter(executable="codex-test").run(envelope(repository_root=repository, write_policy="bounded_write"))
    assert result.result_category == "succeeded"
    assert commands[0][commands[0].index("--sandbox") + 1] == "workspace-write"


def test_retry_policy_is_one_bounded_retry() -> None:
    assert RetryPolicy().decide("relay.noop", 1, failure_class="timeout")["retry"] is True
    assert RetryPolicy().decide("relay.noop", 2, failure_class="timeout")["retry"] is False


def test_capacity_freshness_bound_is_validated() -> None:
    from riverview.autonomy import CapabilityRegistry

    with pytest.raises(ValueError, match="freshness"):
        CapabilityRegistry().select("bounded-engineering", max_age_seconds=0)


def test_dispatch_rejects_protected_classification() -> None:
    from riverview.autonomy import CapabilityRegistry

    with pytest.raises(ValueError, match="protected"):
        CapabilityRegistry().dispatch("bounded-engineering", classification="undercurrent")


def test_continuous_frontier_is_bounded() -> None:
    with pytest.raises(ValueError, match="frontier limit"):
        ContinuousMomentumEngine().frontier(limit=65)
