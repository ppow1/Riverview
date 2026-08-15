# RIV-CAP-0002 — Lane ownership and result reconciliation

SYMPTOM: Two bounded executions request the same mutable path, or a provider result
cannot be accepted as the requested objective result.

LIKELY BOUNDARY: `lane_path_owners`, execution scope, correlation, or the typed
reconciliation record.

SAFE DIAGNOSTIC: Inspect active `execution_lanes` and `lane_path_owners`; compare the
result execution/correlation, changed paths, validation evidence, commit SHA, and
requested acceptance envelope.

EXPECTED HEALTHY RESULT: A second owner is rejected while the first lane is active;
release permits a deliberate reacquisition; accepted results retain one execution,
one correlation, and one reconciliation record.

KNOWN FAILURE: `RIV-CAP-0003` rejects invalid lane input, active path conflicts, or
wrong-owner release. `RIV-REC-0001` rejects invalid reconciliation decisions, and
the database foreign key rejects results for unknown execution envelopes.

REPAIR: Release only the verified owner, or repair the result's bounded identity and
evidence. Never steal a live path or accept a provider's prose as completion.

VERIFY: Re-run the conflict/release probe and inspect the durable lane and
reconciliation rows; confirm no duplicate logical owner or result.

DO NOT: use overlapping lanes, bypass correlation, delete historical results, or
merge conflicting provider output by consensus alone.

EVIDENCE: `execution_lanes`, `lane_path_owners`, `reconciliation_records`, River
correlation, and the source publication record.
