# Riverview Standalone Root Reconciliation — 2026-08-26

Status: CANDIDATE VERIFIED; CONTROLLED CUTOVER PENDING

## Selected candidate

- Candidate root: `A:\Riverview\standalone`
- Git remote: `https://github.com/ppow1/Riverview.git`
- Baseline: verified network `origin/main` `ec9075bfec7655fe67e7c4455bfd9c644b2d2d52`
- Candidate branch: `main`
- Candidate reconciliation commit: `f87064204fa179e26a0c7ae3d6541ec67419a074` (final local candidate SHA).
- Previous live checkout retained unchanged: `A:\Riverview\repo`
- No historical checkout was deleted, cleaned, reset, moved, or rewritten.

## Reconciliation inputs

1. Current GitHub-main checkout `A:\theestate\Riverview`, including preserved
   Grace/Jessica changes and Phase 0 authority corrections.
2. Live checkout `A:\Riverview\repo`, detached at
   `c29d6256e05bd0c98188a5113346cb3895f8259a`.
3. Live checkout tracked spatial/operator changes were compared and applied
   selectively to the candidate:
   - `src/riverview/operator/lan_spatial.py`
   - `src/riverview/spatial/prototype.py`
4. All 11 live untracked paths were copied without modification under:
   `reconciliation/preserved-runtime-repo-2026-08-26/`.
5. Preservation manifest:
   `reconciliation/RUNTIME_ARTIFACT_PRESERVATION_MANIFEST.json`.
6. Exact tracked runtime diff:
   `reconciliation/reconciliation-runtime-spatial.patch`.

## Classification

- Current-main documents/source/tests: preserved in candidate and included in
  the candidate reconciliation commit.
- Spatial/operator tracked modifications: unique valuable runtime work;
  selectively applied to the candidate after clean patch application.
- Spatial GLB and dated spatial reports/checkpoints: preserved under the
  reconciliation preservation area pending later reviewed classification.
- Promotion/synchronization scripts: preserved under the reconciliation
  preservation area; not executed during this tranche.
- Runtime-generated logs/status/locks: not copied into candidate source state.
- Old runtime checkout: retained intact as rollback/reference evidence.

## Runtime changes prepared

- Candidate launcher defaults to its own root via its script location and sets
  `RIVERVIEW_REPOSITORY`, `RIVERVIEW_RUNTIME_REGISTRY`, and a nonsecret launch
  mechanism marker.
- Runtime status now reports repository root, branch/ref, Python executable,
  launch mechanism, and Git SHA.
- Operator `/health` now reports source root, branch/ref, Python executable,
  provider/model endpoint identity, database target without credentials, launch
  mechanism, and source SHA.
- Runtime process adoption now rejects same-command processes whose working
  directory belongs to another checkout, preventing the candidate supervisor
  from adopting old-root services.

## Duplicate-process finding

The existing task owns one supervisor process tree rooted at the old checkout,
but the old supervisor has multiple same-command Relay/CME-related processes
and reports `duplicate-process` for Relay. Process evidence shows repeated
children under the old supervisor and a two-process Python launcher wrapper.
This is a real ownership defect or stale process accumulation, not a reason to
silently kill processes. Controlled cutover must stop the old task/service tree,
verify old-root process disappearance, then start exactly one candidate
supervisor and read back its status.

## Database continuity

The candidate uses the existing configured Riverview PostgreSQL metadata and
DPAPI credential boundary. No database migration, history, or record was
changed. PostgreSQL compatibility must be verified after candidate startup by
health/status and a read-only connection/schema check.

## Verification completed

- Candidate imports and compilation passed.
- Candidate bounded suite: 57 passed.
- Candidate source SHA before final provenance patch:
  `4fe0118670a0cf7540a4104d13582ea862a8692f`.
- Candidate is derived from current network `origin/main` and contains the
  preserved implementation increment plus selected spatial/runtime work.

## Cutover procedure

1. Commit candidate provenance/ownership repair and this report.
2. Update the existing `\\Riverview Runtime Supervisor` task to invoke the
   candidate launcher without changing unrelated task policy.
3. End the old task through the controlled task boundary; do not delete or
   clean the old checkout.
4. Verify old-root Riverview processes have exited and old runtime status is
   retained as rollback evidence.
5. Start the task once and verify candidate status, one supervisor owner,
   service roots, ports, provider/model, and PostgreSQL compatibility.
6. Exercise Operator `/health`, authenticated runtime status, Grace chat, and
   Jessica surface from the candidate.
7. If cutover fails, restore task invocation to the old launcher only through a
   bounded rollback action; preserve all evidence.

## Acceptance state

This is technical reconciliation preparation, not institutional acceptance.
Grace cognition and Jessica live behavioral acceptance remain separate and are
not claimed by this report.

No 3060, small-brain/big-brain, shared-cognition, or escalation optimization
work is included.
