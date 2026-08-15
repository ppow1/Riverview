import pytest

from riverview.intake import ProjectIntake


def test_incomplete_intake_names_exact_missing_fields() -> None:
    intake = ProjectIntake("", "", (), "", (), classification="")
    assert intake.missing_fields() == ("project_id", "mission", "repositories", "requested_outcome", "acceptance_criteria", "classification")
    with pytest.raises(ValueError, match="missing=project_id,mission"):
        intake.validate()


def test_complete_intake_is_valid_but_not_execution_authority() -> None:
    intake = ProjectIntake("demo", "Improve bounded diagnostics", ("A:/repo",), "tested checkpoint", ("tests pass",))
    intake.validate()
