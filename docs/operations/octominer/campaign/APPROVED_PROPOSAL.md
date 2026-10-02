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


