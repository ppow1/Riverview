# OCTOMINER 1 MULTI-P100 BIOS CAMPAIGN — PROJECT REQUIREMENTS

Status: CANONICAL CAMPAIGN QUICK-REFERENCE

Authority: This document is a concise operational projection of `APPROVED_PROPOSAL.md`, `REGROUND_CONTRACT.md`, and the durable SNAIL campaign state. If this document conflicts with those sources, the approved proposal / durable campaign evidence wins and this document must be corrected.

## Primary requirement / North Star

Achieve stable operation of OctoMiner 1 with **10 or more Tesla P100 16 GB GPUs**.

The known two-P100 boundary is the problem being solved. Intermediate work is valuable only insofar as it advances, explains, verifies, or safely supports that objective.

## Success requirements

A claimed population level is successful only after physical testing at that population verifies the required chain:

1. Firmware initializes sufficiently to continue boot.
2. Required PCIe/MMIO/BAR resources are assigned.
3. The operating system boots.
4. All target P100 GPUs enumerate.
5. NVIDIA driver initialization succeeds.
6. A defined workload operates.
7. Stability is demonstrated for the campaign-defined qualification interval.
8. Evidence is preserved in the durable campaign record.

No claim of 3/4/10-P100 support may be made before that physical population is actually tested.

## Secondary requirements

- Preserve practical boot behavior where possible.
- POST/firmware latency is a measured engineering variable, **not the primary campaign goal**. A slow candidate that materially advances the 10-P100 objective is evidence, not automatically a failure.
- Candidate development is incremental by default: make the smallest justified firmware change and preserve what is learned.
- Preserve the known booting C0 baseline.
- Stock recovery is a contingency/end-of-branch operation and remains Steward-gated.

## Evidence and verification requirements

- A command being sent is never proof that its intended effect occurred.
- State-changing actions require independent verification through the defined observation path.
- Every test must define objective, hypothesis, exact change, held-constant variables, pass condition, fail condition, timeout/failure policy, and recovery/branch behavior before execution.
- Every action, observation, timeout, retry, branch, state transition, notification, and Steward interaction belongs in durable campaign evidence/event history.
- SNAIL persistent state/evidence is authoritative; model/chat memory is not.
- New qualified knowledge must be promoted into the durable local campaign record and appropriate GitHub documentation.

## Reground requirements

A full campaign reground is required:

- after every completed test before designing/authorizing the next test;
- before every phase transition;
- at the beginning of a new ChatGPT session/context;
- after an architecture contradiction, rediscovery of already-known information, or disagreement between conversation and durable evidence.

Use this order before new discovery:

1. Campaign-local canonical material and SNAIL durable state/evidence.
2. Authoritative Riverview/GitHub documentation and known-good implementation.
3. Local filesystem verification.
4. Live-system discovery.
5. New investigation only when the prior sources genuinely do not answer the question.

Operational rule: **DURABLE KNOWLEDGE BEFORE DISCOVERY. DISCOVERY BEFORE INVENTION.**

## Authority and safety boundaries

- Steward (Pat): campaign authority, physical operator, pause/inquiry/abort, physical GPU moves, JIT reset, stock-recovery authorization, investigation redirection.
- SNAIL: persistent campaign controller and durable task owner.
- Octo2/80B: reasoning worker, not campaign database and not unrestricted hardware authority.
- ChatGPT: engineering lead / experiment planner; must use durable evidence and must not treat unobserved actions as success.
- Hardware mutation may occur only through the campaign's qualified/authorized path and current authority gate.
- Current persisted direction must be obeyed before any candidate mutation.
- PowerShell used for this campaign must contain **no `else` token**.
- Diagnostic/discovery PowerShell result packets must be collected and copied to the clipboard for handoff.

## Steward Status requirements

The Steward Status site is a first-class control plane. It must expose, persistently and visibly:

- campaign name;
- campaign goal: stable 10+ P100s;
- current round/phase;
- current task/test objective;
- current SNAIL state and authority/intervention state;
- latest evidence / verified machine state / next proposed action;
- links to this Project Requirements document and the canonical Process Map;
- snapshot controls and recent event history.

Every SNAIL snapshot/review packet must include copies of, or immutable references plus readable content for, the Project Requirements and Process Map so a future AI/human review receives the campaign North Star and operating path with the snapshot.

## Current known campaign position

The campaign has advanced beyond the recovered 2026-10-06 planning checkpoint:

- Campaign: Octo1 Multi-P100 BIOS
- Campaign status: ACTIVE
- Last verified physical baseline: C0
- BIOS mutations recorded by the recovered SNAIL runtime before C1 physical qualification: 0
- C1 candidate: `OCTOMINER1-C1-128G-UNFLASHED.bin`
- C1 full-image SHA-256: `1aa985e185a5eb2dbfcd732d38e75788244752565236f419e9c42860cae37741`
- C1 offline validation: PASSED
- C1 physical validation: PENDING
- Current software phase: C1 PHYSICAL QUALIFICATION PREP
- Standing campaign GO remains in force for routine in-scope candidate writing, verification, rebooting, testing, rejection, and iterative progression.
- Steward intervention is reserved for the explicit campaign boundaries: physical work, stock recovery, scope expansion, or genuinely unresolved conditions that automation cannot reconcile.

This section is informational. The live SNAIL state is authoritative after the updated runtime migrates and reconciles the recovered checkpoint.
