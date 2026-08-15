import pytest

from riverview.intake import EngineeringTask, RepositoryMap, reject_path_overlap


def test_repository_map_requires_authority_and_ownership() -> None:
    mapping = RepositoryMap("riverview", "A:/Riverview/repo", ("src",), (), (), ("tests",), (), (), ("postgres",), (), ("src",))
    mapping.validate()


def test_decomposition_rejects_overlapping_mutable_paths() -> None:
    def task(name: str, path: str) -> EngineeringTask:
        return EngineeringTask(name, "objective", "bounded", (path,), "codex", ("tests",), "RIV-INT-0002", "grace")
    with pytest.raises(ValueError, match="overlaps"):
        reject_path_overlap((task("a", "src/a.py"), task("b", "src/a.py")))
