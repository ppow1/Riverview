from __future__ import annotations

from pathlib import Path

import pytest

from riverview.autonomy.stale_base import RepositoryDriftAnalyzer

BASE = "a" * 40
HEAD = "b" * 40


def _analyzer(monkeypatch: pytest.MonkeyPatch, changed: str, descendant: bool = True) -> RepositoryDriftAnalyzer:
    analyzer = RepositoryDriftAnalyzer()
    monkeypatch.setattr(analyzer, "_git", lambda _repository, *_args: changed)
    monkeypatch.setattr(analyzer, "_is_ancestor", lambda _repository, _base, _head: descendant)
    return analyzer


def test_exact_base_match_is_safe_without_revalidation_review(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _analyzer(monkeypatch, "").assess(Path.cwd(), BASE, ("docs/engineering-pipeline-smoke-test.md",), proposed_base_sha=BASE)
    assert result.decision == "safe_revalidation"
    assert result.changed_paths == ()


def test_irrelevant_descendant_change_is_revalidatable(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _analyzer(monkeypatch, "docs/notes.md\n").assess(Path.cwd(), BASE, ("docs/engineering-pipeline-smoke-test.md",), proposed_base_sha=HEAD)
    assert result.decision == "safe_revalidation"
    assert result.safe_to_revalidate is True


def test_allowed_path_or_execution_dependency_is_material(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _analyzer(monkeypatch, "docs/engineering-pipeline-smoke-test.md\nsrc/riverview/runner.py\n").assess(Path.cwd(), BASE, ("docs/engineering-pipeline-smoke-test.md",), proposed_base_sha=HEAD)
    assert result.decision == "material_drift"
    assert set(result.material_paths) == {"docs/engineering-pipeline-smoke-test.md", "src/riverview/runner.py"}


def test_governance_change_requires_narrow_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _analyzer(monkeypatch, "src/riverview/intake/authority.py\n").assess(Path.cwd(), BASE, ("docs/engineering-pipeline-smoke-test.md",), proposed_base_sha=HEAD)
    assert result.decision == "narrow_steward_confirmation"
    assert result.material_paths == ()


def test_non_descendant_base_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _analyzer(monkeypatch, "docs/notes.md\n", descendant=False).assess(Path.cwd(), BASE, ("docs/engineering-pipeline-smoke-test.md",), proposed_base_sha=HEAD)
    assert result.decision == "invalid_repository"
    assert result.safe_to_revalidate is False
