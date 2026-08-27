# PL-0007 Operator vNext — Steward Design Context Checkpoint

Status: CAPTURED / PLANNING-ONLY
Date: 2026-08-27
Authority: Steward design direction captured during Operator vNext exploration
Related parking items:
- PL-0007 — Web Capability Archaeology and Consolidation
- PL-0008 — Riverview Web Operator UI Stabilization and Re-architecture

This checkpoint preserves Steward-provided design context that accumulated during a long exploratory conversation and must not be allowed to depend on chat memory. It does not authorize implementation, Ready Bench promotion, authority changes, or removal of existing capability.

## 1. Core relationship: Riverview is the future

The Estate is Riverview's predecessor, not a permanent peer product.

The Estate remains operational because it still contains useful capability that Riverview has not yet absorbed. Riverview is the successor and eventual destination. Migration should selectively preserve useful Estate capabilities, simplify or redesign them where appropriate, and leave behind mechanisms that do not serve the mission.

The key historical failure in the Estate was not lack of capability; it was that governance and weak built-in troubleshooting made failures expensive and slow to diagnose. Riverview must therefore treat diagnosability, evidence, and recoverability as first-order architecture.

## 2. Operator purpose

The Operator is not merely a website. It is the first major graphical control surface for a much larger operating environment that includes:

- Riverview, Grace/CME, Hermes, Campaign Runner, Codex lanes, local models, ChatGPT-connected work, resident systems, PostgreSQL projections, and validation/recovery flows;
- multiple development PCs and servers;
- two 12-GPU Octominer-class chassis, with future growth beyond current populated GPUs;
- Stream Deck and Estate/Riverview plugins;
- Command Chair physical controls, including multiple USB button/encoder/LCD devices and a multi-button gaming mouse;
- Fire tablet and occasional Surface tablet surfaces;
- a 16x16 HDMI matrix and keyboard/mouse/KVM switching infrastructure;
- Raspberry Pis, microcontrollers, sensors, fabrication/3D-printing equipment, and future physical-control adapters;
- Quest/Spatial presentation and control.

The Operator must expose enormous capability without making the Steward experience enormously complex.

Primary design objective:

> Riverview should make a very busy environment feel quieter.

## 3. Extreme parallelism and momentum

Riverview must assume many concurrent work streams as normal operation, not as an exception.

Typical conditions may include multiple Hermes sessions, multiple Codex CLI lanes, Grace/CME work, Campaign Runner packages, validation/recovery lanes, dozens of browser tabs, multiple applications, hardware work, and many long-lived projects in different states.

The Operator must help answer:

- What is moving?
- What is waiting?
- What completed?
- What broke?
- What needs the Steward?
- What can continue without the Steward?
- What changed while the Steward was elsewhere?
- Where was this work left?
- What should be resumed now?

The desired attention projection is not a conventional notification inbox. It should compress many concurrent states into the small number of things that genuinely require Steward judgment.

## 4. Responsiveness is a hard requirement

This is a local system. Riverview controls its database, runtime, projections, and source code. The Operator should therefore feel local and effectively immediate.

Required direction:

- immediate visible reaction to clicks;
- render shell/workspace first, hydrate second;
- no backend probe, database reconstruction, AI call, telemetry query, or slow subsystem may block the initial workspace transition;
- bounded initial conversation/history loads;
- lazy/progressive older history;
- last-known-good projections with explicit stale/degraded state;
- localized DOM updates rather than broad rerenders;
- independent panel degradation;
- reconnect/failure states that do not blank unrelated UI;
- event/streaming updates where useful;
- measurable interaction/hydration acceptance.

A beautiful interface that pauses after every click is a failure.

## 5. Visual direction

The UI is dark-first, not a light interface with a dark theme added later.

Desired character:

- modern 2026-quality interaction design;
- restrained, calm, contemporary command interface;
- charcoal/navy foundation;
- cyan/blue for active/healthy affordances;
- selective warm gold for deliberate attention/decision structure;
- subtle depth and motion;
- dense only where density has operational value;
- no generic old-fashioned admin dashboard;
- no neon red/green Christmas-tree status wall;
- no attempt to clone ChatGPT, although the interaction grammar of sidebar + dominant workspace + composer is acceptable.

The Estate/Riverview concept art is visual-language reference material, not a requirement to render ornate castle artwork behind operational surfaces.

## 6. Information architecture direction

The Office of the Steward demonstrated the failure of exposing too much institutional capability as a huge horizontal tab surface. The replacement should use hierarchy and progressive disclosure.

Exploratory top-level grouping discussed with the Steward includes approximately five stable working domains, with names still subject to refinement:

- Converse / Conversations
- Work
- Resources / Estate
- Activity / Now
- Explore / Settings & Evidence / deeper institutional discovery

Global capabilities such as CME, Snapshot, Attention, and System Pulse should not be forced into ordinary page-tab semantics.

The common question is not "how do we fit every capability on one screen?" It is "what does the Steward need to do now, and how quickly can deeper capability be reached when needed?"

## 7. Snapshot is a first-class requirement

Snapshot is a proven operational success and must survive.

The current compact Snapshot icon is preferred over a large labeled button.

Snapshot should remain globally available and should evolve as a first-class diagnostic/evidence bundle capable of preserving enough application/system state for rapid human or AI troubleshooting.

The workflow must remain fast enough that a useful diagnostic bundle can be produced and handed to another investigator in seconds.

Snapshot and screen snip are distinct:

- Screen snip captures visual evidence from the Steward's display.
- Riverview Snapshot captures diagnostic/system/application state.

Both workflows are valuable and should remain low-friction.

## 8. CME remains global

Grace's Continuous Motion Engine is not merely another page. It is a cross-cutting institutional process and should remain globally accessible through the compact CME control/icon.

Its deeper status screen can be opened when needed, but the Operator should not treat CME as an ordinary navigation destination whose visibility disappears outside one tab.

## 9. Persistent System Pulse

A quiet persistent system-status surface should make infrastructure health visible without dominating the screen. A thin bottom rail or equivalent persistent region is a strong candidate.

It should be able to represent over time:

- Riverview core/runtime/services;
- Grace/CME;
- Hermes;
- Operator/Web surfaces;
- Spatial services;
- development PC and other important PCs;
- GPU Tower 1;
- GPU Tower 2;
- future compute nodes;
- Raspberry Pis/microcontrollers and other important infrastructure when appropriate.

Healthy state should be visually quiet.

Heartbeat can be represented through a subtle pulse or illumination change rather than a dedicated blinking red/green light.

States must distinguish at minimum:

- healthy/reporting;
- stale;
- intentionally off;
- starting/reconnecting;
- unexpectedly unreachable;
- attention required.

Clicking an entity should inspect it without destroying the current workspace.

Dangerous infrastructure actions such as shutdown/restart/wake must be explicit and governed, not hidden behind accidental double-click behavior.

## 10. Liveness, working state, and progress are separate

A major usability lesson from direct Hermes CLI operation is that the Steward must never have to infer whether a long-running operation is alive from incidental terminal text.

Every long-running Riverview operation must expose three independent concepts:

1. **Liveness** — the session/process/worker is connected and responsive.
2. **Working state** — actively reasoning/executing/tooling, waiting on a tool, waiting on another service, idle, blocked, or waiting on the Steward.
3. **Progress** — only when meaningfully measurable.

Required UX direction:

- healthy heartbeat/pulse independent of progress;
- small active spinner or equivalent while work is actually executing;
- continuously updated last-heartbeat / last-meaningful-activity age;
- explicit "waiting on tool", "waiting on service", "needs Steward", "stale", "blocked", and "unreachable" states;
- elapsed time where useful;
- real progress/percentage only when the underlying operation can measure it honestly;
- never fabricate a progress percentage simply to make the UI look active.

Hard requirement:

> No long-running Riverview operation may appear visually static while healthy work is in progress. Every active operation must expose a continuously updating liveness indicator independent of task progress.

At the aggregate level, Riverview should be able to summarize states such as "Hermes: 2 working, 1 waiting" or "Codex: 3 active" without requiring the Steward to inspect each terminal.

## 11. Compute/GPU topology and density

The Steward owns two GPU chassis capable of 12 GPUs each. The resource model must support both from the beginning even if only a few GPUs are populated now.

The model should naturally support:

`Compute -> Tower -> Slot 1..12 -> GPU -> model/process/workload`

for each independent chassis, without making 24 GPUs an artificial hard ceiling.

The normal Operator surface should aggregate upward so one unhealthy GPU does not require inspecting 24 rows to discover the problem.

A detailed resource drilldown may intentionally use mining-dashboard-style density because repeated hardware rows are naturally scannable.

Useful future GPU/tower fields include:

- model;
- slot/physical identity;
- VRAM used/available;
- utilization;
- temperature;
- power;
- fan/thermal state;
- health;
- loaded model;
- process/workload;
- reservation/allocation;
- worker/agent/campaign association;
- diagnostic/error history.

Riverview should go beyond ordinary mining telemetry by associating hardware consumption with institutional workload when that association is actually proven.

## 12. Voice-first interaction

The Steward now primarily dictates rather than types.

Current successful workflow uses Windows voice typing triggered from physical controls, especially paired adjacent buttons on the gaming mouse, with Stream Deck feedback indicating microphone state.

Do not make replacing Windows voice typing a prerequisite for Operator vNext.

The website must be an excellent dictation target:

- stable text focus;
- no background refresh stealing focus;
- large practical composer;
- long-form dictation tolerance;
- draft preservation across navigation;
- no premature submission due to pauses;
- fast mouse/touch correction;
- clipboard and screenshot paste that works directly;
- optional on-screen microphone fallback;
- architecture capable of future local transcription and wake-word experiments without making them foundational.

Wake-word control remains exploratory.

## 13. Preserve existing muscle memory

Do not redesign successful physical workflows merely because the web interface is being redesigned.

The gaming mouse currently provides high-frequency operations such as copy, paste, Enter, duplicate dictation-toggle buttons, and duplicate screen-snip buttons. Screen snips automatically reach the clipboard and can be pasted directly into ChatGPT/conversation workflows.

The Stream Deck provides labeled actions, mode/context controls, status feedback, and pre-programmed screen layouts.

Command Chair physical controls include buttons, rotary encoders, LCD-capable devices, and other USB HID surfaces.

Design principle:

> Preserve muscle memory. Add capability around it.

A new Operator that turns a one-button physical workflow into a multi-click web workflow is a regression even if it looks prettier.

## 14. Multi-surface logical action architecture

The browser is one presentation/control surface, not the institution itself.

Riverview should evolve a device-independent logical action layer so the same semantic action can be invoked from web, Stream Deck, Command Chair, gaming mouse, tablet, automation, or future Quest/Spatial interfaces.

Examples of possible logical actions include snapshot capture, CME inspect, resource inspect, wake, SSH, conversation creation, attention open, workspace switch, notification acknowledgement, and dictation start/stop.

The device adapter changes; action meaning, authority, idempotency, diagnostics, and result state do not.

Do not duplicate every physical control on the website merely because it is possible.

## 15. Command Chair and screen-layout environment

The broader operating environment includes a Command Chair with Stream Deck, keyboard/mouse, gaming mouse, multiple additional button/encoder/LCD devices, Fire tablet, and occasional Surface tablet.

The existing Stream Deck environment already includes workspace/profile concepts for activities such as Codex development, CAD, 3D printing, and other screen arrangements.

Future Riverview architecture may treat workspace as a semantic concept that coordinates display routing, input target, Stream Deck context, and Operator workspace. This is a future capability direction, not current implementation scope.

## 16. HDMI matrix, KVM, and physical routing

The Steward has a network-capable 16x16 HDMI matrix and multiple keyboard/mouse/KVM switching capabilities.

Future Riverview should prefer semantic actions such as "put GPU Server 2 on lower-right display" or "give keyboard/mouse to GPU Server 2" rather than expose raw matrix-port operations as the primary user model.

Adapters can translate semantic actions into device-specific commands.

This is future integration context, not Operator vNext first-pass scope.

## 17. Quest / Spatial direction

Quest/Spatial is eventually another Riverview presentation/control surface, not a permanent Estate peer system.

The Steward intends to use hand tracking rather than controllers and has ADB/scrcpy-style troubleshooting/mirroring capability for observing the headset on large desktop displays. Programmatic casting remains unresolved.

The browser Operator should not embed business logic in a way that forces the future Spatial client to reverse-engineer DOM behavior.

Shared underlying concepts should include entities, state, actions, events, relationships, capabilities, attention, and history.

Desktop Operator, 2D world/institution view, and future Quest spatial presentation should be different projections over the same Riverview semantics.

## 18. World view vs Operator view

The Riverview/Estate concept art is valuable as a world/institution model and visual identity source.

Distinguish:

- **Operator View** — fast, quiet, information-efficient control and conversation surface;
- **World View** — 2D interactive institutional/map representation where spatial metaphor helps understanding;
- **Spatial View** — future Quest/3D representation of the same underlying Riverview entities/state/actions.

Do not force every technical object to have a literal castle room. Spatialization should be used where it improves human understanding.

## 19. Dense vs quiet surfaces

Do not impose one universal information density across Riverview.

- Conversations should breathe.
- Attention should be sparse.
- System Pulse should be compact and quiet.
- GPU/resource telemetry may be dense.
- Diagnostics may be extremely dense when explicitly opened.

The information determines the appropriate presentation density.

## 20. Troubleshooting and diagnosability

Every important component should be able to answer:

- What are you?
- What state are you in?
- Are you alive?
- What are you doing?
- What just happened?
- Why are you in this state?
- What depends on you?
- What can be done about it?

Failure behavior, evidence, recovery hints, and verification are part of capability completion.

The Operator should make it possible to drill from aggregate problem -> entity -> workload/process -> diagnostic evidence without reconstructing the system manually from unrelated logs.

## 21. Project scale and long-term cognitive relief

Riverview must support not only minute-to-minute concurrency but also large numbers of long-lived or dormant projects.

The Steward's broader environment includes many projects and endeavors in different states. The institution should remember enough context that a dormant project can later answer:

- What was this?
- Why did it matter?
- What decisions had already been made?
- Where did we stop?
- What exists now?
- What remains?
- What would it take to resume?

Riverview's job is to reduce how much must remain continuously resident in the Steward's head.

## 22. Concurrent development / integration problem discovered during this exploration

Repository synchronization and cleanup work during this exploration exposed a recurring concurrency problem across AI engineering lanes.

Historical attempts have included:

- branch-per-task, which created branch/worktree proliferation and reconciliation debt;
- module-heavy development, which reduced some code coupling but did not eliminate integration debt;
- multiple workers directly advancing main, which reduced branch clutter but created moving-target publication and authority races.

A future proposal should explore a hybrid model:

- one canonical main;
- short-lived bounded task branches/worktrees;
- explicit base SHA per lane;
- bounded ownership scope;
- one serialized integration/publication gate;
- validation before publication;
- immediate retirement of successfully integrated task worktrees;
- modules used for code isolation, not as a substitute for source-control coordination.

This checkpoint records the concept only. It does not change current development workflow by itself.

## 23. Current post-cleanup repository baseline

At the end of the PL-0004 historical archive/workspace cleanup maintenance window, canonical Riverview authority was reported and published as:

`3228454edabcc8c8539aa4c85068e6515ea66222`

with canonical local root:

`A:\Riverview\standalone`

and canonical published repository:

`ppow1/Riverview main`.

The private non-authoritative historical archive is:

`ppow1/Riverview-Historical-Archive`.

This checkpoint must be re-anchored to then-current canonical main before any future implementation package is promoted or executed.

## 24. Explicit non-actions

This checkpoint does not authorize:

- Operator implementation;
- Ready Bench promotion;
- Stream Deck mapping redesign;
- Quest runtime changes;
- Command Chair mapping changes;
- GPU/Octominer configuration changes;
- wake-word implementation;
- HDMI/KVM control implementation;
- Grace/CME authority changes;
- Hermes/Campaign Runner policy changes;
- PostgreSQL authority changes;
- resident canon changes;
- concurrent-development workflow changes.

It preserves design context so future elaboration does not require the Steward to reconstruct this long conversation manually.
