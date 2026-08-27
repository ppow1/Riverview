# Interactive Surface Acceptance Contract

## Purpose

Use this checklist to test large multi-page or multi-tab interfaces that a human cannot realistically re-check manually after every change.

## Traversal checklist

For each route/tab/view:

- open through the real navigation control;
- measure acknowledgement, shell, usable, and hydration timing;
- verify title/current-selection state;
- inspect all visible interactive controls;
- open every safe menu/dropdown/drawer/accordion;
- exercise safe selectors/toggles/forms;
- test empty, loading, success, stale, reconnect, failure, and no-data states when available;
- wait through normal refresh intervals;
- navigate away and back;
- verify state persistence expectations;
- capture evidence for representative and failing states.

## Cross-view sequences

Run sequences that combine controls across views. At minimum test:

- A -> B -> A state retention;
- rapid A -> B -> C navigation for stale-response races;
- expand -> refresh -> remain expanded;
- draft -> refresh -> draft preserved;
- focus -> hydration -> focus preserved;
- scroll -> refresh -> no unexpected jump;
- setting change -> leave -> return -> intended persistence;
- media selection -> playback -> leave -> return;
- long operation -> working -> waiting/completed;
- reconnect/degraded state -> recovery.

## Coverage contract

Maintain a control inventory with stable identifiers when possible.

Report counts:

- total discovered controls;
- safe controls;
- exercised safe controls;
- blocked destructive/authority controls;
- PASS/PARTIAL/FAIL/BLOCKED counts.

A broad acceptance claim without a coverage denominator is invalid.

## Visual contract

Inspect screenshots/full-page images rather than relying only on DOM assertions.

Check:

- hierarchy and information density;
- clipping/overlap;
- meaningful empty states;
- obvious current identity/context;
- discoverability of settings/navigation;
- visible feedback after clicks;
- liveness/activity motion;
- human-readable status language;
- responsive behavior at target viewport sizes.

## Performance contract

Record real browser timing around user actions. HTTP response time alone does not prove a fast UI.

Default local-surface alerts:

- acknowledgement > 100 ms: warn;
- shell > 500 ms: warn;
- usable/hydrated > 2 s: slow/fail depending on context;
- ordinary view > 10 s: fail unless explicitly justified.

## Resource contract

Collect baseline, per-view, post-leave, and repeated-cycle browser resource samples.

Flag:

- persistent memory ratchet;
- persistent DOM node growth;
- duplicate listeners/subscriptions/timers;
- repeated network fan-out after revisits;
- CPU/long-task spikes that correspond to visible stalls.

Do not require complete garbage collection to baseline; look for persistent trend and failure to settle.

## Evidence contract

Prefer one archive per acceptance run or bounded tranche containing:

- manifest;
- tested URL/routes;
- browser/version/viewport;
- timing samples;
- resource samples;
- control inventory/results;
- viewport/full-page PNGs;
- MHTML/page archives;
- PDFs where supported;
- DOM/rendered HTML;
- diagnostics/provenance;
- failure screenshots/logs.

Inspect the archive before declaring it valid.
