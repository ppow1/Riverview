# OctoMiner BIOS Campaign — Current State

## Checkpoint

Timestamp: 2026-10-01

Phase: Campaign Infrastructure Qualification

Status: INFRASTRUCTURE QUALIFIED

Objective:

Establish autonomous and observable infrastructure before BIOS candidate
execution.

## Qualified Scaffolding Tests

- T-SCAF-001 — PASS
  OCTO2 80B dependency monitor qualification.

- T-SCAF-002 — PASS
  OCTO2 reboot and automatic 80B recovery observation.

- T-SCAF-003 — PASS
  OCTO2 Monitor V2 parallel qualification and V1 handoff.

- T-SCAF-004 — PASS
  Five-node campaign infrastructure health qualification.

Current authoritative test totals:

- Total: 4
- Passed: 4
- Failed: 0
- Pending: 0
- Aborted: 0
- Unmarked: 0

## Infrastructure Baseline

### DEV

Status: READY

Role:

- campaign controller
- Steward dashboard host
- campaign repository host

### OCTO1

Address: 192.168.1.160

SSH alias: octo1

Status: READY

Qualified management path:

- SSH/22

### OCTO2

Address: 192.168.1.162

SSH alias: octo2

Status at checkpoint: READY

Worker state:

80B_READY

Current boot ID:

abdc5f55-ef04-4b50-ac9a-bd6dfac9c7c7

Qwen3-Next 80B llama-server PID at the qualified checkpoint:

752

OCTO2 health authority:

controller/octo2_monitor_v2.py

## OCTO2 Reboot Counter

Current count:

2

The count is authoritative from the controlled reboot qualification forward.

Current authoritative boot ID:

abdc5f55-ef04-4b50-ac9a-bd6dfac9c7c7

The earlier historical asterisk is no longer required.

## PiKVM

Address: 192.168.1.169

SSH alias: pikvm

Status: READY

Qualified management paths:

- SSH/22
- HTTP/80
- HTTPS/443

## Video-KVM Pi

Address: 192.168.1.101

SSH alias: video1

Status: READY

Qualified management path:

- SSH/22

## Steward Dashboard

Address:

http://127.0.0.1:8785/

Qualified capabilities:

- live campaign status
- authoritative test-result counting
- five-node infrastructure health
- OCTO2 80B state
- OCTO2 reboot count
- campaign event display
- downloadable campaign Snapshot ZIP

Snapshot packages the dashboard, controller, runtime state, campaign
documentation, test documents, and Git state so the visible campaign context
can be transferred back into ChatGPT for review.

## OCTO2 Monitor V2

Monitor V2 is the active OCTO2 campaign witness.

Qualified behavior includes:

- SSH reachability
- boot-ID tracking
- persistent last-known boot identity
- explicit boot-change events
- llama-server PID detection
- API-readiness detection
- 80B_LOADING distinction
- 80B_READY detection
- persistent reboot counting

The approximately six-minute 80B cold-load observation remains an observed
data point rather than a universal startup specification.

## Important Proven Recovery Sequence

The campaign has directly observed:

80B_READY
→ OCTO2_UNREACHABLE
→ new OCTO2 boot ID
→ 80B_LOADING
→ 80B_READY

OCTO2 automatically restarted its 80B service after reboot without Steward
intervention.

## Current Infrastructure Result

At the infrastructure qualification checkpoint:

- DEV — GREEN / READY
- OCTO1 — GREEN / READY
- OCTO2 — GREEN / READY
- PiKVM — GREEN / READY
- Video-KVM Pi — GREEN / READY

## Architectural Follow-Up

Generic infrastructure TCP checks currently execute synchronously from the
Steward API with bounded 0.75-second timeouts.

This is acceptable for current campaign qualification.

Future improvement:

Move generic infrastructure probing into a persistent monitor/cache so dashboard
HTTP latency is independent of unavailable hosts.

## Next Campaign Boundary

Infrastructure scaffolding is qualified.

The next phase may begin implementing and qualifying the machinery required for
actual BIOS candidate execution.

No BIOS candidate should be treated as qualified merely because the
infrastructure scaffolding is qualified.
