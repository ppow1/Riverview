---
name: interactive-surface-acceptance
description: "Perform evidence-backed exploratory acceptance testing for human-facing web, dashboard, control, admin, spatial/WebXR, and local-service surfaces. Use when Hermes must verify that a rendered UI actually works rather than merely passing self-authored tests: discover and exercise safe interactive elements, traverse tabs/pages/forms/media/settings, measure acknowledgement/render/hydration latency and browser resource behavior, detect state-loss/leaks across repeated navigation, capture Snapshot/evidence at key states, visually inspect rendered results, and return PASS/PARTIAL/FAIL. Require explicit approval for destructive or authority-changing controls."
---

# Interactive Surface Acceptance

Treat this skill as an automated operator/beta tester, not as a unit-test runner.

## Core acceptance rule

Never equate implementation existence, HTTP 200, DOM presence, or self-authored tests with user acceptance.

Use this sequence:

`goal -> live browser interaction -> evidence capture -> visual/structural interpretation -> acceptance verdict`

Self-authored tests are necessary evidence when relevant, but never sufficient evidence for a human-facing surface.

## Start from the live surface

1. Identify the exact live URL, launch/runtime owner, expected user role, and acceptance brief.
2. Open the real surface in a real browser context.
3. Verify the browser is on the intended page target, not an extension/background target.
4. Record baseline browser/tab resource measurements before interaction.
5. Capture an initial evidence state before modifying anything.

If the target is Riverview, also apply the Riverview clean-state skill and current `AI_HINTS.md` before engineering changes.

## Build a surface inventory

Discover and record all meaningful interactive controls and dynamic regions, including:

- primary navigation, tabs, routes, drawers, accordions, menus, dialogs;
- buttons, links, dropdowns, selectors, toggles, sliders, forms, editors, search;
- audio/video/media controls and resident voice selectors;
- add/remove participant or membership controls;
- settings and preference controls;
- pagination, progressive loading, scroll regions, tree expansion;
- status, liveness, progress, error, reconnect, and attention indicators;
- debug/diagnostic controls;
- spatial/WebXR controls when the browser can exercise them safely.

Produce a coverage denominator. Do not claim broad coverage without stating how many discovered safe controls were exercised.

## Classify interactions before clicking

Classify every discovered control:

- `SAFE_READ_ONLY`: execute automatically.
- `REVERSIBLE_TEST_MUTATION`: execute automatically only when a test fixture/sandbox or safe rollback exists.
- `DESTRUCTIVE_OR_AUTHORITY_CHANGING`: require explicit approval before execution.
- `UNKNOWN`: inspect/classify before execution.

Never blindly click shutdown, delete, revoke, reset, publish, promote, send-to-external-party, power-control, or authority-changing actions.

## Exercise the real user path

For every safe control:

1. Record pre-state.
2. Perform the real UI interaction.
3. Measure acknowledgement latency.
4. Measure visible shell/content transition latency.
5. Measure hydration/usable-state latency.
6. Confirm the expected visible result.
7. Confirm state does not regress after normal refresh/reconnect intervals.
8. Record post-state and browser resource metrics.
9. Capture evidence for important state changes or failures.

Prefer native browser interaction over direct API calls for acceptance. Use direct APIs only as diagnostic support or when browser control is technically unavailable, and state that limitation explicitly.

## Test sequences, not only isolated controls

Create realistic multi-step sequences that expose state-retention bugs. Examples:

- switch tab -> open dropdown -> change selection -> play audio -> switch away -> return -> verify persistence;
- expand tree -> type draft -> wait through two refresh cycles -> verify expansion, draft, focus, scroll;
- open settings -> change reversible option -> reload/revisit -> verify persisted effect;
- navigate A -> B -> C -> A repeatedly -> verify stale responses do not overwrite the active view;
- create/select room -> change participant -> send message -> revisit room -> verify identity/history;
- start a long operation -> observe liveness -> wait -> verify working/waiting/completed states.

For timer/refresh-driven UIs, always wait through enough normal refresh cycles to expose destructive rehydration.

## Visual acceptance

Do not ask only whether the DOM changed. Inspect what the user actually sees.

At key states:

1. capture viewport and full-page PNG when supported;
2. capture MHTML/page archive when supported;
3. capture PDF when supported;
4. capture DOM/rendered HTML and relevant state/diagnostics;
5. inspect the visual output;
6. compare it with the explicit acceptance goal.

Use Snapshot or the platform's equivalent evidence package when available.

Look for:

- missing controls or capabilities despite backend support;
- misleading claims of completion;
- raw implementation enums leaking into human UI;
- controls that are present but visually unusable;
- duplicate/oversized status panels;
- excessive whitespace or density;
- clipped/hidden content;
- focus theft;
- scroll jumps;
- state reset after refresh;
- stale content overwriting current content;
- inaccessible or ambiguous controls;
- visible liveness that does not correspond to real work.

Do not declare visual acceptance from screenshots you have not inspected.

## Latency and hydration measurements

Measure user-perceived timing, not only HTTP transport.

For each tested interaction record when practical:

- `ack_ms`: click/key -> immediate visible acknowledgement;
- `shell_ms`: click -> destination shell/structure visibly changes;
- `usable_ms`: click -> intended control/content is usable;
- `hydrate_ms`: click -> expected live data is hydrated;
- `media_start_ms`: media action -> audible/visible playback begins;
- `reconnect_ms`: failure/reconnect -> truthful usable state restored.

For local control surfaces, flag obvious latency aggressively. Unless the acceptance brief says otherwise, use these default interpretation bands:

- acknowledgement <= 100 ms: good;
- shell transition <= 500 ms: good;
- ordinary local usable/hydrated state <= 2 s: acceptable target;
- > 2 s: investigate/flag slow;
- > 10 s for ordinary navigation/hydration: fail unless the operation itself inherently requires it and the UI remains alive and usable.

These are acceptance defaults, not claims about network-heavy external systems.

## Browser resource efficiency

Measure the browser tab/process as the surface is exercised. Prefer Chrome/Chromium DevTools Protocol or equivalent browser-native metrics.

Record when available:

- renderer/tab memory footprint;
- JS heap used/total;
- DOM node count;
- document/frame count;
- event-listener count where available;
- CPU/task time or long tasks;
- network request count and transferred bytes;
- active timers/subscriptions/observers when discoverable;
- memory before entering a view;
- memory after hydration;
- memory after leaving the view;
- memory after repeated navigation cycles.

Do not treat a single high number as a leak by itself. Look for ratcheting growth that fails to settle after leaving/revisiting views.

Run repeated navigation loops for important pages, preferably 5-10 cycles when cheap enough. Flag persistent growth and correlate it with DOM/listener/subscription growth.

Use `scripts/evaluate_acceptance.py` to summarize latency/resource samples when a metrics JSON file is available. See `references/metrics-schema.md`.

## Long-running operation liveness

Verify that long-running work exposes separate concepts:

- `liveness`: alive/responding;
- `working_state`: working, waiting, blocked, needs-user, completed, unreachable;
- `progress`: only when honestly measurable.

A healthy long-running operation must not appear visually static.

Test:

- heartbeat/pulse continues while alive;
- spinner/activity only appears during actual active work;
- waiting states stop pretending to work;
- stale/unreachable transitions occur when heartbeats stop;
- needs-user state is obvious;
- no fabricated percentage appears.

## Snapshot/evidence acceptance

When a Snapshot/evidence system exists, exercise it through the actual UI control.

Verify the resulting artifact, not just the request:

- archive exists and opens;
- route/view identity is correct;
- PNG(s) show the real rendered state;
- MHTML/page archive represents the correct page;
- PDF represents the correct page;
- DOM/rendered HTML is present when promised;
- manifest maps route/view to artifacts;
- diagnostics/state/provenance are included as promised;
- sensitive data is not unintentionally captured;
- evidence capture does not destroy the user's current UI state.

## Settings, media, and specialty controls

For settings:

- change only reversible/safe settings automatically;
- verify the visible/runtime effect;
- verify persistence or intended non-persistence after navigation/reload;
- restore the baseline when appropriate.

For audio/media:

- verify selector options;
- select an option;
- trigger playback through the real control;
- verify playback actually starts using available browser/media state or observable output;
- record startup latency;
- verify switching away/back does not corrupt the chosen state.

For spatial/WebXR:

- exercise browser-accessible controls and diagnostics;
- distinguish machine-side/browser proof from headset/physical-human acceptance;
- do not claim hand tracking, comfort, stereoscopy, teleport, or real headset acceptance without evidence from that boundary.

## Coverage and verdict

Return per-control or per-capability results using:

- `PASS`: expected user-visible behavior demonstrated with evidence.
- `PARTIAL`: some required behavior works but acceptance is incomplete or boundary evidence is missing.
- `FAIL`: expected behavior is absent, broken, misleading, excessively slow, unstable, or loses state.
- `BLOCKED`: cannot safely exercise due to authorization/environment limitation.

Always report:

- discovered safe interactions;
- exercised interactions;
- coverage percentage/count;
- failures and partials;
- latency outliers;
- resource-growth/leak findings;
- state-persistence failures;
- evidence locations;
- any untested destructive/authority-changing controls.

Do not report `PASS` for a capability merely because code/tests for it exist.

## Completion gate

Before saying a human-facing tranche is complete, require all of the following where applicable:

1. implementation/tests pass;
2. live runtime is reachable;
3. real browser controls were exercised;
4. important interaction sequences were exercised;
5. latency was measured;
6. resource behavior was sampled;
7. state survived refresh/navigation;
8. evidence was captured and inspected;
9. rendered result was compared to the acceptance brief;
10. unresolved PARTIAL/FAIL/BLOCKED items are explicit.

If any required gate is missing, state that acceptance is incomplete.

## References

Read `references/acceptance-contract.md` for the detailed traversal/evidence checklist.
Read `references/metrics-schema.md` when collecting metrics for automated evaluation.
