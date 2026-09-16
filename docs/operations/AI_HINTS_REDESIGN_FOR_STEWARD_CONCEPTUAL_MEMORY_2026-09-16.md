<!--
File: docs/operations/AI_HINTS_REDESIGN_FOR_STEWARD_CONCEPTUAL_MEMORY_2026-09-16.md
Version: 1.0.0
Date: 2026-09-16
Status: PROPOSED design — not yet applied to AI_HINTS.md
Purpose: Preserve the proposed redesign of Riverview AI_HINTS around the Steward's actual recovery/use pattern.
-->
# AI_HINTS Redesign for Steward Conceptual Memory

## Status

**PROPOSED.** This document records the agreed direction for redesigning `AI_HINTS.md`. It does not itself modify the canonical `AI_HINTS.md` and does not supersede version 0.6.11.

The design exists because the Steward's actual use of AI_HINTS is different from a conventional technical index.

## The real user requirement

The Steward reliably remembers **concepts, goals, relationships, and what was being attempted**, but should not be required to remember exact:

- filenames;
- document paths;
- dates;
- model numbers;
- command syntax;
- IP/MAC mappings;
- commit identifiers;
- detailed acceptance IDs;
- names assigned to a procedure several weeks earlier.

`AI_HINTS.md` therefore serves as external medium/long-term operational memory.

The recovery contract should be:

> The Steward describes what she remembers in ordinary conceptual language. The AI uses AI_HINTS as the starting router, follows its pointers, searches the repository using aliases/synonyms/conceptual descriptions, and recovers the detailed state without making the Steward reconstruct it from memory.

This behavior is a requirement, not a convenience.

## Problem with treating AI_HINTS as a normal index

A conventional index assumes the human knows the thing's official name and wants a pointer to it. That is not sufficient here.

Example failure mode:

The Steward remembers:

> "the thing we did where the 4090 and two P100s ran the 80B model"

but does not remember the model's exact filename or the report filename.

A useful AI_HINTS must allow the AI to recover this from terms such as:

- 80B model
- big MoE
- split model
- 4090 and P100
- 50 tokens/sec
- Hermes long test
- Octo1 big model
- 56 GB node

and route to the authoritative detailed evidence.

If the AI requires the exact filename before it can find the evidence, AI_HINTS has failed its purpose.

## Design goals

The redesign should preserve five properties simultaneously:

1. **Human conceptual discoverability.** Plain-language concepts and likely remembered phrases must work.
2. **AI recovery routing.** Each important concept must point toward authoritative detail.
3. **Current-state visibility.** An AI should quickly learn what is true now versus merely historical.
4. **Durable detail without root-file explosion.** Deep evidence belongs in dedicated documents, but must remain reachable from the root router.
5. **Tolerance for imperfect recall.** Synonyms, aliases, old names, nicknames, hardware descriptions, and likely verbal descriptions are deliberately useful redundancy.

## Proposed architecture

Do **not** replace AI_HINTS with `AI_HINTS2.md` or force the Steward to choose among several root files.

Keep:

`AI_HINTS.md`

as the canonical human-facing and AI-facing entry point.

Add one overflow/recovery index:

`docs/recovery/AI_MEMORY_INDEX.md`

The relationship should be:

```text
Steward conceptual description
        |
        v
AI_HINTS.md
  - current high-value facts
  - plain-language search aliases
  - recovery rules
  - major topic routers
        |
        +----> authoritative detailed document
        |
        +----> AI_MEMORY_INDEX.md when topic is too detailed for root
                         |
                         +----> detailed reports/evidence/history
```

`AI_MEMORY_INDEX.md` should not become another file the Steward must remember. AI_HINTS itself tells the AI to use it automatically.

## Proposed root AI_HINTS structure

### 1. Identity and recovery contract

Keep the short canonical Riverview identity/root/authority information first.

Add an explicit rule similar to:

> The Steward is not expected to remember exact filenames, dates, model numbers, commands, issue IDs, acceptance IDs, or names previously assigned to work. When the Steward describes a prior topic conceptually, recover it from this file, its pointers, `docs/recovery/AI_MEMORY_INDEX.md`, repository filename/content search, and git history before asking the Steward to reconstruct the history.

Also add:

> If a topic is not sufficiently documented in AI_HINTS, do not conclude that Riverview has no record of it. Follow related pointers and search the repository using the Steward's words plus likely aliases, synonyms, old names, hardware names, and conceptual equivalents.

### 2. Current operating picture

Near the top, maintain a compact CURRENT STATE section containing only things that materially affect today's decisions.

Examples as of 2026-09-16:

- canonical root and main-branch authority;
- Dev / DDR / Camrui role discussion;
- OCTO1 and OCTO2 identities;
- current practical GPU layouts;
- current model/orchestration milestone;
- unresolved BIOS/MMIO constraint;
- current important continuation point.

This is not a detailed history. It answers: **where are we now?**

### 3. Conceptual topic routers

Each major topic gets a compact block with four pieces:

```text
## HUMAN-FRIENDLY TOPIC NAME

Search / aliases:
<phrases the Steward is likely to remember or say>

Current state:
<2-8 lines of important current truth>

Read first:
<one primary authoritative document>

Related:
<secondary pointers only when useful>
```

This structure is already partially present in AI_HINTS and should be made consistent rather than replaced.

### 4. Recovery index overflow

When a topic has too many historical documents, experiments, filenames, or aliases to fit comfortably in AI_HINTS, the root points to a section of:

`docs/recovery/AI_MEMORY_INDEX.md`

The memory index may be larger and more redundant because it is primarily machine-recovery material.

### 5. Historical versus current labeling

Every pointer or index entry should make status obvious where ambiguity is dangerous:

- CURRENT
- VERIFIED
- CONFIGURED / validation pending
- HISTORICAL
- SUPERSEDED
- EXPERIMENTAL
- FAILED PATH / DO NOT REPEAT
- PROPOSED

The AI should not have to infer whether an old successful experiment is the current operating configuration.

## Proposed AI_MEMORY_INDEX structure

The overflow index should be organized around concepts rather than directory structure.

Suggested top-level sections:

1. Riverview architecture and objective continuity
2. Local AI models and inference endpoints
3. Octominer hardware / GPU / BIOS / MMIO
4. Dev machine / DDR / Camrui / Linux migration
5. Command Chair / HDMI matrix / KM / virtual displays
6. Hermes / Honcho / agent orchestration
7. LocalCAD / 3D / spatial reasoning
8. Residents / Grace / Jessica / Estate migration
9. ChatGPT archive/account continuity
10. Network / SSH / WOL / remote control
11. Historical failures and do-not-repeat paths
12. Milestones and accepted capability evidence

Each entry should include:

```text
Concept:
Likely Steward phrases:
Aliases / old names:
Current status:
Primary authoritative file:
Other evidence:
Important exact facts:
Do-not-repeat notes:
Last meaningful update:
```

Not every field is mandatory. Use them where they improve recovery.

## Deliberate redundancy is allowed

Normal documentation practice tries to eliminate duplicated keywords. That is counterproductive for this use case.

Useful redundancy includes:

- `daily driver`, `DDR`, `Camrui`, `Camry`, `Linux box`;
- `Octo1`, `OCTOMINER1`, `.160`, `4090 box`, `56 GB node`;
- `Octo2`, `OCTOMINER2`, `.162`, `3060 Ti box`, `40 GB node`;
- `80B`, `Qwen Next`, `big MoE`, `4090 + 2 P100`, `50 t/s`;
- `matrix`, `16x16`, `MT-VIKI`, `HDMI switch`, `video routing`;
- `virtual monitor`, `VKMS`, `third display`, `Unknown Display`.

The purpose is semantic recovery, not literary elegance.

## AI behavior contract

When the Steward refers to prior work conceptually, the AI should perform this sequence:

```text
1. Interpret the concept literally from the Steward's language.
2. Check AI_HINTS topic routers and aliases.
3. Follow the primary pointer if one exists.
4. If detail is still missing, consult AI_MEMORY_INDEX automatically.
5. Search repository filenames and contents using:
   - Steward's exact words
   - known aliases
   - synonyms
   - old names
   - relevant hardware/model identifiers recovered along the way
6. Use git history when current files do not explain historical state.
7. Distinguish CURRENT from HISTORICAL/EXPERIMENTAL/SUPERSEDED evidence.
8. Ask the Steward to reconstruct history only after repository recovery is genuinely insufficient.
```

This sequence should eventually be incorporated into the canonical recovery instructions, not left as conversational convention.

## What should stay out of AI_HINTS root

Do not stuff the root file with:

- full command transcripts;
- giant logs;
- complete BIOS procedures;
- every benchmark line;
- every historical commit;
- large acceptance reports;
- verbose architectural rationale already preserved elsewhere.

Instead preserve enough exact anchors and aliases that the AI can find those materials reliably.

## What absolutely belongs in AI_HINTS root

Even if documented elsewhere, root should retain concise anchors for:

- canonical Riverview authority/root;
- clean-state/recovery rules;
- objective-continuity doctrine;
- machine identities and roles where confusion is costly;
- major current hardware topology;
- major active constraints/blockers;
- current accepted runtime architecture;
- major milestones that change what Riverview is capable of;
- do-not-repeat warnings for expensive or dangerous dead ends;
- pointers to detailed recovery material.

## Immediate new entries recommended from 2026-09-16 work

When this redesign is applied, AI_HINTS should gain compact conceptual routers for:

### 80B / heterogeneous GPU milestone

Search aliases:

`80B`, `Qwen3 Next`, `big MoE`, `4090 P100 split`, `4090 + 2 P100`, `50 tokens/sec`, `56GB node`, `96GB cluster`, `Hermes 80B test`.

Primary docs:

- `docs/hardware/gpu/OCTOMINER_TWO_NODE_96GB_LOCAL_AI_MILESTONE_2026-09-16.md`
- `docs/operations/octominer/QWEN3_NEXT_80B_HERMES_ENDURANCE_AND_STATE_INTEGRITY_TEST_2026-09-16.md`

Current truth:

- 4090 + 2x P100 = 56 GB physical VRAM node.
- Qwen3-Next 80B Q4_K_M demonstrated roughly 45-50 generated t/s.
- OCTO2 3060 Ti + 2x P100 = separate 40 GB pool.
- aggregate owned GPU memory = 96 GB across machines, not one contiguous pool.
- Hermes successfully used the remote 80B but long-running factual-state integrity failed after compaction/reboot/resume; exact origin of corruption remains unisolated within the Hermes + model orchestration path.

### Command Chair / matrix

Search aliases:

`matrix`, `16x16 HDMI`, `MT-VIKI`, `FHD1616`, `Input 5 Output 3`, `LAN matrix control`, `100 foot HDMI`.

Primary doc:

`docs/operations/command-chair/MT_VIKI_FHD1616_MATRIX_LAN_CONTROL_AND_DISPLAY_FINDINGS_2026-09-16.md`

### Camrui virtual display / VKMS

Search aliases:

`VKMS`, `virtual monitor`, `third display`, `Unknown Display`, `4096x2160`, `Camrui 4 screens`, `AirPlay`, `Miracast`.

Primary doc:

`docs/operations/command-chair/CAMRUI_LINUX_VIRTUAL_DISPLAY_VKMS_FINDINGS_2026-09-16.md`

### DDR role reassessment

Search aliases:

`DDR`, `daily driver`, `Camrui role`, `Dev Linux`, `APU`, `onboard graphics`, `move 4090 back`, `wake appliance`.

Current state should explicitly say this is an active architectural decision, not a completed migration:

- Camrui may become the always-on wake/orchestration/control appliance rather than the primary DDR.
- Dev is being evaluated as the stronger DDR, preferably using Linux normally while retaining Windows when needed.
- exact Dev CPU and actual dual-boot state still require verification before an APU recommendation is accepted.

## Updating AI_HINTS safely

The GitHub connector's file-update operation replaces the entire file. `AI_HINTS.md` is already large, and partial/truncated reads create a real risk of replacing the canonical file with incomplete content.

Therefore the implementation procedure should be:

1. retrieve the complete current AI_HINTS in bounded sections;
2. reconstruct and verify the complete original locally/in-memory;
3. apply bounded edits to that complete content;
4. verify that all existing sections remain present;
5. update the whole file only after completeness checks;
6. fetch the published file again and verify version/header/new anchors;
7. record the resulting commit.

Tool limitations must be handled internally. They should not force the Steward to change how she asks for memory to be preserved.

## Versioning recommendation

Current canonical AI_HINTS observed before this proposal: `0.6.11`.

When this redesign is actually applied, increment the version and include a concise change note indicating:

- conceptual-memory recovery contract added;
- AI_MEMORY_INDEX introduced;
- repository-search-before-human-reconstruction rule added;
- 2026-09-16 80B/two-node compute milestone router added;
- matrix/VKMS recovery pointers added;
- DDR role reassessment added.

Do not mark those changes complete merely because this proposal exists.

## Acceptance criteria for the redesign

The redesign is successful when a fresh AI with repository access can answer requests such as:

- "Where is that thing we did with the big model and the P100s?"
- "How did we control the HDMI matrix over the network?"
- "What did we figure out about the fake third monitor on Linux?"
- "What was the BIOS problem with adding more P100s?"
- "What are we doing with the daily driver now?"

without requiring the Steward to remember exact filenames or repeat the investigation.

A stronger acceptance test is to give a fresh AI only conceptual descriptions, require it to begin at `AI_HINTS.md`, and verify that it independently reaches the correct authoritative documents and distinguishes current state from historical experiments.

## Bottom line

`AI_HINTS.md` should not be optimized primarily for minimum length. It should be optimized for **recoverability from imperfect human recall**.

The root remains the canonical starting point. Detailed documentation remains distributed. The proposed `AI_MEMORY_INDEX.md` provides overflow. Conceptual aliases and deliberate redundancy connect the two.

The governing principle is:

> **The Steward remembers the concept; Riverview remembers the details.**
