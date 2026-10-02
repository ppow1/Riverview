# CAMPAIGN REGROUND PACKET

Generated: 2026-10-02T17:16:13-04:00

This packet is generated from durable campaign evidence. It is intended to be reviewed before the next test is designed.


========================================================================
# SOURCE: REGROUND_CONTRACT.md
========================================================================

# REGROUND CONTRACT

## Purpose

Prevent campaign reasoning from drifting because of ChatGPT context loss,
session changes, long-context compression, or failure to consult durable
project evidence.

Durable campaign state and canonical project documents are authoritative.
Conversational memory is not a substitute for them.

## Mandatory Reground Boundaries

A REGROUND is required:

1. After every completed test, before designing or authorizing the next test.
2. Before every campaign phase transition.
3. At the beginning of a new ChatGPT session/context.
4. After any detected architecture contradiction, rediscovery of already-known
   information, or disagreement between conversational assumptions and durable
   campaign evidence.

## Canonical Reground Sources

The reground packet must include, when present:

1. Original approved proposal / operating contract.
2. CAMPAIGN_STATE.md
3. PROVEN_FACTS.md
4. PROVEN_NOT_WORKING.md
5. LESSONS_LEARNED.md
6. OPEN_QUESTIONS.md
7. README.md
8. All completed test records relevant to the current phase.
9. Current Git state.
10. Current Steward/API state when available.

The original proposal is an architectural contract. Later campaign documents
may refine it only when the change is explicitly documented.

## Required Reground Output

Before the next test is designed, the reasoning/planning layer must explicitly
reconstruct:

- CURRENT PHASE
- CAMPAIGN GOAL
- CURRENT ROUND GOAL
- CURRENT TEST/TRANSITION STATE
- APPROVED ARCHITECTURE AND PLAYER ROLES
- PROVEN FACTS THAT MATTER NOW
- PROVEN FAILURES / APPROACHES NOT TO REPEAT
- APPLICABLE LESSONS LEARNED
- OPEN QUESTIONS
- THINGS THAT MUST NOT BE REDISCOVERED
- SAFETY / AUTHORITY BOUNDARIES
- NEXT ROADMAP STEP
- PROPOSED NEXT TEST

## Gate Rule

No next test may be designed or executed until the reground output has been
reviewed against the canonical packet.

If the packet contradicts conversational assumptions, the packet wins.

If required evidence is missing or ambiguous, stop and resolve the ambiguity
rather than reconstructing the answer from memory.

## Failure Rule

Rediscovering an architecture, interface, machine role, known failure, or
previously proven fact that is already documented is a process defect.

When this occurs:

1. Stop advancement.
2. Record the incident in LESSONS_LEARNED.md.
3. Perform a full reground.
4. Correct campaign state/documentation if necessary.
5. Resume only from the documented roadmap position.

## Phase Transition Rule

A phase transition requires a FULL REGROUND.

The transition record must identify:

- phase being closed
- completion evidence
- unresolved defects
- next phase
- entry criteria
- first permitted test

## Authority

This contract is part of the persistent campaign operating contract.

Chat history, model context, and human recollection may assist interpretation,
but none supersede durable campaign evidence.

## Mandatory Architecture Authority

Before advancing to a new test or campaign phase, the reground process MUST read:

- APPROVED_PROPOSAL.md

APPROVED_PROPOSAL.md is the canonical architecture and role-assignment authority.
The reground packet must preserve the approved roles and relationships rather than
reconstructing them from memory.


## Durable Knowledge Before Discovery

The campaign MUST consult durable engineering knowledge before rediscovering an
existing component from the live system.

For any existing architecture, service, adapter, script, machine role,
interface, workflow, or previously solved engineering problem, use this order:

1. Campaign-local canonical material:
   - APPROVED_PROPOSAL.md
   - REGROUND_PACKET.md
   - CAMPAIGN_STATE.md
   - PROVEN_FACTS.md
   - PROVEN_NOT_WORKING.md
   - LESSONS_LEARNED.md
   - OPEN_QUESTIONS.md
   - applicable test contracts and qualified campaign artifacts.

2. Authoritative project repositories:
   Search the applicable GitHub repository for documentation, known-good
   configurations, tests, scripts, operating procedures, prior decisions, and
   established interfaces before attempting to reconstruct how the component
   works.

   Existing infrastructure documented in repositories such as Riverview must
   be treated as existing engineering knowledge, not as an unknown system to
   rediscover.

3. Local filesystem:
   Compare the documented/known-good implementation against the files actually
   installed on the relevant machine.

4. Live-system discovery:
   Inspect processes, ports, devices, runtime configuration, logs, and behavior
   to verify the durable record or diagnose a discrepancy.

5. New investigation:
   Design new probes or implementations only when the durable record and live
   verification genuinely do not answer the question.

Operational principle:

DURABLE KNOWLEDGE BEFORE DISCOVERY.
DISCOVERY BEFORE INVENTION.

Live discovery SHOULD verify, qualify, or diagnose documented infrastructure.
It SHOULD NOT routinely reconstruct architecture that is already documented.

When current local campaign work produces new qualified infrastructure,
interfaces, tests, lessons, or operating procedures, that knowledge MUST be
promoted into the durable project record at an appropriate qualified
checkpoint. During active development the local campaign repository may be
ahead of GitHub; after useful qualification, GitHub should be brought current
so a future session, machine, or context can recover the engineering state
without rediscovery.

If an existing named component is encountered, the reground process must ask:

- Is this already documented?
- Is there a known-good implementation?
- Is there already a qualification/test script?
- Is there an established interface contract?

Only after those sources are checked should new discovery or implementation
work begin.


========================================================================
# SOURCE: APPROVED_PROPOSAL.md
========================================================================

# APPROVED PROPOSAL — AUTHORITATIVE TEXT EXTRACTION



> Source: OctoMiner1_Multi-P100_BIOS_Automation_Proposal_v1.0.docx

> Source SHA256: 65E24D30C90896137B9EC6095B008B26AA50B6778B1D2786C23E34431F0A422D

> This Markdown is a deterministic text extraction.

> The hash-identified DOCX remains the authoritative source.



OCTOMINER 1 MULTI-P100 BIOS AUTOMATION PROGRAM

Proposal, Roadmap, Roles, Interfaces, Contracts, Seams, Evidence, and Definition of Finished

Campaign objective

Develop and validate firmware behavior that can support more than the current two-P100 boundary on OctoMiner 1, with a preferred end target of stable operation with 10 or more Tesla P100 GPUs, while preserving practical boot behavior and producing complete evidence for every experiment.

Version 1.0 — 1 October 2026

1. Executive proposal

This program converts the manually proven KVM/control path into a persistent, multi-day engineering campaign. The system will observe, reason, act, verify, document, and continue across tests without depending on any one chat session. A command being sent is not proof of success; the effect must be independently observed through the HDMI acquisition path or another defined verification channel.

The current booting OctoMiner 1 state becomes Candidate 0 (C0). Candidate development is incremental by default: change the smallest justified set of firmware variables, record the hypothesis before execution, perform the write and verification, observe boot behavior, classify the result, and preserve what was learned. Recovery to stock is a contingency and end-of-branch operation, not a routine step between candidates.

Campaign GO is standing authorization for BIOS-region experimentation within the defined envelope. The controller does not request approval before every candidate write. Stock recovery remains Steward-gated. Physical reset is initially implemented as a just-in-time human handoff: pause, notify the Steward, request a reset-button press, independently verify the resulting reboot, then continue.

2. Proven starting point and constraints

OctoMiner 1 is presently booting and sufficiently stable to serve as the initial baseline.

PiKVM control endpoint: SSH alias pikvm; USB multifunction gadget is enumerated by OctoMiner 1 and HID keyboard input has been demonstrated.

Video acquisition endpoint: SSH alias video1; MacroSilicon UVC capture is available as /dev/video0 and has captured 1920×1080 MJPEG from OctoMiner 1.

Windows FFplay has displayed the live OctoMiner 1 console. Machine perception should consume video1 directly; FFplay remains a human viewer, not the authoritative automation sensor.

Passwordless SSH is established for octo1, video1, and pikvm.

PiKVM must not be casually rebooted because of the carrier boot-switch constraint. Independent power has been added so target USB power loss does not normally remove PiKVM power.

Automated motherboard reset is not yet wired. Until it exists, RESET_OCTO1 is a Steward-assisted operation.

The known stock boundary is specifically a P100 population problem, not a generic GPU-count problem: two P100s can coexist with another commercial GPU, while adding a third P100 has previously prevented normal boot.

Riverview documents a proven BIOS-region recovery path using x64 UEFI shell and Intel CSME 11.x Fpt.efi, deliberately leaving descriptor and ME regions untouched.

Previous high-MMIO experiments established that merely increasing allocation is insufficient if firmware initialization latency becomes unacceptable.

3. Goals and scope

3.1 Campaign goal

Reach stable operation beyond the current two-P100 boundary, preferably 10+ Tesla P100 GPUs, while retaining acceptable firmware initialization, OS boot, device enumeration, driver initialization, workload operation, and stability.

3.2 Immediate Phase-1 goal

Produce and install a high-MMIO BIOS candidate that behaves like the stock BIOS in practical boot timing and normal operation, eliminating the catastrophic initialization delay seen in earlier large-MMIO experiments. The result is qualified for later physical testing with at least three P100s; Phase 1 does not claim that three-P100 capability has been proven.

3.3 Exploratory follow-on

If a working high-MMIO solution is found, investigate whether the successful allocation behavior can be exposed as a BIOS/Setup setting rather than remaining a hard-coded firmware value. This is an exploratory objective, not a requirement for campaign success and must not delay validation of a working hard-coded solution.

3.4 Explicitly deferred

Production-grade credential management and security hardening.

Automatic GPIO/transistor reset implementation.

Claims of 3/4/10-P100 support before the corresponding physical population has actually been tested.

Automatic stock recovery without Steward approval.

4. Players and roles

Player

Role

Responsibilities

Boundary

Steward (Pat)

Authority / physical operator

Starts campaign; Pause/Inquiry/Abort; performs physical GPU moves and JIT reset; decides whether to authorize stock recovery; may redirect investigation.

Not required for routine candidate writes, retries, observations, or ordinary test progression.

ChatGPT

Engineering lead / experiment planner

Maintain roadmap; formulate hypotheses; define candidates, tests and acceptance criteria; synthesize accumulated evidence; formulate next rounds.

Must not treat unobserved actions as success or erase prior evidence.

Hermes

Executor / orchestrator

Own deterministic runtime execution: PowerShell/SSH/process control, tool adapters, event publication, evidence collection, state-machine advancement.

Must not invent unapproved destructive scope or silently cross a safety boundary.

OctoMiner 2 80B

Deep local reasoning worker

Analyze difficult BIOS screens, failure evidence, candidate comparisons and round synthesis when useful.

Reasoning service, not unrestricted hardware authority.

Dev-machine 8B

Fast local utility model

Cheap classification, log parsing, known-screen recognition, bounded summarization.

Not final authority for BIOS mutation.

Codex

Scarce implementation/debugging reserve

Use only when bounded coding/debugging work materially accelerates progress or other methods stall.

Not normal runtime loop; conserve available usage.

Playwright

Optional browser/UI adapter

Reuse existing browser automation if a required interface is best controlled through a browser.

Do not use when SSH/API/direct process control is simpler.

Riverview notification system

Escalation channel

Audio/visible notification when the Steward is genuinely required.

No routine chatter; status console is the normal feedback channel.

5. Runtime architecture and seams

STEWARD STATUS CONSOLE  <---- authoritative campaign/event state   | Pause / Inquiry / Abort / Physical work complete   vCAMPAIGN CONTROLLER   |-- experiment planner contract --> ChatGPT / reasoning services   |-- executor contract -----------> Hermes   |-- HID adapter -----------------> pikvm ------> OctoMiner 1   |-- video adapter ---------------> video1 <---- HDMI from OctoMiner 1   |-- target OS adapter -----------> octo1 SSH   |-- notify adapter --------------> Riverview notification   `-- reset adapter (MVP) ---------> Steward presses RESET

Seam

Input contract

Output contract

Finished when

Planner → Controller

Test specification: objective, hypothesis, change set, pass/fail criteria, timeout/failure policy.

Immutable test plan + candidate manifest.

Plan is complete enough to execute without improvising destructive scope.

Controller → Hermes

One bounded operation with ID, timeout, expected evidence.

Structured result + timestamps + evidence references.

Result persisted, including failure/timeout.

Controller → PiKVM

Explicit HID primitive or sequence.

Action acknowledgement plus later independent visual verification.

Observed target effect or classified observation failure.

Controller → video1

Capture request: frame/video window and format.

Timestamped media/evidence + capture metadata.

Artifact stored and classified or marked unreadable.

Controller → octo1

Bounded diagnostic/test command.

stdout/stderr/exit code/timing.

Result persisted and associated with test step.

Controller → Steward

Physical action or recovery decision request.

Explicit acknowledgement/action complete/decision.

Controller re-verifies physical state before resuming.

Event store → Status console

Append-only events + current campaign state.

Live dashboard and scrollable history.

Heartbeat age ≤30 seconds during active run.

6. Steward Status Console — mandatory control plane

The console is a first-class campaign component. The experiment controller may never perform invisible work. During an active run it publishes a heartbeat/status event at least every 30 seconds. “No change” is a valid update. If the producer becomes stale, the console must visibly report STALE / CONTROLLER HEARTBEAT LOST rather than continuing to display an old working state.

6.1 Persistent campaign analytics banner

CAMPAIGN: OctoMiner 1 Multi-P100 BIOS     TARGET: stable 10+ P100Calendar elapsed: 3d 14:22:17   Automation active: 19:47:31Steward wait: 04:16:08          Steward pause: 11:03:42System/recovery wait: 03:14:56Tests: 23   PASS: 7   FAIL: 10   PARTIAL: 4   INCONCLUSIVE: 2Candidates: 11   BIOS writes: 14   Accepted baselines: 3SW reboots: 18   Hard resets: 2   Recoveries: 0Steward notifications: 4   Physical interventions: 3ATTENTION: none

Counters are derived from the authoritative event log, not separately maintained display variables. Steward-wait and Steward-pause time are explicitly excluded from automation performance accounting.

6.2 Always-visible goal hierarchy

CAMPAIGN GOAL — stable operation with 10+ P100s.

CURRENT ROUND GOAL — e.g., qualify a normal-boot high-MMIO family.

CURRENT TEST OBJECTIVE — exactly what T017 is trying to prove.

TARGET P100 POPULATION — explicitly state 3, 4, 5, etc. during physical capacity testing. Avoid ambiguous language such as “third GPU.”

6.3 Scrollable flight recorder

Every action, observation, timeout, retry, branch, state transition, notification, and Steward interaction is appended with a timestamp. The Steward can leave for ten minutes, return, scroll the last events, and reconstruct what happened without asking the AI to remember it.

19:50:19 [T017/S05] Reboot requested19:50:49             Waiting for POST — 30 sec19:51:19             Waiting for POST — 60 sec19:52:19             Waiting for POST — 120 sec19:53:19 [T017/S06] POST detection timeout — FAIL19:53:20 [T017/S07] Diagnostic branch started19:53:34             Physical RESET required — Steward notified

6.4 Controls

Control

Semantics

PAUSE

Acknowledge immediately. Finish only an atomic operation that cannot safely be interrupted, persist checkpoint, then stop before the next state-changing action. Pause survives overnight/restart.

INQUIRY

Do not automatically stop the run. Expose current objective, reason, evidence, last actions, and next planned action so the Steward can question the path.

ABORT

Terminate the current campaign/run at the next safe boundary, preserve all evidence, and enter an explicit stopped state. Stock recovery is not implied.

PHYSICAL WORK COMPLETE

Acknowledge a requested human action. Controller must independently re-establish/verify machine state before continuing.

VERIFY & RESUME

After a long pause, re-run preflight and reconcile actual hardware/software state with persisted believed state before progression.

7. Authority, destructive operations, and recovery

7.1 Standing campaign authorization

When the Steward issues campaign GO, BIOS-region candidate creation, writing, verification, rebooting, testing, rejection, and iterative candidate progression are pre-authorized within the approved campaign scope. The controller does not stop for repeated “final permission” prompts before each BIOS write. The Steward accepts that BIOS writing is destructive and can make the unit unbootable or potentially unrecoverable.

7.2 Technical boundaries

BIOS-region experimentation is in scope.

Descriptor and ME writes are out of scope unless the campaign is explicitly expanded.

PiKVM reboot/power-cycle is prohibited during ordinary automation.

Stock recovery is not automatic. It requires PAUSE + notification + explicit Steward authorization.

A failed candidate is not equivalent to a failed campaign. Diagnose and continue when the experimental path remains useful.

7.3 Recovery semantics

Recovery is a contingency or end-of-branch operation. Candidate transition C3→C4 is normal experimentation. Rollback may return to a useful prior candidate. Recovery means restoring the known-good stock BIOS using the documented UEFI/Fpt.efi BIOS-region procedure and is Steward-gated.

7.4 Write-state durability

CANDIDATE_PREPAREDWRITE_STARTEDWRITE_RETURNED_SUCCESSREADBACK_STARTEDREADBACK_VERIFIEDREBOOT_STARTEDPOST_OBSERVEDOS_BOOTEDFUNCTIONAL_TEST_PASSEDACCEPTED_BASELINE

WRITE_STARTED and WRITE_RETURNED_SUCCESS are distinct states. If execution is interrupted after WRITE_STARTED, firmware state is indeterminate until independently reconciled; the controller must not assume success or failure.

8. Non-optional experiment evidence contract

A test that does not produce a complete test record does not count as a completed test. The controller must refuse normal progression until the record is closed or explicitly marked incomplete/inconclusive with the reason preserved.

8.1 Pre-test record

Test ID, candidate ID, parent candidate/test, round ID.

Objective and exact target population if applicable.

Observed problem/symptoms motivating the test.

Hypothesis.

Why the proposed change should work.

Exact change from parent and variables deliberately held constant.

Expected result.

Pass, partial, fail and inconclusive criteria.

Ordered procedure.

Per-step timeout, heartbeat interval, failure class, and failure action.

Contingency/recovery options and required evidence.

8.2 During-test record

Timestamped commands/actions and return status.

Video frames/clips and screen classifications.

BIOS image/candidate hashes and write/readback state.

Boot timing and observation timing.

PCI/GPU/driver/workload/stability outputs as applicable.

Retries, branches, notifications and Steward interactions.

Concise reasoning breadcrumbs explaining why a branch was selected.

8.3 Post-test / after-action record

Observed result and classification: PASS / PARTIAL / FAIL / INCONCLUSIVE.

Expected versus observed behavior.

Failure boundary when applicable.

What the test proved.

What it disproved.

What remains unknown.

What was learned.

Implication for the next test.

New questions created.

Evidence index and references.

History is append-only. Later evidence may supersede a prior conclusion, but the original record is never rewritten to make earlier reasoning look better in hindsight.

9. Running campaign knowledge state

CAMPAIGN OBJECTIVECURRENT ACCEPTED FACTSDISPROVEN HYPOTHESESSUPPORTED BUT UNPROVEN HYPOTHESESUNTESTED HYPOTHESESKNOWN HARDWARE/FIRMWARE LIMITSOPEN QUESTIONSCURRENT BEST CONFIGURATIONCOMPLETED TEST INDEXNEXT TEST + WHY IT IS NEXT

After a defined batch (initially ten substantive tests, or sooner if progress stalls), the campaign performs a synthesis checkpoint across all test reports. The review asks what was actually tested, what was never isolated, whether tests conflict, whether the same hypothesis was repeatedly varied, what observations remain unexplained, and which branch of the search space has been neglected. The next round is generated from that synthesis rather than from the most recent failure alone.

10. Candidate/test state machine and failure policy

PRECHECK -> PREPARE -> WRITE -> VERIFY -> REBOOT -> OBSERVE                                            |                                            v                        POST -> BOOT -> PCI -> DRIVER -> WORKLOAD -> STABILITY

Each step declares one of five failure actions: CONTINUE, BRANCH, RETRY, HALT, or STEWARD. A failed observation step does not automatically imply machine failure. Example: POST may not be recognized within 180 seconds, yet a later Linux-console observation may prove that boot succeeded and only the POST observation failed.

Failure action

Meaning

CONTINUE

Preserve failure and collect later evidence that may answer the question.

BRANCH

Enter a predefined diagnostic branch appropriate to the failure boundary.

RETRY

Repeat with bounded retry count and recorded reason.

HALT

Stop because continuing could destroy evidence or violate scope.

STEWARD

Pause/notify because a physical action or human decision is genuinely required.

11. Multi-day persistence and checkpointing

The campaign is designed for days or weeks, not a single session. Browser refreshes, model/session changes, controller restarts, overnight pauses and equipment shutdowns must not destroy continuity. Durable campaign state—not chat history—is authoritative.

Checkpoint campaign/round/test/candidate IDs.

Persist exact current step and last completed atomic operation.

Persist BIOS write/readback state.

Persist believed hardware state and outstanding physical requests.

Persist evidence locations and next intended action.

Persist pause reason and all timing-accounting state.

On resume, verify actual state before trusting yesterday’s believed state.

12. Roadmap and definition of finished

Phase

Deliverable

Definition of finished

0 — Re-anchor

Canonical project spec + recovery/MMIO knowledge refreshed from Riverview.

Known prior work, recovery rules, host interfaces and constraints are captured in campaign state; no rediscovery dependency.

1 — Controller skeleton

Persistent campaign state, event store, adapters, run IDs.

Controller can start/stop/resume and append durable events without BIOS mutation.

2 — Status console

Analytics banner, goal hierarchy, ≤30s heartbeat, flight recorder, Pause/Inquiry/Abort.

Multi-minute dry run demonstrates live updates, scrollback, stale detection and persistent pause/resume.

3 — Closed-loop KVM

pikvm HID + video1 capture + octo1 checks.

One command causes a known target action and independently verifies the visible effect without Steward intervention.

4 — C0 baseline

Measured stock/current boot and system evidence.

Repeated boot observations establish practical timing envelope and current PCI/GPU state; evidence complete.

5 — BIOS entry/navigation

Automated reboot observation and BIOS navigation primitives.

Controller can reach/recognize relevant BIOS screens and return evidence reproducibly.

6 — Candidate framework

Manifest, write-state tracking, verification, test record lifecycle.

A non-destructive/dummy candidate lifecycle proves documentation and failure handling end to end.

7 — High-MMIO round

Incremental candidates aimed at high MMIO with stock-equivalent boot behavior.

At least one candidate is independently verified, boots within measured acceptable tolerance, reaches HiveOS, and passes current-hardware stability tests.

8 — Steward physical gate

Install third P100 temporarily.

Status console explicitly requests 3-P100 configuration; Steward completes physical work; controller verifies/resumes.

9 — 3-P100 validation

Cross known stock boundary.

All three P100s survive firmware allocation, enumerate, initialize, and pass defined workload/stability tests—or failure is fully documented.

10 — Capacity ladder

4, 5, 6… P100 tests as hardware permits.

Each population has its own explicit objective/report; progress continues toward 10+ or an evidence-backed platform limit.

11 — BIOS-setting exploration

Explore exposing successful MMIO behavior as configurable Setup option.

Exploration documented; success is optional and does not invalidate a working hard-coded firmware solution.

12 — Hardening

Security, automated reset, operational polish.

Only after proof-of-function: credentials/security tightened, reset adapter replaced with GPIO/transistor if desired, deployment documented.

13. Immediate next steps before campaign GO

1. Freeze this proposal as the initial operating contract and place a canonical copy in Riverview.

2. Retrieve and index the existing OctoMiner BIOS/MMIO/recovery documentation and prior candidate artifacts so Phase 0 starts from repository evidence, not reconstructed memory.

3. Create the persistent campaign directory/schema: campaign state, event log, test records, candidate manifests, evidence tree and round synthesis documents.

4. Build the Steward Status Console first enough to show campaign analytics, current goals, heartbeat, flight recorder and Pause/Inquiry controls during a dry run.

5. Implement deterministic adapters for pikvm HID, video1 capture, octo1 diagnostics and Riverview notifications. Keep FFplay as an optional human view.

6. Run a non-destructive closed-loop KVM proof: action through PiKVM, independent observation through video1, complete test record and dashboard history.

7. Capture C0 baseline and measure repeated boot timing before defining the numerical tolerance for “stock-equivalent” boot behavior.

8. Only then begin the first high-MMIO candidate round under the standing campaign authorization.

14. Prototype implementation policies

Function beats form during proof-of-function. Existing trusted-LAN SSH keys/passwords and simple configuration are acceptable; production security is deferred.

Codex is last-resort/scarce assistance, not the default coding path.

Playwright is available where it provides leverage but is not mandatory.

Notifications are exceptional. Routine progress belongs on the status console.

No active run goes more than 30 seconds without a heartbeat/status publication.

No undocumented experiment, branch, failure, candidate, or conclusion.

No automatic stock recovery.

No ambiguous “GPU count” language in capacity tests; state the P100 population explicitly.




========================================================================
# SOURCE: CAMPAIGN_STATE.md
========================================================================

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


========================================================================
# SOURCE: PROVEN_FACTS.md
========================================================================

# Proven Facts

## PF-001 — Octo2 80B inference operational
Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf successfully answered a live
OpenAI-compatible inference request on port 8080.

## PF-002 — Octo2 80B automatically returns after reboot
llama-server.service uses Restart=always and was observed running automatically
after the current Octo2 boot.

## PF-003 — Octo2 current GPU population
2 x Tesla P100-PCIE-16GB
1 x NVIDIA GeForce RTX 4090

## PF-004 — PiKVM HID path to OctoMiner1 works
OctoMiner1 enumerates the PiKVM composite HID device.

## PF-005 — Dedicated video acquisition works
video1 detects the MacroSilicon HDMI capture device as UVC and successfully
captured an OctoMiner1 MJPEG frame.

## PF-006 — DEV-side OCTO2 dependency monitor qualified
T-SCAF-001 proved that the campaign controller can independently detect OCTO2
boot identity, uptime, Qwen3-Next 80B process presence and API readiness.
The validated healthy state is `80B_READY`.

## PF-007 — OCTO2 spontaneous reboot observed during campaign
OCTO2 changed boot ID from
0557fb2e-0286-422f-b270-300795631ef1
to
45093b9d-0398-4e1d-a523-07b1513f750e
during T-SCAF-002.

## PF-008 — Campaign monitor survives OCTO2 reboot
DEV monitor PID 16416 remained operational through the observed OCTO2 outage
and subsequent recovery.

## PF-009 — OCTO2 automatically restarted the 80B service
After the observed reboot, systemd started llama-server.service without Steward
intervention and created llama-server PID 755.

## PF-010 — One measured 80B cold load required approximately six minutes
During T-SCAF-002, llama-server.service started at 20:58:19 EDT.
Model loading began at 20:58:23 EDT.
The server reported the model loaded and began listening on port 8080 at
21:04:18 EDT.

## PF-011 — Running llama-server PID does not prove API readiness
During T-SCAF-002, PID 755 existed while the monitor correctly observed
80B_NOT_READY. API readiness occurred later.

## PF-012 — OCTO2 recovery required no Steward intervention in T-SCAF-002
The observed reboot recovered through Linux boot, systemd service startup,
model loading and API readiness without manual action.

## PF-013 — Five-node campaign infrastructure health is live

T-SCAF-004 qualified live Steward health reporting for DEV, OCTO1, OCTO2,
PiKVM, and Video-KVM Pi. All five reported READY / GREEN during qualification.

## PF-014 — OCTO1 management path is qualified

OCTO1 is reachable at 192.168.1.160. SSH/22 and key-based SSH access through
the `octo1` alias were verified.

## PF-015 — PiKVM management path is qualified

PiKVM is reachable at 192.168.1.169. SSH/22, HTTP/80, HTTPS/443, and key-based
SSH access through the `pikvm` alias were verified.

## PF-016 — Video-KVM Pi management path is qualified

Video-KVM Pi is reachable at 192.168.1.101. SSH/22 and key-based SSH access
through the `video1` alias were verified.

## PF-017 — OCTO2 reboot count synchronized at two

Following the controlled reboot qualification, the OCTO2 campaign reboot count
was synchronized at 2 and is authoritative from that event forward.

## PF — OCTO1 independent video acquisition path proven

OCTO1 HDMI is observed through the dedicated video-acquisition Raspberry Pi.
That system is an observation/acquisition endpoint, not an HID-control endpoint.

Proven acquisition path:

OCTO1 HDMI
-> dedicated video-acquisition Pi
-> /dev/video0
-> single ffmpeg capture owner
-> SSH stream to DEV
-> controller/video1_relay.py
-> FFplay human view + runtime/video1/latest.jpg
-> HermesVisionGateway
-> hermes-multimodal
-> local Qwen3-VL 8B vision path on the DEV/3060 Ti system.

The relay was qualified with:
- one remote /dev/video0 owner,
- DEV SSH child,
- FFplay child,
- FFmpeg snapshot decoder,
- continuously generated latest.jpg.

Hermes multimodal successfully analyzed an acquired OCTO1 frame and reported:
SCREEN_TYPE=Linux terminal/console
TEXT_ENTRY_VISIBLE=TRUE
SAFE_FOR_UNSUBMITTED_TEXT=TRUE
DANGEROUS_OR_AMBIGUOUS_STATE=FALSE
CONFIDENCE=HIGH
DECISION=SAFE

The video-acquisition Pi must not be searched for or treated as the OCTO1 HID
actuator merely because the campaign also contains KVM/control infrastructure.

## PF — T-SCAF-005 video1 remained live after HID action

During T-SCAF-005 Step 4 failure diagnosis, the independent video1 acquisition
path remained live.

Successive latest.jpg observations:

23:57:43
23:57:45
23:57:47
23:57:49
23:57:51
23:57:53

The file timestamp advanced continuously while the SHA256 remained unchanged.

Interpretation:
- video1 acquisition and DEV snapshot generation were active,
- OCTO1 was displaying a static image,
- identical hashes represented identical visible pixels rather than a stale
  acquisition artifact.

Hermes independently observed a fresh OCTO1 frame and reported:
- terminal/console screen,
- visible prompt root@OCTO1N1:~#,
- empty input line,
- marker T-SCAF-005-KVM-PROOF absent,
- confidence HIGH.

Therefore the T-SCAF-005 Step-4 failure cannot currently be attributed to a
stale video1 frame.

## 2026-10-02 — OCTOMINER1 Control / Observation Proven Facts

- PiKVM role: HID/control.
- ideo1 Raspberry Pi role: independent HDMI/UVC acquisition.
- OCTOMINER1 SSH role: target OS diagnostics/configuration, not visual proof.
- PiKVM KVMD HID text endpoint: POST /hid/print.
- KVMD request acceptance alone does not prove physical HID delivery.
- PiKVM USB gadget can enter a state where KVMD is online but the USB link is not attached.
- Successful recovery observed tonight included Steward physical intervention; remote PiKVM reboot alone was NOT proven sufficient.
- After recovery OCTOMINER1 enumerated PiKVM 1d6b:0104 and its HID keyboard/mouse interfaces.
- PiKVM HID successfully caused OCTOMINER1 to execute ls.
- Independent ideo1 acquisition captured the resulting physical display change.
- ideo1 capture device is /dev/video0.
- Qualified ideo1 capture mode is MJPEG 1920x1080 at 30 fps.
- DEV relay implementation is controller/video1_relay.py.
- Machine-observation frame is 
untime/video1/latest.jpg.
- Advancing JPEG timestamps with identical hashes can represent a healthy live stream viewing a static screen.
- OCTOMINER1 active Xorg output is HDMI2.
- OCTOMINER1 supports 1920x1080 at 60 Hz.
- OCTOMINER1 was successfully changed from 3840x2160@30 to 1920x1080@60.
- 1080p materially improves captured terminal readability.
- Current 3060 Ti vision model improves substantially at 1080p but remains unqualified for BIOS-grade transcription.
- OCTOMINER reset/power intervention remains manual.
- PiKVM USB-link recovery currently may require manual Steward intervention.


========================================================================
# SOURCE: PROVEN_NOT_WORKING.md
========================================================================

# Proven Not Working / Known Failure Conditions

## PNW-001 — Riverview telemetry monitor currently cannot start
riverview-octo-monitor.service requires /mnt/octo-models-stage.
That filesystem is not currently mounted, causing a systemd dependency failure.

## PNW-002 — Riverview monitor deployment state is stale
/opt/riverview-octo-control/state.json describes the previous Qwen3-Coder 30B
deployment on port 8101, not the currently running Qwen3-Next 80B service on
port 8080.

## PNW-003 — Octo2 has an unresolved reboot problem
Root cause unknown.
The BIOS campaign must tolerate and record Octo2 outages rather than assuming
continuous availability.

## PNW-004 — Automated physical reset is not yet available
Current implementation is Steward notification followed by manual RESET.

## PNW-005 — Original OCTO2 monitor parser produced false worker-down state
T-SCAF-001 demonstrated that parsing multiple shell-derived fields through one
SSH command can shift field boundaries. The original implementation falsely
reported `80B_PROCESS_DOWN`.

Corrective rule: use simple remote output and perform structural parsing in the
DEV-side controller.

## PNW-006 — Boot-change event can be lost across unreachable samples
The current OCTO2 monitor compares boot identity against the immediately
previous sample.

During T-SCAF-002, unreachable samples contained no boot ID, so the monitor
failed to emit an explicit `octo2_boot_changed` event when OCTO2 returned with
a new boot ID.

Required correction:
retain `last_known_boot_id` across unreachable samples.


========================================================================
# SOURCE: LESSONS_LEARNED.md
========================================================================

# Campaign Lessons Learned

## LL-001 — Preserve knowledge outside the chat

Every meaningful test must leave durable evidence containing:

- goal
- hypothesis
- preconditions
- action
- observation
- result
- postmortem
- lessons
- implications for the next test

The repository is the campaign memory.

## LL-002 — Host availability and model availability are separate states

An online OCTO2 does not imply that the 80B reasoning worker is usable.

The controller must distinguish host reachability, model-process presence,
model loading and API readiness.

## LL-003 — Process presence is not inference readiness

During T-SCAF-002, llama-server PID 755 existed for several minutes while the
80B model was loading and the API was not ready.

A PID check alone is insufficient.

## LL-004 — Timeout policy must be operation-specific

One generic timeout is inappropriate.

Separate timeout policies are required for operations including:

- POST / boot
- SSH return
- video acquisition
- BIOS programming
- 80B cold loading
- Steward response
- software reboot
- physical reset request

Timeouts should be based on measured campaign behavior where possible.

## LL-005 — Retain last known boot identity across outages

An unreachable sample must not erase the last known boot ID.

Boot-transition detection must compare a newly observed boot ID against the
last successfully observed boot ID.

## LL-006 — Monitoring belongs outside the monitored machine

The campaign monitor runs on DEV.

This allowed T-SCAF-002 to preserve evidence while OCTO2 itself was offline.

A monitor located only on OCTO2 could not provide equivalent outage evidence.

## LL-007 — Keep SSH boundary operations simple

Complex shell parsing across:

Windows -> SSH -> Linux shell

caused the first OCTO2 monitor implementation to misparse /proc/uptime and
falsely report the 80B process as down.

Prefer simple line-oriented remote output and parse structure locally.

## LL-008 — Preserve diagnostic information

Return codes and stderr should not be discarded when diagnosing infrastructure.

The initial monitor helper hid information that was useful for separating SSH
failure from host failure.

## LL-009 — Be cautious with PowerShell control flow and nested quoting

Multiple campaign scaffolding attempts demonstrated unreliable results from
complex PowerShell blocks containing nested here-strings, subexpressions and
if/else control flow.

Campaign implementation rule:

- prefer Python for substantive controller logic
- keep PowerShell primarily as a launcher / inspection surface
- avoid `else` where simple independent operations suffice
- test nontrivial PowerShell behavior before using it against campaign state
- never infer success from partial script execution

## LL-010 — Preserve failed telemetry rather than silently deleting it

Known-invalid observations from a controller defect remain useful evidence.

They must be labeled as invalid or attributable to instrumentation rather than
rewritten as genuine machine failures.

## LL-011 — Distinguish observation from policy

One measurement does not establish a universal threshold.

T-SCAF-002 measured approximately six minutes for one 80B cold start.

The initial 8-minute escalation threshold is therefore a provisional campaign
policy, not a proven invariant.

## LL-012 — Automatic recovery should remain automatic when proven

T-SCAF-002 required no Steward action for OCTO2 recovery.

The host rebooted, systemd restarted llama-server, the model loaded, and the
monitor returned to 80B_READY.

The campaign should observe this recovery before escalating to the Steward.

## Bounded network probes

Dashboard health checks must use explicit short timeouts. An earlier
Test-NetConnection probe demonstrated that an unavailable TCP port can make an
interactive health check appear hung.

Steward therefore uses bounded socket probes. Generic infrastructure monitoring
should eventually move to a persistent monitor/cache so HTTP response latency
is independent of unavailable hosts.

Also verify dictated port numbers before incorporating them into a persistent
management contract. Port 2222 entered the initial qualification only because
of a dictation error.

## LL — Context availability is not project grounding

### Observation

During campaign infrastructure work, the reasoning/planning layer began
reconstructing the role of the DEV RTX 3060 Ti and proposed rediscovery work
even though the approved campaign proposal had already defined the local
utility-model role, Hermes executor role, OCTO2 80B reasoning role, PiKVM HID
path, and video1 machine-perception path.

### Failure Mode

Information existing somewhere in conversation history or model context was
treated as though it would remain reliably active during later reasoning.

It did not.

The result was unnecessary rediscovery and temporary architectural drift.

### Rule

Context availability is not equivalent to project grounding.

Before advancing to another test, phase, or new reasoning session, reload the
authoritative campaign documents.

Do not reconstruct architecture, interfaces, machine roles, known failures, or
previously proven facts from conversational memory when canonical documentation
exists.

### Corrective Action

REGROUND_CONTRACT.md defines mandatory reground gates.

The controller must generate a canonical reground packet at required
boundaries. The next test is not designed until that packet has been reviewed.


### Durable knowledge must precede rediscovery

A process defect occurred during T-SCAF-005 preparation when an existing
HermesVisionGateway component was discovered locally and the next instinct was
to reverse-engineer its live implementation. Riverview already contained
documentation, a known-good deployment, and a multimodal qualification test
for that component.

The defect was not merely forgetting one interface. The failure was using the
wrong information-retrieval order.

Correct order:

campaign canonical record -> authoritative project repository -> installed
local implementation -> live runtime verification -> new investigation.

Durable knowledge before discovery; discovery before invention.

New locally qualified work must subsequently be promoted back into the durable
project record at an appropriate checkpoint so future sessions do not repeat
the investigation.

## Lesson — Do not conflate video acquisition with HID control

A dedicated video-acquisition system and an HID/control system are separate
architectural roles.

When a machine is documented and proven as the OCTO1 video-acquisition endpoint,
do not search that machine for keyboard injection, KVMD HID, marker typing, or
other actuation primitives.

For OCTO1 observation, preserve the proven chain:

OCTO1 HDMI -> video acquisition -> DEV relay -> machine/human perception.

If an action must later be injected into OCTO1, recover the authority for that
separate control path from durable campaign documentation before discovery or
invention.

Role names and nearby KVM terminology must never override the proven physical
data path.

## Lesson — Static video content cannot be used as a liveness test

For the video1 acquisition pipeline, an unchanged frame hash does NOT establish
that acquisition has stalled.

A static OCTO1 console can legitimately produce identical decoded JPEG content
across successive acquisitions.

Video-frame freshness must be established using acquisition/write timing or
another independent freshness indicator.

Observed T-SCAF-005 evidence:
- latest.jpg timestamps continued advancing approximately every two seconds.
- successive SHA256 hashes remained identical.
- therefore the video1 relay remained live while the visible OCTO1 screen
  remained unchanged.

Do not classify HASH_CHANGES=False as a frozen video pipeline when the frame
timestamp continues advancing.

## 2026-10-02 — OCTOMINER1 Closed-Loop Control / Observation Qualification

### Architecture — DO NOT CONFLATE THESE ROLES

The OCTOMINER1 BIOS campaign uses separate control and observation systems.

**CONTROL / ACTUATION**

DEV machine
-> SSH to pikvm
-> PiKVM KVMD HTTP HID API
-> PiKVM USB HID gadget
-> physical OCTOMINER1 keyboard input

PiKVM is the HID/control path.

PiKVM is NOT the authoritative video-acquisition path for this campaign.

**INDEPENDENT VIDEO OBSERVATION**

OCTOMINER1 HDMI
-> video matrix/path
-> ideo1 Raspberry Pi
-> HDMI/UVC capture device /dev/video0
-> remote ffmpeg MJPEG stream
-> DEV controller/video1_relay.py
-> 
untime/video1/latest.jpg

ideo1 is an observation/acquisition appliance.

Do NOT search ideo1 for keyboard/HID/actuation functions.

**TARGET OS DIAGNOSTIC PATH**

DEV
-> SSH octo1
-> OCTOMINER1 operating system

OCTOMINER1 SSH may be used for OS diagnostics and configuration when
authorized, but it is NOT independent proof of what appears on the
physical HDMI console.

### Proven PiKVM HID Method

The installed KVMD implementation exposes:

POST /hid/print

The request body is the text to type.

After successful USB enumeration, the following closed-loop test worked:

- PiKVM HID sent ls with LF terminator.
- OCTOMINER1 physically received and executed the command.
- OCTOMINER1 HDMI output changed.
- ideo1 independently captured the changed display.
- latest.jpg changed.
- The resulting screen visibly contained the ls command and directory output.

An HTTP success response from /hid/print proves KVMD accepted the request.
It does NOT by itself prove OCTOMINER1 received the keystrokes.

Closed-loop verification through ideo1 is required.

### PiKVM USB Failure / Recovery Limitation

A failure was observed where:

- KVMD remained online.
- /hid/print accepted requests.
- PiKVM's USB gadget was configured.
- PiKVM UDC reported 
ot attached.
- KVMD keyboard reported online: false.
- KVMD mouse reported online: false.
- OCTOMINER1 showed no response to accepted HID requests.

Therefore:

**KVMD API acceptance is not proof of physical HID delivery.**

The eventual recovery MUST NOT be attributed solely to a remote PiKVM reboot.

The Steward performed physical intervention involving the PiKVM/OCTOMINER1
USB/power connection and boot-switch sequence. After that physical recovery
sequence, the PiKVM returned and OCTOMINER1 successfully enumerated:

1d6b:0104 Linux Foundation Multifunction Composite Gadget

OCTOMINER1 kernel logs identified:

Product: PiKVM Composite Device

and enumerated PiKVM keyboard and mouse HID interfaces.

Current limitation:

**Recovery from this PiKVM USB-link failure requires Steward/manual
intervention until a reliable remote recovery procedure is separately
proven.**

Do not claim a remote reboot alone repairs this failure.

### Manual OCTOMINER Intervention

OCTOMINER reboot/reset/power intervention remains a manual Steward operation
at this stage of the campaign.

Do not assume unattended OCTOMINER reset capability.

### video1 Acquisition Qualification

ideo1 is a Raspberry Pi dedicated to HDMI/UVC acquisition.

Qualified capture device:

/dev/video0

Observed qualified mode:

- MJPEG
- 1920x1080
- 30 fps

The remote capture process uses ffmpeg against /dev/video0.

The DEV relay:

controller/video1_relay.py

fans the SAME MJPEG stream to:

1. the human ffplay viewer, and
2. an ffmpeg decoder that continuously replaces:


untime/video1/latest.jpg

Important freshness lesson:

A static OCTOMINER screen can legitimately produce consecutive JPEGs with
identical hashes.

**Identical image hashes do NOT prove the video relay is frozen.**

File modification timestamps were observed continuously advancing while the
screen remained visually static.

Use timestamp freshness plus controlled screen-change evidence when
qualifying the acquisition path.

### OCTOMINER1 Display Resolution

OCTOMINER1 uses Intel HD Graphics 530 / i915 for the active display.

DRM connector:

card0-HDMI-A-2

Xorg output:

HDMI2

Previous active mode:

3840x2160 @ 30 Hz

Supported preferred mode:

1920x1080 @ 60 Hz

The active Xorg display was successfully changed with:

DISPLAY=:0 xrandr --output HDMI2 --mode 1920x1080 --rate 60

The resulting 1080p HDMI image is substantially more readable through the
1920x1080 ideo1 capture path than the previous 4K desktop scaled into the
capture.

### Vision Model Qualification

Current vision path:


untime/video1/latest.jpg
-> local multimodal gateway
-> 3060 Ti vision model

At 3840x2160 OCTOMINER output, blind transcription was severely inaccurate
and hallucinated/garbled substantial screen content.

After changing OCTOMINER1 to 1920x1080, blind transcription improved
dramatically and correctly recovered substantial visible text.

However, the current model still does NOT provide sufficiently exact,
complete, dependable screen transcription for BIOS-control decisions.

Current qualification:

**3060TI_VISION_FOR_BIOS=UNQUALIFIED**

**1080P_IMPROVES_VISION_SUBSTANTIALLY=True**

Do not reduce the qualification test to questions such as whether a single
word or command appears on screen.

For BIOS work we require sufficiently reliable reading of the complete
relevant screen state, because a wrong menu item, value, warning, selection,
or prompt can cause an incorrect control decision.

Potential next architecture investigation:

1. stronger vision-language model that fits available OCTOMINER2 VRAM, and/or
2. dedicated OCR/transcription stage followed by the large reasoning model.

### Closed-Loop Architecture Proven Tonight

CONTROL:

DEV -> PiKVM -> KVMD HID -> USB -> OCTOMINER1

OBSERVATION:

OCTOMINER1 HDMI -> video1 -> /dev/video0 -> ffmpeg -> video1_relay.py -> latest.jpg

VISION:

latest.jpg -> vision model

The CONTROL and OBSERVATION paths are deliberately independent.

The control/observation mechanism is proven.

The remaining major machine-perception blocker is sufficiently accurate
vision/OCR for BIOS work.

Recorded: 2026-10-02 01:13:03 -04:00


========================================================================
# SOURCE: OPEN_QUESTIONS.md
========================================================================

# Open Questions

- What causes the spontaneous Octo2 reboot behavior?
- Can PiKVM virtual mass storage reliably deliver BIOS candidates while HID remains usable?
- What exact stock boot-time distribution should define the firmware latency tolerance?
- Which high-MMIO firmware mechanism can increase P100 capacity without the previously observed boot delay?
- After a working solution is found, can the MMIO setting be exposed through BIOS Setup rather than remaining hard-coded?
- Why are unauthenticated requests currently reaching the Riverview Octo control API and receiving HTTP 401 responses?


========================================================================
# SOURCE: README.md
========================================================================

# OctoMiner 1 Multi-P100 BIOS Campaign

## Campaign Goal
Develop and validate firmware capable of supporting 10+ Tesla P100 16GB GPUs
while retaining practical stock-equivalent boot behavior.

## Current Phase
PHASE 0 — Automation scaffolding and interface qualification.

## Current Hardware Validation Target
No expanded-P100 claim yet.

First physical boundary test after firmware qualification:
3 x Tesla P100 16GB.

## Campaign Rule
No experiment is complete without PRE, execution evidence, POST analysis,
and an explicit statement of what was learned.


========================================================================
# COMPLETED / RECORDED TEST DOCUMENTS
========================================================================


------------------------------------------------------------------------
## TEST SOURCE: T-SCAF-001.md
------------------------------------------------------------------------

# T-SCAF-001 — OCTO2 80B Dependency Monitor Qualification

## Goal

Prove that the DEV-side BIOS campaign controller can independently determine
whether OCTO2 and its Qwen3-Next 80B reasoning worker are available.

## Expected Result

Every 10 seconds the monitor should record:

- OCTO2 SSH reachability
- Linux boot ID
- system uptime
- Qwen3-Next 80B llama-server PID
- port 8080 API readiness
- derived worker state

A healthy worker must report `80B_READY`.

## Initial Test

FAIL.

The first implementation returned `80B_PROCESS_DOWN` even though the previously
validated 80B service was believed to still be operating.

Observed output included two numeric values after `uptime=` and an empty PID.

## Root Cause

The remote command used `/proc/uptime` through a nested SSH/shell parsing
expression. `/proc/uptime` contains both uptime and aggregate idle time.

The command/parsing boundary did not produce the field layout expected by the
controller. The PID field was therefore parsed incorrectly and the monitor
generated a false `80B_PROCESS_DOWN` classification.

## Corrective Action

The monitor was rebuilt so that the remote side returns three simple lines:

1. boot ID
2. complete `/proc/uptime`
3. matching llama-server PID

Python performs the final field extraction locally.

## Retest

PASS.

Three consecutive observations:

- 2026-10-01T20:53:32-04:00 — `80B_READY`
  - uptime: 1278.27
  - PID: 757
  - boot: 0557fb2e-0286-422f-b270-300795631ef1

- 2026-10-01T20:53:42-04:00 — `80B_READY`
  - uptime: 1288.49
  - PID: 757
  - boot: 0557fb2e-0286-422f-b270-300795631ef1

- 2026-10-01T20:53:52-04:00 — `80B_READY`
  - uptime: 1298.70
  - PID: 757
  - boot: 0557fb2e-0286-422f-b270-300795631ef1

## Conclusion

The DEV-side OCTO2 dependency monitor is qualified for campaign use.

The failed samples remain part of the evidence history and must not be
interpreted as an actual OCTO2 or 80B outage.

## Lesson Learned

Prefer simple remote commands with local parsing across SSH boundaries.

For small generated controller files, deterministic complete-file generation is
preferred over complex PowerShell in-place patching with nested here-strings.

## Status

PASS

TEST_RESULT: PASS


------------------------------------------------------------------------
## TEST SOURCE: T-SCAF-002.md
------------------------------------------------------------------------

# T-SCAF-002 — OCTO2 Reboot and 80B Recovery Observation

## Goal

Determine whether the DEV-side campaign monitor survives an actual OCTO2 outage
and correctly observes recovery of both the host and the Qwen3-Next 80B worker.

## Trigger

Unplanned / spontaneous OCTO2 reboot during campaign scaffolding.

No reboot was intentionally commanded as part of this test.

## Prior Known Boot

Boot ID:
0557fb2e-0286-422f-b270-300795631ef1

80B PID before reboot:
757

Prior worker state:
80B_READY

## Observed Timeline

### 20:57:24 EDT

Campaign monitor reported:

OCTO2_UNREACHABLE

Additional unreachable samples followed at approximately 10-second intervals.

### New Boot

New boot ID:

45093b9d-0398-4e1d-a523-07b1513f750e

This independently confirms an OCTO2 reboot occurred.

### 20:58:19 EDT

systemd started:

llama-server.service

New llama-server PID:

755

### 20:58:23 EDT

llama-server began loading:

Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf

### 20:58:27 EDT

Campaign monitor observed the recovered host and classified the worker:

80B_NOT_READY

At this point:

- SSH worked
- the new boot ID was visible
- llama-server PID 755 existed
- inference API was not yet ready

### 21:04:18 EDT

llama-server journal reported:

- model loaded
- listening on 0.0.0.0:8080

Observed service-start-to-listen time:

approximately 5 minutes 59 seconds

Observed model-load-start-to-listen time:

approximately 5 minutes 55 seconds

### 21:04:25 EDT

Campaign monitor independently transitioned:

80B_NOT_READY -> 80B_READY

### 21:07:29 EDT

Monitor remained operational.

State:

80B_READY

Boot ID:

45093b9d-0398-4e1d-a523-07b1513f750e

PID:

755

API ready:

true

## Result

PASS

The DEV-side campaign monitor survived a real OCTO2 outage and continued
operating through:

1. host loss
2. OCTO2 reboot
3. SSH recovery
4. automatic llama-server service startup
5. extended 80B model loading
6. API recovery
7. return to 80B_READY

No Steward intervention was required for OCTO2 recovery.

## Defect Discovered

The monitor did NOT emit an explicit `octo2_boot_changed` event.

Cause:

The implementation compared the current boot ID only with the immediately
previous sample. During the outage, unreachable samples contained an empty boot
ID. The old boot identity was therefore lost before the new boot became visible.

Required correction:

Maintain a persistent `last_known_boot_id` independent of the immediately
previous health sample.

## Important Interpretation

`80B_NOT_READY` during this event did not mean that llama-server had failed.

PID 755 existed while the 80B model was still loading.

The campaign must distinguish at least:

- OCTO2_UNREACHABLE
- OCTO2_UP_MODEL_PROCESS_DOWN
- OCTO2_UP_80B_LOADING
- 80B_READY

## Timeout Evidence

One observed 80B cold start required approximately six minutes.

This is an observed data point, not yet a universal startup-time specification.

A temporary campaign threshold of 8 minutes is reasonable for initial
qualification, but it must remain configurable and should be revised as more
cold-start samples are collected.

## Status

PASS

TEST_RESULT: PASS


------------------------------------------------------------------------
## TEST SOURCE: T-SCAF-003.md
------------------------------------------------------------------------


## T-SCAF-003 — OCTO2 Monitor V2 Parallel Qualification

### Goal
Qualify monitor V2 beside the proven V1 witness without interrupting monitoring.

### V1
PID: 16416

### V2
PID: 33480

### Observations
V2 remained alive and produced consecutive healthy samples at:

- 21:12:10
- 21:12:20
- 21:12:31
- 21:12:41

All samples reported:

- SSH: true
- Boot ID: 45093b9d-0398-4e1d-a523-07b1513f750e
- llama PID: 755
- API ready: true
- State: 80B_READY

V2 stderr was empty.

### Boot Tracking Correction
V2 maintains `last_known_boot_id` independently from the immediately previous
health sample.

The code structure has been verified.

Live boot-transition qualification remains pending until the next naturally
occurring OCTO2 reboot.

### Result
PASS — normal-operation parallel qualification.

V2 is approved to replace V1 as the active OCTO2 campaign monitor.

TEST_RESULT: PASS


------------------------------------------------------------------------
## TEST SOURCE: T-SCAF-004.md
------------------------------------------------------------------------

TEST_RESULT: PASS

# T-SCAF-004 — Five-Node Infrastructure Health Qualification

## Goal

Prove that the Steward dashboard can report live management-path health for all
five systems involved in the OctoMiner BIOS campaign without modifying or
restarting any remote machine.

## Qualified Nodes

### DEV

Role:
Campaign controller and Steward dashboard host.

Observed state:

- READY
- GREEN
- Steward controller running

### OCTO1

Address:

192.168.1.160

SSH alias:

octo1

Observed:

- ICMP reachable
- TCP/22 reachable
- SSH authentication successful
- hostname: OCTOMINER1

Steward result:

- READY
- GREEN
- SSH/22 reachable

### OCTO2

Address:

192.168.1.162

Health authority:

octo2_monitor_v2.py

Observed:

- SSH reachable
- Qwen3-Next 80B API ready
- state: 80B_READY
- reboot counter: 2
- reboot count authoritative from controlled synchronization event

Steward result:

- READY
- GREEN
- SSH + 80B API ready

### PiKVM

Address:

192.168.1.169

SSH alias:

pikvm

Observed:

- ICMP reachable
- TCP/22 reachable
- TCP/80 reachable
- TCP/443 reachable
- SSH authentication successful
- hostname: pikvm

Steward result:

- READY
- GREEN
- SSH/22 + HTTP/80 + HTTPS/443 reachable

### Video-KVM Pi

Address:

192.168.1.101

SSH alias:

video1

Observed:

- ICMP reachable
- TCP/22 reachable
- SSH authentication successful
- hostname: raspberrypi

Steward result:

- READY
- GREEN
- SSH/22 reachable

## Probe Design

Steward uses bounded TCP probes implemented with socket.create_connection().

Probe timeout:

0.75 seconds

Port 2222 is not part of the management-health contract. Its earlier inclusion
was caused by a dictation error.

OCTO2 remains governed by its dedicated monitor rather than generic TCP
reachability because its operational states include model loading and API
readiness.

## Performance

Measured /api/status response during qualification:

127 ms

## Process Integrity

OCTO2 Monitor V2 remained:

PID 43172

No OCTO2 reboot occurred during this qualification.

No remote-machine configuration was changed.

## Result

PASS

All five campaign systems were represented by live health information:

DEV — GREEN
OCTO1 — GREEN
OCTO2 — GREEN
PiKVM — GREEN
Video-KVM Pi — GREEN

## Architectural Follow-Up

The bounded synchronous probes are acceptable for campaign qualification.

A future improvement is to move generic infrastructure probing into a
persistent monitor/cache so dashboard HTTP requests never directly depend on
network-probe latency.

## Status

PASS


------------------------------------------------------------------------
## TEST SOURCE: T-SCAF-005.md
------------------------------------------------------------------------

# T-SCAF-005 — Closed-Loop KVM Proof

## Purpose

Prove one complete non-destructive automation loop:

PiKVM HID -> OCTO1 -> independent video1 observation.

This test qualifies the deterministic KVM control/observation path required
before BIOS candidate execution.

## Architecture Authority

The current REGROUND_PACKET.md is the required architecture authority for this
test.

Relevant roles:

- PiKVM: HID/control path to OCTO1.
- video1: independent HDMI/UVC observation path from OCTO1.
- octo1: target operating-system diagnostic path.
- Steward: human control/gating authority.

## Preconditions

1. Campaign reground gate PASS.
2. PiKVM reachable by SSH.
3. PiKVM KVMD HID API available.
4. video1 reachable by SSH.
5. Existing video1 capture stream remains running and MUST NOT be killed merely
   to obtain a second /dev/video0 handle.
6. OCTO1 reachable by SSH.
7. OCTO1 boot ID recorded before execution.
8. Steward can see the authoritative video1 console feed.
9. Before any marker text is sent, the visible OCTO1 console MUST be confirmed
   to be in a harmless text-entry state where unsubmitted text cannot trigger
   an action merely by being typed.

## Test Marker

T-SCAF-005-KVM-PROOF

## Execution Contract

### Step 1 — Baseline

Record:

- OCTO1 boot ID.
- OCTO1 uptime.
- current foreground console.
- PiKVM HID availability.
- video1 capture-process PID/state.

PASS requires all management paths to remain healthy.

### Step 2 — Establish Safe Visible Input State

Using observation through video1, establish that the visible OCTO1 console is
at a harmless text-entry location.

Do NOT proceed if the visible target is:

- BIOS/UEFI setup,
- bootloader command entry,
- password entry,
- destructive/recovery prompt,
- package/configuration prompt,
- an application where arbitrary typed text can invoke an action,
- or any state whose behavior is uncertain.

If safety cannot be established, result is INCONCLUSIVE and no HID marker is
sent.

### Step 3 — HID Action

Through the supported PiKVM KVMD HID API, type exactly:

T-SCAF-005-KVM-PROOF

Do NOT append Enter/Return.

No shell command is intentionally executed.

### Step 4 — Independent Observation

The authoritative observation source is video1.

PASS requires the exact marker:

T-SCAF-005-KVM-PROOF

to become visibly present on the OCTO1 console after the PiKVM HID action.

Observation through OCTO1 SSH alone is NOT sufficient to satisfy this step.

### Step 5 — Cleanup

After visual PASS, send Ctrl+U through the supported PiKVM HID interface only
if the established text-entry environment is known to interpret Ctrl+U as
harmless line clearing.

If that interpretation is not established, do not improvise cleanup. Stop and
record the visible state for Steward review.

### Step 6 — Target Health Verification

After the HID proof, independently verify through OCTO1 SSH:

- boot ID unchanged,
- SSH remains reachable,
- no reboot occurred.

## PASS Criteria

PASS only if all are true:

1. Safe visible text-entry state established before HID execution.
2. Marker entered through PiKVM HID.
3. No Enter/Return sent with marker.
4. Exact marker independently observed through video1.
5. OCTO1 remains reachable.
6. OCTO1 boot ID remains unchanged.
7. No unintended command or target action is observed.
8. Existing video1 capture stream remains operational.

## Failure Classification

- HID action fails -> FAIL.
- HID succeeds but marker cannot be independently observed -> FAIL.
- video1 unavailable or observation ambiguous -> INCONCLUSIVE.
- Safe text-entry state cannot be established -> INCONCLUSIVE.
- Unexpected target behavior -> HALT and STEWARD.
- OCTO1 reboot/boot-ID change -> HALT and STEWARD.

## Prohibitions

This test does NOT authorize:

- BIOS writes,
- BIOS configuration changes,
- reboot,
- reset,
- power cycle,
- Enter/Return after the test marker,
- PiKVM reboot,
- termination of the established video1 stream,
- USB mass-storage manipulation,
- stock recovery,
- unrelated remote configuration changes.

## Result

PENDING

## Execution Evidence — Step 3 / Step 4

Step 3:
- KVMD accepted POST /hid/print.
- Marker requested: T-SCAF-005-KVM-PROOF
- Enter/Return was not included.
- KVMD response: ok=true.
- CURL_EXIT=0.
- HID API action result: PASS at the API acceptance layer.

Step 4:
- Authoritative observation source: video1.
- video1 acquisition remained live as proven by advancing latest.jpg timestamps.
- Hermes observation of a fresh frame reported the marker absent with HIGH
  confidence.
- visible OCTO1 input line remained empty.

Current classification:
- Step 3 API acceptance: PASS.
- Step 4 independent visible observation: FAIL.
- T-SCAF-005 overall: FAIL pending failure analysis.
- Cleanup is NOT authorized.
- No Ctrl+U has been sent.
- No HID retry is authorized until the failure mechanism is understood.

Important distinction:
KVMD API acceptance proves that the control service accepted the request.
It does not prove that OCTO1 visibly received the resulting HID events.


========================================================================
# CURRENT GIT COMMIT
========================================================================

commit 15071fba8a34d053cbdeab2be0eeeaabc1ef55ae
Author:     ppow1 <p.powell.2024@gmail.com>
AuthorDate: Thu Oct 1 23:04:33 2026 -0400
Commit:     ppow1 <p.powell.2024@gmail.com>
CommitDate: Thu Oct 1 23:04:33 2026 -0400

    Add mandatory campaign reground architecture gate

========================================================================
# CURRENT GIT STATUS
========================================================================

M LESSONS_LEARNED.md
 M PROVEN_FACTS.md
 M REGROUND_CONTRACT.md
 M REGROUND_PACKET.md
?? controller/video1_relay.py
?? runtime/
?? tests/T-SCAF-005.md

========================================================================
# CURRENT STEWARD STATE
========================================================================

{
  "dashboard_time": "2026-10-02T17:16:13-04:00",
  "campaign": {
    "name": "OctoMiner BIOS Campaign",
    "phase": "Campaign Infrastructure Qualification",
    "objective": "Establish autonomous test infrastructure before BIOS candidate execution",
    "status": "BUILDING"
  },
  "tests": {
    "total": 5,
    "passed": 4,
    "failed": 0,
    "pending": 0,
    "aborted": 0,
    "unmarked": 1,
    "completed": 4
  },
  "bios_updates": 0,
  "software_resets": 0,
  "hard_resets": 0,
  "octo2_reboots": {
    "count": 9,
    "prior_history_known": true,
    "authoritative_from_here": true,
    "previous_boot_id": "06f61b30-2839-4231-ba4f-f35feb27fabf",
    "last_boot_id": "3f3213a8-7cb0-463f-aa0f-32e38e34a50a",
    "last_reboot_observed_at": "2026-10-02T14:56:20-04:00",
    "baseline_note": "Count synchronized after controlled OCTO2 reboot qualification on 2026-10-01."
  },
  "steward_notifications": 0,
  "steward_wait_seconds": 0,
  "paused": false,
  "steward_needed": false,
  "current_operation": "Building Steward dashboard",
  "infrastructure": {
    "dev": {
      "name": "DEV",
      "status": "READY",
      "color": "green",
      "detail": "Steward controller running"
    },
    "octo1": {
      "name": "OCTO1",
      "status": "READY",
      "color": "green",
      "detail": "SSH/22 reachable"
    },
    "octo2": {
      "name": "OCTO2",
      "status": "READY",
      "color": "green",
      "detail": "SSH + 80B API ready"
    },
    "pikvm": {
      "name": "PiKVM",
      "status": "READY",
      "color": "green",
      "detail": "SSH/22 + HTTP/80 + HTTPS/443 reachable"
    },
    "videokvm": {
      "name": "Video-KVM Pi",
      "status": "READY",
      "color": "green",
      "detail": "SSH/22 reachable"
    }
  },
  "octo2": {
    "timestamp": "2026-10-02T17:16:09-04:00",
    "ssh": true,
    "boot_id": "3f3213a8-7cb0-463f-aa0f-32e38e34a50a",
    "uptime_sec": "8401.49",
    "llama_pid": "738",
    "api_ready": true,
    "state": "80B_READY"
  },
  "events": [
    {
      "timestamp": "2026-10-01T22:45:37-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_READY",
      "new_state": "OCTO2_UNREACHABLE"
    },
    {
      "timestamp": "2026-10-01T22:46:53-04:00",
      "event": "octo2_boot_changed",
      "old_boot_id": "abdc5f55-ef04-4b50-ac9a-bd6dfac9c7c7",
      "new_boot_id": "7f15e67d-db78-4396-a71e-d13773504684"
    },
    {
      "timestamp": "2026-10-01T22:46:53-04:00",
      "event": "octo2_state_changed",
      "old_state": "OCTO2_UNREACHABLE",
      "new_state": "80B_LOADING"
    },
    {
      "timestamp": "2026-10-01T22:52:30-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_LOADING",
      "new_state": "80B_READY"
    },
    {
      "timestamp": "2026-10-01T23:05:53-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_READY",
      "new_state": "OCTO2_UNREACHABLE"
    },
    {
      "timestamp": "2026-10-01T23:06:03-04:00",
      "event": "octo2_state_changed",
      "old_state": "OCTO2_UNREACHABLE",
      "new_state": "80B_READY"
    },
    {
      "timestamp": "2026-10-02T01:33:26-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_READY",
      "new_state": "OCTO2_UNREACHABLE"
    },
    {
      "timestamp": "2026-10-02T05:55:47-04:00",
      "event": "octo2_boot_changed",
      "old_boot_id": "7f15e67d-db78-4396-a71e-d13773504684",
      "new_boot_id": "76ccae58-46ac-4338-a214-cc09157c0236"
    },
    {
      "timestamp": "2026-10-02T05:55:47-04:00",
      "event": "octo2_state_changed",
      "old_state": "OCTO2_UNREACHABLE",
      "new_state": "80B_LOADING"
    },
    {
      "timestamp": "2026-10-02T06:01:45-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_LOADING",
      "new_state": "80B_READY"
    },
    {
      "timestamp": "2026-10-02T07:54:22-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_READY",
      "new_state": "OCTO2_UNREACHABLE"
    },
    {
      "timestamp": "2026-10-02T07:54:45-04:00",
      "event": "octo2_boot_changed",
      "old_boot_id": "76ccae58-46ac-4338-a214-cc09157c0236",
      "new_boot_id": "769f8b16-4f1e-4ac3-ab00-0ccbdd554366"
    },
    {
      "timestamp": "2026-10-02T07:54:45-04:00",
      "event": "octo2_state_changed",
      "old_state": "OCTO2_UNREACHABLE",
      "new_state": "80B_LOADING"
    },
    {
      "timestamp": "2026-10-02T08:00:33-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_LOADING",
      "new_state": "80B_READY"
    },
    {
      "timestamp": "2026-10-02T09:32:53-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_READY",
      "new_state": "OCTO2_UNREACHABLE"
    },
    {
      "timestamp": "2026-10-02T09:33:17-04:00",
      "event": "octo2_boot_changed",
      "old_boot_id": "769f8b16-4f1e-4ac3-ab00-0ccbdd554366",
      "new_boot_id": "3b5fa70a-f41a-4fec-92ab-fc1803143792"
    },
    {
      "timestamp": "2026-10-02T09:33:17-04:00",
      "event": "octo2_state_changed",
      "old_state": "OCTO2_UNREACHABLE",
      "new_state": "80B_LOADING"
    },
    {
      "timestamp": "2026-10-02T09:39:15-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_LOADING",
      "new_state": "80B_READY"
    },
    {
      "timestamp": "2026-10-02T10:14:12-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_READY",
      "new_state": "OCTO2_UNREACHABLE"
    },
    {
      "timestamp": "2026-10-02T10:15:27-04:00",
      "event": "octo2_boot_changed",
      "old_boot_id": "3b5fa70a-f41a-4fec-92ab-fc1803143792",
      "new_boot_id": "9ae17645-c5e5-4313-bbbd-1ba7ea5a9a68"
    },
    {
      "timestamp": "2026-10-02T10:15:27-04:00",
      "event": "octo2_state_changed",
      "old_state": "OCTO2_UNREACHABLE",
      "new_state": "80B_LOADING"
    },
    {
      "timestamp": "2026-10-02T10:21:25-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_LOADING",
      "new_state": "80B_READY"
    },
    {
      "timestamp": "2026-10-02T11:53:35-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_READY",
      "new_state": "OCTO2_UNREACHABLE"
    },
    {
      "timestamp": "2026-10-02T11:56:25-04:00",
      "event": "octo2_boot_changed",
      "old_boot_id": "9ae17645-c5e5-4313-bbbd-1ba7ea5a9a68",
      "new_boot_id": "06f61b30-2839-4231-ba4f-f35feb27fabf"
    },
    {
      "timestamp": "2026-10-02T11:56:25-04:00",
      "event": "octo2_state_changed",
      "old_state": "OCTO2_UNREACHABLE",
      "new_state": "80B_LOADING"
    },
    {
      "timestamp": "2026-10-02T12:02:03-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_LOADING",
      "new_state": "80B_READY"
    },
    {
      "timestamp": "2026-10-02T14:55:01-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_READY",
      "new_state": "OCTO2_UNREACHABLE"
    },
    {
      "timestamp": "2026-10-02T14:56:20-04:00",
      "event": "octo2_boot_changed",
      "old_boot_id": "06f61b30-2839-4231-ba4f-f35feb27fabf",
      "new_boot_id": "3f3213a8-7cb0-463f-aa0f-32e38e34a50a"
    },
    {
      "timestamp": "2026-10-02T14:56:20-04:00",
      "event": "octo2_state_changed",
      "old_state": "OCTO2_UNREACHABLE",
      "new_state": "80B_LOADING"
    },
    {
      "timestamp": "2026-10-02T15:01:58-04:00",
      "event": "octo2_state_changed",
      "old_state": "80B_LOADING",
      "new_state": "80B_READY"
    }
  ]
}

========================================================================
# REQUIRED REASONING RESPONSE
========================================================================

Before proposing another campaign test, explicitly report:

1. CURRENT PHASE
2. CAMPAIGN GOAL
3. CURRENT ROUND GOAL
4. CURRENT TEST / TRANSITION STATE
5. APPROVED ARCHITECTURE AND PLAYER ROLES
6. PROVEN FACTS THAT MATTER NOW
7. PROVEN FAILURES / APPROACHES NOT TO REPEAT
8. APPLICABLE LESSONS LEARNED
9. OPEN QUESTIONS
10. THINGS THAT MUST NOT BE REDISCOVERED
11. SAFETY / AUTHORITY BOUNDARIES
12. NEXT ROADMAP STEP
13. PROPOSED NEXT TEST

Do not substitute conversational memory for the sources above.
