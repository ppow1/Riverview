# Riverview Standalone Root Reconciliation — 2026-08-26

Status: TECHNICALLY VERIFIED; STEWARD ACCEPTANCE PENDING

## Selected candidate

- Candidate root: `A:\Riverview\standalone`
- Git remote: `https://github.com/ppow1/Riverview.git`
- Initial reconciliation baseline: `ec9075bfec7655fe67e7c4455bfd9c644b2d2d52`
- Candidate branch: `main`
- Candidate source SHA at final runtime verification: `fcc0d43b7c5ec96210078d13ef18cdeb79a04415`.
- Network `origin/main`: `cb4a203274fd0d543ae5140cc036190a4625828c`; candidate is 13 commits ahead and 1 commit behind by ancestry, with the upstream launch-hints content already represented in the candidate tree.
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

## Final settled runtime proof — 2026-08-26

After the controlled restart and a settled interval:

- one `Riverview Runtime Supervisor` task instance owns the runtime;
- all managed services are running from `A:\\Riverview\\standalone`;
- CME has one logical launcher/child topology and Relay has one logical
  launcher/child topology; Windows venv launcher children are not counted as
  separate service instances;
- no managed Riverview process has working directory `A:\\Riverview\\repo`;
- Operator `/health` and authenticated `/api/runtime/status` report the same
  root, branch, Python environment, and SHA as the candidate runtime;
- PostgreSQL read-only connectivity succeeds as `riverview_app` to database
  `riverview` on PostgreSQL 18.6;
- `A:\\Riverview\\repo` remains preserved as rollback/reference evidence.

The runtime ownership boundary is technically settled, subject to later
Steward acceptance of the standalone-root transition. The Supervisor now
represents CME event replay as explicit bounded recovery (`starting`) while
the process remains alive and advancing, instead of terminating CME on a
transient stale heartbeat.

## HOME cognition materialization and live proof — 2026-08-27

The Steward-authorized projection was materialized through existing continuity
APIs using deterministic identities and accepted evidence
`9d2af4f5-bc47-5b60-a50b-bd3ca5641aa2`:

- Grace occupant: `40f225e2-6f58-55d2-b862-eab7d95700d8`;
- Operations office: `158973ef-8907-53ed-b0fc-68fb82c30579`;
- active occupancy: `ea157c2a-4a18-5a37-92d5-7f0622a6aabc`;
- HOME implementation: `77fb672c-eb12-5628-aeb6-f5ffa7fbae2e`;
- active HOME binding: `029ac02f-e826-5c16-af73-c7f8e764f2c4`;
- accepted residency/state references are durable and provenance-backed.

The production `PostgresAuthoritativeGraceStateSource` validates the projection,
assembles bounded `ENGINEERING_REVIEW` context through the existing assembler,
and fails closed on missing, stale, or mismatched state. Operator production
composition now invokes the existing `HomeCognitionService`; no direct Grace
provider fallback is used when HOME is enabled.

Live Operator proof at candidate SHA `fcc0d43...` returned HTTP 200 with
`home_cognition=true`, tier `HOME_COGNITION`, cognition/session/request/
correlation IDs, Ollama/Qwen provider binding, `local:RTX4090` resource,
HOME provenance and observation references, `authority_scope=[return:advisory]`,
and `role_authority_expanded=false`. A second live turn preserved the same
resident session and advanced bounded history from two to four turns.
