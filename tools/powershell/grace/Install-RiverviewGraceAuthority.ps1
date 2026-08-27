# Riverview RV-005.1 Grace Identity and Authority Contract Installer
# Version: 0.1.0
# Purpose: Implement the bounded Grace identity and authority contract with PostgreSQL authority, tests, diagnostics, and acceptance.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.1.0'
$ExpectedHead='ff565726f87c9034b50853d643e9428b0333f4d3'
$CheckpointId='RIV-GRC-0001'
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
    $Path=Join-Path $Directory "RV-005.1-Grace-Authority-Installer-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
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
    Add-Section 'RIVERVIEW RV-005.1 GRACE IDENTITY AND AUTHORITY CONTRACT INSTALLER'
    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    if(-not(Test-Path(Join-Path $RepositoryPath '.git'))){ throw "${CheckpointId}: Riverview Git repository not found." }

    $Head=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    $Branch=(git.exe -C $RepositoryPath branch --show-current).Trim()
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Branch: $Branch"
    Add-Line "Local HEAD: $Head"
    Add-Line "Installer version: $ToolVersion"

    Add-Section 'CHARTER AND RV-005.1 SCOPE ANCHOR'
    Add-Line 'Current waypoint: RV-005.1 - Grace identity and authority contract.'
    Add-Line 'Grace coordinates progression but does not replace the River, PostgreSQL, the Estate, or the Steward.'
    Add-Line 'Exact action: implement durable Grace identity, explicit authority grants/prohibitions, decision evaluation, diagnostic evidence, and authority-rejection acceptance.'
    Add-Line 'Prohibited: objective/stage engine, automatic enqueue, provider dispatch, arbitrary shell/SQL, implicit authority from conversation text, Undercurrent access, roadmap completion, commit, or push.'

    if($Branch -ne 'main'){ throw "${CheckpointId}: Expected branch main, observed $Branch." }
    if($Head -ne $ExpectedHead){ throw "${CheckpointId}: Expected HEAD $ExpectedHead, observed $Head." }
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: Riverview virtual environment not found.' }

    Add-Section 'SELF-INSTALLATION'
    $Canonical=Join-Path $RepositoryPath 'tools\powershell\grace\Install-RiverviewGraceAuthority.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $Canonical) -Force | Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($Canonical)){
        Copy-Item $PSCommandPath $Canonical -Force
        Add-Line "Installed installer: $Canonical" Green
    }

    Add-Section 'PRE-INSTALL WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }
    if(@(git.exe -C $RepositoryPath diff --cached --name-only).Count -ne 0){ throw "${CheckpointId}: staged files exist." }

    Add-Section 'WRITE RV-005.1 SLICE'

    $Migration = @'
-- Riverview Grace Identity and Authority Contract
-- Version: 0.1.0
-- Migration: 0009

BEGIN;

CREATE TABLE grace_identities (
    grace_id text PRIMARY KEY,
    display_name text NOT NULL,
    role text NOT NULL,
    authority_version text NOT NULL,
    enabled boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE grace_authority_rules (
    grace_id text NOT NULL REFERENCES grace_identities(grace_id),
    capability text NOT NULL,
    effect text NOT NULL CHECK(effect IN ('allow','deny','escalate')),
    scope text NOT NULL,
    requires_steward boolean NOT NULL DEFAULT false,
    reason text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(grace_id,capability)
);

CREATE TABLE grace_authority_decisions (
    decision_id uuid PRIMARY KEY,
    grace_id text NOT NULL REFERENCES grace_identities(grace_id),
    capability text NOT NULL,
    requested_scope text NOT NULL,
    decision text NOT NULL CHECK(decision IN ('allow','deny','escalate')),
    reason text NOT NULL,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    correlation_id uuid,
    decided_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO grace_identities(grace_id,display_name,role,authority_version)
VALUES('grace','Grace','operational_coordinator','0.1.0')
ON CONFLICT(grace_id) DO UPDATE SET
    display_name=EXCLUDED.display_name,
    role=EXCLUDED.role,
    authority_version=EXCLUDED.authority_version,
    enabled=true,
    updated_at=now();

INSERT INTO grace_authority_rules(grace_id,capability,effect,scope,requires_steward,reason) VALUES
('grace','read_authoritative_state','allow','bounded_river_metadata',false,'Grace may read bounded authoritative operational metadata required for coordination.'),
('grace','evaluate_progression','allow','declared_dependencies_and_evidence',false,'Grace may evaluate whether accepted work is ready to progress.'),
('grace','record_coordination_evidence','allow','grace_authority_decisions',false,'Grace may record its own bounded coordination decisions and evidence.'),
('grace','change_mission','deny','all',true,'Mission changes belong to the Steward.'),
('grace','change_authority_model','deny','all',true,'Authority-model changes belong to the Steward.'),
('grace','bypass_steward_checkpoint','deny','all',true,'Required Steward checkpoints cannot be bypassed.'),
('grace','arbitrary_sql','deny','all',true,'Grace receives named capabilities, never arbitrary SQL authority.'),
('grace','arbitrary_shell','deny','all',true,'Grace receives named capabilities, never arbitrary shell authority.'),
('grace','access_undercurrent','deny','ordinary_river',true,'Undercurrent access is excluded from ordinary Grace coordination.'),
('grace','infer_authority_from_conversation','deny','all',true,'Conversation text never silently grants executable authority.')
ON CONFLICT(grace_id,capability) DO UPDATE SET
    effect=EXCLUDED.effect,
    scope=EXCLUDED.scope,
    requires_steward=EXCLUDED.requires_steward,
    reason=EXCLUDED.reason,
    updated_at=now();

COMMIT;
'@
    $MigrationPath=Join-Path $RepositoryPath 'database\migrations\0009_grace_authority.sql'
    New-Item -ItemType Directory -Path (Split-Path -Parent $MigrationPath) -Force | Out-Null
    Write-Utf8NoBom -Path $MigrationPath -Content $Migration
    Add-Line 'WROTE  database/migrations/0009_grace_authority.sql' Green

    $Init = @'
"""Grace coordination contracts for Project Riverview.

Version: 0.1.0
"""

from riverview.grace.authority import AuthorityDecision, GraceAuthority

__all__ = ["AuthorityDecision", "GraceAuthority"]
'@
    $InitPath=Join-Path $RepositoryPath 'src\riverview\grace\__init__.py'
    New-Item -ItemType Directory -Path (Split-Path -Parent $InitPath) -Force | Out-Null
    Write-Utf8NoBom -Path $InitPath -Content $Init
    Add-Line 'WROTE  src/riverview/grace/__init__.py' Green

    $Authority = @'
"""PostgreSQL-backed Grace authority contract.

Version: 0.1.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from riverview.database import connect


@dataclass(frozen=True)
class AuthorityDecision:
    capability: str
    requested_scope: str
    decision: str
    reason: str
    requires_steward: bool


class GraceAuthority:
    """Evaluate bounded Grace capabilities from authoritative PostgreSQL rules."""

    grace_id = "grace"

    def identity(self) -> dict[str, Any]:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT grace_id,display_name,role,authority_version,enabled
                FROM grace_identities
                WHERE grace_id=%s
                """,
                (self.grace_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("RIV-GRC-0001: Grace identity is missing.")
            names = [column.name for column in cursor.description]
            return dict(zip(names, row, strict=True))

    def evaluate(
        self,
        capability: str,
        requested_scope: str,
        *,
        correlation_id: UUID | None = None,
        evidence_refs: list[str] | None = None,
        persist: bool = False,
    ) -> AuthorityDecision:
        if not capability or not requested_scope:
            raise ValueError("RIV-GRC-0001: capability and requested_scope are required.")

        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT effect,scope,requires_steward,reason
                FROM grace_authority_rules
                WHERE grace_id=%s AND capability=%s
                """,
                (self.grace_id, capability),
            )
            row = cursor.fetchone()

            if row is None:
                decision = AuthorityDecision(
                    capability=capability,
                    requested_scope=requested_scope,
                    decision="escalate",
                    reason="No explicit Grace authority rule exists for this capability.",
                    requires_steward=True,
                )
            else:
                effect, allowed_scope, requires_steward, reason = row
                if effect == "allow" and allowed_scope not in {"all", requested_scope}:
                    decision = AuthorityDecision(
                        capability=capability,
                        requested_scope=requested_scope,
                        decision="escalate",
                        reason=(
                            f"Capability is allowed only for scope {allowed_scope!r}; "
                            f"requested scope was {requested_scope!r}."
                        ),
                        requires_steward=True,
                    )
                else:
                    decision = AuthorityDecision(
                        capability=capability,
                        requested_scope=requested_scope,
                        decision=effect,
                        reason=reason,
                        requires_steward=requires_steward or effect != "allow",
                    )

            if persist:
                cursor.execute(
                    """
                    INSERT INTO grace_authority_decisions(
                        decision_id,grace_id,capability,requested_scope,decision,
                        reason,evidence_refs,correlation_id
                    )
                    VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
                    """,
                    (
                        uuid4(),
                        self.grace_id,
                        capability,
                        requested_scope,
                        decision.decision,
                        decision.reason,
                        json.dumps(evidence_refs or []),
                        correlation_id,
                    ),
                )

            return decision
'@
    $AuthorityPath=Join-Path $RepositoryPath 'src\riverview\grace\authority.py'
    Write-Utf8NoBom -Path $AuthorityPath -Content $Authority
    Add-Line 'WROTE  src/riverview/grace/authority.py' Green

    $Acceptance = @'
"""Live PostgreSQL acceptance for RV-005.1.

Version: 0.1.0
"""

from __future__ import annotations

import json

from riverview.grace.authority import GraceAuthority


def acceptance() -> dict[str, object]:
    authority = GraceAuthority()
    identity = authority.identity()

    allowed = authority.evaluate(
        "evaluate_progression",
        "declared_dependencies_and_evidence",
        persist=True,
        evidence_refs=["acceptance:rv0051"],
    )
    denied = authority.evaluate(
        "arbitrary_sql",
        "all",
        persist=True,
        evidence_refs=["acceptance:rv0051"],
    )
    unknown = authority.evaluate(
        "invented_capability",
        "all",
        persist=True,
        evidence_refs=["acceptance:rv0051"],
    )
    conversation = authority.evaluate(
        "infer_authority_from_conversation",
        "all",
        persist=True,
        evidence_refs=["acceptance:rv0051"],
    )

    if not identity["enabled"]:
        raise RuntimeError("RIV-GRC-0001: Grace identity is disabled.")
    if allowed.decision != "allow":
        raise RuntimeError("RIV-GRC-0001: allowed progression evaluation was rejected.")
    if denied.decision != "deny":
        raise RuntimeError("RIV-GRC-0001: arbitrary SQL was not denied.")
    if unknown.decision != "escalate":
        raise RuntimeError("RIV-GRC-0001: unknown capability did not escalate.")
    if conversation.decision != "deny":
        raise RuntimeError("RIV-GRC-0001: conversation-derived authority was not denied.")

    return {
        "status": "healthy",
        "grace_id": identity["grace_id"],
        "role": identity["role"],
        "authority_version": identity["authority_version"],
        "allowed_progression_evaluation": allowed.decision,
        "arbitrary_sql": denied.decision,
        "unknown_capability": unknown.decision,
        "conversation_authority": conversation.decision,
    }


if __name__ == "__main__":
    print(json.dumps(acceptance(), indent=2, sort_keys=True))
'@
    $AcceptancePath=Join-Path $RepositoryPath 'src\riverview\grace\acceptance.py'
    Write-Utf8NoBom -Path $AcceptancePath -Content $Acceptance
    Add-Line 'WROTE  src/riverview/grace/acceptance.py' Green

    $Tests = @'
"""Contract tests for RV-005.1 Grace authority.

Version: 0.1.0
"""

from __future__ import annotations

from riverview.grace.authority import GraceAuthority


def test_grace_identity_is_operational_coordinator() -> None:
    identity = GraceAuthority().identity()
    assert identity["grace_id"] == "grace"
    assert identity["role"] == "operational_coordinator"
    assert identity["enabled"] is True


def test_allowed_progression_evaluation_is_bounded() -> None:
    decision = GraceAuthority().evaluate(
        "evaluate_progression",
        "declared_dependencies_and_evidence",
    )
    assert decision.decision == "allow"
    assert decision.requires_steward is False


def test_scope_mismatch_escalates() -> None:
    decision = GraceAuthority().evaluate(
        "evaluate_progression",
        "undeclared_scope",
    )
    assert decision.decision == "escalate"
    assert decision.requires_steward is True


def test_prohibited_authority_is_rejected() -> None:
    authority = GraceAuthority()
    for capability in (
        "change_mission",
        "change_authority_model",
        "bypass_steward_checkpoint",
        "arbitrary_sql",
        "arbitrary_shell",
        "access_undercurrent",
        "infer_authority_from_conversation",
    ):
        decision = authority.evaluate(capability, "all")
        assert decision.decision == "deny"
        assert decision.requires_steward is True


def test_unknown_capability_escalates() -> None:
    decision = GraceAuthority().evaluate("unregistered_capability", "all")
    assert decision.decision == "escalate"
    assert decision.requires_steward is True
'@
    $TestsPath=Join-Path $RepositoryPath 'tests\test_grace_authority.py'
    Write-Utf8NoBom -Path $TestsPath -Content $Tests
    Add-Line 'WROTE  tests/test_grace_authority.py' Green

    $Checkpoint = @'
<!-- Version: 0.1.0 -->
# RIV-GRC-0001 - Grace authority contract unavailable or exceeded

Component owner: `riverview.grace.authority`.

Trigger: Grace evaluates a coordination capability and the durable identity/rule is missing, unknown, out of scope, or prohibited.

Failure classes:
- Grace identity missing or disabled.
- Explicit authority rule missing.
- Requested scope exceeds the allowed scope.
- A prohibited capability is requested.
- Conversation text is being treated as implicit authority.

Evidence captured:
- Grace identity and authority version.
- Requested capability and scope.
- Allow/deny/escalate decision.
- Reason and evidence references.
- Optional correlation ID.

Safe distinguishing probes:
1. Run `python -m riverview.grace.acceptance`.
2. Inspect the bounded Grace authority tables through approved diagnostics.
3. Confirm the current roadmap checkpoint and Steward authorization.

Smallest safe repair:
- Restore the missing durable Grace identity/rule from the accepted migration.
- Do not widen authority to make a failing request pass.
- Unknown or broader-than-declared requests escalate instead of defaulting to allow.

Recovery verification:
- Contract tests pass.
- Live PostgreSQL-backed acceptance passes.
- Arbitrary SQL/shell, Steward-checkpoint bypass, Undercurrent access, mission/authority changes, and conversation-derived authority are rejected.

Escalation boundary:
- Any requested widening of Grace authority.
- Any mission, authority-model, or protected-boundary change.
- Any ambiguity about Steward intent.

Applicable revision: RV-005.1 / Grace authority v0.1.0.

Validation state: first-pass implementation evidence.
'@
    $CheckpointPath=Join-Path $RepositoryPath 'docs\operations\troubleshooting\checkpoints\RIV-GRC-0001_GRACE_AUTHORITY.md'
    New-Item -ItemType Directory -Path (Split-Path -Parent $CheckpointPath) -Force | Out-Null
    Write-Utf8NoBom -Path $CheckpointPath -Content $Checkpoint
    Add-Line 'WROTE  docs/operations/troubleshooting/checkpoints/RIV-GRC-0001_GRACE_AUTHORITY.md' Green

    Add-Section 'APPLY MIGRATION'
    $MigrationRunner = @'
from __future__ import annotations

import hashlib
from pathlib import Path

from riverview.database import connect

root = Path(r"__ROOT__")
path = root / "database/migrations/0009_grace_authority.sql"
checksum = hashlib.sha256(path.read_bytes()).hexdigest()

with connect() as connection, connection.cursor() as cursor:
    cursor.execute(
        "SELECT checksum_sha256 FROM schema_migrations WHERE migration_id='0009'"
    )
    row = cursor.fetchone()
    if row is not None:
        if row[0] != checksum:
            raise RuntimeError(
                "RIV-DB-0006: migration 0009 checksum differs from applied ledger."
            )
        print("migration_0009=already_applied checksum_verified=true")
    else:
        sql = path.read_text(encoding="utf-8")
        cursor.execute(sql)
        cursor.execute(
            """
            INSERT INTO schema_migrations(migration_id,version,checksum_sha256)
            VALUES('0009','0.1.0',%s)
            """,
            (checksum,),
        )
        print(f"migration_0009=applied checksum={checksum}")
'@
    $MigrationRunner=$MigrationRunner.Replace('__ROOT__',$RepositoryPath.Replace('\','\\'))
    $RunnerPath=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\runtime\apply_0009.py'
    New-Item -ItemType Directory -Path (Split-Path -Parent $RunnerPath) -Force | Out-Null
    Write-Utf8NoBom -Path $RunnerPath -Content $MigrationRunner
    Invoke-Captured -FilePath $Python -ArgumentList @($RunnerPath) -Label 'migration_0009'

    Add-Section 'STATIC ACCEPTANCE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','compileall','-q','src\riverview\grace') -Label 'compile'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','ruff','check','src\riverview\grace','tests\test_grace_authority.py') -Label 'ruff'
    Add-Line 'Static acceptance passed.' Green

    Add-Section 'CONTRACT TESTS'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','pytest','-q','tests\test_grace_authority.py') -Label 'tests'
    Add-Line 'Grace authority contract tests passed.' Green

    Add-Section 'POSTGRESQL-BACKED LIVE ACCEPTANCE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.acceptance') -Label 'live_acceptance'
    Add-Line 'PostgreSQL-backed Grace authority acceptance passed.' Green

    Add-Section 'FINAL WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }

    Add-Section 'RV-005.1 LOCAL COMPLETION RESULT'
    Add-Line 'Grace has one durable identity and an explicit PostgreSQL-backed authority contract.' Green
    Add-Line 'Unauthorized state-change attempts are rejected by contract tests and live acceptance.' Green
    Add-Line 'Conversation text does not create authority.' Green
    Add-Line 'Diagnostics and Cookbook guidance are included in the slice.' Green
    Add-Line 'No objective/stage engine, automatic enqueue, provider dispatch, roadmap completion, commit, or push was performed.' Green
    Add-Line 'RV-005.1 is locally acceptance-complete. Next stage: exact-scope publication.' Green

    Save-Report
}
catch {
    Add-Section 'RV-005.1 INSTALLER BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'No commit or push was performed.' Yellow
    Save-Report
    throw
}
