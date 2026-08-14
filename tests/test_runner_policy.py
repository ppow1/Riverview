"""Policy tests for the restricted local runner.

Version: 0.5.0
"""

from pathlib import Path

from riverview.runner import RestrictedRunner


def test_runner_repository_is_resolved(tmp_path: Path) -> None:
    runner = RestrictedRunner(tmp_path, "test")
    assert runner.repository == tmp_path.resolve()