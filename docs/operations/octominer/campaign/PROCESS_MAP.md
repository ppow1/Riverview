# OCTOMINER 1 MULTI-P100 BIOS CAMPAIGN — PROCESS MAP

Status: CANONICAL CAMPAIGN QUICK-REFERENCE

Authority: This map operationalizes `APPROVED_PROPOSAL.md`, `REGROUND_CONTRACT.md`, SNAIL operations, and durable campaign state. Those sources remain authoritative if a conflict is discovered.

## Campaign flow

```text
START / RECOVER
      |
      v
LOCATE + LOAD EXISTING SNAIL RUNTIME
      |
      v
RECONCILE DURABLE STATE
state.json + events.jsonl + checkpoints + evidence + snapshots
      |
      v
FULL REGROUND
approved proposal + campaign state + proven facts + failures
+ lessons + open questions + relevant completed tests + Git state
      |
      v
CONFIRM NORTH STAR
stable operation with 10+ Tesla P100 16 GB GPUs
      |
      v
IDENTIFY CURRENT PHASE / ROUND / TEST
      |
      v
BUILD IMMUTABLE TEST PLAN
objective + hypothesis + exact delta + constants held
+ expected result + pass/fail + timeout + recovery/branch
      |
      v
AUTHORITY / SAFETY GATE
qualified adapter? permitted scope? Steward gate required?
      |
      +---- NOT AUTHORIZED ----> WAITING_FOR_STEWARD / STOP
      |
      v
EXECUTE ONE BOUNDED OPERATION
      |
      v
INDEPENDENTLY VERIFY EFFECT
command acceptance alone is not success
      |
      v
PRESERVE EVIDENCE + APPEND EVENT + CHECKPOINT
      |
      v
CLASSIFY RESULT
PASS / FAIL / PARTIAL / INCONCLUSIVE
      |
      v
UPDATE DURABLE KNOWLEDGE
proven facts + failures + lessons + open questions
      |
      v
FULL REGROUND BEFORE NEXT TEST
      |
      v
ADVANCES 10-P100 OBJECTIVE?
      |
      +---- NO ----> branch/stop/re-plan from evidence
      |
      v
NEXT INCREMENTAL CANDIDATE / PHYSICAL POPULATION TEST
      |
      v
3 P100 -> 4 -> 5/6 -> 8 -> 10+ as justified by evidence
      |
      v
VERIFY OS + ENUMERATION + DRIVER + WORKLOAD + STABILITY
      |
      v
10+ P100 QUALIFIED
```

## Persistent ownership loop

SNAIL owns campaign continuity. Octo2/80B and ChatGPT are reasoning resources, not the durable campaign database.

```text
SNAIL durable state/evidence
        |
        v
observe -> reason -> validate -> authorize -> execute -> verify
   ^                                                   |
   |                                                   v
   +--------- checkpoint / evidence / next work <------+
```

A reboot, model restart, chat change, or worker replacement must resume from durable state rather than reconstructing the campaign from memory.

## Required order when a question appears

```text
1. Campaign-local canonical material + SNAIL evidence
2. Riverview/GitHub known-good documentation/implementation
3. Local filesystem verification
4. Live-system discovery
5. New investigation
```

If an answer exists at an earlier level, do not rediscover it at a later level.

## Candidate/test loop

For each candidate or test:

1. Reground.
2. State the exact relationship to the 10+ P100 objective.
3. State hypothesis.
4. State exact change from accepted baseline/candidate.
5. State variables held constant.
6. State expected observation.
7. State pass/fail/partial/inconclusive criteria.
8. State timeout and recovery/branch behavior.
9. Check authority and adapter qualification.
10. Execute only the bounded operation.
11. Independently observe the effect.
12. Preserve immutable evidence.
13. Append event(s).
14. Checkpoint.
15. Classify result.
16. Update durable knowledge.
17. Reground before designing the next test.

## Physical GPU-capacity ladder

The preferred end target is 10+ P100s. Population steps are evidence-driven rather than ceremonial, but claims require physical qualification at the claimed population.

```text
C0 / known booting baseline
        |
        v
firmware candidate demonstrates useful resource behavior
        |
        v
3 x P100 physical qualification
        |
        v
higher populations as evidence justifies
        |
        v
10+ x P100 physical qualification
```

At each population, record at minimum:

- POST/firmware behavior and timing;
- PCIe/MMIO/BAR assignment evidence;
- OS boot result;
- exact P100 enumeration count;
- NVIDIA driver initialization;
- workload result;
- stability result;
- failure evidence if unsuccessful.

Boot latency is diagnostic/secondary. It must be recorded, but it must not silently replace the 10+ P100 objective.

## Recovery after DEV/worker reboot

```text
Do not initialize a new campaign
        |
        v
locate existing runtime
        |
        v
read state/events/checkpoints/evidence
        |
        v
restore required services
        |
        v
start/recover SNAIL against the existing runtime
        |
        v
SNAIL reconciles from disk
        |
        v
confirm state against last durable checkpoint
        |
        v
resume only from documented campaign position
```

## PowerShell campaign rules

- No `else` token.
- Diagnostic/discovery scripts collect a complete `$Result` packet.
- The complete result packet is displayed and copied to the clipboard.
- Scripts identify mutation status explicitly.
- Do not claim an action succeeded from command acceptance alone.

## Snapshot / handoff contract

Every campaign snapshot/review packet must carry enough context that a new AI/human reviewer cannot reasonably miss the objective or process. Include:

1. `PROJECT_REQUIREMENTS.md` content.
2. `PROCESS_MAP.md` content.
3. current `state.json` projection.
4. relevant recent event history.
5. current evidence references.
6. current phase/task/direction and authority boundary.
7. Git revision / document revision when available.

The Steward Status site must provide visible links to the requirements and process map so the same canonical material is available during live operation and in captured screenshots.

## Current recovery point

Recovered durable state after the 2026-10-06 DEV Windows reboot:

- ACTIVE campaign.
- C1 PLANNING.
- WAITING_FOR_STEWARD.
- C0 is last verified baseline.
- zero SNAIL-recorded BIOS mutations.
- next task: generate C1 BIOS planning proposal for Steward/external review.
- preserve C0; no C1 mutation without later Steward/external-review authorization.

The live SNAIL state supersedes this informational recovery-point section after the campaign advances.