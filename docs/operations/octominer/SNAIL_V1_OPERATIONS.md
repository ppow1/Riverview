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
# START / recover the durable controller
python -m riverview.snail --runtime var/snail start

# STOP at a resumable checkpoint
python -m riverview.snail --runtime var/snail stop

# STATUS
python -m riverview.snail --runtime var/snail status

# TEST
python -m pytest tests/test_snail_runtime.py

# explicit restart/recovery
python -m riverview.snail --runtime var/snail resume

# ingest the existing Octo2 Monitor V2 projection (normally scheduled by DEV)
python -m riverview.snail --runtime var/snail observe-worker \
  /path/to/campaign-runtime/octo2-current-v2.json

# dashboard (single maintained process)
python -m riverview.snail.server --runtime var/snail --host 127.0.0.1 --port 8785 \
  --latest-frame var/snail/video1/latest.jpg
```

Dashboard: `http://127.0.0.1:8785/`. Its control API is `POST /api/control`; status is
`GET /api/status`; the freshness-labelled video image is `GET /api/frame`.

## Worker and recovery contract

The production coordinator records Octo2 observations with `worker_observation`. A transition
to unavailable checkpoints `WAITING_FOR_WORKER`. Only a changed boot ID creates authoritative
reboot evidence. Once genuinely `80B_READY`, SNAIL reconstructs the pending packet from disk.
Verified operation IDs are replay fences, so recovery cannot repeat an already verified state
change. The worker response is rejected unless every structured contract field is present.

## Evidence and safety

Decision-relevant `latest.jpg` frames are copied into content-addressed immutable evidence before
use. The dashboard marks frames **STALE** and shows actual age after the configured threshold.
Every model action passes deterministic scope, target, type, authority, state, evidence, syntax,
and replay checks. A PowerShell `else` token rejects the complete script before execution.

Hardware paths for BIOS mutation, physical reset, and BIOS-grade vision are implemented as
policy gates but remain **HARDWARE-UNQUALIFIED**. They require later controlled qualification;
this release does not authorize C1 mutation.
