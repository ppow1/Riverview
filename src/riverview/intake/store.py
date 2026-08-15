"""Durable intake persistence; drafts never dispatch by themselves."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from riverview.database import connect

from .contract import ProjectIntake


class ProjectIntakeStore:
    def create_draft(self, intake: ProjectIntake, *, correlation_id: UUID, intake_id: UUID | None = None) -> UUID:
        intake.validate()
        intake_id = intake_id or uuid4()
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO project_intakes
                (intake_id,project_id,mission,repositories,requested_outcome,acceptance_criteria,constraints_json,artifact_refs,urgency,classification,steward_checkpoints,required_reading,external_dependencies,status,correlation_id)
                VALUES(%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,'draft',%s)
                ON CONFLICT(project_id,correlation_id) DO NOTHING""",
                (intake_id, intake.project_id, intake.mission, json.dumps(intake.repositories), intake.requested_outcome,
                 json.dumps(intake.acceptance_criteria), json.dumps(intake.constraints), json.dumps(intake.artifact_refs), intake.urgency,
                 intake.classification, json.dumps(intake.steward_checkpoints), json.dumps(intake.required_reading),
                 json.dumps(intake.external_dependencies), correlation_id),
            )
            cursor.execute("SELECT intake_id FROM project_intakes WHERE project_id=%s AND correlation_id=%s", (intake.project_id, correlation_id))
            return cursor.fetchone()[0]
