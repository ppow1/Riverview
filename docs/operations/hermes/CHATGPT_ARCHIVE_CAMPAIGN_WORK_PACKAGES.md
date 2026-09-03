# ChatGPT Business Archive Campaign - Work Packages and Dependency Plan

Status: Steward-authorized execution roadmap for Hermes / Campaign Runner
Date: 2026-09-03
Parent specification: `docs/operations/hermes/CHATGPT_ARCHIVE_CAMPAIGN_SPECIFICATION.md`

## 1. Execution model

This roadmap translates the A-N campaign phases into bounded Campaign Runner work packages.

The package graph is intentionally finer than the fourteen user-facing phases. Campaign progress shown to the Steward should still aggregate to A-N, while Campaign Runner retains package-level writer/validator/repair/revalidation state.

Repository-changing engineering packages use the existing Riverview/Hermes/Codex path and require independent validation. Accepted batch/corpus processing should preferentially use deterministic local code and authorized local AI resources instead of consuming Codex capacity unnecessarily.

The campaign operator surface is an early dependency because the Steward must be able to observe, pause, resume, and clean-stop long autonomous execution.

## 2. Package conventions

Package IDs use `CAA-WP-####`.

Each package records:

- phase;
- purpose;
- dependencies;
- execution class;
- preferred resource class;
- allowed paths/data boundary;
- outputs;
- acceptance criteria;
- notification behavior.

`preferred resource` is not an unconditional hard pin unless the package explicitly requires a unique capability.

Audio notification is permitted only for `STEWARD_REQUIRED` boundaries or explicitly listed major campaign waypoints.

## 3. Dependency overview

```text
CAA-WP-0001 Campaign operator/control surface
        |
        +--------------------------+
        |                          |
CAA-WP-0100 Capture completion     |
        |                          |
CAA-WP-0200 Baseline snapshot <----+
        |
CAA-WP-0300 Incremental reconciler
        |
CAA-WP-0400 Normalized schema
        |
        +-------------------+
        |                   |
CAA-WP-0500 Media mapper    |
        |                   |
CAA-WP-0600 Static renderer |
        |                   |
CAA-WP-0700 Reconstruction validator
        |
CAA-WP-0800 PDF generator
        |
CAA-WP-0900 PDF semantic validator
        |
        +-------------------------+
        |                         |
CAA-WP-1000 Search/index          |
CAA-WP-1100 Archive viewer <------+ 
        |
CAA-WP-1200 Codex continuity preservation
        |
CAA-WP-1300 ChatGPT-side archival
        |
CAA-WP-1400 Final cutoff reconciliation
```

Supporting fixture and batch packages branch from the accepted schema/media/reconstruction machinery.

## 4. Phase 0 - campaign operations surface

### CAA-WP-0001 - Campaign status/control projection

Phase: preflight / operations

Purpose: implement the small persistent operator surface required before multi-day autonomous execution.

Dependencies:

- parent campaign specification accepted as execution basis;
- existing Campaign Runner/PostgreSQL status fields available;
- existing Riverview status/Operator projection inspected before adding a new projection.

Execution class: bounded engineering.

Preferred writer resource: Codex C1/C2/C3 selected by current resource policy.

Independent validator: different worker identity; preferably different Codex seat.

Authorized work:

- inspect and extend existing read projection/status surface;
- implement a small Windows/PowerShell operator monitor if that is the least-complex first surface;
- implement persisted pause/resume/clean-stop control seam using existing Campaign Runner lifecycle;
- add tests for truthful state projection and control behavior.

Required display:

- campaign state;
- phase A-N and title;
- phase fraction and percentage;
- current package/role/resource;
- package counts;
- bounded corpus fractions plus percentages;
- heartbeat age;
- last meaningful progress age;
- retry/recovery state;
- Steward-required state;
- next expected action;
- last major waypoint.

Controls:

- `P` safe-boundary pause;
- `R` persisted resume;
- `X` clean restartable stop;
- `PAUSE_PENDING` must remain visible until safe pause is actually achieved.

Acceptance:

1. surface reads authoritative persisted state rather than independent local truth;
2. percentage shown only when denominator is legitimate;
3. heartbeat and meaningful progress are distinct;
4. P/R/X behavior survives process restart and does not duplicate work;
5. no visible full-screen flash every few seconds under normal refresh;
6. independent validator proves state/control semantics.

Notification: none for ordinary operation. Speak only if this package itself becomes blocked and needs Steward action.

## 5. Phase A - capture completion

### CAA-WP-0100 - Finish current conversation evacuation

Phase: A

Purpose: finish the currently known 534-conversation preservation lane.

Current checkpoint at roadmap publication:

- 520 / 534 (97.4%) locally saved;
- 14 / 534 (2.6%) remaining;
- paused for provider rate-limit cooldown.

Execution class: bounded operations / reconciliation.

Preferred resource: existing ChatGPT archive runner and authenticated browser profiles; do not replace working machinery during the final evacuation unless a proven defect requires repair.

Acceptance:

1. runner reaches all currently discoverable conversations;
2. every conversation is preserved or listed as explicit exception;
3. rate-limit failures remain visible evidence;
4. final live-vs-local reconciliation is performed;
5. output inventory becomes eligible for Baseline Snapshot 1.

Major waypoint notification: YES when all original known conversations are preserved or the only remainder is a Steward-visible explicit exception list.

## 6. Phase B - baseline snapshot

### CAA-WP-0200 - Baseline manifest implementation

Dependencies: CAA-WP-0100 accepted; CAA-WP-0001 accepted or available enough to show campaign state.

Execution class: bounded engineering.

Purpose: implement machine-readable immutable Baseline Snapshot 1.

Required fields are defined in the parent specification.

Acceptance:

1. manifest is generated from actual archive artifacts;
2. stable conversation IDs are primary identity;
3. source files/artifacts have hashes or equivalent durable fingerprints;
4. exception state is explicit;
5. rerun is deterministic/idempotent;
6. independent validator checks sampled manifest records against actual archive folders.

### CAA-WP-0210 - Freeze Baseline Snapshot 1

Dependencies: CAA-WP-0200 accepted.

Execution class: deterministic corpus operation.

Purpose: generate and persist the first authoritative complete baseline after current evacuation.

Preferred resource: local deterministic code on dev machine.

Acceptance: snapshot file plus summary report and counts reconcile to Phase A evidence.

## 7. Phase C - incremental reconciliation

### CAA-WP-0300 - Incremental live-vs-local reconciler

Dependencies: CAA-WP-0210.

Execution class: bounded engineering.

Purpose: enumerate current live conversation inventory and classify each record against the baseline.

Required classifications:

- `UNCHANGED_PRESERVED`
- `NEW_NEEDS_CAPTURE`
- `UPDATED_NEEDS_REFRESH`
- `ARCHIVED_REMOTE`
- `LOCAL_ONLY_EXPECTED`
- `EXCEPTION`

Acceptance:

1. stable ID based matching;
2. no title-only identity logic;
3. rerun does not recapture unchanged conversations;
4. newly created test conversation is detected as new in fixture/integration test;
5. updated fixture is detected as changed;
6. independent validator verifies classifications.

### CAA-WP-0310 - Incremental capture adapter

Dependencies: CAA-WP-0300.

Purpose: feed only new/changed conversations back through the accepted preservation path.

Acceptance: no duplicate processing of unchanged baseline records; exception and rate-limit behavior remains truthful.

## 8. Phase D - corpus normalization

### CAA-WP-0400 - Normalized conversation schema

Dependencies: CAA-WP-0210.

Execution class: bounded engineering.

Purpose: define canonical normalized JSON/data representation used by all downstream systems.

Acceptance:

1. preserves conversation identity, ordered messages, roles, timestamps, stable message/turn IDs where available, media slots, attachments, links, code and provenance;
2. separates preservation facts from derived enrichment;
3. versioned schema;
4. representative fixture conversion succeeds;
5. independent validator checks ordering/role/text fidelity against transcripts.

### CAA-WP-0410 - Representative fixture corpus

Dependencies: CAA-WP-0400 schema draft may begin before final acceptance, but fixture use as validation basis requires schema acceptance.

Purpose: create a small privacy-reviewed fixture set for GitHub/Codex engineering.

Cases:

- short text-only;
- long virtualized conversation;
- one pasted image;
- multiple images in one user turn;
- file attachment;
- code/table content;
- known pathological legacy PDF;
- ambiguous media mapping;
- missing-share-URL exception.

Acceptance: fixtures reproduce the required failure/success classes without uploading the full private corpus.

### CAA-WP-0420 - Corpus normalization batch processor

Dependencies: CAA-WP-0400 accepted.

Execution class: deterministic corpus processing.

Purpose: convert archive conversations into normalized records in bounded batches.

Preferred resource: local deterministic processing; local text model only if a field requires semantic extraction and that field is explicitly marked derived.

## 9. Phase E - media/file relationship reconstruction

### CAA-WP-0500 - Complete media-ID/object discovery

Dependencies: CAA-WP-0400.

Purpose: finish the existing local forensic discovery into `oaiusercontent` IDs, object filenames, dimensions, manifests, message IDs, and ordering.

Execution class: read-only investigation.

Preferred resource: deterministic local code first; OCTO1 P100 or dev 4090 only for visual tie-breakers.

Acceptance: durable discovery report states which mapping evidence is deterministic and which remains heuristic.

### CAA-WP-0510 - Deterministic media mapper

Dependencies: CAA-WP-0500, CAA-WP-0400.

Execution class: bounded engineering.

Purpose: implement strongest-evidence-first mapping from conversation/message/image slot to saved object.

Acceptance:

1. direct asset/object IDs outrank heuristics;
2. exact dimensions/order/provenance are used mechanically;
3. visual model never overrides stronger deterministic identity evidence;
4. unresolved remains explicit;
5. confidence/evidence provenance stored per mapping;
6. independent validator tests fixture mappings.

### CAA-WP-0520 - Ambiguous visual matching adapter

Dependencies: CAA-WP-0510.

Purpose: add bounded VLM comparison only for candidate sets that deterministic mapping cannot resolve.

Preferred resource:

1. OCTO1 P100 Gemma VLM;
2. dev RTX 4090 if required by capability/throughput;
3. second local model/resource for independent cross-check on low-confidence cases when useful.

Acceptance: visual inference is auditable, bounded to candidate sets, and cannot fabricate unobserved assets.

### CAA-WP-0530 - Media mapping corpus batches

Dependencies: CAA-WP-0510; CAA-WP-0520 when ambiguous cases require it.

Execution class: corpus processing.

Suggested batch size: 25-50 conversations, adjustable by observed artifact density.

Status surface must show `completed / total (percentage)` and unresolved counts.

## 10. Phase F - static conversation reconstruction

### CAA-WP-0600 - Static HTML renderer

Dependencies: CAA-WP-0400, CAA-WP-0510.

Execution class: bounded engineering.

Purpose: generate offline non-virtualized conversation HTML from normalized records and mapped local media.

Acceptance:

1. no dependency on live ChatGPT rendering;
2. no virtual spacer placeholders;
3. both user and assistant turns render in correct order;
4. images/files appear in mapped positions;
5. code/tables/links remain legible;
6. local-archive provenance is clearly labeled;
7. representative fixture output is stable and printable.

### CAA-WP-0610 - Reconstruction corpus batches

Dependencies: CAA-WP-0600 accepted; media mappings available for processed records.

Execution class: deterministic corpus processing.

## 11. Phase G - reconstruction validation

### CAA-WP-0700 - Reconstruction validator

Dependencies: CAA-WP-0600.

Execution class: bounded engineering / validation tooling.

Acceptance checks:

- beginning/end coverage;
- user/assistant coverage;
- order;
- media slot accounting;
- attachment accounting;
- no virtualized placeholders;
- unresolved cases explicit;
- no invented content.

The validator must be mechanically deterministic wherever possible. Semantic/visual AI checks may supplement, not replace, objective checks.

### CAA-WP-0710 - Reconstruction acceptance batches

Dependencies: CAA-WP-0610, CAA-WP-0700.

Purpose: independently validate corpus reconstruction in bounded batches and create repair queues where defects are found.

Major waypoint notification: YES only when the required full corpus reconstruction reaches accepted state, not per batch.

## 12. Phase H - final PDF production

### CAA-WP-0800 - Static reconstruction PDF generator

Dependencies: CAA-WP-0600, CAA-WP-0700.

Execution class: bounded engineering.

Purpose: generate PDF exclusively from accepted/static reconstruction.

Acceptance: no live ChatGPT Share-page print path; deterministic local render; known pathological fixture no longer produces legacy spacer failure.

### CAA-WP-0810 - PDF corpus generation

Dependencies: reconstruction record accepted and CAA-WP-0800 accepted.

Execution class: deterministic corpus processing.

## 13. Phase I - PDF semantic validation

### CAA-WP-0900 - PDF semantic validator

Dependencies: CAA-WP-0800.

Execution class: bounded engineering.

Acceptance:

- PDF parses;
- text coverage samples beginning/middle/end;
- user and assistant content represented;
- normalized source comparison reaches accepted threshold;
- page density/pagination sanity check;
- expected media accounted for;
- existing historical structurally-valid-but-visually-bad PDF fixture is rejected.

### CAA-WP-0910 - PDF validation batches

Dependencies: CAA-WP-0810, CAA-WP-0900.

Purpose: validate final PDFs and generate explicit repair queue.

## 14. Phase J - search and indexing

### CAA-WP-1000 - Exact/full-text index

Dependencies: CAA-WP-0400; can proceed while later reconstruction batches run.

Purpose: searchable exact/message-level corpus.

Preferred implementation: SQLite FTS5 or equivalent lightweight local full-text index unless existing Riverview architecture demonstrates a better canonical fit.

Acceptance: search returns conversation and matching turn/message references; common exact terms are demonstrably retrievable.

### CAA-WP-1010 - Derived tags/entities/concepts

Dependencies: CAA-WP-1000.

Purpose: enrich normalized records without changing preservation truth.

Preferred resources: local text models (OCTO1 3060, dev 4090 as needed) for high-volume semantic extraction after deterministic metadata extraction.

Acceptance: derived fields are provenance-tagged, rerunnable, and removable without damaging archive truth.

### CAA-WP-1020 - Semantic/vector retrieval

Dependencies: CAA-WP-1000; CAA-WP-1010 helpful but not mandatory.

Purpose: concept search where exact wording differs.

Preferred resource: local embeddings on suitable GPU/CPU infrastructure.

Acceptance: test queries retrieve known semantically related fixture conversations without exact phrase overlap.

## 15. Phase K - local archive viewer

### CAA-WP-1100 - Viewer shell and seat navigation

Dependencies: CAA-WP-0400, CAA-WP-1000.

Purpose: master local browsing/search page with account/seat breakdown.

Acceptance: human can browse C1/C2/C3, search, open a reconstructed conversation, and navigate to a matching turn without File Explorer.

### CAA-WP-1110 - Artifact and metadata access

Dependencies: CAA-WP-1100, CAA-WP-0600.

Purpose: expose links to reconstructed HTML, final PDF, transcript, metadata, raw preserved artifacts, and provenance where appropriate.

### CAA-WP-1120 - Viewer acceptance

Dependencies: CAA-WP-1100, CAA-WP-1110, CAA-WP-1000.

Independent validation includes human-readable smoke test plus deterministic search/navigation tests.

Major waypoint notification: YES when the local searchable viewer is accepted for the required corpus.

## 16. Phase L - Codex continuity preservation

### CAA-WP-1200 - Codex history discovery C1/C2/C3

Dependencies: operator surface helpful but not required; must complete before account transition.

Execution class: read-only investigation.

Purpose: discover stable session/project metadata available from each Codex seat without attempting full raw transcript evacuation.

### CAA-WP-1210 - Codex continuity exporter

Dependencies: CAA-WP-1200.

Purpose: preserve project/session-level summaries, repo/project association, date, outcome, major changed files/commits/PRs, unresolved work, and stable reference.

### CAA-WP-1220 - Index Codex continuity

Dependencies: CAA-WP-1210, CAA-WP-1000.

Purpose: expose Codex continuity records through the same local search system.

## 17. Phase M - ChatGPT-side archival

### CAA-WP-1300 - Owning-seat archive action implementation

Dependencies: baseline ownership identity, accepted local preservation policy, authenticated browser profile path.

Purpose: archive a verified private conversation in ChatGPT using its owning seat.

Rules:

- never delete;
- never archive before required local preservation acceptance;
- rate limit -> deferred state;
- wrong-seat/private-access redirect -> ownership/authentication defect, not silent fallback.

### CAA-WP-1310 - Archive reconciliation batches

Dependencies: CAA-WP-1300 and per-conversation local acceptance.

Execution class: browser operation / reconciliation.

Status surface shows archived / eligible / deferred counts plus percentage when denominator is known.

## 18. Phase N - final cutoff reconciliation

### CAA-WP-1400 - Final live inventory sweep

Dependencies: CAA-WP-0300, current authenticated seats.

Purpose: authoritative final enumeration immediately before account transition.

### CAA-WP-1410 - Final preservation delta closure

Dependencies: CAA-WP-1400, CAA-WP-0310.

Purpose: capture any final new/changed conversations and resolve outstanding recoverable exceptions.

### CAA-WP-1420 - Final campaign acceptance report

Dependencies: all required campaign packages or explicit Steward-accepted exceptions.

Purpose: answer `What, precisely, is not preserved yet?`

Required final sections:

- live conversation coverage;
- local archive coverage;
- normalization/reconstruction coverage;
- media unresolved count;
- final PDF coverage;
- index/viewer status;
- Codex continuity coverage;
- ChatGPT-side archive status;
- unresolved exceptions;
- resource/runtime state;
- exact cutoff timestamp;
- acceptance evidence references.

Major waypoint notification: YES. This is campaign completion / final Steward review boundary.

## 19. Parallelism rules

Parallel work is allowed only where dependencies and path ownership permit it.

Examples of safe parallelism after schema acceptance:

- incremental reconciler engineering;
- fixture expansion;
- media discovery;
- exact/full-text index implementation.

Do not run multiple writers against overlapping repository paths without explicit lane ownership.

Do not let a validator modify the writer's result while performing validation.

Corpus batches may run concurrently across independent records/resources once deterministic machinery and output ownership are accepted.

## 20. Codex capacity strategy through cutoff

Use the existing C1/C2/C3 resource planner and telemetry. Avoid hardcoding a permanent seat order into this campaign.

Operational intent through the cutoff is to consume available subscription capacity productively without creating needless multi-writer concurrency.

One primary writer at a time is acceptable for coherent architecture. Other seats are valuable for independent validation, repair, second review, or unrelated bounded Riverview work.

Where current policy supports it, `DRAIN`, `PRESERVE`, `SOONEST_ROLLOVER`, `MAXIMIZE_RUNWAY`, or other existing modes may be selected through authorized Riverview policy rather than hidden campaign logic.

## 21. Local compute strategy

Prefer deterministic local processing first.

Use:

- OCTO1 3060 Ti for fast local text/semantic batch work;
- OCTO1 P100 for VLM/image comparison and independent visual cross-check;
- dev RTX 4090 for heavier local reasoning/VLM/embedding/overflow work;
- Codex for repository engineering and cases requiring strong coding/reasoning rather than ordinary accepted batch execution.

OCTO1 must be woken and health-verified through existing WOL/SSH/startup artifacts when required.

## 22. Notification map

Silent by default.

Audio callbacks:

- Steward decision/action required;
- exhausted automatic recovery;
- authentication/physical intervention required;
- consequential blocker with no authorized autonomous continuation.

Major spoken waypoints:

1. original known conversation evacuation complete;
2. full required reconstruction accepted;
3. searchable local viewer accepted;
4. final cutoff reconciliation/campaign completion.

No per-batch or per-package celebratory speech.

## 23. Initial runnable sequence

The first dependency-ready work is:

1. preserve/finish CAA-WP-0100 externally as the current runner cools/resumes;
2. start CAA-WP-0001 operator surface engineering without touching the active archive runner;
3. continue CAA-WP-0500 local media discovery already in progress if it remains active and does not conflict;
4. when CAA-WP-0100 accepts, execute CAA-WP-0200/0210 baseline work;
5. then launch CAA-WP-0300 and CAA-WP-0400 according to path/resource availability;
6. after schema acceptance, expand into media/reconstruction/index lanes under the dependency graph above.

The Campaign Runner must not infer dependency readiness from this prose alone once packages are instantiated; authoritative stage/dependency rows own execution readiness.
