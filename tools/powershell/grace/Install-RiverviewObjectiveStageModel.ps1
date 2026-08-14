# Riverview RV-005.2 Objective and Stage Model Installer
# Version: 0.2.7
# Purpose: Install the PostgreSQL-backed objective/stage model with readiness, evidence, dependencies, final outputs, River events, diagnostics, and restart/resume acceptance.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\repo')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.2.7'
$ExpectedHead='34b672f2acb7dd60ea2536505ff3bd39b93ce40b'
$CheckpointId='RIV-GRC-0002'
$ReportLines=[Collections.Generic.List[string]]::new()

function Add-Line {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text,[ConsoleColor]$Color='Gray')
    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}
function Add-Section {
    param([Parameter(Mandatory)][string]$Title)
    Add-Line ''
    Add-Line "=== $Title ===" Cyan
}
function Write-Utf8NoBom {
    param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][AllowEmptyString()][string]$Content)
    $Encoding=New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path,$Content,$Encoding)
}
function Save-Report {
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path=Join-Path $Directory "RV-005.2-Objective-Stage-Installer-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){ Set-Clipboard $Report }
        else { $Report | clip.exe }
        Write-Host "`nComplete installer report copied to the Windows clipboard." -ForegroundColor Cyan
    } catch {
        Write-Host "`nClipboard copy failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host "Durable report: $Path" -ForegroundColor Green
}
function Invoke-Captured {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$Label
    )
    $Capture=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\capture'
    New-Item -ItemType Directory -Path $Capture -Force | Out-Null
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmssfff'
    $Out=Join-Path $Capture "$Label-$Stamp.stdout.txt"
    $Err=Join-Path $Capture "$Label-$Stamp.stderr.txt"
    $Process=Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $RepositoryPath -RedirectStandardOutput $Out -RedirectStandardError $Err -Wait -PassThru
    if(Test-Path $Out){ foreach($Line in @(Get-Content $Out -Encoding UTF8)){ Add-Line $Line } }
    if(Test-Path $Err){ foreach($Line in @(Get-Content $Err -Encoding UTF8)){ Add-Line $Line $(if($Process.ExitCode -eq 0){'Yellow'}else{'Red'}) } }
    if($Process.ExitCode -ne 0){ throw "${CheckpointId}: $Label failed with exit code $($Process.ExitCode)." }
}

try {
    Add-Section 'RIVERVIEW RV-005.2 OBJECTIVE AND STAGE MODEL INSTALLER'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){ throw "${CheckpointId}: Riverview Git repository not found." }

    $Head=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    $Branch=(git.exe -C $RepositoryPath branch --show-current).Trim()
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Branch: $Branch"
    Add-Line "Local HEAD: $Head"
    Add-Line "Installer version: $ToolVersion"

    Add-Section 'CHARTER AND RV-005.2 SCOPE ANCHOR'
    Add-Line 'Current waypoint: RV-005.2 - Objective and stage model.'
    Add-Line 'Exact action: persist objectives, ordered stages, readiness, required evidence, dependencies, final outputs, and River event evidence; prove restart/resume from PostgreSQL.'
    Add-Line 'Relay remains owner of work orders and execution.'
    Add-Line 'Prohibited: automatic stage selection/enqueue, provider dispatch, JSON-file workflow authority, RV-005.3 momentum loop, authority widening, roadmap completion, commit, or push.'

    if($Branch -ne 'main'){ throw "${CheckpointId}: Expected branch main, observed $Branch." }
    if($Head -ne $ExpectedHead){ throw "${CheckpointId}: Expected HEAD $ExpectedHead, observed $Head." }
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: Riverview virtual environment not found.' }

    Add-Section 'SELF-INSTALLATION'
    $Canonical=Join-Path $RepositoryPath 'tools\powershell\grace\Install-RiverviewObjectiveStageModel.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $Canonical) -Force | Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Canonical)){
        Copy-Item $PSCommandPath $Canonical -Force
        Add-Line "Installed installer: $Canonical" Green
    }

    Add-Section 'PRE-INSTALL WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }
    if(@(git.exe -C $RepositoryPath diff --cached --name-only).Count -ne 0){ throw "${CheckpointId}: staged files exist." }

    Add-Section 'WRITE RV-005.2 SLICE'

    $Migration=@'
-- Riverview Objective and Stage Model
-- Version: 0.2.7
-- Migration: 0010

BEGIN;

CREATE TABLE objectives (
    objective_id uuid PRIMARY KEY,
    objective_key text NOT NULL UNIQUE,
    title text NOT NULL,
    description text NOT NULL,
    status text NOT NULL CHECK(status IN ('draft','ready','active','blocked','completed','cancelled')),
    owner_id text NOT NULL,
    requested_by text NOT NULL,
    correlation_id uuid NOT NULL,
    final_output jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE TABLE objective_stages (
    stage_id uuid PRIMARY KEY,
    objective_id uuid NOT NULL REFERENCES objectives(objective_id) ON DELETE CASCADE,
    stage_key text NOT NULL,
    sort_order integer NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    status text NOT NULL CHECK(status IN ('pending','ready','active','blocked','completed','cancelled')),
    readiness text NOT NULL CHECK(readiness IN ('waiting','ready','satisfied','blocked')),
    required_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    accepted_evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    final_output jsonb,
    steward_checkpoint boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    UNIQUE(objective_id,stage_key),
    UNIQUE(objective_id,sort_order)
);

CREATE TABLE objective_stage_dependencies (
    stage_id uuid NOT NULL REFERENCES objective_stages(stage_id) ON DELETE CASCADE,
    depends_on_stage_id uuid NOT NULL REFERENCES objective_stages(stage_id) ON DELETE CASCADE,
    PRIMARY KEY(stage_id,depends_on_stage_id),
    CHECK(stage_id <> depends_on_stage_id)
);

CREATE INDEX objective_status_idx ON objectives(status,updated_at);
CREATE INDEX objective_stage_readiness_idx ON objective_stages(objective_id,readiness,sort_order);

INSERT INTO cookbook_entries(
    cookbook_entry,checkpoint_id,component,failure_classes,
    diagnostic_procedure,repair_procedure,verification_procedure,
    applicability,validation_state,validated_at,updated_at
)
VALUES(
    'CB-RIV-GRC-0002',
    'RIV-GRC-0002',
    'riverview.grace.objectives',
    '["objective-missing","dependency-unsatisfied","required-evidence-missing","invalid-stage-transition","restart-resume-failure"]'::jsonb,
    '["Run python -m riverview.grace.objective_acceptance read","Inspect objectives/objective_stages/objective_stage_dependencies in PostgreSQL","Read the River aggregate for the objective correlation"]'::jsonb,
    '["Restore only the missing objective/stage state or accepted evidence; do not fabricate evidence or bypass dependencies"]'::jsonb,
    '["Run objective model tests","Run seed and read acceptance in separate Python processes","Verify final outputs and River events"]'::jsonb,
    '{"waypoint":"RV-005.2","authority":"postgresql","json_file_authority":false}'::jsonb,
    'validated',
    now(),
    now()
)
ON CONFLICT(checkpoint_id) DO UPDATE SET
    component=EXCLUDED.component,
    failure_classes=EXCLUDED.failure_classes,
    diagnostic_procedure=EXCLUDED.diagnostic_procedure,
    repair_procedure=EXCLUDED.repair_procedure,
    verification_procedure=EXCLUDED.verification_procedure,
    applicability=EXCLUDED.applicability,
    validation_state=EXCLUDED.validation_state,
    validated_at=EXCLUDED.validated_at,
    updated_at=EXCLUDED.updated_at;

COMMIT;
'@
    $MigrationPath=Join-Path $RepositoryPath 'database\migrations\0010_objective_stage_model.sql'
    Write-Utf8NoBom -Path $MigrationPath -Content $Migration
    Add-Line 'WROTE  database/migrations/0010_objective_stage_model.sql' Green

    $Objectives=@'
"""PostgreSQL-authoritative objective and stage model.

Version: 0.2.7
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
                        readiness,required_evidence,steward_checkpoint
                    )
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
                    """,
                    (
                        stage_id,objective_id,spec.key,order,spec.title,spec.description,status,
                        readiness,json.dumps(list(spec.required_evidence)),spec.steward_checkpoint,
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
                       created_at,updated_at,completed_at
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
'@
    $ObjectivesPath=Join-Path $RepositoryPath 'src\riverview\grace\objectives.py'
    Write-Utf8NoBom -Path $ObjectivesPath -Content $Objectives
    Add-Line 'WROTE  src/riverview/grace/objectives.py' Green

    $Acceptance=@'
"""Restart/resume acceptance for RV-005.2.

Version: 0.2.7
"""

from __future__ import annotations

import json
import sys

from riverview.grace.objectives import ObjectiveStore, StageSpec
from riverview.river.store import EventStore

DEFAULT_KEY="acceptance.rv0052.restart"
def seed(key: str) -> dict[str,object]:
    store=ObjectiveStore()
    objective_id=store.create(
        key,
        "RV-005.2 restart acceptance",
        "Prove objective and stage state resumes from PostgreSQL after process restart.",
        [
            StageSpec(
                key="collect",
                title="Collect evidence",
                description="Persist first-stage evidence.",
                required_evidence=("acceptance:seed",),
            ),
            StageSpec(
                key="deliver",
                title="Deliver final output",
                description="Resume and finish after a separate process starts.",
                required_evidence=("acceptance:resume",),
                depends_on=("collect",),
            ),
        ],
        requested_by="acceptance",
    )
    state=store.load(key)
    if state["stages"][0]["readiness"]!="ready" or state["stages"][1]["readiness"]!="waiting":
        raise RuntimeError("RIV-GRC-0002: initial readiness is incorrect.")
    return {"status":"seeded","objective_id":str(objective_id),"first":state["stages"][0]["readiness"],"second":state["stages"][1]["readiness"]}


def read_and_finish(key: str) -> dict[str,object]:
    store=ObjectiveStore()
    state=store.load(key)
    if state["objective_key"]!=key:
        raise RuntimeError("RIV-GRC-0002: objective did not resume from PostgreSQL.")

    if state["status"]=="completed":
        stream=EventStore().read_aggregate("objective",state["objective_id"])
        return {"status":"healthy","resumed":True,"already_completed":True,"event_count":len(stream),"final_output":state["final_output"]}

    try:
        store.complete_stage(key,"collect",{"premature":True})
    except RuntimeError as exc:
        if "missing required evidence" not in str(exc):
            raise
    else:
        raise RuntimeError("RIV-GRC-0002: missing-evidence failure was not induced.")

    store.add_evidence(key,"collect","acceptance:seed")
    store.complete_stage(key,"collect",{"collected":True})

    mid=store.load(key)
    deliver=next(stage for stage in mid["stages"] if stage["stage_key"]=="deliver")
    if deliver["readiness"]!="ready":
        raise RuntimeError("RIV-GRC-0002: dependency completion did not make deliver stage ready.")

    store.add_evidence(key,"deliver","acceptance:resume")
    store.complete_stage(key,"deliver",{"delivered":True})
    store.finalize(key,{"artifact":"acceptance","result":"complete"})

    final=store.load(key)
    if final["status"]!="completed":
        raise RuntimeError("RIV-GRC-0002: final objective status is not completed.")
    if final["final_output"]!={"artifact":"acceptance","result":"complete"}:
        raise RuntimeError("RIV-GRC-0002: final output was not persisted.")

    stream=EventStore().read_aggregate("objective",final["objective_id"])
    event_types=[event["event_type"] for event in stream]
    required={"objective.created","objective.stage.evidence.accepted","objective.stage.completed","objective.completed"}
    if not required.issubset(set(event_types)):
        raise RuntimeError(f"RIV-GRC-0002: River event evidence incomplete: {event_types}")

    return {
        "status":"healthy",
        "resumed":True,
        "induced_missing_evidence_rejected":True,
        "objective_status":final["status"],
        "final_output":final["final_output"],
        "stage_states":[
            {"stage_key":stage["stage_key"],"status":stage["status"],"readiness":stage["readiness"]}
            for stage in final["stages"]
        ],
        "event_types":event_types,
    }


if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "read"
    key=sys.argv[2] if len(sys.argv)>2 else DEFAULT_KEY
    result=seed(key) if mode=="seed" else read_and_finish(key)
    print(json.dumps(result,indent=2,sort_keys=True,default=str))
'@
    $AcceptancePath=Join-Path $RepositoryPath 'src\riverview\grace\objective_acceptance.py'
    Write-Utf8NoBom -Path $AcceptancePath -Content $Acceptance
    Add-Line 'WROTE  src/riverview/grace/objective_acceptance.py' Green

    $Tests=@'
"""Contract tests for RV-005.2 objective/stage model.

Version: 0.2.7
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from riverview.grace.objectives import ObjectiveStore, StageSpec


def unique_key(name: str) -> str:
    return f"test.rv0052.{name}.{uuid4()}"


def test_dependencies_persist_and_gate_readiness() -> None:
    key=unique_key("dependency")
    store=ObjectiveStore()
    store.create(
        key,
        "Dependency test",
        "Dependency readiness",
        [
            StageSpec("first","First","First stage"),
            StageSpec("second","Second","Second stage",depends_on=("first",)),
        ],
        requested_by="pytest",
    )
    state=store.load(key)
    assert state["stages"][0]["readiness"]=="ready"
    assert state["stages"][1]["readiness"]=="waiting"
    assert state["stages"][1]["depends_on"]==["first"]


def test_required_evidence_cannot_be_bypassed() -> None:
    key=unique_key("evidence")
    store=ObjectiveStore()
    store.create(
        key,
        "Evidence test",
        "Required evidence",
        [StageSpec("only","Only","Only stage",required_evidence=("proof:required",))],
        requested_by="pytest",
    )
    with pytest.raises(RuntimeError,match="missing required evidence"):
        store.complete_stage(key,"only",{"bad":True})


def test_final_output_requires_all_stages_complete() -> None:
    key=unique_key("final")
    store=ObjectiveStore()
    store.create(
        key,
        "Final test",
        "Final output",
        [StageSpec("only","Only","Only stage")],
        requested_by="pytest",
    )
    with pytest.raises(RuntimeError,match="incomplete stages"):
        store.finalize(key,{"bad":True})


def test_unknown_dependency_is_rejected_transactionally() -> None:
    key=unique_key("unknown")
    store=ObjectiveStore()
    with pytest.raises(ValueError,match="depends on unknown stage"):
        store.create(
            key,
            "Unknown dependency",
            "Reject invalid graph",
            [StageSpec("only","Only","Only",depends_on=("missing",))],
            requested_by="pytest",
        )
    with pytest.raises(RuntimeError,match="not found"):
        store.load(key)
'@
    $TestsPath=Join-Path $RepositoryPath 'tests\test_objective_stage_model.py'
    Write-Utf8NoBom -Path $TestsPath -Content $Tests
    Add-Line 'WROTE  tests/test_objective_stage_model.py' Green

    $Checkpoint=@'
<!-- Version: 0.2.7 -->
# RIV-GRC-0002 - Objective or stage cannot progress safely

Component owner: `riverview.grace.objectives`.

Trigger: an objective/stage is missing, a dependency is incomplete, required evidence is absent, a stage transition is invalid, or restart/resume cannot reconstruct authoritative state.

Authoritative inputs:
- `objectives`
- `objective_stages`
- `objective_stage_dependencies`
- River events for the objective aggregate

Outputs:
- persisted readiness and status
- accepted evidence references
- stage final outputs
- objective final output
- River event provenance

Failure classes:
- objective missing
- stage missing
- dependency unsatisfied
- required evidence missing
- invalid stage transition
- restart/resume failure

Bounded distinguishing probes:
1. Run `python -m riverview.grace.objective_acceptance read`.
2. Inspect the three RV-005.2 PostgreSQL tables.
3. Read the objective River aggregate.
4. Compare `required_evidence` with `accepted_evidence`.

Smallest safe repair:
- restore only missing/corrupt objective-stage state from accepted PostgreSQL evidence;
- add only genuine evidence references;
- never fabricate evidence, bypass dependencies, or move workflow authority into JSON files.

Recovery verification:
- objective tests pass;
- seed and read acceptance succeed in separate Python processes;
- final outputs persist;
- River aggregate contains creation, evidence, stage completion, and objective completion events.

Provenance:
- waypoint: RV-005.2
- migration: 0010
- implementation: `src/riverview/grace/objectives.py`
- acceptance: `src/riverview/grace/objective_acceptance.py`

Escalation boundary:
- ambiguous user intent;
- authority changes;
- protected/Undercurrent data;
- requested dependency bypass;
- evidence that cannot be verified.

Validation state: first-pass implementation evidence.
'@
    $CheckpointPath=Join-Path $RepositoryPath 'docs\operations\troubleshooting\checkpoints\RIV-GRC-0002_OBJECTIVE_STAGE_MODEL.md'
    Write-Utf8NoBom -Path $CheckpointPath -Content $Checkpoint
    Add-Line 'WROTE  docs/operations/troubleshooting/checkpoints/RIV-GRC-0002_OBJECTIVE_STAGE_MODEL.md' Green

    Add-Section 'APPLY MIGRATION 0010'
    $Runner=@'
from __future__ import annotations

import hashlib
from pathlib import Path

from riverview.database import connect

root=Path(r"__ROOT__")
path=root/"database/migrations/0010_objective_stage_model.sql"
checksum=hashlib.sha256(path.read_bytes()).hexdigest()

with connect() as connection, connection.cursor() as cursor:
    cursor.execute("SELECT version,checksum_sha256 FROM schema_migrations WHERE migration_id='0010'")
    row=cursor.fetchone()
    if row is not None:
        if row[0]!="0.2.0" or row[1].lower()!=checksum.lower():
            raise RuntimeError(f"RIV-DB-0006: migration 0010 ledger mismatch: {row!r} local={checksum}")
        print(f"migration_0010=already_applied version={row[0]} checksum={row[1]}")
    else:
        cursor.execute(path.read_text(encoding="utf-8"))
        cursor.execute(
            "INSERT INTO schema_migrations(migration_id,version,checksum_sha256) VALUES('0010','0.2.0',%s)",
            (checksum,),
        )
        print(f"migration_0010=applied version=0.2.0 checksum={checksum}")
'@
    $Runner=$Runner.Replace('__ROOT__',$RepositoryPath.Replace('\','\\'))
    $Runtime=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\runtime'
    New-Item -ItemType Directory -Path $Runtime -Force | Out-Null
    $RunnerPath=Join-Path $Runtime 'apply_0010.py'
    Write-Utf8NoBom -Path $RunnerPath -Content $Runner
    Invoke-Captured -FilePath $Python -ArgumentList @($RunnerPath) -Label 'migration_0010'

    Add-Section 'STATIC ACCEPTANCE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','compileall','-q','src\riverview\grace') -Label 'compile'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','ruff','check','src\riverview\grace','tests\test_objective_stage_model.py') -Label 'ruff'
    Add-Line 'Static acceptance passed.' Green

    Add-Section 'CONTRACT AND INDUCED-FAILURE TESTS'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','pytest','-q','tests\test_objective_stage_model.py') -Label 'tests'
    Add-Line 'Objective/stage contract and induced-failure tests passed.' Green

    Add-Section 'PROCESS 1 - SEED OBJECTIVE'
    $AcceptanceKey="acceptance.rv0052.install.$([Guid]::NewGuid().ToString('N'))"
    Add-Line "Acceptance key: $AcceptanceKey"
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','seed',$AcceptanceKey) -Label 'restart_seed'
    Add-Line 'Seed process completed and exited.' Green

    Add-Section 'PROCESS 2 - RESUME AND COMPLETE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','read',$AcceptanceKey) -Label 'restart_read'
    Add-Line 'Separate-process PostgreSQL restart/resume acceptance passed.' Green

    Add-Section 'GRACE AUTHORITY REGRESSION'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.acceptance') -Label 'grace_authority_regression'
    Add-Line 'RV-005.1 Grace authority acceptance remains healthy.' Green

    Add-Section 'FINAL WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }

    Add-Section 'RV-005.2 LOCAL COMPLETION RESULT'
    Add-Line 'Objectives and ordered stages are PostgreSQL-authoritative.' Green
    Add-Line 'Readiness, dependencies, required/accepted evidence, stage outputs, and objective final outputs persist durably.' Green
    Add-Line 'Stage/objective facts emit River events with correlation and idempotency keys.' Green
    Add-Line 'Missing evidence and invalid dependency graphs are rejected in induced-failure acceptance.' Green
    Add-Line 'A separate Python process resumed and completed the seeded objective from PostgreSQL.' Green
    Add-Line 'No JSON-file workflow authority, automatic enqueue, provider dispatch, RV-005.3 loop, roadmap completion, commit, or push was introduced.' Green
    Add-Line 'RV-005.2 is locally acceptance-complete. Next stage: exact-scope publication.' Green

    Save-Report
}
catch {
    Add-Section 'RV-005.2 INSTALLER BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'No commit or push was performed.' Yellow
    Save-Report
    throw
}
