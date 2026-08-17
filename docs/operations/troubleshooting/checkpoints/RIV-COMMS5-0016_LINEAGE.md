# RIV-COMMS5-0016 — Comms5 lifecycle lineage projection

## Symptom

Seed status or lineage omits cancellation/supersession history, points to the
wrong replacement, or invents objective/work progression.

## Probe

Compare `seed_status`, `seed_lineage`, recent submissions, lifecycle events,
River facts, and the objective projection using only bounded metadata.

## Repair

Project the canonical seed row and lifecycle ledger. Represent absent objective,
work, or result state as `not_created` or `not_observed`; do not create a second
status machine.

## Verification

Check draft, cancelled, superseded, and promoted specimens through Comms5 after
service restart and confirm no protected payloads are returned.
