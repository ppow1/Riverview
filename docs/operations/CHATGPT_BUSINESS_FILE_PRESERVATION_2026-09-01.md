# ChatGPT Business File Preservation — Working Recovery Record

Date: 2026-09-01
Status: Proven working procedure; file phase intentionally paused for conversation recovery

## Purpose

This record preserves the working method used to evacuate ChatGPT Business Library content from the three Business seats before the planned account/workspace transition. It exists so the file phase can be resumed and reconciled later without reconstructing the method from conversation history.

This is a preservation/recovery record, not a claim that every API-visible object has been recovered. The current stopping point deliberately accepts a small tail of unresolved objects because continued ChatGPT use can create additional Library objects before final reconciliation.

## Seat mapping

- C1 / Seat 1 — `p.powell.2024@gmail.com`
- C2 / Seat 2 — `patlee2019@gmail.com`
- C3 / Seat 3 — `contact@ionoge.com`

Local tooling root:

`A:\AI\Tools\ChatGPTConversationArchive`

Archive roots:

- C1: `archive\current-business-seat`
- C2: `archive\seat-patlee2019-gmail-com`
- C3: `archive\seat-contact-ionoge-com`

Inventory roots follow the same seat naming under `inventory\`.

## What the Library denominator means

The useful preservation denominator is the population returned by the ChatGPT Library API and filtered to nodes whose `kind` is `file`. This is broader than the Storage UI label **Files**. Image-category Library entries are also `kind=file` objects.

Therefore the archive's `FilesTotal` should be understood operationally as **Library objects to preserve**, including images, not merely the Storage UI's ordinary-file counter.

This was independently demonstrated on C2:

- API-visible Library objects: 3,301
- image MIME objects: 2,220
- non-image MIME objects: 1,081
- Storage UI showed approximately 1,080 Files and 2,219 Images

The two-object difference between UI category counters and API-visible objects was intentionally not used as a reason to discard API-visible content. Preservation favors retaining every exposed Library object.

C1 also independently demonstrated the broader denominator: its Storage UI showed 1,101 Files + 3,505 Images = 4,606 UI-counted items, while the API inventory contained 4,647 Library objects. Earlier reconciliation identified the additional API-visible population rather than treating the API denominator as ordinary files only.

## Proven inventory method

The working inventory path attaches to an authenticated ChatGPT browser through Chrome DevTools Protocol / Playwright, captures the authenticated `/backend-api/` request headers from the browser session, and walks the Library endpoint through cursor convergence.

Endpoint used during the successful C2 inventory:

`GET /backend-api/files/library/nodes`

Continue requesting with the returned cursor until `cursor` is absent. Accumulate all returned `items`, then retain every item where:

`kind === 'file'`

Write those records as JSONL to the seat's:

`inventory\<seat>\library-objects.jsonl`

Important lesson: do **not** filter images out of this inventory. `library_file_category`, `mime_type`, and related metadata can be used for reporting, but the preservation set should contain all API-visible `kind=file` objects.

## Proven download/resolution chain

The successful file recovery logic resolves each Library object through the first-party ChatGPT backend rather than trying to scrape rendered Library cards.

The proven resolver sequence is:

1. Enumerate Library nodes.
2. Resolve the Library file's available versions.
3. Resolve the backing file download endpoint.
4. When required, resolve Estuary content to a fresh signed content URL.
5. Download bytes to a temporary `.part` file.
6. Validate the response before accepting it.
7. Compute SHA-256 / retain integrity metadata.
8. Atomically rename the completed temporary file into the final local object location.
9. Persist checkpoint/state so interruption does not require starting from zero.

Relevant first-party endpoints encountered in the working implementation include:

- `/backend-api/files/library/files/{library_file_id}/versions?limit=20`
- `/backend-api/files/download/{file_id}?inline=true`
- `/backend-api/estuary/content?id=file_{object_id}`

Signed URLs should be treated as ephemeral. Resolve them fresh when needed rather than caching them for a later bulk run.

## Safety properties that mattered

The working file lane follows these rules:

- Download sequentially / conservatively rather than spawning uncontrolled parallel workers.
- Run exactly one preservation worker per seat/lane unless a later tested design explicitly changes that rule.
- Write to `.part` first; never present a partial response as a completed object.
- Validate HTTP status, content/body characteristics, and expected byte behavior before finalizing.
- Use atomic rename for completed bytes.
- Preserve SHA-256 evidence where available.
- Resume from durable state instead of redownloading completed objects.
- Never delete a local successful object merely because later API/UI accounting changes.
- Never reduce the preservation population merely to force agreement with the Storage UI counter.
- Do not close or restart an operator's normal Chrome session as part of archive recovery.
- Prefer a dedicated isolated authenticated archive Chromium/CDP instance for a seat when browser binding would otherwise be ambiguous.

## Browser binding lesson

Shared/browser-profile ambiguity consumed substantial time. A generic `browser.contexts()[0]` is only acceptable when the CDP endpoint is known to belong to one isolated archive browser. It is unsafe as a seat identity mechanism when several profiles/accounts share a browser process.

For C2, the successful correction was a dedicated Playwright Chromium instance using its own user-data directory and CDP port 9226. The operator logged that isolated browser into C2. The preservation worker then attached to that dedicated endpoint without disturbing normal Chrome.

C1 used its own dedicated archive Chromium/CDP endpoint on port 9224.

General rule: **bind a preservation worker to an isolated authenticated browser endpoint, not merely to "the first context" of a multi-account browser.**

Do not call `browser.close()` on an operator/shared browser. The archive runners were adjusted so attachment teardown did not close the live browser.

## C2 classification discovery

The C2 inventory exposed useful metadata fields including:

- `kind`
- `library_file_category`
- `library_artifact_type`
- `mime_type`
- `file_extension`
- `file_id`
- `origination_message_id`
- `origination_thread_id`
- file size/upload/processing timestamps

C2's 3,301 objects included 2,220 image MIME objects and 1,081 non-image objects. This established that a `kind=file` Library inventory includes both the Storage UI's Files and Images populations. A temporary attempt to filter C2 to the 1,081 non-image objects was reversed; the correct preservation target is the full 3,301-object inventory.

## Current stopping-point counts

At the 2026-09-01 stopping point, the live local-file dashboard reported approximately:

- C1: 4,598 / 4,647 Library objects locally present
- C2: 3,293 / 3,301 Library objects locally present
- C3: 3,286 / 3,287 Library objects locally present

These counts are based on physical local artifacts, not worker heartbeat/state claims.

The remaining tails are not being pursued now. In particular, C2 reached 3,293/3,301 with one worker but the last eight stopped advancing. The operator elected to stop file work and move to conversation preservation.

C1 and C3 had already been treated operationally as complete enough for this phase. Do not interpret that as proof that the remaining API-visible exceptions are unrecoverable.

## Why file work is being paused rather than declared permanently finished

Continued use of ChatGPT can create new Library objects, especially through screenshots/images and other conversation activity. Therefore a perfect denominator today can become stale before the final Business preservation deadline.

The correct operational approach is:

1. Preserve the large existing population now.
2. Pause file work once the remaining tail is no longer productively moving.
3. Complete the higher-risk conversation preservation work.
4. Before the final transition/cancellation deadline, rerun Library inventory for all three seats.
5. Compare fresh API inventory against physically preserved local objects.
6. Download newly created or previously unresolved objects.
7. Produce a final reconciliation report with remaining exceptions explicitly listed.

The operator identified September 16 as the practical deadline/checkpoint for final reconciliation.

## Live dashboard semantics

The useful dashboard measures physical progress, not merely state-machine activity.

For each seat it reports:

- FilesSaved — physically present completed Library artifacts
- FilesTotal — frozen/current API Library-object denominator
- FilesLeft
- FileGain
- ConvSaved
- ConvTotal
- ConvLeft
- ConvGain
- Workers — diagnostic only

The key rule is: **a running worker is not progress. Progress is an increase in locally completed artifacts.**

This distinction mattered because earlier conversation workers remained alive while producing no useful movement.

## What not to repeat

- Do not equate the Storage UI's **Files** number with the complete Library preservation population.
- Do not exclude images.
- Do not use an ambiguous shared Chrome context as proof of seat identity.
- Do not launch multiple workers against the same state/inventory; concurrent writers previously produced inconsistent bookkeeping.
- Do not use worker heartbeat as evidence of preservation progress.
- Do not throw away API-visible objects simply to make the denominator equal the UI counter.
- Do not spend hours chasing a tiny exception tail while the user is still actively creating new Library objects; defer that tail to final reconciliation.
- Do not disturb normal Chrome merely to create an automation attachment point.

## Resume / final reconciliation checklist

Before final Business shutdown/transition:

1. Stop/archive unrelated preservation workers so there is one controlled writer per lane.
2. Verify each seat's dedicated authenticated archive-browser binding.
3. Re-enumerate Library nodes through cursor exhaustion for C1, C2, and C3.
4. Preserve the prior inventory as evidence; do not overwrite the only historical denominator without a backup.
5. Compare fresh object IDs/file IDs against the local object store and durable state.
6. Download only missing/new/retryable objects using the proven resolver chain.
7. Re-hash completed local objects where integrity is uncertain.
8. Record permanent/retryable exceptions separately from successful physical objects.
9. Freeze final denominators only after active ChatGPT use has ended or the operator explicitly chooses the cutoff.
10. Keep this file-recovery phase separate from conversation Share/capture recovery; the conversation pipeline has different throttle and failure behavior.

## Conversation work deliberately out of scope here

Conversation preservation is not considered solved by this document. Current known conversation state at this stopping point includes C1 with a frozen denominator of 534 conversations and approximately 93 physically complete canonical captures; C2 and C3 conversation denominators still need inventory.

The conversation pipeline should be decomposed into separate stages: originating-seat Share creation, Share identity reuse, and shared-snapshot capture. Existing Share identities should be reused rather than recreated. Throttling is currently being treated operationally as seat-scoped unless evidence proves otherwise.

That work should receive its own recovery record once the inventory/capture strategy is proven.

## Bottom line

The file-preservation method is proven at scale. It successfully evacuated thousands of API-visible Library objects from each seat, including images, using authenticated first-party Library metadata plus first-party file resolution/download endpoints and durable local artifact validation.

The correct next action is **not** to redesign the file pipeline. Pause it, preserve this procedure, complete conversation recovery, then perform one final three-seat Library reconciliation before the Business preservation deadline.
