# RUN-002R Repair Report

- **Package:** RUN-002R
- **Role:** C1 repair writer
- **Status:** REPAIR_COMPLETE_READY_FOR_REVALIDATION

## Validator finding repaired

C2 identified one blocking contradiction: RUN-002 derived current phase from
ordered `objective_stages` but section P also required
`objectives.active_stage_id`, creating two possible authorities.

## Targeted correction

Sections changed: A.2, A.3, P (minimal physical database changes), and R
(acceptance test matrix). The current-phase wording was aligned across the
existing A/I/Q definitions; no new state model was added.

The authoritative current-phase rule is: current phase is derived
deterministically from authoritative `objective_stages` lifecycle/order—the
first ordered `phase_key` containing an incomplete required package. This
derived result, not an objective-level field, drives phase progress, lifecycle
evaluation, dashboard projections, and restart/reconciliation behavior.

`objectives.active_stage_id` is **NOT NEEDED / DEFERRED**. No separately
writable projection or cache is introduced.

Acceptance test 31 proves that authoritative objective-stage state has one
current-phase authority and that no objective-level active-stage value can
contradict it or independently advance campaign lifecycle.

No unrelated RUN-002 architecture was changed. No runtime code or migration
was implemented.
