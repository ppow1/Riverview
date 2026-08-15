"""Bounded archaeology and decomposition records for RV-012."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RepositoryMap:
    repository_identity: str
    root: str
    entry_points: tuple[str, ...]
    runtime_seams: tuple[str, ...]
    dependency_seams: tuple[str, ...]
    test_seams: tuple[str, ...]
    data_seams: tuple[str, ...]
    deployment_seams: tuple[str, ...]
    authoritative_sources: tuple[str, ...]
    unknowns: tuple[str, ...]
    mutable_ownership: tuple[str, ...]

    def validate(self) -> None:
        if not self.repository_identity.strip() or not self.root.strip():
            raise ValueError("RIV-INT-0002: repository identity and root are required.")
        if not self.authoritative_sources or not self.mutable_ownership:
            raise ValueError("RIV-INT-0002: authoritative sources and ownership are required.")


@dataclass(frozen=True, slots=True)
class EngineeringTask:
    task_id: str
    objective_id: str
    instruction: str
    allowed_paths: tuple[str, ...]
    provider_need: str
    acceptance: tuple[str, ...]
    checkpoint: str
    merge_owner: str

    def validate(self) -> None:
        if not self.task_id.strip() or not self.objective_id.strip() or not self.instruction.strip():
            raise ValueError("RIV-INT-0003: task identity and bounded instruction are required.")
        if not self.allowed_paths or any(path.startswith(("/", "\\")) for path in self.allowed_paths):
            raise ValueError("RIV-CAP-0002: task paths must be non-empty relative paths.")
        if not self.acceptance or not self.checkpoint.strip() or not self.merge_owner.strip():
            raise ValueError("RIV-INT-0003: task acceptance, checkpoint, and merge owner are required.")


def reject_path_overlap(tasks: tuple[EngineeringTask, ...]) -> None:
    """Fail closed before decomposition can assign overlapping mutable paths."""
    for index, task in enumerate(tasks):
        for sibling in tasks[index + 1 :]:
            if set(task.allowed_paths) & set(sibling.allowed_paths):
                raise ValueError("RIV-CAP-0002: task path ownership overlaps; reschedule one lane.")
