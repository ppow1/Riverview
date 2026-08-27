<!-- Version: 0.2.0 | Date: 2026-08-27 | Status: CAPTURED | Planning-only exploration -->
# PL-0007 — Operator vNext Capability Architecture Exploration

Status: `CAPTURED` in the Parking Lot. This is an elaboration artifact linked to both the existing captured PL-0007, **Web Capability Archaeology and Consolidation**, and the existing captured PL-0008, **Riverview Web Operator UI Stabilization and Re-architecture**. It does not replace, duplicate, promote, or alter either parking item. It is not a Ready Bench item, roadmap promotion, implementation authorization, acceptance record, or authority change.

## 1. Lineage, authority, and exploration status

The archaeology was performed read-only in `A:\Riverview\repo` at detached local commit `99b67d97cdf6f3e860ee6849ce10bcf583ab0273`, based on stale parent `c29d6256e05bd0c98188a5113346cb3895f8259a`. Authoritative GitHub `origin/main` is `3be31945eed8d47cbb12acf6be3d28165398caf3`. No publication of `99b67d9` occurred. The current canonical local source for this correction is `A:\Riverview\standalone`.

This file is documentation-only. It preserves the prior exploration's archaeology while correcting its lineage and status evidence. It must remain planning-only, retain `CAPTURED`, and must not trigger Ready Bench promotion. The Parking Lot board and both source parking items remain authoritative and unchanged.

## 2. Executive evidence and status

This exploration compares two existing local operator surfaces and their surrounding control, execution, resident, spatial, and resource projections:

- Riverview Operator source is in `src/riverview/operator/`; the local page at `http://127.0.0.1:18082/` returned HTTP 200 and rendered the `Riverview Operator` shell on 2026-08-27. Its source exposes Conversations, Activity, Architecture, Notifications, Settings, CME, bounded Snapshot, resident/session/room/chat/activity/event/notification/runtime routes, and bounded voice transcription.
- Unauthenticated Operator probes returned HTTP 401 for `/api/runtime/status`, `/api/residents`, and `/api/events?after=0`; guessed routes returned HTTP 404. This proves reachability and protected-route behavior only, not authenticated feature health or database state.
- Office source is read-only evidence from the adjacent Estate repository at `A:\theestate\src\estate\core\steward_command_center.py` and related `office_*` modules. The local Office page at `http://127.0.0.1:8765/` and `/status.json` returned HTTP 200 on 2026-08-27. The JSON reported `status: running`, `local_only: true`, `estate_status: Warnings`, `health_state: warning`, `latest_verdict: blocked`, and `latest_validation_status: not_run`.
- Observed Office counts were `pending_decisions: 53`, `mailbox_open_count: 27`, `notification_unacknowledged_count: 973`, `execution_active_count: 2`, `execution_attention_required_count: 13`, `dispatch_ready_count: 1`, and `dispatch_running_count: 0`. These are local projection values, not claims of end-to-end health or acceptance.
- Office service access reported Estate Core `healthy`, Resident Gateway `unknown`, and Open WebUI `unknown`. The page reported `UI runtime: script not initialized; navigation may not work` and a JavaScript-disabled `noscript` diagnostic. These are observations, not repairs.
- The roadmap evidence identifies `RV-016.5` as the first unfinished dependency-ready leaf. Machine-side spatial evidence exists, while real Quest/3D, comfort, frame-time, reconnect, and Steward experiential acceptance remain incomplete. This exploration makes no Ready Bench claim.
- `RV-018.6_RESIDENT_CONVERSATION_PARITY_AUDIT.md` records resident/session identity and provider-routing equivalence at browser/component level, while durable multi-session memory publication, provider-generated multi-resident responses, fresh human resident-switch acceptance, and live human SillyTavern acceptance remain partial or pending.

Vocabulary is deliberate: `designed` means specified in source/docs; `implemented` means code exists; `installed` means an installation artifact exists; `running` means a live probe reported it; `proven` means the cited boundary was exercised; and `accepted` means acceptance evidence says so. `partial`, `unknown`, `not proven`, `pending`, `warning`, `blocked`, and `not_run` retain their source meanings. No status here upgrades implementation or acceptance evidence.

## 3. Capability matrix

Classification is planning vocabulary only: `PRESERVE` keeps an outcome or boundary; `REDESIGN` changes presentation or contract while retaining intent; `SUBSUME` puts a capability behind a common projection; `DEFER` keeps it outside the next slice; `RETIRE` removes an obsolete duplicate; `NEW` identifies a capability not yet established.

| Capability | Source | Purpose | Current implementation/state | Value | Classification | Destination | Loading/performance | Diagnostics | Dependencies/risks |
|---|---|---|---|---|---|---|---|---|---|
| Riverview Operator shell and navigation | `src/riverview/operator/ui.py`; live `/` | Local operator entry surface | Implemented; live HTTP 200 and shell rendered; authenticated feature health not proven | Coherent local workspace | REDESIGN | Shared shell / Now | Render shell first; hydrate projections second; proposed 250 ms p95 shell target | Route, hydration, stale, and reconnect checkpoints | Auth and durable-state availability |
| Estate / Office command surface | Estate `steward_command_center.py` and `office_*`; live `/status.json` | Legacy operational and decision context | Running locally with explicit warning, blocked verdict, and not-run validation | Preserve Estate predecessor capability during migration | PRESERVE | Estate compatibility projection and deep links | Independent load; warning/stale must remain visible | Source, status, artifact, and validation evidence | Estate remains predecessor/owner; no wholesale copy |
| Successor migration boundary | Charter, Foundation, PL-0007, PL-0008 | Replace capabilities incrementally without subordination | Designed boundary; no cutover accepted | Preserve mission, identity, authority, and useful behavior | REDESIGN | Migration map and bounded adapters | Projections remain independently loadable | Authority, provenance, parity, and acceptance checkpoints | Riverview is successor; Estate is predecessor, not a Riverview subsystem |
| System Pulse and CME | Operator CME HUD/routes; Office status JSON | Quiet global operational posture | CME-related routes exist; protected route behavior observed; common pulse not proven | One truthful read-only heartbeat | SUBSUME | Global shell rail / persistent System Pulse | Quiet heartbeat; bounded refresh; never blocks shell | Source watermark, freshness, stale, state, and authority | PostgreSQL authority, auth, source divergence |
| Snapshot and diagnostic bundle | Operator `snapshot.py`; ADR-0002; Cookbook | Capture reproducible local evidence | Bounded Snapshot exists; common bundle not proven | One compact, first-class recovery artifact | SUBSUME | Global Snapshot icon and Settings & Evidence | Local bounded export; no upload | Manifest, redaction, size, freshness, excluded-content reasons | Protected payloads, secrets, classification |
| Conversations, rooms, sessions, and rehydration | Operator routes, `projection.py`, `room_admin.py`; RV-018.6 | Resident-bound continuity | Identity/routing equivalence proven at component boundary; several durable/human boundaries partial | Preserve resident canon and context | PRESERVE | Conversations | Immediate shell and bounded progressive history hydration | Missing, archive, room mismatch, correlation, provider failure | Durable state and resident boundaries |
| Activity, events, and history | `activity.py`, event routes, Office activity | Traceable operational history | Bounded projections and cursors exist; full cross-surface truth not proven | Explain what happened without reconstruction | SUBSUME | Now / Conversations | Cursor-based bounded history; progressive loading | Deduplication, cursor gap, stale source, replay | Retention and cross-source semantics |
| Work, campaigns, workers, and CME momentum | PostgreSQL work/lease state; `campaign/`; CME evidence | Observe execution and progression | Persisted lifecycle mechanisms exist; observation must not imply dispatch/acceptance | Make extreme parallelism legible and safe | SUBSUME | Work and System Pulse | Independent lanes; bounded fan-in; no slow lane blocks shell | Lease, fence, stale, blocker, validation, acceptance checkpoints | Deliberate ownership, evidence, resource limits |
| Resource and workload topology | Office capacity evidence; `reasoning/gpu.py`; Campaign Runner | Relate resources to work | Signals are separate; GPU identity/unknown conditions remain; workload provenance incomplete | Dense drilldown without false capacity claims | REDESIGN | Estate / Resources and Work | Lazy drilldown; summary stays compact | Identity mismatch, stale sample, quota, reservation, provenance | Never merge seat fuel, GPU telemetry, reservation, or ownership |
| Two-chassis compute hierarchy | Estate/resource archaeology; future adapter | Represent physical capacity | Not established as a canonical Riverview projection | Stable drilldown model | NEW | Resources drilldown: `Compute -> Tower -> Slot1..12 -> GPU -> model/process/workload` for each of two independent chassis | Summary collapsed; nodes hydrate on demand | Missing tower/slot/GPU, stale telemetry, identity mismatch | No ownership, power, SSH/WOL, or model inference without evidence |
| Visual direction and attention budget | Operator/Office surfaces; Steward requirements | Make a busy environment quieter | No accepted vNext visual system; current warning density is evidence | Restrained modern 2026 operator experience | REDESIGN | Charcoal/navy shell with cyan/gold accents | Visual shell never waits on data | Status semantics, contrast, density, attention/noise budget | No status-light overload; attention must be intentional |
| Logical actions and control adapters | Estate command surface; Stream Deck inventory/plugin; voice contracts | Common safe commands | Registered-action fixtures exist; live device dispatch and unified namespace not proven | Preserve muscle memory across surfaces | SUBSUME | Versioned device-independent logical action registry | Immediate acknowledgement, async result | Unknown, collision, confirmation, disconnect, idempotency | Stream Deck, Command Chair, mouse, dictation, web, tablet, future Quest |
| Stream Deck, Command Chair, gaming mouse | Stream Deck inventory/RV-011.1 and installed config | Physical operator control | Stream Deck inventory captured; live SDK/button/rotary and Command Chair ownership not fully proven | Preserve established control habits | PRESERVE | Controls projection over shared actions | Offline/unknown explicit; no profile mutation | Installed-vs-repo drift, device disconnect, ambiguity | Installed Stream Deck tree is runtime truth |
| Windows voice typing and screenshot muscle memory | Charter; voice/transcription routes; local Windows behavior | Dictation, drafts, clipboard, direct screenshot paste | Bounded transcription exists; long-dictation/focus/clipboard/direct-paste acceptance not established here | Keep familiar low-friction input | PRESERVE | Voice and capture adapters over shared actions | Stable focus; nonblocking draft buffer; no truncation | Microphone, timeout, empty transcript, clipboard, paste, focus checkpoints | Windows behavior remains valid; no second authority |
| Spatial / Quest presentation-control adapter | RV-016.5 and Quest evidence | Future immersive presentation/control | Machine-side and some presentation evidence exist; teleport/hand input and acceptance incomplete | Future surface without authority split | DEFER | Spatial adapter over shared entities and logical actions | Reconnect/timeout visible; cannot block web workspace | XR input, frame time, reconnect, physical acceptance | Not a peer authority; no Quest runtime change |
| Diagnostics and recovery | ADR-0002; Cookbook; RIV-UI checkpoints | Explain failure and verify recovery | Checkpoints and evidence vocabulary exist; unified bundle/recovery flow not proven | First-order operational capability | PRESERVE | System Pulse, side panel, Settings & Evidence | Failure projection is nonblocking and retains last-good | Stable checkpoint, probe, repair hint, verification, evidence ref | Never relabel unknown/warning/blocked as healthy |
| Navigation, preferences, search, parking, roadmap | Operator local state; Estate navigation/search; roadmap and Parking Lot docs | Find context and planning state | Sources and deep links exist; browser state is not authority | Reduce navigation cost | REDESIGN | Five-domain IA with named deep links | URL first; lazy hydration; safe defaults | Corrupt preference, forbidden/stale result, board/status evidence | Do not alter roadmap or Parking Lot through this artifact |

## 4. Proposed operator information architecture

The future Operator has five stable destinations, each with one primary question:

1. **Now** — persistent quiet System Pulse, current objective/waypoint, CME posture, worker/dispatch state, attention, and last-good evidence.
2. **Conversations** — resident-bound conversations, rooms, sessions, rehydration, search, voice, artifacts, and activity.
3. **Work** — objectives, campaigns, attempts, validation, roadmap, parking, and request/approval boundaries.
4. **Estate** — residents, services/models, notifications/mailboxes/recalls, controls, Spatial, resources, and predecessor compatibility projections.
5. **Settings & Evidence** — preferences, compact global Snapshot, diagnostic bundle, Cookbook links, provenance, and local-only export.

Mission Control, Roadmap, Parking Lot, Validation, Search, and Settings remain named deep links within those domains, not parallel authorities.

The visual direction is dark-first, restrained, and modern for 2026: charcoal and navy foundations, cyan for active/healthy affordances, gold for deliberate attention or decision, and typography/spacing that favors calm hierarchy. It must not turn every state into a bright status light. Attention is an explicit budget: every badge, sound, motion, notification, and escalation consumes noise budget and must identify urgency, owner, freshness, and next action; healthy quiet is the default.

## 5. System Pulse, render order, and performance contract

The System Pulse is globally accessible from the shell/rail, including when the user is in Conversations, Work, Estate, or Settings. CME is a global operational capability, not an ordinary page-only feature. The Pulse remains persistent and quiet, with an always-available click target that opens a side panel or overlay without losing the current workspace.

Its explicit states are: healthy quiet heartbeat with freshness; stale; intentionally off; starting/reconnecting; unreachable; and attention-required. Each state carries `observed_at`, source, freshness/stale-after, reason, authority, and diagnostic/evidence references. `healthy` is never inferred from missing data.

Render and hydration are separate phases:

- Render the shell, rail, current route, and stable placeholders immediately.
- Hydrate second through bounded, cancelable projections and progressive history loading.
- Never let a slow database, event stream, provider, telemetry source, or side panel block first render or unrelated workspace interaction.
- Use localized DOM mutations and generation/cursor checks so one arriving projection cannot rebuild or destabilize the whole page.
- Keep bounded history windows, load older history progressively, and preserve the last good projection with an explicit stale/degraded marker.
- Reconnect with bounded backoff and cursor reconciliation; show starting/reconnecting or unreachable rather than spinning indefinitely.

Proposed targets, not current measurements: shell render within 250 ms p95 after a local click; first projection or explicit failure within 1,000 ms p95; local acknowledgement within 300 ms p95; lost-stream detection within 2 seconds. These targets require future measurement and are not completion claims.

## 6. Entities, projections, and resource drilldown

Riverview is the successor/replacement system; The Estate is the predecessor/legacy capability source during migration. The migration preserves useful Estate capability through bounded adapters and derived compatibility projections. Neither browser state nor a compatibility surface becomes authority.

The resource model must expose two independent chassis. Each has the same hierarchy, with no implied shared ownership:

```text
Chassis A                    Chassis B
  Compute                      Compute
    Tower                      Tower
      Slot1 ... Slot12           Slot1 ... Slot12
        GPU                        GPU
          model                      model
          process                    process
          workload                   workload
```

General UI remains restrained and summary-oriented; resources, workload, provenance, and dependencies receive dense drilldown on demand. A workload row must identify its associated resource only when the evidence proves the association, with source, observation time, allocation/reservation basis, model/process identity, and provenance. Seat fuel, provider availability, GPU telemetry, reservation, allocation, and ownership remain separate fields.

All projections are maintained authoritative or derived read models. They are versioned, carry source references and watermarks, and are updated from events/state through typed adapters. Per-click reconstruction from scattered files, live probes, or browser memory is prohibited as an architectural direction.

## 7. Shared logical actions and operator continuity

The shared action layer uses versioned, device-independent logical actions across web, controllers, tablets, and a future Quest adapter. Stream Deck, Command Chair, gaming mouse, dictation, screenshots, Windows voice typing, and future surfaces invoke the same registered intent vocabulary, confirmation class, target, correlation/idempotency key, timeout, and result states. The adapter changes; the entity and action meaning does not.

Windows voice typing remains a valid input path. The future contract preserves stable focus, long dictation, drafts, clipboard workflows, and direct screenshot paste. Voice can submit to the same action layer but is not a second authority. Quest/Spatial is a future presentation/control adapter over shared entities and logical actions, not a peer authority and not a source of canonical state.

## 8. Explicit attention/noise-budget contract

The operator should feel quieter as capability increases. Healthy data is quiet and fresh; attention is reserved for a meaningful blocker, stale dependency, required Steward decision, recovery step, or unsafe ambiguity. Every attention signal must have a source, freshness, owner, urgency, and next action. Duplicate notifications across shell, page, device, and side panel are coalesced. Motion, sound, color, and persistent badges are opt-in consequences of severity, not defaults. This contract is a future design requirement, not evidence that current surfaces satisfy it.

## 9. Projection and state architecture

The proposed architecture is a read model, not a new authority:

```text
PostgreSQL events / operational state + bounded Estate artifacts
                         |
       typed adapters, redaction, freshness, correlation
                         |
       versioned projection gateway / System Pulse assembler
          |                  |                  |
   Operator UI       Estate compatibility       Snapshot/diagnostic bundle
          |
  logical action intents -> registered adapter -> evidence/result projection
```

PostgreSQL remains authoritative for Riverview operational state under ADR-0001. Estate files remain Estate-owned source evidence. Browser storage is preference/cache only. Large, private, protected, and adult-oriented payloads stay outside ordinary River projections. Every projection includes schema version, source references, observed timestamp, stale threshold, authority label, classification, and failure checkpoint where applicable.

## 10. Logical action and diagnostic bundle shape

Only registered intents are accepted, such as `riverview.operator.open`, `riverview.pulse.refresh`, `riverview.conversation.start`, `riverview.snapshot.capture`, `riverview.validation.inspect`, `riverview.streamdeck.control.invoke`, and `riverview.spatial.open`. Each has a version, target, required fields, classification, confirmation policy, allowed adapter, idempotency key, correlation ID, timeout, and result schema. Arbitrary shell, SQL, URL, Python, device, or provider commands are rejected.

The compact global Snapshot icon creates a local diagnostic bundle containing a manifest, redacted System Pulse, active route/state, selected conversation metadata without protected bodies unless explicitly permitted, activity cursor/watermark, diagnostic summaries, source paths/URLs, and a README. It records schema version, capture time, service identity, Git SHA where available, authority, classification, redaction policy, freshness, and excluded-content reasons. It does not upload, mutate PostgreSQL authority, or imply acceptance.

## 11. Requirement audit

The audit is against the 18 Steward requirements for this correction, not against future implementation completion. `COMPLETE` means the requirement is explicitly represented in this exploration; `PARTIAL` means represented but current evidence or design coverage is incomplete; `MISSING` means not represented; `CONTRADICTED` means an explicit conflict with authority or evidence. Citations are to this exploration's numbered sections and matrix rows.

| # | Steward requirement | Classification | Exact exploration citation | Evidence/status note |
|---:|---|---|---|---|
| 1 | Riverview successor and Estate predecessor migration | COMPLETE | §1, §3 “Successor migration boundary”, §6 | Explicit authority boundary; no cutover claim |
| 2 | Extreme parallelism and CME momentum | PARTIAL | §3 “Work, campaigns, workers, and CME momentum”, §5 | Lifecycle/projection direction is present; dispatch/validation acceptance remains unproven |
| 3 | Compressed attention | COMPLETE | §4, §8 | Quiet shell, compact pulse, and explicit noise budget are stated |
| 4 | Immediate nonblocking render-first/hydrate-second, bounded history, progressive loading, localized DOM mutations, no slow subsystem blocking | COMPLETE | §5 | All requested mechanics are explicit; targets remain proposed |
| 5 | Dark-first restrained modern 2026 visual direction with charcoal/navy, cyan/gold, no status-light overload | COMPLETE | §4 | Palette and restraint are explicit; no current vNext implementation claimed |
| 6 | Compact global Snapshot icon and first-class diagnostic bundle | PARTIAL | §3 “Snapshot and diagnostic bundle”, §10 | Existing bounded Snapshot is observed; common bundle is future design |
| 7 | CME globally accessible from shell/rail, not ordinary page-only | PARTIAL | §3 “System Pulse and CME”, §5 | Global requirement is explicit; current route protection and global implementation are not proven |
| 8 | Persistent quiet System Pulse with healthy/fresh, stale, off, starting/reconnecting, unreachable, attention-required, click-to-inspect side panel/overlay | PARTIAL | §4, §5 | Complete design enumeration; current implementation not proven |
| 9 | Two independent chassis with Compute → Tower → Slot1..12 → GPU → model/process/workload | COMPLETE | §3 “Two-chassis compute hierarchy”, §6 | Exact hierarchy and independence are explicit; canonical projection is not implemented |
| 10 | Restrained general UI with dense resource drilldown | COMPLETE | §4, §6 | Summary/drilldown split is explicit; future design |
| 11 | Workload/resource association and provenance | PARTIAL | §3 “Resource and workload topology”, §6 | Required fields and evidence rule are explicit; current associations remain incomplete |
| 12 | Preserve Stream Deck, Command Chair, gaming mouse, dictation, screenshot muscle memory | PARTIAL | §3 “Stream Deck, Command Chair, gaming mouse”, §7 | Preservation is explicit; Command Chair ownership and some live boundaries remain unknown |
| 13 | Shared versioned device-independent logical actions across web/controllers/tablets/future Quest | PARTIAL | §3 “Logical actions and control adapters”, §7, §10 | Contract is explicit; unified namespace and all adapters are not proven |
| 14 | Windows voice typing valid with stable focus, drafts, long dictation, clipboard, direct screenshot paste | PARTIAL | §3 “Windows voice typing and screenshot muscle memory”, §7 | Preservation requirement is explicit; full acceptance is not established |
| 15 | Spatial/Quest future presentation/control adapter over shared entities, not peer authority | COMPLETE | §3 “Spatial / Quest presentation-control adapter”, §6, §7 | Boundary is explicit and current acceptance is not overstated |
| 16 | Maintained authoritative/derived projections instead of per-click reconstruction | COMPLETE | §6, §9 | Projection authority and anti-reconstruction rule are explicit |
| 17 | Diagnostics/recovery as first-order capability | COMPLETE | §3 “Diagnostics and recovery”, §5, §10 | Diagnostics, recovery, and evidence are primary capabilities; unified flow remains future |
| 18 | Busy environment made quieter with explicit attention/noise-budget contract | COMPLETE | §4, §8 | Contract is explicit; current surfaces are not claimed compliant |

No requirement is classified `CONTRADICTED`; the `PARTIAL` classifications preserve uncertainty rather than overstating current implementation.

## 12. Planning-only implementation decomposition

These are bounded future tranches, not commitments and not Ready Bench promotion:

| Future tranche | Planning outcome | Dependencies | Acceptance boundary / non-action |
|---|---|---|---|
| A. Contract inventory | Versioned capability, entity, action, status, pulse, provenance, and attention schemas | This artifact, Charter, ADRs, PL-0007, PL-0008 | Schema review only; no runtime mutation or roadmap promotion |
| B. Projection and pulse | Redacted freshness-aware read projections and quiet global Pulse | A, PostgreSQL authority, diagnostics | Authenticated read probes and stale/unknown tests; no dispatch |
| C. Shell and hydration | Five-domain IA, render-first/hydrate-second, bounded history, reconnect, localized updates | A/B, Operator checkpoints | Browser boundary tests; no Office source changes |
| D. Work/resource topology | Two-chassis hierarchy, workload association, provenance, parallel-lane/CME projections | A/B, current evidence, future telemetry boundaries | Read-only drilldown and explicit unknowns; no ownership inference |
| E. Logical actions and continuity | Shared versioned actions for web, controls, tablet, voice, screenshots, and future Spatial | A/B, Stream Deck and voice contracts | Fixture/boundary tests; no physical profile mutation |
| F. Snapshot and recovery | Compact global Snapshot icon and first-class diagnostic bundle | B/C, redaction and Cookbook rules | Local export inspection and recovery evidence; no upload or authority mutation |
| G. Human migration acceptance | Steward-reviewed comparison of Operator and Estate predecessor outcomes | A–F, named Quest/control boundaries | Fresh acceptance required; no cutover claim |

## 13. Open Steward decisions

1. Is the five-domain IA and quiet System Pulse direction acceptable while named deep links remain?
2. Which logical-action namespace and version policy should govern Stream Deck, Command Chair, voice, tablet, and future Quest adapters?
3. Which resource telemetry and workload associations are sufficiently evidenced for the first projection?
4. Should Estate expose a bounded Riverview compatibility projection, or should Operator consume only Riverview-owned state and link to Estate?
5. Which responsiveness/noise-budget targets should be measured before adoption?
6. Which physical Command Chair controls have approved ownership after live event capture?
7. When RV-016.5 acceptance is complete, should Spatial remain a separate surface or appear as an Estate adapter?

## 14. Explicit scope and non-actions

This package modifies only this documentation artifact. It does not modify UI source, Quest runtime, device profiles, Stream Deck configuration, PostgreSQL, implementation/runtime/device/Octominer code, resident canon, Grace/CME policy, Office artifacts, the Parking Lot board, roadmap state, or Ready Bench state. It does not run authenticated mutation probes, map physical controls, select models, dispatch work, start/stop services, or claim live/database-verified/accepted status beyond cited observations. The correction will be committed locally only; no publication is made in this pass.

## 15. Evidence index

### Governing and parking authority

- `AI_HINTS.md`
- `docs/governance/RIVERVIEW_CHARTER.md`
- `docs/architecture/RIVERVIEW_FOUNDATION.md`
- `docs/operations/RIVERVIEW_EXECUTION_PLAN.md`
- `docs/operations/RIVERVIEW_ENGINEERING_INTERACTION_CONTRACT.md`
- `docs/operations/PARKING_LOT_AND_READY_BENCH.md`
- `docs/operations/parking_lot/PL-0007-web-capability-archaeology-and-consolidation.md`
- `docs/operations/parking_lot/PL-0008-web-operator-ui-stabilization-and-rearchitecture.md`
- `docs/operations/boards/parking_lot.md`
- `docs/operations/boards/ready_bench.md`
- `docs/operations/roadmap/README.md`
- `docs/operations/roadmap/RIVERVIEW_MASTER_ROADMAP.json`
- `docs/decisions/ADR-0001_POSTGRESQL_AUTHORITY.md`
- `docs/decisions/ADR-0002_DIAGNOSTICS_FIRST.md`

### Prior artifact and corrected lineage

- `A:\Riverview\repo` detached local commit `99b67d97cdf6f3e860ee6849ce10bcf583ab0273`
- stale parent `c29d6256e05bd0c98188a5113346cb3895f8259a`
- authoritative GitHub `origin/main` `3be31945eed8d47cbb12acf6be3d28165398caf3`
- current canonical local source `A:\Riverview\standalone`
- no publication of `99b67d9`

### Riverview and Estate archaeology

- `src/riverview/operator/ui.py`, `live_service.py`, `projection.py`, `room_admin.py`, `activity.py`, `snapshot.py`, `voice.py`, `transcription.py`
- `src/riverview/status/`, `src/riverview/diagnostics/`, `src/riverview/reasoning/gpu.py`, `src/riverview/campaign/`, `src/riverview/residents/`, `src/riverview/spatial/`
- `docs/operations/troubleshooting/README.md` and checkpoints `RIV-UI-0021`, `RIV-UI-0022`, `RIV-UI-0024` through `RIV-UI-0032`
- `docs/operations/roadmap/evidence/RV-010_BROWSER_OPERATOR_SURFACE.md`, `RV-010_PREFLIGHT_STATUS.md`, `RV-011_CONTROL_AUDIT.md`, `RV-016.5_QUEST_WEBXR_SPATIAL_IMMERSIVE_OBSERVABILITY_SCREEN_MIRROR_CHECKPOINT.md`, `RV-017.1_ESTATE_CAPABILITY_INVENTORY.json`, `RV-017.2_PARITY_MATRIX.json`, `RV-018.4_CAPACITY_BASELINE.md`, `RV-018.5_EXTENSION_CONTRACT.md`, `RV-018.6_RESIDENT_CONVERSATION_PARITY_AUDIT.md`
- `docs/operations/stream_deck/STREAM_DECK_CURRENT_INVENTORY.md`, `.json`, `STREAM_DECK_MAINTENANCE_AND_REPAIR_GUIDE.md`; `config/stream_deck/`; native plugin evidence
- `docs/RIVERVIEW_QUEST2_RECOVERY_PRIVATE_QUEST_WIRELESS_ADB_CAPABILITY_2026-08-21.md`
- Read-only Estate source: `A:\theestate\src\estate\core\steward_command_center.py`, `office_command_surface.py`, `office_executive_workspace.py`, `office_unified_search.py`, `office_settings_help_about_actions.py`, `office_validation_actions.py`, `office_parking_lot_controls.py`, `office_resident_actions.py`, `office_ai_service_actions.py`, `compute_office_panel.py`, `campaign_momentum_observer.py`
- Live observations: Riverview `http://127.0.0.1:18082/` and protected/404 routes; Estate `http://127.0.0.1:8765/` and `/status.json`; these are observation evidence only.

The durable artifact intentionally uses the requested PL-0007 filename as an elaboration linked to the existing PL-0007 and PL-0008 items. It leaves both captured items, the Parking Lot board, and Ready Bench state unchanged.
