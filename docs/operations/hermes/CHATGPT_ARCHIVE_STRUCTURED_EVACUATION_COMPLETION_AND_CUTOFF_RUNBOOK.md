# ChatGPT Structured Evacuation Completion and Cutoff Runbook

Status: Canonical recovery/runbook for the September 2026 ChatGPT account transition
Date: 2026-09-06
Owner: Steward
Archive root: `A:\AI\Tools\ChatGPTConversationArchive`
Riverview canonical root: `A:\Riverview\standalone`

## 1. Purpose

This document records the completed C1/C2/C3 structured ChatGPT evacuation, the exact operational lessons required to reproduce it, what the resulting structured data buys us, and the procedure to use between this checkpoint and the planned 2026-09-14/15 account transition.

This is the fast-recovery source for the final evacuation. Do not reconstruct the process from chat memory.

The large private archive corpus remains local on the A: drive. GitHub stores this runbook and related engineering/specification material only; it is not the authority for the preserved conversation bytes.

## 2. Completed structured-evacuation state

All three authenticated seat populations have completed structured evacuation.

### C1

Seat/archive label: `current-business-seat`

Final result:

- expected conversations: `534`
- structured COMPLETE: `534 / 534`
- unresolved: `0`
- structured messages: `102,156`
- conversations containing file IDs: `256`
- total unique-per-chat file IDs: `10,662`
- chats with spreadsheet names: `55`
- structured JSON bytes: `443,245,767`
- final runner exit code: `0`

Canonical local paths:

- structured root: `A:\AI\Tools\ChatGPTConversationArchive\archive\current-business-seat\structured-conversations`
- runner: `A:\AI\Tools\ChatGPTConversationArchive\c1-structured-evacuation-production-v2.mjs`
- checkpoint: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C1-Structured-Evacuation-Checkpoint.json`
- manifest JSON: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C1-Structured-Evacuation-Manifest.json`
- manifest CSV: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C1-Structured-Evacuation-Manifest.csv`
- report: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C1-Structured-Evacuation-Report.txt`

Authenticated browser/CDP used by the working process:

- C1 CDP port: `9224`

Important: the C1 final report contains stale historical next-step text saying to repeat C2 as 128 and C3 as 2. Ignore that text. Those were old population baselines and have been superseded by the completed live inventories below.

### C2

Seat/archive label: `seat-c2-patlee2019`

Final result:

- current conversations discovered: `155`
- structured COMPLETE: `155 / 155`
- missing: `0`
- incomplete: `0`
- structured messages: `76,052`
- structured file references observed: `7,335`
- raw structured pages preserved: `314`

Canonical local paths:

- structured root: `A:\AI\Tools\ChatGPTConversationArchive\archive\seat-c2-patlee2019\structured-conversations`
- runner: `A:\AI\Tools\ChatGPTConversationArchive\c2-structured-evacuation-production.mjs`
- checkpoint: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C2-Structured-Evacuation-Checkpoint.json`
- manifest: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C2-Structured-Evacuation-Manifest.json`
- report: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C2-Structured-Evacuation-Report.txt`

Authenticated browser/CDP used by the working process:

- C2 CDP port: `9226`

### C3

Seat/archive label: `seat-c3-contact-ionoge`

Final result:

- current conversations discovered: `3`
- structured COMPLETE: `3 / 3`
- missing: `0`
- incomplete: `0`
- structured messages: `1,518`
- structured file references observed: `77`
- raw structured pages preserved: `6`

Canonical local paths:

- structured root: `A:\AI\Tools\ChatGPTConversationArchive\archive\seat-c3-contact-ionoge\structured-conversations`
- runner: `A:\AI\Tools\ChatGPTConversationArchive\c3-structured-evacuation-production.mjs`
- checkpoint: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C3-Structured-Evacuation-Checkpoint.json`
- manifest: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C3-Structured-Evacuation-Manifest.json`
- report: `A:\AI\Tools\ChatGPTConversationArchive\diagnostics\C3-Structured-Evacuation-Report.txt`

Authenticated browser/CDP used by the working process:

- C3 CDP port: `9227`

## 3. What this evacuation actually preserved

The structured evacuation is materially different from the earlier transcript/PDF/browser-render capture.

For each conversation, the authenticated ChatGPT conversation endpoint was queried and, when necessary, walked backward through `page_info.start_cursor` / `has_previous_page` pagination until the beginning of the conversation was reached. The local merged `conversation.json` is therefore built from the structured conversation representation rather than from a virtualized browser DOM.

The resulting structured source preserves, where present:

- conversation ID and title;
- creation/update timestamps;
- ordered message records;
- user, assistant, tool, and system roles;
- stable message IDs;
- structured content types;
- text and code content;
- model/tool metadata;
- tool calls and tool results;
- file/object references such as `file_...` IDs;
- citation/source metadata;
- pagination evidence;
- raw source pages in the seat-specific capture roots.

This means the structured evacuation alone is sufficient to build an OctoChat/pseudo-chat representation of a conversation without depending on the old transcript, PDF, MHTML, or browser HTML.

A direct proof was performed on a random C2 conversation:

- conversation ID: `6a74cb17-8d08-83ea-a4aa-6fb6cbe2959e`
- title: `Estate Parking Lot Recovery`
- source: its evacuated `conversation.json`

That file alone exposed the readable user/assistant exchange plus the deeper tool/code/source structure needed for optional Activity/Evidence/Raw views.

The object layer remains separate. A structured file reference proves that a message referred to a file/object, but does not by itself guarantee that the binary object bytes were recovered. Missing binaries no longer block preservation of the conversation or its attachment slot/provenance.

## 4. Why the structured pass was necessary

Earlier browser/PDF work showed that ChatGPT's live/saved web presentation can be virtualized. A visually large page or PDF is not proof that every historical turn is present.

The structured pass solved that by preserving the underlying conversation data directly.

Operational consequences:

1. The structured `conversation.json` becomes the primary preservation source for chat reconstruction.
2. Old transcripts/PDFs/screenshots remain useful evidence/derivatives, but are not required to reconstruct ordinary conversation text and ordering.
3. Historical image/file-binary recovery can continue later without holding the core archive hostage.
4. Search/indexing can operate on structured messages and file references rather than reverse-engineering rendered pages.

## 5. Important lessons from the working evacuation

### 5.1 Seat rate limits are independent operationally

C1, C2, and C3 were successfully run independently, including overlap between C1 and C2. Do not impose a one-seat-at-a-time rule merely from habit. Use separate seat/browser/output state and treat the provider's observed per-seat throttling independently.

### 5.2 Checkpointing is essential

Completed conversations are checkpointed. If a runner is stopped or exhausts retries, resume from the existing checkpoint rather than rebuilding completed work.

Do not delete checkpoints before the final cutoff reconciliation.

### 5.3 429 handling

The working runners use bounded retry/backoff for HTTP 429. The proven production pattern included:

- normal pacing around 3 seconds;
- multiple retry attempts;
- progressively longer waits, including 30, 60, 120, and 180 second ranges on the hardened C1 path.

Long runs may spend substantial time sleeping while still making forward progress. A visible 429 is not itself a failure.

### 5.4 5xx/request-timeout handling

C2 demonstrated that HTTP `500 Request timeout` can be transient. Its runner was patched to retry `500`, `502`, `503`, and `504` with bounded exponential waits. That recovery succeeded in production.

Do not assume a 5xx means corrupt conversation data.

If a future runner lacks the 5xx patch, either add the already-proven bounded retry behavior or allow it to fail safely and resume from checkpoint. Do not discard the capture.

### 5.5 Browser/CDP identity

The working structured process depended on authenticated Chrome/CDP sessions. Preserve the established seat profiles and ports through final cutoff.

Do not casually reset browser profiles/cookies or change ports before the final delta capture.

The account/workspace ID observed inside the structured session is not sufficient to distinguish seats. Seat identity for this campaign is the combination of the established authenticated browser/profile, CDP port, archive root, and checkpoint/manifest lineage.

### 5.6 Do not trust stale denominators

C2 was previously believed to contain 128 conversations but live inventory discovered 155.

C3 was previously believed to contain 2 conversations but live inventory discovered 3.

Therefore the final cutoff must inventory each live seat again. Never use an old hardcoded denominator as proof of completeness.

## 6. What to do between 2026-09-06 and 2026-09-14

The historical rescue is complete. Between now and cutoff, normal use can continue, but preserve the evacuation machinery and avoid unnecessary churn.

### Required behavior

- Keep the current structured roots, checkpoints, manifests, reports, and runners intact.
- Keep the authenticated C1/C2/C3 browser profiles usable.
- Do not delete or rename seat roots casually.
- Do not rerun all historical conversations merely because new chats are created.
- New/updated conversations should be treated as a delta against the completed baseline.
- Large local archive bytes remain on A:, not in GitHub.

### Recommended daily discipline

No full daily evacuation is required unless ChatGPT account state becomes unstable.

If desired, perform a lightweight live inventory and record only the conversation IDs/counts that are new or updated since the 2026-09-06 baseline. The important requirement is that any work done after this checkpoint can be found on cutoff day.

Do not spend the intervening week re-solving historical image/object recovery unless it is independently useful. It is not on the critical path to closing the Business seats.

## 7. Final evacuation procedure for 2026-09-14/15

The final operation is a reconciliation/delta capture, not another blind historical rescue.

### Step 1 - Freeze ordinary use at the cutoff boundary

When ready to close the Business seats, stop creating/editing conversations long enough to make the final inventory deterministic.

Record the cutoff time.

### Step 2 - Verify local baseline state

For C1, C2, and C3 verify that the completed baseline reports still exist and still say COMPLETE.

Expected completed baseline populations as of 2026-09-06:

- C1: `534`
- C2: `155`
- C3: `3`

These are baseline counts, not final-cutoff denominators.

### Step 3 - Start/verify the established authenticated browser sessions

Use the established seat profiles/CDP ports:

- C1: `9224`
- C2: `9226`
- C3: `9227`

Verify the intended seat is authenticated before capture.

Do not substitute one seat's profile/output root for another.

### Step 4 - Inventory each seat live

Query the current conversation inventory for each seat using the same authenticated mechanism used by the structured runners.

Persist the current conversation IDs and metadata.

Do not declare completion from the old 534/155/3 counts.

### Step 5 - Reconcile by stable conversation ID

Compare each live seat inventory to its 2026-09-06 manifest/checkpoint.

Classify each conversation at minimum as:

- `UNCHANGED_PRESERVED`
- `NEW_NEEDS_CAPTURE`
- `UPDATED_NEEDS_REFRESH`
- `EXCEPTION`

Use stable conversation ID, not title.

Where practical, use `update_time` plus local capture metadata to identify updated conversations. If a conversation's changed state is ambiguous, refresh it rather than guessing.

### Step 6 - Capture only new/updated conversations

Use the existing structured runner logic and the same seat-specific output roots/checkpoint lineage.

Requirements for every newly captured/refreshed conversation:

- authenticated HTTP 200 structured retrieval;
- backward pagination continued until `has_previous_page` is false;
- merged `conversation.json` written locally;
- raw page JSON retained where the runner does so;
- local checkpoint/manifest updated only after that conversation reaches COMPLETE;
- 429 retry/backoff respected;
- transient 5xx/request-timeout retry behavior retained where supported.

Do not recapture all historical conversations unless reconciliation proves that the existing baseline cannot be trusted.

### Step 7 - Re-inventory after delta capture

Run the live inventory again after all deltas are captured.

For every live conversation ID, prove one of:

- it maps to a complete local structured conversation, or
- it is an explicit acknowledged exception.

Do not allow silent gaps.

### Step 8 - Build the cross-seat unique corpus manifest

Do not simply add C1 + C2 + C3 counts and call that the unique corpus size. The same conversation can be visible from more than one seat/workspace context.

Build a final cross-seat manifest keyed by conversation ID containing at minimum:

- conversation ID;
- title;
- created/update timestamps;
- seat provenance(s);
- local structured path(s);
- completion status;
- file-reference count;
- source manifest/checkpoint lineage;
- duplicate/cross-seat relationship;
- exception state.

The final unique-conversation count must come from this deduped manifest.

### Step 9 - Produce final cutoff report

The report must state, per seat:

- live conversations discovered at cutoff;
- complete local structured captures;
- unresolved/exception count;
- new conversations captured since baseline;
- refreshed/updated conversations since baseline;
- final message count if recalculated;
- file-reference totals if recalculated;
- checkpoint/manifest/report paths.

It must also state:

- total cross-seat references;
- unique conversation IDs after deduplication;
- duplicate/cross-seat count;
- any explicit exceptions;
- cutoff timestamp;
- decision whether Business-seat historical conversational preservation is complete.

### Step 10 - Only then close/downgrade the paid Business environment

Do not transition to the free-account configuration until the final reconciliation report proves that every live conversation is locally preserved or explicitly excepted.

## 8. Pseudo-chat / OctoChat reconstruction rule

For new archive-viewer work, prefer the structured conversation source.

Recommended layered renderer:

### Reading view

Show ordinary user and assistant turns, Markdown, code blocks, timestamps, attachments/file slots, and useful citations.

### Activity view

Optionally expose tool calls, searches, repository reads, and execution results.

### Evidence view

Expose message IDs, models, content types, turn IDs, source metadata, and preservation provenance.

### Raw view

Expose or link to the untouched source `conversation.json` and raw page files.

Do not require the old PDF or transcript to render the reading view when structured source exists.

## 9. Historical object/media recovery status

Historical media/object recovery is not required to preserve ordinary conversational text/structure and is not a blocker for the September cutoff.

Continue to preserve any already-recovered binaries and their provenance.

For unresolved object references:

- retain the file/object ID and message association;
- render an unresolved attachment placeholder if necessary;
- search local storage later when useful;
- do not fabricate binary identity or placement.

## 10. Related canonical documents

Read together with:

- `docs/operations/hermes/CHATGPT_ARCHIVE_CAMPAIGN_SPECIFICATION.md`
- `docs/operations/hermes/CHATGPT_ARCHIVE_CAMPAIGN_HERMES_SUBMISSION.md`
- `docs/operations/HERMES_C1_C2_C3_RESOURCE_ORCHESTRATION.md`

This runbook supersedes the old 128/2 C2/C3 population assumptions for archive-preservation purposes.

## 11. Recovery shortcut

If a future worker is told only:

> Finish the ChatGPT archive before account cutoff.

then:

1. read this document completely;
2. verify the three local baseline reports/checkpoints/manifests;
3. preserve the established authenticated seat/browser profiles;
4. live-inventory all three seats;
5. reconcile by conversation ID;
6. capture only new/updated conversations;
7. re-inventory and prove no silent gaps;
8. build the cross-seat deduped manifest;
9. write the final cutoff report;
10. do not close the Business seats until the report proves completion or records explicit Steward-accepted exceptions.

## 12. Preservation decision as of 2026-09-06

Historical structured evacuation is complete at the seat level:

- C1 `534/534`
- C2 `155/155`
- C3 `3/3`

The remaining critical-path work before the planned 2026-09-14/15 transition is final live inventory, delta capture of new/updated conversations, cross-seat deduplication, and final cutoff reconciliation/reporting.
