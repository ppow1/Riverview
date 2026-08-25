# RUN-002RV — Independent Repair Revalidation

Package: RUN-002RV  
Role: C2 independent repair revalidator  
Original validation: `docs/codex-reports/seat-2/RUN-002V-validation.md`  
Repaired specification: `docs/codex-reports/seat-1/RUN-002-campaign-runner-specification.md`  
Repair report: `docs/codex-reports/seat-1/RUN-002R-repair-report.md`

## Verdict

## PASS

The original RUN-002V blocking defect is resolved. RUN-002 now has one
authoritative current-phase rule and is ready to serve as the basis for RUN-003
implementation.

## Authoritative current-phase rule — VERIFIED

The repaired specification states that the current phase is the `phase_key` of
the first ordered phase containing an incomplete required package. It is
deterministically derived from authoritative `objective_stages.sort_order`,
`phase_key`, and lifecycle state.

The same rule is consistent across:

- section A.2 campaign/objective model;
- section A.3 stage/package model;
- section I.2 current-phase progress;
- section Q state-transition semantics;
- section N restart/reconciliation behavior;
- section O one-GO operation; and
- section R acceptance testing.

## `objectives.active_stage_id` disposition — VERIFIED

`objectives.active_stage_id` is explicitly `NOT NEEDED / DEFERRED` in section P.
The repaired specification states that no objective-level active-stage value,
writable projection, or cache is introduced.

It is no longer specified as:

- authoritative lifecycle state;
- independently writable phase state;
- required database state;
- dashboard authority;
- restart/resume authority; or
- transition authority.

The remaining references to `active_stage_id` are disposition statements and
the acceptance test proving that no such value can contradict or independently
advance lifecycle. They do not create a second source of truth.

## Residual contradiction search — CLEAR

The repaired specification was searched for `active_stage_id`, active/current
stage and phase terminology, phase authority/progress, objective stages,
lifecycle, and transitions.

The results contain only the single derived current-phase rule, its consistent
dashboard/progress/state uses, and the explicit deferred/not-needed disposition
of `objectives.active_stage_id`. No residual statement restores an independent
objective-level current-phase authority.

## Directly affected sections

### Campaign/objective model — PASS

Objectives remain the campaign aggregate and objective stages remain the sole
package/dependency model. No duplicate phase-state model is introduced.

### Overall and current-phase progress — PASS

Overall progress remains derived from accepted required packages. Current-phase
progress is derived from the first ordered phase with incomplete required work.

### Dashboard projection — PASS

The dashboard uses the derived phase result. No objective-level active-stage
field is required for dashboard authority.

### State transitions — PASS

Lifecycle evaluation and downstream eligibility use the derived phase result.
The repaired matrix includes acceptance test 31 for the one-authority rule.

### Crash/restart/resume — PASS

Restart and reconciliation rebuild from PostgreSQL objective-stage lifecycle and
ordering state rather than a separately stored active-stage value.

### One-GO operation — PASS

Package eligibility and phase progression remain derivable from authoritative
stage/dependency state without an operator-maintained phase field.

### Physical database recommendations — PASS

Section P removes `active_stage_id` from required objective extensions and
places it under explicit deferred/not-needed items. No migration or runtime
implementation was introduced by the repair.

### Acceptance-test matrix — PASS

Test 31 states that given authoritative objective-stage lifecycle/order, the
current phase is deterministic and no separately writable objective-level
active-stage value can contradict it or independently advance campaign
lifecycle.

## Repair scope — VERIFIED

The specification diff is limited to:

- clarifying the derived current-phase wording in A.2 and A.3;
- removing `active_stage_id` from required physical changes;
- explicitly deferring it as not needed; and
- adding the corresponding acceptance test.

The repair report confirms no runtime code, migration, or unrelated RUN-002
architecture was changed. The actual diff confirms that scope.

## Original RUN-002V defect

RESOLVED

## Implementation readiness

READY_FOR_RUN-003
