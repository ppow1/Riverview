# SNAIL v1.0 Operations

SNAIL is a DEV-hosted, persistent campaign controller. Octo2/80B is a stateless reasoning
worker; it is never the campaign database. Campaign behavior is configured independently from
the engine in `src/riverview/snail/campaigns/octo1_multi_p100.json`.

## Install and storage

From the repository root, install with `python -m pip install -e .`. The examples below use
`var/snail` as the runtime root:

* authoritative state: `var/snail/state.json`
* append-only hash-chained event log: `var/snail/events.jsonl`
* checkpoints: `var/snail/checkpoints/`
* immutable evidence and metadata: `var/snail/evidence/`
* snapshots and review packets: `var/snail/snapshots/*.zip` (`REVIEW_PACKET.md` is inside)
* live mutable video frame: `var/snail/video1/latest.jpg`

Existing production campaign material must be backed up before deployment into its production
runtime root. Atomic state replacement and immutable, content-addressed evidence protect normal
runtime updates.

## Commands

```text
# START / recover and run the autonomous coordinator
python -m riverview.snail --runtime var/snail run \
  --monitor-state /path/to/campaign-runtime/octo2-current-v2.json \
  --latest-frame /path/to/campaign-runtime/video1/latest.jpg

# STOP at a resumable checkpoint
python -m riverview.snail --runtime var/snail stop

# STATUS
python -m riverview.snail --runtime var/snail status

# TEST / complete production qualification
python -m pytest tests/test_snail_runtime.py tests/test_snail_coordinator.py \
  tests/test_snail_steward_integration.py

# request explicit recovery while the service is running
python -m riverview.snail --runtime var/snail resume

# ingest the existing Octo2 Monitor V2 projection (normally scheduled by DEV)
python -m riverview.snail --runtime var/snail observe-worker \
  /path/to/campaign-runtime/octo2-current-v2.json

```

`run` (and its `start` alias) is the supported production coordinator entry point. It does not
bind an HTTP port and does not return after merely setting `READY`. The coordinator waits without
busy-spinning, consumes the existing
Octo2 Monitor V2 projection, calls the configured 80B endpoint when reasoning is needed, validates
and executes only allowlisted adapters, independently reads effects back, checkpoints, and chooses
the next work item. `STOP` is a durable queued control: the coordinator reaches its next atomic
boundary, checkpoints, and shuts down the coordinator. Re-running `run` reconstructs and reconciles
from disk before any state-changing work.

The existing `riverview.status.server` remains the sole Steward HTTP owner. For the qualified
OctoMiner deployment it is launched on `127.0.0.1:8785` with the SNAIL runtime mounted:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File \
  tools/powershell/status/Start-RiverviewStewardStatus.ps1 \
  -RepositoryPath A:\Riverview\standalone -Port 8785 \
  -SnailRuntime A:\Riverview\standalone\var\snail
```

This preserves the existing River status, roadmap, worker, escalation, work, and diagnostic
projection while adding SNAIL to the same page. SNAIL never binds 8785, so restarting or stopping
the coordinator cannot collide with or terminate Steward. The integrated endpoints are:

* dashboard: `http://127.0.0.1:8785/`
* existing River projection: `GET /api/status`
* SNAIL projection: `GET /api/snail/status`
* durable SNAIL controls: `POST /api/snail/control`
* freshness-labelled video1 image: `GET /api/snail/frame`

## Worker and recovery contract

The production coordinator records Octo2 observations through `StewardEnvironmentObserver`. A
transition to unavailable checkpoints `WAITING_FOR_WORKER`. Only a changed boot ID creates authoritative
reboot evidence. Once genuinely `80B_READY`, SNAIL reconstructs the pending packet from disk.
Verified operation IDs are replay fences, so recovery cannot repeat an already verified state
change. The worker response is rejected unless every structured contract field is present.

The production coordinator is `SnailCoordinator`; it is the sole state-machine driver. The current
authorized executor is `LocalPlanningAdapter`. It writes only a fixed C1 review-proposal path or
the harmless qualification marker—never a model-selected filesystem path—and verifies by
independent byte-for-byte read-back before preserving effect evidence. Hardware mutation, reset,
power, and stock-recovery operations have no executable adapter and remain prohibited.

## Evidence and safety

Decision-relevant `latest.jpg` frames are copied into content-addressed immutable evidence before
use. The dashboard marks frames **STALE** and shows actual age after the configured threshold.
Every model action passes deterministic scope, target, type, authority, state, evidence, syntax,
and replay checks. A PowerShell `else` token rejects the complete script before execution.

Hardware paths for BIOS mutation, physical reset, and BIOS-grade vision are implemented as
policy gates but remain **HARDWARE-UNQUALIFIED**. They require later controlled qualification;
this release does not authorize C1 mutation.

## Recovery and inspection

Reasoning requests/responses are under `var/snail/reasoning/`; the current environment projection
is `var/snail/observations/latest-environment.json`; generated review artifacts are under
`var/snail/artifacts/`. Before execution, SNAIL records `AUTHORIZED_NOT_EXECUTED`, then records
`EXECUTION_UNCERTAIN` durably before calling an adapter. After a crash in either execution window,
recovery verifies the effect first. It never blindly replays an uncertain state change. A verified
C1 planning proposal causes a Snapshot and a durable `WAITING_FOR_STEWARD` authority-boundary
event rather than firmware mutation.
