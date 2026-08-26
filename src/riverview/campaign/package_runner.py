"""RUN-005A package-engineer execution and package-boundary acceptance loop.

The loop is intentionally adapter based: package-specific execution, repair,
local verification, candidate creation, and independent acceptance remain
outside the lifecycle store.  The store owns the durable package projection
and ordered repair ledger, so restart does not depend on process memory.
"""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import UUID

from .lifecycle import CampaignLifecycleStore, DefectInput, LifecycleGateError

PACKAGE_CHECKPOINT = "RIV-CAM-005A"


@dataclass(frozen=True, slots=True)
class PackageDefect:
    """One independently observable package failure and its bounded evidence."""

    defect: DefectInput
    root_cause_key: str
    checkpoint: str
    failing_command: str
    stdout_ref: str
    stderr_ref: str
    root_cause: str

    def __post_init__(self) -> None:
        if not self.root_cause_key.strip() or not self.checkpoint.strip() or not self.root_cause.strip():
            raise ValueError(f"{PACKAGE_CHECKPOINT}-0001: defect root-cause evidence is incomplete.")
        if len(self.root_cause_key) > 256 or len(self.checkpoint) > 256:
            raise ValueError(f"{PACKAGE_CHECKPOINT}-0002: defect root-cause evidence exceeds its bound.")


@dataclass(frozen=True, slots=True)
class PackagePass:
    defects: tuple[PackageDefect, ...] = ()
    verification: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RepairResult:
    repaired: bool
    changed_paths: tuple[str, ...] = ()
    description: str = ""
    verification: str = ""


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_ref: str
    version_hash: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AcceptanceResult:
    accepted: bool
    defects: tuple[PackageDefect, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class PackageRunOutcome:
    state: str
    package_run_id: UUID
    candidate: Candidate | None = None
    ledger_entries: int = 0
    acceptance_dispatches: int = 0
    reason: str = ""


class PackageExecutor(Protocol):
    def execute(self, *, worktree_ref: str, repair_generation: int) -> PackagePass: ...

    def repair(self, defect: PackageDefect, *, worktree_ref: str, repair_generation: int) -> RepairResult: ...

    def verify_repair(self, defect: PackageDefect, repair: RepairResult, *, worktree_ref: str) -> bool: ...

    def full_verify(self, *, worktree_ref: str, repair_generation: int) -> PackagePass: ...

    def create_candidate(self, *, worktree_ref: str, repair_generation: int) -> Candidate: ...


class IndependentAcceptance(Protocol):
    def __call__(self, candidate: Candidate, *, worktree_ref: str) -> AcceptanceResult: ...


class PackageEngineerLoop:
    """Own bounded package repair until one final independent acceptance gate."""

    def __init__(self, lifecycle: CampaignLifecycleStore, *, objective_id: UUID, stage_id: UUID,
                 worktree_ref: str, executor: PackageExecutor,
                 independent_acceptance: IndependentAcceptance,
                 max_repairs_per_root: int = 3, max_package_passes: int = 100) -> None:
        if max_repairs_per_root < 1 or max_package_passes < 1:
            raise ValueError(f"{PACKAGE_CHECKPOINT}-0003: repair bounds are invalid.")
        self.lifecycle = lifecycle
        self.objective_id = objective_id
        self.stage_id = stage_id
        self.worktree_ref = str(Path(worktree_ref))
        self.executor = executor
        self.independent_acceptance = independent_acceptance
        self.max_repairs_per_root = max_repairs_per_root
        self.max_package_passes = max_package_passes

    def run(self) -> PackageRunOutcome:
        package_run_id = self.lifecycle.begin_package_run(
            objective_id=self.objective_id, stage_id=self.stage_id, worktree_ref=self.worktree_ref,
        )
        projection = self.lifecycle.package_run(stage_id=self.stage_id) or {}
        # Terminal acceptance is durable package state.  Inspect it before
        # touching the package adapter: a new process must not replay
        # engineering, regenerate a candidate, or dispatch another validator.
        if projection.get("state") == "accepted":
            candidate = self._candidate_from_projection(projection, require_dispatch=True)
            return self._outcome(
                package_run_id, "accepted", int(projection.get("acceptance_dispatch_count") or 0),
                candidate=candidate,
            )
        if projection.get("state") == "awaiting_independent_acceptance":
            # The dispatch is durable, but its validator result may arrive in a
            # different process.  Waiting is a resume state, not an invitation
            # to replay engineering or dispatch a second validator.
            candidate = self._candidate_from_projection(projection, require_dispatch=True)
            return self._outcome(
                package_run_id, "awaiting_independent_acceptance",
                int(projection.get("acceptance_dispatch_count") or 0), candidate=candidate,
            )
        if projection.get("state") == "candidate_ready":
            # A crash after durable candidate creation but before dispatch can
            # resume at the one remaining atomic boundary.
            candidate = self._candidate_from_projection(projection, require_dispatch=False)
            acceptance_dispatches = self.lifecycle.dispatch_package_acceptance(
                package_run_id=package_run_id, candidate_ref=candidate.candidate_ref,
                candidate_version_hash=candidate.version_hash,
                verification=dict(projection.get("internal_verification") or {}),
            )
            result = self.independent_acceptance(candidate, worktree_ref=self.worktree_ref)
            if result.accepted:
                self.lifecycle.record_package_acceptance(package_run_id=package_run_id, accepted=True)
                return self._outcome(package_run_id, "accepted", acceptance_dispatches, candidate=candidate)
            self.lifecycle.record_package_acceptance(package_run_id=package_run_id, accepted=False, reason=result.reason)
            # Continue below only after the validator has supplied structured
            # defects; the package engineer owns the next repair pass.
            if not result.defects:
                reason = f"{PACKAGE_CHECKPOINT}-0006: independent validator failed without structured defects."
                self.lifecycle.update_package_run(package_run_id=package_run_id, state="escalated", last_error=reason)
                return self._outcome(package_run_id, "escalated", acceptance_dispatches, reason)
            generation = int(projection.get("repair_generation") or 0) + 1
            root_attempts = self._root_attempts(package_run_id)
            escalation = self._repair_all(package_run_id, result.defects, generation, root_attempts)
            if escalation is not None:
                self.lifecycle.update_package_run(package_run_id=package_run_id, state="escalated", last_error=escalation)
                return self._outcome(package_run_id, "escalated", acceptance_dispatches, escalation)
            self.lifecycle.update_package_run(package_run_id=package_run_id, state="verifying", repair_generation=generation)
            projection = self.lifecycle.package_run(stage_id=self.stage_id) or {}
        generation = int(projection.get("repair_generation") or 0)
        acceptance_dispatches = int(projection.get("acceptance_dispatch_count") or 0)
        root_attempts = self._root_attempts(package_run_id)
        candidate: Candidate | None = None

        for _ in range(self.max_package_passes):
            self.lifecycle.update_package_run(package_run_id=package_run_id, state="executing", repair_generation=generation)
            package_pass = self.executor.execute(worktree_ref=self.worktree_ref, repair_generation=generation)
            if not isinstance(package_pass, PackagePass):
                raise LifecycleGateError(f"{PACKAGE_CHECKPOINT}-0004: package executor returned an invalid pass.")
            if package_pass.defects:
                self.lifecycle.update_package_run(package_run_id=package_run_id, state="repairing")
                escalation = self._repair_all(package_run_id, package_pass.defects, generation, root_attempts)
                if escalation is not None:
                    self.lifecycle.update_package_run(package_run_id=package_run_id, state="escalated", last_error=escalation)
                    return self._outcome(package_run_id, "escalated", acceptance_dispatches, escalation)
                generation += 1
                self.lifecycle.update_package_run(package_run_id=package_run_id, state="verifying", repair_generation=generation)
                full = self.executor.full_verify(worktree_ref=self.worktree_ref, repair_generation=generation)
                if full.defects:
                    # Full verification findings are deliberately fed back through
                    # the same ledger/repair path rather than silently discarded.
                    escalation = self._repair_all(package_run_id, full.defects, generation, root_attempts)
                    if escalation is not None:
                        self.lifecycle.update_package_run(package_run_id=package_run_id, state="escalated", last_error=escalation)
                        return self._outcome(package_run_id, "escalated", acceptance_dispatches, escalation)
                    generation += 1
                continue

            self.lifecycle.update_package_run(package_run_id=package_run_id, state="verifying", internal_verification=package_pass.verification)
            full = self.executor.full_verify(worktree_ref=self.worktree_ref, repair_generation=generation)
            if full.defects:
                escalation = self._repair_all(package_run_id, full.defects, generation, root_attempts)
                if escalation is not None:
                    self.lifecycle.update_package_run(package_run_id=package_run_id, state="escalated", last_error=escalation)
                    return self._outcome(package_run_id, "escalated", acceptance_dispatches, escalation)
                generation += 1
                continue

            candidate = self.executor.create_candidate(worktree_ref=self.worktree_ref, repair_generation=generation)
            self.lifecycle.record_package_candidate(
                package_run_id=package_run_id, candidate_ref=candidate.candidate_ref,
                candidate_version_hash=candidate.version_hash,
                verification={"package_pass": package_pass.verification, "full_pass": full.verification},
            )
            acceptance_dispatches = self.lifecycle.dispatch_package_acceptance(
                package_run_id=package_run_id, candidate_ref=candidate.candidate_ref,
                candidate_version_hash=candidate.version_hash,
                verification={"package_pass": package_pass.verification, "full_pass": full.verification},
            )
            result = self.independent_acceptance(candidate, worktree_ref=self.worktree_ref)
            if not isinstance(result, AcceptanceResult):
                raise LifecycleGateError(f"{PACKAGE_CHECKPOINT}-0005: independent acceptance returned an invalid result.")
            if result.accepted:
                self.lifecycle.record_package_acceptance(package_run_id=package_run_id, accepted=True)
                return self._outcome(package_run_id, "accepted", acceptance_dispatches, candidate=candidate)

            self.lifecycle.record_package_acceptance(package_run_id=package_run_id, accepted=False, reason=result.reason)
            if not result.defects:
                reason = f"{PACKAGE_CHECKPOINT}-0006: independent validator failed without structured defects."
                self.lifecycle.update_package_run(package_run_id=package_run_id, state="escalated", last_error=reason)
                return self._outcome(package_run_id, "escalated", acceptance_dispatches, reason)
            self.lifecycle.update_package_run(package_run_id=package_run_id, state="repairing", repair_generation=generation + 1)
            escalation = self._repair_all(package_run_id, result.defects, generation + 1, root_attempts)
            if escalation is not None:
                self.lifecycle.update_package_run(package_run_id=package_run_id, state="escalated", last_error=escalation)
                return self._outcome(package_run_id, "escalated", acceptance_dispatches, escalation)
            generation += 1

        reason = f"{PACKAGE_CHECKPOINT}-0007: package pass bound exhausted without acceptance."
        self.lifecycle.update_package_run(package_run_id=package_run_id, state="escalated", last_error=reason)
        return self._outcome(package_run_id, "escalated", acceptance_dispatches, reason)

    def _repair_all(self, package_run_id: UUID, defects: tuple[PackageDefect, ...], generation: int,
                    root_attempts: dict[str, int]) -> str | None:
        for defect in defects:
            count = root_attempts.get(defect.root_cause_key, 0) + 1
            root_attempts[defect.root_cause_key] = count
            ledger_id = self.lifecycle.record_package_ledger_entry(
                package_run_id=package_run_id, objective_id=self.objective_id, stage_id=self.stage_id,
                root_cause_key=defect.root_cause_key, checkpoint=defect.checkpoint,
                failing_command=defect.failing_command, observed_behavior=defect.defect.observed_behavior,
                expected_behavior=defect.defect.expected_behavior, stdout_ref=defect.stdout_ref,
                stderr_ref=defect.stderr_ref, evidence_ref=defect.defect.evidence_ref,
                root_cause=defect.root_cause,
                acceptance_criterion_ref=defect.defect.acceptance_criterion_ref,
                severity=defect.defect.severity, required_repair=defect.defect.required_repair,
                repair_generation=generation,
            )
            if count > self.max_repairs_per_root:
                self.lifecycle.update_package_ledger_entry(
                    ledger_id=ledger_id, status="escalated", repair_description="",
                    changed_paths=(), repair_verification="repair bound exceeded", verification_result="failed",
                )
                return f"{PACKAGE_CHECKPOINT}-0008: root defect {defect.root_cause_key} exceeded repair bound."
            repair = self.executor.repair(defect, worktree_ref=self.worktree_ref, repair_generation=generation)
            if not repair.repaired:
                self.lifecycle.update_package_ledger_entry(
                    ledger_id=ledger_id, status="escalated", repair_description=repair.description,
                    changed_paths=repair.changed_paths, repair_verification=repair.verification,
                    verification_result="failed",
                )
                return f"{PACKAGE_CHECKPOINT}-0009: repair failed for root defect {defect.root_cause_key}."
            verified = self.executor.verify_repair(defect, repair, worktree_ref=self.worktree_ref)
            self.lifecycle.update_package_ledger_entry(
                ledger_id=ledger_id, status="repaired" if verified else "escalated",
                repair_description=repair.description, changed_paths=repair.changed_paths,
                repair_verification=repair.verification, verification_result="passed" if verified else "failed",
            )
            if not verified:
                return f"{PACKAGE_CHECKPOINT}-0010: local repair verification failed for {defect.root_cause_key}."
        return None

    def _root_attempts(self, package_run_id: UUID) -> dict[str, int]:
        attempts: dict[str, int] = {}
        for entry in self.lifecycle.package_ledger(package_run_id=package_run_id):
            key = str(entry["root_cause_key"])
            attempts[key] = attempts.get(key, 0) + 1
        return attempts

    def _outcome(self, package_run_id: UUID, state: str, dispatches: int,
                 reason: str = "", candidate: Candidate | None = None) -> PackageRunOutcome:
        return PackageRunOutcome(state, package_run_id, candidate,
                                 len(self.lifecycle.package_ledger(package_run_id=package_run_id)),
                                 dispatches, reason)

    @staticmethod
    def _candidate_from_projection(projection: dict[str, Any], *, require_dispatch: bool) -> Candidate:
        candidate_ref = projection.get("candidate_ref")
        version_hash = projection.get("candidate_version_hash")
        dispatch_count = projection.get("acceptance_dispatch_count")
        dispatched_ref = projection.get("acceptance_candidate_ref")
        dispatched_version = projection.get("acceptance_candidate_version_hash")
        if (not isinstance(candidate_ref, str) or not candidate_ref.strip() or
                not isinstance(version_hash, str) or not version_hash.strip()):
            raise LifecycleGateError(f"{PACKAGE_CHECKPOINT}-0011: package candidate evidence is malformed.")
        if isinstance(dispatch_count, bool) or not isinstance(dispatch_count, int) or dispatch_count < 0:
            raise LifecycleGateError(f"{PACKAGE_CHECKPOINT}-0012: package acceptance dispatch count is malformed.")
        if require_dispatch and (dispatch_count < 1 or dispatched_ref != candidate_ref or dispatched_version != version_hash):
            raise LifecycleGateError(f"{PACKAGE_CHECKPOINT}-0013: package acceptance evidence is incomplete or mismatched.")
        return Candidate(candidate_ref, version_hash, dict(projection.get("internal_verification") or {}))


def _load_callable(spec: str) -> Any:
    module_name, separator, function_name = spec.partition(":")
    if not separator or not module_name or not function_name:
        raise SystemExit(f"{PACKAGE_CHECKPOINT}-CLI: callable must use module:function syntax.")
    return getattr(importlib.import_module(module_name), function_name)


def main(argv: list[str] | None = None) -> int:
    """PowerShell-facing adapter entrypoint.

    Package-specific adapters are explicit so the runner never guesses a
    provider, model, identity, or repair authority from shell text.
    """
    parser = argparse.ArgumentParser(description="Run one bounded package-engineer self-repair loop.")
    parser.add_argument("--objective-id", required=True, type=UUID)
    parser.add_argument("--stage-id", required=True, type=UUID)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--adapter", required=True, help="module:function returning (executor, acceptance)")
    parser.add_argument("--max-repairs-per-root", type=int, default=3)
    args = parser.parse_args(argv)
    executor, acceptance = _load_callable(args.adapter)(args)
    outcome = PackageEngineerLoop(
        CampaignLifecycleStore(), objective_id=args.objective_id, stage_id=args.stage_id,
        worktree_ref=args.worktree, executor=executor, independent_acceptance=acceptance,
        max_repairs_per_root=args.max_repairs_per_root,
    ).run()
    print(json.dumps({"state": outcome.state, "package_run_id": str(outcome.package_run_id),
                      "candidate": outcome.candidate.candidate_ref if outcome.candidate else None,
                      "ledger_entries": outcome.ledger_entries,
                      "acceptance_dispatches": outcome.acceptance_dispatches,
                      "reason": outcome.reason}))
    return 0 if outcome.state == "accepted" else 2


if __name__ == "__main__":
    raise SystemExit(main())
