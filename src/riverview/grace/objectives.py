"""PostgreSQL-authoritative objective and stage model.

Version: 0.2.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect
from riverview.river.events import Classification, RiverEvent


@dataclass(frozen=True)
class StageSpec:
    key: str
    title: str
    description: str
    required_evidence: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    steward_checkpoint: bool = False
    declared_action: dict[str, Any] | None = None


class ObjectiveStore:
    """Durable objective/stage state. This model never enqueues work."""

    def _append_event(self, cursor: Any, event: RiverEvent) -> None:
        cursor.execute(
            """
            INSERT INTO river_events(
                event_id,event_type,aggregate_type,aggregate_id,correlation_id,
                causation_id,idempotency_key,classification,payload,occurred_at
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
            ON CONFLICT(idempotency_key) DO NOTHING
            """,
            (
                event.event_id,
                event.event_type,
                event.aggregate_type,
                event.aggregate_id,
                event.correlation_id,
                event.causation_id,
                event.idempotency_key,
                event.classification.value,
                json.dumps(dict(event.payload)),
                event.occurred_at,
            ),
        )

    def create(
        self,
        objective_key: str,
        title: str,
        description: str,
        stages: list[StageSpec],
        *,
        owner_id: str = "grace",
        requested_by: str = "steward",
        correlation_id: UUID | None = None,
    ) -> UUID:
        if not objective_key.strip() or not stages:
            raise ValueError("RIV-GRC-0002: objective_key and at least one stage are required.")
        keys=[stage.key for stage in stages]
        if len(keys) != len(set(keys)):
            raise ValueError("RIV-GRC-0002: stage keys must be unique.")

        objective_id=uuid4()
        correlation=correlation_id or uuid4()

        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO objectives(
                    objective_id,objective_key,title,description,status,owner_id,requested_by,correlation_id
                )
                VALUES(%s,%s,%s,%s,'ready',%s,%s,%s)
                ON CONFLICT(objective_key) DO NOTHING
                RETURNING objective_id
                """,
                (objective_id,objective_key,title,description,owner_id,requested_by,correlation),
            )
            row=cursor.fetchone()
            if row is None:
                cursor.execute("SELECT objective_id FROM objectives WHERE objective_key=%s",(objective_key,))
                return cursor.fetchone()[0]

            stage_ids: dict[str, UUID]={}
            for order,spec in enumerate(stages,start=1):
                stage_id=uuid4()
                stage_ids[spec.key]=stage_id
                readiness="ready" if not spec.depends_on else "waiting"
                status="ready" if readiness=="ready" else "pending"
                cursor.execute(
                    """
                    INSERT INTO objective_stages(
                        stage_id,objective_id,stage_key,sort_order,title,description,status,
                        readiness,required_evidence,steward_checkpoint,declared_action
                    )
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb)
                    """,
                    (
                        stage_id,objective_id,spec.key,order,spec.title,spec.description,status,
                        readiness,json.dumps(list(spec.required_evidence)),spec.steward_checkpoint,json.dumps(spec.declared_action) if spec.declared_action else None,
                    ),
                )

            for spec in stages:
                for dependency in spec.depends_on:
                    if dependency not in stage_ids:
                        raise ValueError(
                            f"RIV-GRC-0002: stage {spec.key!r} depends on unknown stage {dependency!r}."
                        )
                    cursor.execute(
                        """
                        INSERT INTO objective_stage_dependencies(stage_id,depends_on_stage_id)
                        VALUES(%s,%s)
                        """,
                        (stage_ids[spec.key],stage_ids[dependency]),
                    )

            self._append_event(
                cursor,
                RiverEvent(
                    event_type="objective.created",
                    aggregate_type="objective",
                    aggregate_id=objective_id,
                    correlation_id=correlation,
                    idempotency_key=f"objective.created:{objective_key}",
                    classification=Classification.RIVER,
                    payload={"objective_key":objective_key,"stage_count":len(stages)},
                ),
            )

        return objective_id

    def create_in_transaction(
        self,
        cursor: Any,
        objective_key: str,
        title: str,
        description: str,
        stages: list[StageSpec],
        *,
        owner_id: str = "grace",
        requested_by: str = "steward",
        correlation_id: UUID | None = None,
    ) -> UUID:
        """Create or recover an objective using the caller's transaction."""
        if not objective_key.strip() or not stages:
            raise ValueError("RIV-GRC-0002: objective_key and at least one stage are required.")
        keys = [stage.key for stage in stages]
        if len(keys) != len(set(keys)):
            raise ValueError("RIV-GRC-0002: stage keys must be unique.")
        objective_id = uuid4()
        correlation = correlation_id or uuid4()
        cursor.execute(
            """INSERT INTO objectives(
                   objective_id,objective_key,title,description,status,owner_id,requested_by,correlation_id)
               VALUES(%s,%s,%s,%s,'ready',%s,%s,%s)
               ON CONFLICT(objective_key) DO NOTHING
               RETURNING objective_id""",
            (objective_id, objective_key, title, description, owner_id, requested_by, correlation),
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute("SELECT objective_id FROM objectives WHERE objective_key=%s FOR UPDATE", (objective_key,))
            existing = cursor.fetchone()
            if existing is None:
                raise RuntimeError("RIV-GRC-0002: objective idempotency reconciliation found no objective.")
            return existing[0]
        for order, spec in enumerate(stages, start=1):
            stage_id = uuid4()
            readiness = "ready" if not spec.depends_on else "waiting"
            status = "ready" if readiness == "ready" else "pending"
            cursor.execute(
                """INSERT INTO objective_stages(
                       stage_id,objective_id,stage_key,sort_order,title,description,status,
                       readiness,required_evidence,steward_checkpoint,declared_action)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb)""",
                (stage_id, objective_id, spec.key, order, spec.title, spec.description, status,
                 readiness, json.dumps(list(spec.required_evidence)), spec.steward_checkpoint,
                 json.dumps(spec.declared_action) if spec.declared_action else None),
            )
        for spec in stages:
            for dependency in spec.depends_on:
                if dependency not in keys:
                    raise ValueError(f"RIV-GRC-0002: stage {spec.key!r} depends on unknown stage {dependency!r}.")
                cursor.execute(
                    """INSERT INTO objective_stage_dependencies(stage_id,depends_on_stage_id)
                       SELECT s.stage_id,d.stage_id FROM objective_stages s, objective_stages d
                       WHERE s.objective_id=%s AND s.stage_key=%s AND d.objective_id=%s AND d.stage_key=%s""",
                    (objective_id, spec.key, objective_id, dependency),
                )
        self._append_event(cursor, RiverEvent(
            event_type="objective.created", aggregate_type="objective", aggregate_id=objective_id,
            correlation_id=correlation, idempotency_key=f"objective.created:{objective_key}",
            classification=Classification.RIVER, payload={"objective_key": objective_key, "stage_count": len(stages)},
        ))
        return objective_id

    def load(self, objective_key: str) -> dict[str, Any]:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT objective_id,objective_key,title,description,status,owner_id,requested_by,
                       correlation_id,final_output,created_at,updated_at,completed_at
                FROM objectives WHERE objective_key=%s
                """,
                (objective_key,),
            )
            objective=cursor.fetchone()
            if objective is None:
                raise RuntimeError(f"RIV-GRC-0002: objective {objective_key!r} not found.")
            objective_names=[column.name for column in cursor.description]
            result=dict(zip(objective_names,objective,strict=True))

            cursor.execute(
                """
                SELECT stage_id,stage_key,sort_order,title,description,status,readiness,
                       required_evidence,accepted_evidence,final_output,steward_checkpoint,
                       declared_action,created_at,updated_at,completed_at
                FROM objective_stages
                WHERE objective_id=%s
                ORDER BY sort_order
                """,
                (result["objective_id"],),
            )
            stage_names=[column.name for column in cursor.description]
            stages=[dict(zip(stage_names,row,strict=True)) for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT s.stage_key,d.stage_key
                FROM objective_stage_dependencies x
                JOIN objective_stages s ON s.stage_id=x.stage_id
                JOIN objective_stages d ON d.stage_id=x.depends_on_stage_id
                WHERE s.objective_id=%s
                ORDER BY s.sort_order,d.sort_order
                """,
                (result["objective_id"],),
            )
            dependencies: dict[str,list[str]]={}
            for stage_key,dependency_key in cursor.fetchall():
                dependencies.setdefault(stage_key,[]).append(dependency_key)

            for stage in stages:
                stage["depends_on"]=dependencies.get(stage["stage_key"],[])
            result["stages"]=stages
            return result

    def add_evidence(self, objective_key: str, stage_key: str, evidence_ref: str) -> None:
        if not evidence_ref.strip():
            raise ValueError("RIV-GRC-0002: evidence_ref must not be empty.")
        with connect() as connection, connection.cursor() as cursor:
            objective,stage=self._lock_stage(cursor,objective_key,stage_key)
            accepted=list(stage["accepted_evidence"] or [])
            if evidence_ref not in accepted:
                accepted.append(evidence_ref)
                cursor.execute(
                    """
                    UPDATE objective_stages
                    SET accepted_evidence=%s::jsonb,updated_at=now()
                    WHERE stage_id=%s
                    """,
                    (json.dumps(accepted),stage["stage_id"]),
                )
            self._append_event(
                cursor,
                RiverEvent(
                    event_type="objective.stage.evidence.accepted",
                    aggregate_type="objective",
                    aggregate_id=objective["objective_id"],
                    correlation_id=objective["correlation_id"],
                    idempotency_key=f"objective.stage.evidence:{objective_key}:{stage_key}:{evidence_ref}",
                    classification=Classification.RIVER,
                    payload={"stage_key":stage_key,"evidence_ref":evidence_ref},
                ),
            )

    def complete_stage(
        self,
        objective_key: str,
        stage_key: str,
        final_output: dict[str, Any],
    ) -> None:
        with connect() as connection, connection.cursor() as cursor:
            objective,stage=self._lock_stage(cursor,objective_key,stage_key)
            if stage["status"]=="completed":
                return
            if stage["readiness"]!="ready":
                raise RuntimeError(
                    f"RIV-GRC-0002: stage {stage_key!r} is not ready; readiness={stage['readiness']!r}."
                )
            missing=sorted(set(stage["required_evidence"] or [])-set(stage["accepted_evidence"] or []))
            if missing:
                raise RuntimeError(
                    f"RIV-GRC-0002: stage {stage_key!r} missing required evidence: {missing}"
                )

            cursor.execute(
                """
                UPDATE objective_stages
                SET status='completed',readiness='satisfied',final_output=%s::jsonb,
                    completed_at=now(),updated_at=now()
                WHERE stage_id=%s
                """,
                (json.dumps(final_output),stage["stage_id"]),
            )
            self._refresh_readiness(cursor,objective["objective_id"])
            cursor.execute(
                """
                UPDATE objectives
                SET status=CASE
                    WHEN EXISTS(
                        SELECT 1 FROM objective_stages
                        WHERE objective_id=%s AND status <> 'completed'
                    ) THEN 'active'
                    ELSE status
                END,
                updated_at=now()
                WHERE objective_id=%s
                """,
                (objective["objective_id"],objective["objective_id"]),
            )
            self._append_event(
                cursor,
                RiverEvent(
                    event_type="objective.stage.completed",
                    aggregate_type="objective",
                    aggregate_id=objective["objective_id"],
                    correlation_id=objective["correlation_id"],
                    idempotency_key=f"objective.stage.completed:{objective_key}:{stage_key}",
                    classification=Classification.RIVER,
                    payload={"stage_key":stage_key,"final_output":final_output},
                ),
            )

    def finalize(self, objective_key: str, final_output: dict[str, Any]) -> None:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT objective_id,correlation_id,status
                FROM objectives WHERE objective_key=%s FOR UPDATE
                """,
                (objective_key,),
            )
            row=cursor.fetchone()
            if row is None:
                raise RuntimeError(f"RIV-GRC-0002: objective {objective_key!r} not found.")
            objective_id,correlation_id,status=row
            if status=="completed":
                return
            cursor.execute(
                """
                SELECT stage_key FROM objective_stages
                WHERE objective_id=%s AND status <> 'completed'
                ORDER BY sort_order
                """,
                (objective_id,),
            )
            incomplete=[item[0] for item in cursor.fetchall()]
            if incomplete:
                raise RuntimeError(
                    f"RIV-GRC-0002: objective cannot finalize; incomplete stages: {incomplete}"
                )
            cursor.execute(
                """
                UPDATE objectives
                SET status='completed',final_output=%s::jsonb,completed_at=now(),updated_at=now()
                WHERE objective_id=%s
                """,
                (json.dumps(final_output),objective_id),
            )
            self._append_event(
                cursor,
                RiverEvent(
                    event_type="objective.completed",
                    aggregate_type="objective",
                    aggregate_id=objective_id,
                    correlation_id=correlation_id,
                    idempotency_key=f"objective.completed:{objective_key}",
                    classification=Classification.RIVER,
                    payload={"final_output":final_output},
                ),
            )

    def _lock_stage(self, cursor: Any, objective_key: str, stage_key: str) -> tuple[dict[str,Any],dict[str,Any]]:
        cursor.execute(
            """
            SELECT objective_id,correlation_id,status
            FROM objectives WHERE objective_key=%s FOR UPDATE
            """,
            (objective_key,),
        )
        objective_row=cursor.fetchone()
        if objective_row is None:
            raise RuntimeError(f"RIV-GRC-0002: objective {objective_key!r} not found.")
        objective={"objective_id":objective_row[0],"correlation_id":objective_row[1],"status":objective_row[2]}

        cursor.execute(
            """
            SELECT stage_id,status,readiness,required_evidence,accepted_evidence
            FROM objective_stages
            WHERE objective_id=%s AND stage_key=%s
            FOR UPDATE
            """,
            (objective["objective_id"],stage_key),
        )
        stage_row=cursor.fetchone()
        if stage_row is None:
            raise RuntimeError(f"RIV-GRC-0002: stage {stage_key!r} not found.")
        stage={
            "stage_id":stage_row[0],
            "status":stage_row[1],
            "readiness":stage_row[2],
            "required_evidence":stage_row[3],
            "accepted_evidence":stage_row[4],
        }
        return objective,stage

    def _refresh_readiness(self, cursor: Any, objective_id: UUID) -> None:
        cursor.execute(
            """
            SELECT s.stage_id,s.status,
                   bool_and(d.status='completed') FILTER (WHERE d.stage_id IS NOT NULL) AS deps_done,
                   count(d.stage_id) AS dep_count
            FROM objective_stages s
            LEFT JOIN objective_stage_dependencies x ON x.stage_id=s.stage_id
            LEFT JOIN objective_stages d ON d.stage_id=x.depends_on_stage_id
            WHERE s.objective_id=%s
            GROUP BY s.stage_id,s.status
            """,
            (objective_id,),
        )
        for stage_id,status,deps_done,dep_count in cursor.fetchall():
            if status=="completed":
                continue
            ready=(dep_count==0) or bool(deps_done)
            cursor.execute(
                """
                UPDATE objective_stages
                SET readiness=%s,status=%s,updated_at=now()
                WHERE stage_id=%s
                """,
                ("ready" if ready else "waiting","ready" if ready else "pending",stage_id),
            )
