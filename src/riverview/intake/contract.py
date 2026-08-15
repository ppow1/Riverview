"""Project intake is evidence and intent capture, never execution authority."""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_FIELDS = ("project_id", "mission", "repositories", "requested_outcome", "acceptance_criteria", "classification")


@dataclass(frozen=True, slots=True)
class ProjectIntake:
    project_id: str
    mission: str
    repositories: tuple[str, ...]
    requested_outcome: str
    acceptance_criteria: tuple[str, ...]
    constraints: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    urgency: str = "normal"
    classification: str = "operational"
    steward_checkpoints: tuple[str, ...] = ()
    required_reading: tuple[str, ...] = ()
    external_dependencies: tuple[str, ...] = ()

    def missing_fields(self) -> tuple[str, ...]:
        values = {
            "project_id": self.project_id,
            "mission": self.mission,
            "repositories": self.repositories,
            "requested_outcome": self.requested_outcome,
            "acceptance_criteria": self.acceptance_criteria,
            "classification": self.classification,
        }
        return tuple(name for name in REQUIRED_FIELDS if not values[name])

    def validate(self) -> None:
        missing = self.missing_fields()
        if missing:
            raise ValueError(f"RIV-INT-0001: incomplete project intake; missing={','.join(missing)}")
        if self.urgency not in {"low", "normal", "high", "critical"}:
            raise ValueError("RIV-INT-0001: urgency is unsupported.")
        if self.classification not in {"public", "operational", "private", "sensitive"}:
            raise ValueError("RIV-SEC-0001: intake classification is closed.")
        if any(not isinstance(item, str) or not item.strip() for values in (self.repositories, self.acceptance_criteria) for item in values):
            raise ValueError("RIV-INT-0001: intake lists must contain bounded non-empty values.")
