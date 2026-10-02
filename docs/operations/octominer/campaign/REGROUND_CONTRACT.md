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
