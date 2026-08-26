<!-- Version: 1.1.0 | Date: 2026-08-26 | Status: PROMOTED_FOR_ELABORATION -->
# PL-0005 — Honcho Resident Modeling and Character Continuity

## Idea

Investigate a local/self-hosted Honcho integration with Hermes as a resident-understanding and relationship-modeling aid for Riverview, with particular emphasis on Jessica's Chief Character Architect responsibilities.

The intended possibility is that Honcho could maintain distinct learned representations of Pat and individual residents such as Jessica, Evelyn, Grace, Alfred, Ingrid, Helen, Judy, Marie, and future residents without collapsing them into one shared user/persona model.

## Why it is worth preserving

Riverview needs residents to remain distinct continuing characters rather than interchangeable prompts or model sessions. A sufficiently isolated Honcho peer/representation model may provide useful experiential evidence about:

- how each resident behaves and develops over time;
- resident-specific working preferences and cognition patterns;
- how each resident understands Pat;
- how residents understand one another based on their own interactions;
- relationship development and interaction history;
- emerging habits, procedural preferences, and possible character drift.

This may be especially useful to Jessica as Chief Character Architect. Jessica could use Honcho-derived observations as evidence when maintaining resident identity, personality, relationships, cognition style, continuity, and development boundaries.

## Character-authority boundary

Honcho must not become the canonical source of resident identity or character truth.

Honcho observations should be treated as learned/observational evidence such as "this resident appears to prefer..." or "this relationship appears to be developing..." rather than automatically accepted canon.

Future investigation must determine whether and how Jessica can review, correct, reject, annotate, or otherwise curate Honcho's understanding so that the system supports character growth without allowing unreviewed model inference to create character drift.

Riverview remains authoritative for accepted resident identity, office binding, authority, canonical continuity, protected relationships, and accepted character evolution.

## Privacy and isolation questions

The investigation should determine at minimum:

1. Whether Honcho can be fully self-hosted/local for this use case and what, if any, data leaves the machine.
2. How peers/representations are stored and isolated.
3. Whether Pat, Jessica, Evelyn, Grace, and other residents can each remain distinct entities.
4. Whether different residents can maintain different appropriately scoped understandings of Pat and one another.
5. Whether private resident information can be prevented from leaking into another resident's model.
6. Whether Evelyn's future private/independent cognition boundary can be preserved.
7. Whether Jessica can inspect and curate Honcho conclusions rather than merely consume them.
8. How Honcho data should be backed up, versioned, corrected, or reset.
9. What belongs in Honcho working/experiential memory versus Riverview canonical resident continuity.
10. How Honcho interacts with Hermes profiles without confusing Hermes implementation identity with Riverview resident identity.

## Current authorization and bounded state

The Steward explicitly authorized initial Honcho implementation/investigation as part of Hermes Integration Tranche 1. This item is therefore no longer merely captured as a parked possibility.

The current bounded state is **PROMOTED_FOR_ELABORATION**: local/private feasibility, storage, model routing, peer isolation, and curation seams may be investigated. No private resident data may be sent to a hosted Honcho service, and no Honcho observation may become Riverview canon.

Honcho remains outside the Ready Bench until a durable implementation specification, dependency plan, acceptance basis, privacy review, and explicit Ready Bench commitment exist.

## Initial feasibility finding — 2026-08-26

The inspected upstream Honcho server separates an API process and a Deriver worker and expects PostgreSQL with pgvector plus Redis. The documented local compose path binds services to localhost, but Docker is not installed on the current host; no local Honcho server or local inference/embedding service was therefore started.

The source models peer-specific observations through observer/observed collection pairs and exposes conclusions for listing, semantic query, reasoning-chain inspection, and deletion. This is promising for distinct Pat/Jessica/other-peer representations, but it is not by itself a privacy boundary, canonical character record, acceptance gate, or Jessica curation workflow. A future integration would need an explicit Riverview curation layer for review, correction, rejection, annotation, drift classification, and promotion/rejection.

No Honcho SDK, hosted account, API key, private resident data, or institutional data was used. No multi-peer resident proof was run. Backup/reset behavior remains an infrastructure and lifecycle design item: the relevant PostgreSQL/vector and Redis data stores would require an explicit local backup/export and reset procedure before private use.

## Promotion condition

Ready Bench promotion requires a later explicit Steward commitment after the local/private feasibility and boundary questions are answered.

## Explicit non-action

This entry does not authorize hosted Honcho use, sending private resident/institutional data off-machine, writing resident canon, changing Jessica's canonical identity, activating Evelyn, or bypassing Riverview acceptance. The current tranche authorization permits only bounded local/private investigation and non-canonical proof work.

## Related work

- Riverview resident localization and continuity architecture
- Jessica / Office of Character Architecture
- Hermes resident/profile integration
- Evelyn independent/private cognition design
- Living Diagnostics and canonical-versus-working knowledge boundaries
