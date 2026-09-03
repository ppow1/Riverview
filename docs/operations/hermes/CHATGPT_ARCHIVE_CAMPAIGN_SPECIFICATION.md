# ChatGPT Business Archive Preservation and Local Knowledge Campaign

Status: Steward-authorized campaign specification draft for Hermes/Campaign Runner execution
Date: 2026-09-03
Owner: Steward
Execution authority: Riverview Campaign Runner / PostgreSQL lifecycle
Execution broker: Hermes

## 1. Objective

Preserve, reconcile, reconstruct, validate, index, and make locally browsable the current ChatGPT Business conversation corpus and related Codex continuity before the planned account transition around 2026-09-14/15.

The campaign must produce a trustworthy local archive that is:

- complete enough to survive loss of the current ChatGPT account context;
- independently validated rather than accepted from writer claims;
- human-readable;
- machine-searchable and queryable;
- media-aware, including copied/pasted images and attached files;
- incrementally reconcilable through the cutoff date;
- restartable and auditable;
- governable from a simple operator surface without requiring constant Steward supervision.

The local archive root is:

`A:\AI\Tools\ChatGPTConversationArchive`

The canonical Riverview engineering root remains:

`A:\Riverview\standalone`

Large private archive data remains local. GitHub is the engineering source of truth for implementation/specification, not the authority for the preserved corpus bytes.

## 2. Existing Riverview machinery to reuse

This campaign shall extend/reuse existing Riverview/Hermes infrastructure and must not create competing orchestration authorities.

Required existing foundations include:

- PostgreSQL-backed Campaign Runner objective/stage/work/attempt lifecycle;
- writer -> independent validator -> repair_writer -> revalidator -> acceptance flow;
- exact attempt fencing, leases, stale-result rejection, restart/resume, and persisted recovery;
- Riverview Relay / RestrictedRunner execution boundary;
- existing Hermes native Codex execution adapter;
- accepted C1/C2/C3 `CODEX_HOME` bindings and safe identity provenance;
- durable Codex resource policy/telemetry and current planner behavior;
- existing local AI startup/recovery artifacts for OCTO1;
- existing WindowsPresenter/notifier path;
- existing River event, diagnostics, Steward escalation, and status projections.

Do not build a second campaign database, second seat manager, second notification system, second work graph, or second scheduler merely for this archive campaign.

## 3. Campaign authority and acceptance

A campaign is one PostgreSQL objective. A work package is one objective stage and its accepted execution chain.

A writer result, generated file, commit, report, PDF existence, or worker statement is never sufficient proof of acceptance.

Every material engineering package must have an immutable validation basis and an independent validator identity.

Validation failures persist as evidence and create bounded repair/revalidation work. Failed or stale attempts are never overwritten into success.

Steward acceptance remains outside machine completion claims.

## 4. Current evacuation checkpoint

Current observed conversation inventory for the active evacuation lane:

- total known conversations: 534;
- locally preserved at latest checkpoint: 520 / 534 (97.4%);
- remaining: 14 / 534 (2.6%);
- current condition at specification time: paused for provider rate-limit cooldown.

This checkpoint is operational evidence, not final campaign acceptance.

Once the current queue reaches zero, the resulting complete inventory becomes Baseline Snapshot 1 and the campaign moves from emergency evacuation to reconciliation.

## 5. Execution resources

Campaign packages declare capability requirements. The resource layer chooses an eligible implementation/analysis resource based on capability, locality, availability, remaining Codex capacity, validation independence, and cost.

### 5.1 Codex resources

Existing authenticated resources:

- C1 -> `A:\AI\CodexProfiles\C1`
- C2 -> `A:\AI\CodexProfiles\C2`
- C3 -> `A:\AI\CodexProfiles\C3`

The accepted execution path is:

`Riverview -> Campaign Runner -> HermesCampaignRoleExecutor -> Hermes -> selected CODEX_HOME -> native Codex app-server`

Use the existing planner/policy/telemetry surfaces. Do not invent a parallel token/quota manager.

Where practical, repository-changing implementation should use one Codex resource and independent validation should use a different worker identity/resource.

### 5.2 Local AI resources

The campaign may also use local compute through Hermes/Riverview-supported paths.

#### OCTO1

Canonical human-facing node name for this campaign: `OCTO1`.

Existing repository artifacts may still use `OCTOMINER1`; do not casually rename working infrastructure solely for naming consistency.

Current hardware:

- RTX 3060 Ti 8 GB;
- Tesla P100 16 GB;
- small local system disk, approximately 120 GB class, therefore not suitable as an authoritative model warehouse or archive replica.

Current proven provisional workers:

- 3060 Ti: Qwen text worker, 16K context, fast local text/semantic work;
- P100: Gemma 3 12B full-VL, 32K context, image understanding / second opinion / independent visual cross-check.

Existing startup artifacts must be reused:

- `tools/local-ai/Start-Octominer1-Qwen3060Chat.ps1`
- `tools/local-ai/Start-Octominer1-GemmaP100VL.ps1`
- `tools/local-ai/Start-Octominer1-ChatWorkers.ps1`
- `docs/operations/LOCAL_AI_CHAT_WORKER_TESTING_AND_STARTUP.md`
- `docs/operations/octominer/OCTOMINER_REMOTE_POWER_AND_WOL.md`

Required OCTO1 activation sequence:

`resource requested -> check reachability -> Wake-on-LAN Magic Packet if required -> wait for host -> verify SSH -> verify GPU/runtime -> verify/start required inference endpoint -> execute -> persist provenance/result`

OCTO1 unavailability is a resource condition, not automatically a campaign failure.

#### Dev machine RTX 4090

The development machine RTX 4090 24 GB is available for heavier local reasoning/VLM/embedding/overflow work.

Do not consume it for routine tasks when OCTO1 or deterministic local code is adequate.

### 5.3 Model storage policy

Canonical model warehouse remains under the A: drive AI hierarchy, principally `A:\AI\Models` and current established model roots.

OCTO1 local model storage is a working cache, not authoritative storage.

Preferred model movement behavior:

`canonical A: model warehouse -> stage only required model to OCTO1 -> retain frequently used checkpoints while space permits -> evict replaceable copies when necessary`

Do not replicate the entire ChatGPT archive onto OCTO1 merely to run local inference. Send only the bounded artifacts required by the active job.

The currently missing 4 TB spinning disk on the dev machine is outside this campaign's critical path. Do not block archive work on that hardware issue while sufficient existing A: capacity remains.

## 6. Operator surface requirement

Before long autonomous execution, provide a persistent glanceable Campaign Runner status/control surface.

A small PowerShell window is acceptable for the first implementation. A later Riverview/Operator/Stream Deck surface may wrap the same control contract.

The surface must read from authoritative persisted Campaign Runner/Riverview state rather than maintaining an independent truth store.

### 6.1 Required display

At minimum show:

- campaign name;
- campaign state;
- current phase letter/title;
- completed phases / total phases and percentage;
- current work package;
- current role (`writer`, `validator`, `repair_writer`, `revalidator`, batch worker, etc.);
- selected resource (`C1`, `C2`, `C3`, `OCTO1-P100`, `OCTO1-3060Ti`, `DEV-4090`, deterministic local worker, etc.);
- package counts accepted/running/queued/blocked/failed;
- bounded corpus progress where measurable;
- active worker heartbeat age;
- last meaningful progress timestamp and time since meaningful progress;
- retry/recovery state;
- Steward-attention state;
- next expected action;
- latest major campaign waypoint.

### 6.2 Percentage rule

Every bounded progress counter with a legitimate denominator must display both fraction and percentage.

Examples:

- `520 / 534 (97.4%)`
- `143 / 400 (35.8%)`
- `6 / 14 phases (42.9%)`

While incomplete, display one decimal place. At true completion, `100%` is sufficient.

Never fabricate percentages when no legitimate denominator exists. For open-ended discovery show count plus a truthful statement such as `total still being determined`.

### 6.3 Refresh behavior

Prefer approximately 30-second refresh or event-driven refresh rather than full-screen repaint every few seconds.

The implementation should avoid the annoying visible flash behavior of the current evacuation status window. Update changed lines/regions where practical.

### 6.4 P / R / X Steward controls

The status window is also a bounded operator console.

- `P` = PAUSE AT SAFE BOUNDARY
- `R` = RESUME FROM PERSISTED STATE
- `X` = CLEAN STOP

`P` does not suspend an arbitrary process in the middle of a filesystem/database operation. It stops admission/claiming of new work and waits for the active operation to reach the nearest safe persisted checkpoint.

If an active attempt has not yet reached that boundary, display `PAUSE_PENDING` and identify what is still running.

`R` resumes the same persisted campaign lineage. It must not replay already accepted work or create a duplicate campaign.

`X` requests a clean, restartable stop: stop claiming new work, checkpoint safely, persist state, release resources/leases correctly, and leave the campaign resumable.

A forced process kill remains an emergency/recovery case, not normal X behavior.

Operator pause/stop actions must become durable control/audit events with a reason such as `operator_manual_pause`.

## 7. Steward notifier policy

Reuse the existing Riverview notification store and `src/riverview/notifications_audio.py` adapter to `estate.core.steward_annunciator.WindowsPresenter`.

Do not build another speech/notifier path.

Audio is exceptional. It is not routine progress chatter.

Allowed campaign audio use is limited to:

### 7.1 Callback required

Speak when safe autonomous progression requires the Steward, including:

- `STEWARD_REQUIRED` decision/approval;
- authentication/manual intervention that cannot be resolved safely;
- automatic recovery exhausted;
- package blocked with no authorized autonomous path;
- consequential ambiguity requiring human judgment;
- physical intervention required.

### 7.2 Major campaign waypoint

Speak only for genuinely major campaign milestones, not every work-package completion.

Examples:

- all original known conversations preserved;
- first complete reconstruction/validation of the full corpus;
- local searchable viewer accepted;
- final pre-cutoff reconciliation accepted;
- campaign completion.

Ordinary batch completion, model loading, worker dispatch, individual validator completion, or minor phase substeps remain silent.

Delivery is not acknowledgement and acknowledgement is not institutional acceptance.

The spoken text should be short and identify the campaign/reason. Full detail remains in persisted campaign evidence/status.

## 8. Phase plan A-N

The campaign consists of fourteen principal phases. Phase-letter completion is determined from accepted required packages, not from a manual counter.

### Phase A - Capture completion

Objective: finish preservation of the currently known conversation inventory.

Requirements:

- resume current archival runner after cooldown using the known working process;
- avoid unnecessary browser/profile/cookie resets while the process is working;
- preserve rate-limit checkpoints honestly;
- finish all recoverable chats or record explicit exceptions;
- do not infer completion solely from folder count.

Acceptance:

- current live inventory compared to local capture state;
- every known conversation is locally preserved or explicitly excepted;
- baseline inventory evidence produced.

### Phase B - Baseline snapshot

Objective: freeze Baseline Snapshot 1 when Phase A is accepted.

Required record per conversation where available:

- conversation ID;
- title;
- original/private URL;
- share URL;
- seat/account provenance;
- created/updated timestamps;
- local artifact paths;
- artifact hashes;
- transcript status;
- HTML/MHTML status;
- file/object preservation status;
- legacy PDF status;
- reconstruction status;
- media mapping status;
- ChatGPT-side archive state;
- exception state.

The baseline must be machine-readable and rerunnable.

### Phase C - Incremental reconciliation

Objective: support normal ChatGPT use between Baseline Snapshot 1 and the 2026-09-14/15 cutoff without reprocessing the whole corpus unnecessarily.

Classification states should include at minimum:

- `UNCHANGED_PRESERVED`
- `NEW_NEEDS_CAPTURE`
- `UPDATED_NEEDS_REFRESH`
- `ARCHIVED_REMOTE`
- `LOCAL_ONLY_EXPECTED`
- `EXCEPTION`

Compare by stable conversation identity, not title.

Final cutoff acceptance must prove that every live conversation maps to verified local preservation or an explicit acknowledged exception.

### Phase D - Corpus normalization

Objective: produce one canonical machine-readable normalized conversation representation.

Each normalized conversation should preserve:

- conversation ID;
- seat/account provenance;
- title and timestamps;
- ordered messages;
- stable turn/message IDs when recoverable;
- author role;
- text;
- code blocks;
- links;
- image slots;
- attachments/files;
- media mapping provenance;
- reconstruction provenance;
- derived search/index fields kept separate from preservation truth.

Downstream renderer, PDF generator, indexer, viewer, and AI retrieval should consume the normalized representation rather than independently reverse-engineering `page.html`.

### Phase E - Media/file relationship reconstruction

Objective: reconnect preserved objects/images/files to the messages/slots where they appeared.

Use strongest available evidence first:

1. direct retained asset/object identifier;
2. conversation-specific manifest identity;
3. message/turn identity;
4. exact dimensions;
5. attachment/capture order;
6. aspect ratio;
7. timestamps/provenance;
8. visual-model comparison;
9. unresolved.

`UNRESOLVED` is valid evidence. Fabricated placement is prohibited.

Use deterministic code where possible. Use OCTO1 P100 / other VLM resources only for genuinely ambiguous semantic/visual comparisons.

### Phase F - Static conversation reconstruction

Objective: create a faithful, offline, non-virtualized HTML representation for each conversation.

Do not simply print or reopen the captured ChatGPT HTML.

The live/saved page can contain virtualization placeholders and large estimated-height spacer blocks; the historical PDF process demonstrated that printing this DOM can produce huge blank pages and incomplete visual conversation content.

Static HTML should be generated from normalized conversation data plus mapped local media.

Human-facing header should clearly identify the artifact as a local saved ChatGPT conversation rather than a live OpenAI service.

### Phase G - Reconstruction validation

Independent validator must compare reconstructed output to authoritative preservation sources.

Acceptance evidence includes:

- beginning coverage;
- ending coverage;
- user-role coverage;
- assistant-role coverage;
- message ordering;
- media-slot accounting;
- attachment/file accounting;
- no virtualization placeholder artifacts;
- unresolved mappings listed explicitly;
- no fabricated content.

Writer cannot self-accept.

### Phase H - Final PDF production

Generate final archival PDF from accepted static reconstruction only.

Do not navigate back to the live ChatGPT Share page merely to make the PDF.

Historical PDFs remain provenance artifacts and should be labeled legacy/unverified unless they pass the new semantic validator.

### Phase I - PDF validation

Validator must check content rather than merely PDF structure/file size.

At minimum:

- PDF parses successfully;
- representative beginning/middle/end text exists;
- both user and assistant content is represented;
- semantic/text coverage is consistent with normalized source;
- pagination/density is plausible;
- expected media appears or a documented exception exists.

The old `valid PDF` definition based primarily on structural/size checks is insufficient.

### Phase J - Search and indexing

Objective: make the corpus practically searchable beyond ChatGPT's native search.

Minimum layers:

- exact/full-text search, preferably SQLite FTS5 or equivalent;
- structured metadata/tag/entity search;
- derived concept/summary fields;
- message-level search where practical;
- semantic/vector retrieval as a later layer using local embeddings where appropriate.

Useful derived fields may include:

- projects;
- people/residents/offices;
- hardware;
- software;
- products;
- vehicles;
- locations;
- technologies;
- decisions;
- open questions;
- tasks;
- code languages;
- tags;
- concepts/entities.

Derived tags are not preservation authority and should be rerunnable.

### Phase K - Local Archive Viewer

Objective: provide a human-readable master interface instead of requiring File Explorer traversal.

Desired interaction model:

- master page;
- seat/account browsing;
- conversation sidebar/list;
- global search box;
- open reconstructed conversation in main pane;
- jump to matching message/turn;
- tags/projects/concepts filters;
- links to raw transcript/HTML/MHTML/metadata/PDF/share references where useful;
- clearly labeled `Saved ChatGPT Conversation - Local Archive` presentation.

The familiar ChatGPT-like interaction pattern may be used for private local archival viewing, while clearly identifying the interface as a local saved copy.

Human-readable HTML and machine-readable index/search data must derive from the same normalized conversation source.

### Phase L - Codex continuity preservation

Before account transition, inventory C1/C2/C3 Codex history and preserve lightweight project/session continuity.

Do not attempt to preserve every raw Codex utterance unless later shown necessary.

Desired summary record includes where available:

- seat;
- project/repository;
- session/task title;
- date/time range;
- branch/worktree;
- short summary;
- outcome/status;
- significant files changed;
- commits/PRs;
- unresolved work / next step;
- stable reference/identifier.

These summaries should be indexed alongside ChatGPT conversations.

### Phase M - ChatGPT-side archival

Only after local preservation/reconstruction acceptance, archive conversations inside ChatGPT using the owning authenticated seat.

The original private conversation URL and ownership provenance determine which seat performs the remote Archive operation.

Rate limiting produces a deferred state such as `ARCHIVE_PENDING_RATE_LIMIT`, not deletion or silent account substitution.

Never delete conversations as part of this campaign.

### Phase N - Final cutoff reconciliation

Run immediately before account transition around 2026-09-14/15.

Final campaign evidence must answer exactly what remains unpreserved.

Acceptance requires:

- live ChatGPT inventory accounted for;
- locally preserved conversation inventory reconciled;
- all new/changed conversations since baseline captured or explicitly excepted;
- normalized corpus produced;
- required reconstructions accepted or exceptions recorded;
- media mappings resolved to accepted confidence or explicitly unresolved;
- final PDFs generated from accepted reconstruction and validated;
- local search/index operational;
- local viewer operational;
- required C1/C2/C3 Codex continuity summaries preserved;
- ChatGPT-side archive state reconciled according to policy;
- no hidden outstanding preservation work;
- concise final acceptance/exception report delivered to Steward.

## 9. Engineering packages versus corpus-processing packages

Do not burn Codex capacity merely to run already accepted batch machinery.

Separate:

### Engineering packages

Examples:

- implement normalized schema;
- implement deterministic media mapper;
- implement static renderer;
- implement PDF semantic validator;
- implement reconciler;
- implement search/index;
- implement viewer/operator surface.

Preferred path:

`Codex writer -> independent validator -> repair/revalidation if required -> accepted implementation`

### Corpus-processing packages

Once machinery is accepted, process bounded batches using deterministic code and local AI resources where appropriate.

Example:

- `MEDIA-MAP-BATCH-001` conversations 1-50;
- `MEDIA-MAP-BATCH-002` conversations 51-100;
- etc.

Codex should return only when corpus execution reveals a real software defect, ambiguous engineering problem, or validation defect that requires code changes.

## 10. Resource capability declarations

Packages should declare requirements such as:

- `requires_repository_write`
- `requires_private_archive_access`
- `requires_local_archive_bytes`
- `requires_codex`
- `may_use_remote_codex`
- `may_use_local_llm`
- `requires_vlm`
- `requires_large_vram`
- `requires_independent_validator`
- `requires_browser_authenticated_seat`
- `requires_deterministic_validator`

The scheduler/resource layer should choose an eligible resource rather than hardcoding one seat/model into the campaign logic.

## 11. Pause, recovery, and anomaly inspection

The Steward must be able to walk into the room, inspect the status surface, notice anomalous behavior, press `P`, and investigate without the system dispatching additional work.

Example anomaly: unexpected network access or a resource doing work unrelated to the active package.

Pause semantics must make the campaign safe to inspect:

- no new claims after pause request;
- current attempt reaches safe checkpoint if possible;
- current package/resource remains visible;
- last progress and heartbeat remain visible;
- pause reason persists;
- resume continues same lineage.

This does not weaken the existing fencing/stale-result model.

## 12. Network and external-access discipline

Packages must be scoped to the network/resources actually required.

Unexpected external access outside an accepted package is diagnosable evidence and may justify Steward pause/investigation.

Do not introduce arbitrary web/API dependencies for local archive reconstruction when local artifacts are sufficient.

No OpenAI API billing path is required for this campaign. Native Codex seat execution and local inference should use existing authenticated/local mechanisms.

## 13. Required campaign progress evidence

Meaningful progress must be persisted, not inferred from a busy process.

For bounded batch work, record:

- total expected units;
- completed units;
- percentage;
- current unit/batch;
- last meaningful progress timestamp;
- attempt/worker/resource identity;
- last durable checkpoint;
- errors/exceptions;
- next eligible action.

Heartbeat is liveness. Heartbeat is not progress.

A campaign that is heartbeating but has made no meaningful progress for an anomalous interval must appear visibly stalled/suspect on the operator surface.

## 14. Steward decision gates

Autonomous execution should continue without Steward intervention for ordinary bounded work including:

- selecting an eligible Codex seat under accepted policy;
- using accepted local model workers;
- waking OCTO1 by the verified WOL path;
- checking SSH/health;
- starting an already accepted model endpoint;
- running deterministic validation;
- retrying within accepted bounded recovery rules;
- progressing writer/validator/repair/revalidation lifecycle;
- processing additional corpus batches.

Steward callback is required for genuinely consequential boundaries including:

- destructive operation not already authorized;
- changing authoritative archive root;
- unresolved authentication requiring manual intervention;
- accepting known preservation gaps at final cutoff;
- ambiguous media placement where provenance matters and no accepted confidence rule resolves it;
- changing resource/governance policy outside existing authority;
- exhausted recovery/no safe continuation.

## 15. Initial execution roadmap

After this specification is accepted as campaign basis:

1. complete Phase A evacuation while preserving the current working archive process;
2. implement/verify the Campaign Operator Surface early so multi-day autonomous work is visible and pausable;
3. freeze Baseline Snapshot 1;
4. implement incremental reconciler;
5. define and independently validate normalized conversation schema;
6. finish current media-ID/object discovery and use results to design the deterministic mapper;
7. create a small representative fixture corpus for engineering tests rather than uploading the private full corpus to GitHub;
8. implement reconstruction + validation;
9. implement final PDF generation + semantic validation;
10. process corpus in bounded batches using local compute where practical;
11. implement search/index and viewer;
12. preserve Codex project/session summaries;
13. perform ChatGPT-side archival only after local acceptance;
14. run final cutoff reconciliation and deliver exception report.

## 16. Representative fixture corpus

GitHub/Codex engineering tests should use a small privacy-reviewed representative fixture set, not the full private archive.

Fixture cases should include:

- short text-only conversation;
- long conversation with virtualized DOM behavior;
- one pasted image;
- multiple pasted images in one message;
- attachments/files;
- code block/table content;
- known pathological legacy PDF with huge whitespace/missing visual assistant content;
- ambiguous media mapping case;
- no-share-URL exception case.

Local Codex CLI / Hermes integration testing may then run accepted implementation against the real A: archive.

## 17. Failure classification

At minimum distinguish:

- provider/account rate limit;
- authentication/manual-intervention required;
- local worker unavailable;
- OCTO1 wake/SSH failure;
- model endpoint unavailable;
- repository engineering defect;
- deterministic validator failure;
- media mapping unresolved;
- reconstruction mismatch;
- PDF semantic mismatch;
- stale/fenced attempt;
- safe-boundary pause pending;
- external/unexpected behavior requiring investigation.

Failures remain evidence and must not be silently converted to success.

## 18. Major invariants

1. Local preservation bytes are never made dependent on GitHub availability.
2. Archive originals are preserved; reconstruction/derived/index data is additive.
3. Conversation identity is stable-ID based, not title based.
4. Writer cannot self-accept.
5. Stale results cannot become authoritative.
6. Existing Campaign Runner/PostgreSQL lifecycle remains authority.
7. Existing C1/C2/C3 resource binding remains authority for Codex identity.
8. Existing notifier/WindowsPresenter path is reused.
9. Existing OCTO1 WOL/SSH/startup artifacts are reused.
10. Percentages are displayed only when denominators are real.
11. P/R/X controls operate through persisted safe control semantics, not brute process suspension.
12. Audio is reserved for callback or major campaign waypoints.
13. The static reconstruction, not the live virtualized ChatGPT page, is the source for final PDF generation.
14. Unresolved media placement is preferable to invented placement.
15. Final cutoff acceptance is reconciliation-based, not folder-count based.

## 19. Recovery references

Before implementing or diagnosing this campaign, consult the current canonical repository copies of at least:

- `AI_HINTS.md`
- `docs/codex-reports/seat-1/RUN-002-campaign-runner-specification.md`
- `docs/operations/hermes/CAMPAIGN_RUNNER_BOOTSTRAP_RECOVERY.md`
- `docs/operations/HERMES_C1_C2_C3_RESOURCE_ORCHESTRATION.md`
- `docs/operations/roadmap/evidence/C1_C2_C3_HERMES_NATIVE_BINDING_2026-08-27.md`
- `docs/operations/LOCAL_AI_CHAT_WORKER_TESTING_AND_STARTUP.md`
- `docs/operations/octominer/OCTOMINER_REMOTE_POWER_AND_WOL.md`
- `src/riverview/notifications_audio.py`
- `docs/operations/CHATGPT_BUSINESS_FILE_PRESERVATION_2026-09-01.md`

Apply mandatory Riverview clean-state preflight before repository-changing work.

## 20. Campaign completion statement

This campaign is complete only when its final reconciliation and independent validation can truthfully answer:

`What, precisely, is not preserved yet?`

with either:

`Nothing required remains unpreserved.`

or a complete, explicit, Steward-visible exception list.
