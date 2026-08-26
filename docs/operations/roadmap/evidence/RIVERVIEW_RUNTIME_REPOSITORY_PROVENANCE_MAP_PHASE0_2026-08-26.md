<!--
File: docs/operations/roadmap/evidence/RIVERVIEW_RUNTIME_REPOSITORY_PROVENANCE_MAP_PHASE0_2026-08-26.md
Version: 1.0.0
Date: 2026-08-26
Purpose: Phase 0 forensic map of Riverview repository and runtime provenance.
-->

# Riverview Runtime Provenance Map — Phase 0

Status: DISCOVERY COMPLETE; CONSOLIDATION NOT AUTHORIZED
Authority: Steward direction, verified A: filesystem/Git/process evidence
Search scope: A: repository/source archaeology; C: only live executable/dependency paths

## Architectural correction

The Estate and Riverview are separate systems. The Estate is the legacy/current
operational system and capability source during migration. Riverview is the
successor/replacement system. Temporary adapters, shared PostgreSQL, or reused
Estate presenters do not make Riverview a subsystem of The Estate.

A filesystem path is not institutional authority. No permanent canonical
Riverview root is declared by this report.

## Current authoritative Git evidence

The current checkout used for this Phase 0 work is:

- Path: `A:\theestate\Riverview`
- Git root: `A:\theestate\Riverview`
- Branch: `main`
- HEAD: `ec9075bfec7655fe67e7c4455bfd9c644b2d2d52`
- origin URL: `https://github.com/ppow1/Riverview.git`
- origin/main: `ec9075bfec7655fe67e7c4455bfd9c644b2d2d52`
- Worktree: dirty only from the pre-existing Grace/Jessica changes and this report
- Published state: HEAD equals network `origin/main`

This is the current GitHub main checkout, not yet the permanently established
standalone filesystem authority.

## Live runtime map

### Riverview Runtime Supervisor

- Task: `\\Riverview Runtime Supervisor`
- Status: Running
- Task launcher: `A:\\Riverview\\repo\\tools\\powershell\\runtime\\Start-RiverviewRuntimeSupervisor.ps1`
- Task repository argument: `A:\\Riverview\\repo`
- Supervisor process IDs observed: `19020`, `19036`
- Working directory: `A:\\Riverview\\repo`
- Runtime status SHA: `c29d6256e05bd0c98188a5113346cb3895f8259a`
- Owner: `riverview.runtime.supervisor`
- Important finding: installed lifecycle ownership is bound to the detached alternate checkout.

### Riverview Operator website/API

- Listener: `127.0.0.1:18082`
- Process IDs observed: `24148`, `24176`
- Command: `.venv/Scripts/python.exe -m riverview.operator.live_service`
- Executable/environment: `A:\\Riverview\\repo\\.venv\\Scripts\\python.exe` / Python 3.14 runtime
- Working directory: `A:\\Riverview\\repo`
- Health: HTTP 200
- Served SHA: `c29d6256e05bd0c98188a5113346cb3895f8259a`
- Startup: Runtime Supervisor task and supervisor registry
- Auto-restart: enabled in the runtime registry
- Database: current Riverview PostgreSQL connection
- Classification: live installed service, provenance mismatch with current main checkout

### Grace conversation

Observed path:

`Operator -> /api/chat -> ResidentConversationGateway.chat -> OllamaReasoningAdapter.complete -> Ollama /api/generate -> typed ReasoningResponse -> Operator projection`

- Source checkout: `A:\\Riverview\\repo`
- Provider: `ollama:qwen3-coder:30b-qwencode-20k`
- Ollama listener: `127.0.0.1:11434`
- Ollama process: `C:\\Users\\wille\\AppData\\Local\\Programs\\Ollama\\ollama.exe serve`
- Model inventory confirms `qwen3-coder:30b-qwencode-20k`; the Ollama service is shared local infrastructure
- Hardware: NVIDIA GeForce RTX 4090, 24,564 MiB total; 22,547 MiB used at observation
- Persistence: Operator conversation projection and current Riverview PostgreSQL
- Cognition path: real provider-neutral chat generation, but not `HomeCognitionService` / `HOME_COGNITION` F1-F3-P1-P2/F2 provenance path
- No 3060/small-brain/big-brain/shared-cognition optimization was inspected or implemented

### Jessica conversation/character path

- Runtime source: same live Operator at `A:\\Riverview\\repo`
- Resident identity source: PostgreSQL resident continuity plus bounded registry evidence
- Current accepted Jessica ID observed: `f98ff6cc-907a-5ac9-909f-7165358084d2`
- Current role: `Chief Character Architect`
- Character state path: `CharacterStore` accepted versions plus `ContinuityStore`; current initiative changes are only in the authoritative checkout and are not installed in the live runtime
- Existing workflow: generic inspect/propose/review/publish mechanism; no dedicated live interactive Jessica development surface has been accepted

### PostgreSQL consumers

Read-only `pg_stat_activity` showed eight idle and one active local connection with blank
application names at observation time. Process provenance identifies the active
Riverview consumers as the Runtime Supervisor's children rooted at
`A:\\Riverview\\repo` (Operator, CME, Comms5, Relay, and Spatial). PostgreSQL
authority does not establish repository authority.

### Other live Riverview services

All observed Riverview service processes use `A:\\Riverview\\repo`:

- CME: `riverview.autonomy.live_service`; multiple observed instances; one runtime status marked `duplicate-process`
- Relay: multiple `riverview.relay.worker` processes; runtime status showed duplicate-process failure
- Comms5 HTTP: `127.0.0.1:11826`; `riverview.mcp.comms5_http_server`
- Comms5 transport: runtime-managed reverse transport identity
- Spatial: `127.0.0.1:18443` / LAN `192.168.1.88:18443`; `riverview.operator.lan_spatial_service`; duplicate observed instances
- Ollama is an external local provider dependency, not a Riverview repository
- Stream Deck plugin is installed under the user profile and points at the Operator surface; it is an adapter, not repository authority

## Discovered Riverview Git checkouts/copies

The following A:-scoped Riverview-specific checkouts were identified. No checkout
was moved, deleted, reset, cleaned, merged, or rewritten.

| Path | Branch/state | HEAD | Remote relation | Worktree | Classification |
|---|---|---|---|---|---|
| `A:\\theestate\\Riverview` | `main` | `ec9075b` | origin/main exact | dirty, 4 paths | current GitHub main / candidate source |
| `A:\\Riverview\\repo` | detached | `c29d625` | network origin/main `ec9075b`; 27 commits behind local tracking | dirty, 13 paths | active installed runtime; historical checkout |
| `A:\\Riverview\\main-integration` | `codex/grace-main-integration` | `de22077` | behind current main | clean | historical Grace integration |
| `A:\\Riverview\\main-reconcile` | detached | `fb11720` | behind current main | dirty, 2 paths | historical cognition reconciliation |
| `A:\\Riverview\\p1repair` | `codex/c484-operator-persistent-service-repair` | `82b515b` | branch-only historical line | clean | historical repair worktree |
| `A:\\Riverview\\p3work` | `codex/c484-operator-persistent-service-p3` | `3251993` | branch-only historical line | clean | historical capacity worktree |
| `A:\\Riverview\\run004c-r1` | detached | `ecf5607` | old remote-main snapshot | clean | historical GRC-003/E4 checkpoint |
| `A:\\Riverview\\runtime\\publication\\rv0052-final-20260814-160206` | detached | `34b672f` | old snapshot | dirty, 9 paths | historical publication staging |
| `A:\\riverview-c465-20260819` | `codex/c465-jessica-continuity-contract` | `7bde793` | historical branch | clean | Jessica contract evidence |
| `A:\\riverview-c466-20260819` | `codex/c466-resident-continuity-persistence` | `04b6908` | historical branch | clean | Jessica persistence evidence |
| `A:\\riverview-c467-20260819` | `codex/c479-jessica-uncensored-32b-comparison` | `b786d95` | historical branch | clean | Jessica model comparison worktree |
| `A:\\riverview-verify-20260819-b` | `codex/c464-jessica-archaeology-corpus` | `76f7121` | historical branch | clean | Jessica archaeology worktree |
| `A:\\Riverview\\reference\\theestate` | `main` | `8d1e243` | `ppow1/theestate` | clean | Estate reference checkout, not Riverview |
| `A:\\Riverview\\reference\\CueMastery` | `main` | `9efce59` | `ppow1/CueMastery` | clean | project reference checkout, not Riverview |

The broad A: scan also found hundreds of Estate audit/test worktrees under
`A:\\EstateRuntime\\workspaces\\audit\\estate-main` and many historical Estate
copies at A: top level. Those are not individually classified as Riverview
repositories by this Phase 0 report. Their existence is preserved as a future
archaeology/cleanup scope, not as disposable residue.

## Known checkout comparison

`A:\\theestate\\Riverview` and `A:\\Riverview\\repo` share common ancestor
`c29d6256e05bd0c98188a5113346cb3895f8259a`.

- Current main has 38 commits after that ancestor, including the accepted Hermes
  execution integration, Grace cognition packages, and Tranche 2 checkpoint.
- The runtime checkout has no committed descendants beyond that ancestor.
- Current main contains 63 tracked paths absent from the runtime checkout, including
  the cognition, Hermes, resident-continuity, and campaign-runner implementation.
- The runtime checkout has no tracked paths absent from current main.
- Runtime-only value is uncommitted spatial/operator changes and 11 untracked
  evidence/tool paths; these must be reviewed and preserved before any reconciliation.
- Current-main-only value is committed and remotely verifiable; it is not installed
  in the running service.

## Documentation authority findings

Documents that currently teach stale or ambiguous topology include:

1. `README.md` and `docs/architecture/RIVERVIEW_FOUNDATION.md`: describe The Estate
   at Riverview as Riverview's final environment rather than identifying The Estate
   as a legacy/current system and Riverview as its successor.
2. `tools/powershell/bootstrap/Initialize-RiverviewFoundation.ps1`: embeds the same
   stale foundation wording and must be corrected together with the source document.
3. `docs/operations/GRACE_ENGINEERING_TASK_SUBMISSION_TEMPLATE.md`: uses
   `A:/Riverview/repo` as a repository root before a canonical standalone root has
   been formally reconciled.
4. `docs/operations/roadmap/evidence/RV-012.2_RIVERVIEW_REPOSITORY_MAP.json`:
   records `A:/Riverview/repo` as a root without distinguishing installed runtime
   provenance from development authority.
5. `docs/operations/parking_lot/PL-0004-historical-branch-archaeology-and-cleanup.md`:
   says `main` is authority without naming a reconciled filesystem root.
6. Runtime registry and installed supervisor state under `A:\\Riverview\\repo`:
   operationally point to the detached runtime checkout.

These should be corrected in a reviewed topology/authority tranche after this map
is accepted. This Phase 0 report does not silently rewrite broad architecture.

## Safest standalone recommendation

Do not choose `A:\\theestate\\Riverview` or `A:\\Riverview\\repo` as permanent
canonical root yet.

The safest next tranche is a read-only reconciliation package that:

1. accepts `origin/main` as the committed source baseline;
2. inventories and hashes dirty/untracked runtime artifacts in `A:\\Riverview\\repo`;
3. compares those artifacts against current main and remote branches;
4. classifies/recoveries unique spatial/operator work without touching the dirty checkout;
5. selects one standalone canonical root under `A:\\Riverview`;
6. updates the Runtime Supervisor and all launcher/config pointers atomically;
7. verifies one owner per service, exact SHA, health, and PostgreSQL compatibility;
8. preserves the old runtime checkout as a retained rollback/reference copy until
   the Steward accepts the transition.

Based on current evidence, `A:\\Riverview\\repo` is the natural standalone root
candidate because it already owns the installed runtime, but that is a candidate,
not an authorization or final decision. `A:\\theestate\\Riverview` is the current
main source candidate because it contains the later committed work. The two must
be reconciled, not copied over one another.

## Self-diagnostic requirement

Riverview should eventually expose a bounded provenance projection containing:

- running source SHA/version;
- filesystem/source root;
- launcher and owning supervisor/task;
- database identity/configuration reference;
- provider/model/resource;
- declared canonical root and match/mismatch result;
- duplicate/stale runtime detection;
- evidence and checkpoint for any mismatch.

A minimal `/health` source SHA is useful but insufficient; the future projection
must distinguish declared authority, runtime source, process owner, and database
connection without exposing credentials.

## Phase 0 boundary

Discovery and reporting are complete. No repository relocation, cleanup, branch
removal, merge, reset, archive, runtime ownership change, or Grace/Jessica
implementation continuation was performed after the provenance correction.
