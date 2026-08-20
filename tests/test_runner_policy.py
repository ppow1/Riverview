"""Policy tests for the restricted local runner.

Version: 0.5.0
"""

from pathlib import Path

from riverview.runner import RestrictedRunner


def test_runner_repository_is_resolved(tmp_path: Path) -> None:
    runner = RestrictedRunner(tmp_path, "test")
    assert runner.repository == tmp_path.resolve()


def test_runner_preserves_specific_execution_checkpoint() -> None:
    assert RestrictedRunner._checkpoint_from_error(
        "RIV-EXE-0003: Codex CLI exceeded the bounded execution deadline."
    ) == "RIV-EXE-0003"
    assert RestrictedRunner._checkpoint_from_error("unclassified runner failure") == "RIV-RUN-0001"
