<!-- Version: 1.0.0 | Date: 2026-08-26 | Status: CAPTURED -->
# PL-0012 — Riverview Linux/Ubuntu Hosting and Cross-Platform Portability

## Parking Lot metadata

- **ID:** PL-0012
- **Idea/title:** Riverview Linux/Ubuntu Hosting and Cross-Platform Portability
- **Category:** Runtime Architecture / Infrastructure / Cross-Platform Portability / Local AI
- **Priority:** Strategic
- **Originator:** Steward
- **Date captured:** 2026-08-26
- **Status:** CAPTURED
- **Explicit non-action:** This artifact preserves a future investigation and possible migration direction. It does not authorize moving Riverview off Windows, reinstalling any machine, replacing HiveOS, changing production service ownership, relocating PostgreSQL, changing Stream Deck or operator ownership, altering credentials, or modifying the current runtime topology.

## Why this is worth preserving

Riverview currently runs primarily in a Windows-hosted environment, but its core architecture is not intrinsically Windows-specific. The Riverview Kernel is a Python 3.12 project with PostgreSQL and MCP as core dependencies, while several present deployment assumptions are Windows-specific rather than architectural requirements.

At the same time, the Estate's physical compute topology is changing. The Steward has Octominer X12 Ultra systems available for AI compute, including at least one system currently running Ubuntu 22.04.5 under HiveOS. This creates a plausible future opportunity to separate Riverview's durable server/runtime responsibilities from Windows-only operator surfaces.

A future investigation should determine whether Riverview would benefit from a split architecture in which Linux/Ubuntu hosts long-running server, database, orchestration, MCP, local-AI, and background-worker functions while Windows remains the operator-facing edge for Stream Deck, desktop automation, display management, Windows-native tooling, and any other capabilities that genuinely require Windows.

The objective is not to pursue Linux for its own sake. The question is whether Linux hosting would make Riverview simpler, more reliable, more diagnosable, easier to operate continuously, and better suited to mixed NVIDIA compute hardware without weakening the existing operator experience or creating a second hidden architecture.

## Current architectural observations

The current repository already suggests that the central Riverview application could be portable with bounded deployment work:

- Riverview Kernel is packaged as a Python 3.12 application.
- PostgreSQL is authoritative operational state.
- MCP is a first-class reasoning/data bus.
- Grace, the Continuous Momentum Engine, Relay workers, Comms5, and other services are service-oriented rather than inherently desktop-bound.
- Local AI is a first-class provider and is expected to operate independently of an OpenAI API route.

However, the current runtime configuration contains explicit Windows deployment assumptions, including examples such as:

- `.venv/Scripts/python.exe` rather than a platform-neutral Python executable resolution;
- `ssh.exe` rather than a platform-neutral SSH command;
- `${USERPROFILE}`-based SSH key paths;
- Windows drive-letter paths such as `A:/...`;
- Windows service/startup ownership and scheduled-task patterns in the broader current deployment;
- Stream Deck integration whose runtime truth lives under the Elgato Windows AppData tree.

These are important migration concerns, but they appear to be deployment/runtime seams rather than reasons the core architecture must remain Windows-only.

## Candidate future architecture to investigate

A likely target pattern worth investigating is:

### Linux/Ubuntu server/core side

Potential candidates to host on Linux include:

1. PostgreSQL authoritative operational state.
2. Grace workflow coordination services.
3. Continuous Momentum Engine services.
4. Relay workers.
5. Comms5 HTTP/MCP services and transport components.
6. Other MCP servers that do not require Windows desktop access.
7. Long-running diagnostics, health, recovery, and supervisor functions.
8. Ollama or other approved local-AI inference services.
9. GPU-backed background AI workloads.
10. Durable background automation that benefits from systemd-style lifecycle ownership.
11. Future compute-node adapters for Octominer-hosted GPUs.

### Windows operator/physical edge

Likely Windows-retained responsibilities include:

1. Elgato Stream Deck runtime and physical button integration.
2. Windows desktop automation and any Windows-specific operator tooling.
3. Multi-display/operator workstation behavior.
4. Windows-native launchers or utilities that are still required by the Steward's daily workflow.
5. Any Playwright/browser or desktop interaction that depends on the authenticated Windows operator environment and cannot be safely moved.
6. Hardware/user-interface adapters whose authoritative runtime is Windows-specific.

The investigation must not assume this split is correct. It should prove which boundaries are clean and which are not.

## Key investigation questions

### 1. Complete Windows-dependency inventory

Inspect `src/`, `config/`, `runtime/`, `tools/`, tests, launchers, and operational documentation for all Windows-specific assumptions, including:

- drive-letter paths;
- `Scripts/python.exe` virtual-environment paths;
- PowerShell-only behavior;
- Windows Scheduled Tasks;
- Windows service/process discovery;
- registry use;
- `%USERPROFILE%`, `%APPDATA%`, `%LOCALAPPDATA%`, or similar environment assumptions;
- `.exe` command names;
- process matching semantics that differ on Linux;
- Windows-only Python packages or APIs;
- filesystem case-insensitivity assumptions;
- path separator assumptions;
- named pipes, COM, WMI, Win32, AutoHotkey, or UI-automation dependencies;
- browser/profile paths tied to Windows user data;
- Stream Deck AppData dependencies;
- credential/secret paths tied to the current workstation.

The deliverable should classify every dependency as one of:

- already platform-neutral;
- trivial path/configuration change;
- requires a Linux equivalent;
- should remain Windows-side;
- requires architectural redesign;
- unknown and requiring proof.

### 2. Runtime supervisor portability

Evaluate how the existing Riverview runtime supervisor should behave cross-platform.

Questions include:

- Should the supervisor itself become OS-neutral and resolve executable paths dynamically?
- Should Linux services remain under the Riverview supervisor, systemd, or a layered arrangement where systemd owns the top-level Riverview supervisor?
- How are dependencies, restart policy, startup timeout, health checks, and process identity preserved?
- How is duplicate logical-service detection preserved across Windows and Linux process models?
- How are graceful shutdown and restart semantics made equivalent?
- How is authoritative service ownership made obvious and diagnosable?

Avoid creating unrelated startup mechanisms for every service. The Charter's unified-lifecycle principle should remain intact.

### 3. PostgreSQL placement

Determine whether PostgreSQL should:

- remain where it is initially;
- move to a Linux Riverview core host;
- run on a dedicated infrastructure node;
- or be migrated only after application portability is proven.

The investigation must address:

- backup/restore;
- migration sequencing;
- rollback;
- local network reliability;
- authentication and secrets;
- failure behavior if the database host is unavailable;
- acceptable latency;
- authoritative-state preservation;
- how to prove no split-brain or accidental secondary authority is created.

Database migration should be treated separately from application portability so a Linux test does not unnecessarily put authoritative state at risk.

### 4. Ubuntu versus HiveOS as host operating system

The existing Octominer provides an immediate Linux environment, currently Ubuntu 22.04.5 under HiveOS. The investigation must explicitly compare:

#### Existing HiveOS installation

Potential advantages:

- already installed and operating on the Octominer;
- existing GPU/driver management;
- immediate test environment;
- convenient hardware monitoring.

Potential concerns to verify:

- whether HiveOS should be treated as an appliance-like GPU management layer rather than a general-purpose Riverview server OS;
- update ownership and package-management conflicts;
- service persistence and systemd behavior;
- whether HiveOS may rewrite driver/network/system configuration;
- long-term supportability for PostgreSQL and Riverview services;
- security model and remote-management assumptions;
- whether mining-oriented management introduces unnecessary complexity or authority.

#### Plain Ubuntu Server

Investigate Ubuntu Server 22.04 LTS and an appropriate newer supported LTS release as candidate durable hosts. Compare:

- NVIDIA driver/CUDA compatibility with the actual GPUs;
- Python 3.12 availability and support;
- PostgreSQL support;
- systemd service ownership;
- Docker/container needs, if any;
- networking;
- security updates;
- remote administration;
- hardware monitoring;
- operational simplicity;
- long-term maintenance burden.

The investigation should not assume that the current HiveOS disk must be replaced. A non-destructive test path should be preferred until a durable OS choice is explicitly authorized.

### 5. Mixed NVIDIA GPU implications

One reason Linux may be attractive is Riverview's expected use of mixed NVIDIA compute hardware, including P100-class GPUs and newer GeForce cards.

Investigate:

- Linux driver branches that can support the actual installed mix;
- CUDA/PyTorch/Ollama/llama.cpp/vLLM or other approved runtime compatibility as applicable;
- whether P100, V100, RTX 30-series, RTX 40-series, or other planned cards create incompatible driver/runtime combinations;
- compute-mode and display-mode differences;
- whether cards should be grouped by machine instead of forcing one host to support every generation;
- how Grace/Riverview should discover GPU capability without binding orchestration to one host OS;
- what telemetry is needed to route workloads safely.

This is an investigation of hosting implications, not authorization to change current GPU allocation.

### 6. Local-AI runtime placement

Determine which local-AI services benefit from Linux hosting and which should remain attached to specific GPU machines.

Possible subjects include:

- Ollama;
- llama.cpp;
- approved Hermes runtime components;
- resident reasoning runtimes;
- ComfyUI or other GPU services when relevant;
- model storage;
- shared model/cache paths;
- network inference APIs;
- authentication between Riverview and compute nodes;
- health/capability discovery;
- provider failover and scheduling.

The goal should be a clean provider boundary so Riverview does not care unnecessarily whether a model is running on Windows, Ubuntu, or another approved compute host.

### 7. Filesystem and durable-storage design

Map current Windows paths such as `A:\...` into an intentional cross-platform storage model.

Investigate:

- whether paths should be configuration-driven rather than embedded;
- Linux equivalents such as `/srv/riverview`, `/var/lib/riverview`, `/opt/riverview`, or another deliberate layout;
- model storage versus operational state versus logs versus source checkout;
- shared network storage versus host-local storage;
- ownership and permissions;
- backup responsibilities;
- mount availability and failure behavior;
- case-sensitive filesystem regressions;
- whether configuration should use logical storage roles instead of physical drive letters.

Do not merely replace `A:` with an arbitrary Linux path. The migration should improve portability rather than encode a second platform-specific layout.

### 8. Secrets and identity handling

Inventory all current secrets and identity paths without exposing secret values.

Investigate:

- OpenWebUI/Riverview secret-file locations;
- SSH keys;
- database credentials;
- MCP/Comms5 credentials;
- browser/session identities where applicable;
- service-account identity;
- filesystem permissions;
- environment-variable injection;
- systemd credential/environment mechanisms if appropriate.

No migration artifact should copy credentials into GitHub, logs, ordinary chat, or test fixtures.

### 9. Network topology and service addresses

A split Windows/Linux architecture changes the meaning of `127.0.0.1`.

Inventory every localhost assumption and classify whether the service pair must:

- remain co-located;
- become LAN-addressable;
- use an authenticated tunnel;
- use reverse proxy/TLS;
- or expose only a bounded internal interface.

Investigate firewall rules, bind addresses, DNS/hostnames, DHCP/static addressing, and machine identity so migration does not replace local coupling with insecure LAN exposure.

### 10. Comms5 and remote transport

The current Comms5 transport uses SSH reverse forwarding. Determine how this should work if the HTTP service moves to Linux.

Questions include:

- whether the current reverse tunnel becomes simpler;
- which machine owns the outbound tunnel;
- SSH key placement;
- service restart/recovery;
- remote endpoint identity;
- diagnostics for transport failure;
- whether any Windows-only assumptions remain.

Preserve the existing bounded Comms5 authority model.

### 11. Playwright/ChatGPT doorbell boundary

Riverview architecture treats Playwright as the ChatGPT doorbell. Determine whether this capability:

- must stay on the authenticated Windows workstation;
- can run headless on Linux;
- should be represented as a remote operator adapter;
- or should be split into browser-facing and server-facing pieces.

Do not migrate authenticated browser state merely for architectural neatness. Security, login continuity, and operator recovery are more important than OS uniformity.

### 12. Stream Deck/operator boundary

Stream Deck should initially be assumed to remain Windows-side because the live Elgato AppData configuration is runtime truth.

Investigate how Stream Deck commands should control Linux-hosted Riverview services without becoming a generic remote-shell mechanism. Possible bounded interfaces could include:

- Riverview HTTP/MCP control APIs;
- target-specific SSH actions;
- an operator gateway;
- existing Riverview control mechanisms extended with explicit remote targets.

The Windows operator edge must retain clear health/status information for Linux-hosted services.

### 13. Quest/WebXR/spatial services

Classify each Quest/WebXR/spatial component as:

- browser/client-facing;
- generic network service;
- Windows-dependent;
- GPU-dependent;
- or portable.

Any move must preserve the accepted Quest observability and recovery mechanisms documented in the existing spatial checkpoint.

### 14. Diagnostics and Troubleshooting Cookbook impact

A Linux migration must not reduce diagnosability.

The future design should define stable checkpoints for at least:

- host reachable/unreachable;
- Riverview supervisor running/stopped;
- individual service running/degraded/restarting;
- PostgreSQL reachable/unreachable;
- MCP service reachable/unreachable;
- Comms5 transport healthy/broken;
- GPU visible/driver failure;
- model runtime available/unavailable;
- storage mount present/missing;
- Windows operator edge connected/disconnected;
- cross-host authentication failure;
- network/DNS/port failure.

Cookbook entries and recovery commands should be platform-aware without duplicating the entire troubleshooting architecture.

### 15. Testing and CI portability

Establish a Linux acceptance suite rather than assuming passing Windows tests prove portability.

Investigate:

- unit tests on both Windows and Linux;
- path and case-sensitivity tests;
- supervisor/service lifecycle tests;
- subprocess command construction tests;
- PostgreSQL integration tests;
- MCP/Comms5 boundary tests;
- network split-host tests;
- secret-path/configuration tests;
- recovery from service/host loss;
- acceptance of a Windows operator controlling Linux-hosted services.

Where practical, CI should detect future accidental reintroduction of unbounded Windows-only assumptions in portable core code.

### 16. Migration sequencing and reversibility

Any future migration should be staged so Windows remains a working fallback until Linux acceptance is proven.

A likely investigation sequence is:

1. Produce the full dependency/portability inventory.
2. Make core configuration path/platform handling portable without relocating production services.
3. Establish a clean Linux development/test environment.
4. Run the full Riverview test suite on Linux.
5. Start a non-authoritative copy of selected stateless services on Linux.
6. Verify diagnostics and remote operator control.
7. Move one bounded low-risk service and exercise rollback.
8. Expand service-by-service only when each boundary is accepted.
9. Treat PostgreSQL movement, if desired, as a separately authorized high-consequence tranche.
10. Retire Windows-hosted duplicates only after ownership and recovery are proven.

The investigation should produce explicit rollback criteria for every stateful or externally visible migration step.

## Required investigation deliverables before promotion to implementation

Before this idea should reach the Ready Bench, elaboration should produce at minimum:

1. **Cross-platform dependency inventory** — file/component-level classification of Windows assumptions.
2. **Target topology diagram** — proposed Windows operator edge, Linux core, database, AI/GPU nodes, and external ingress boundaries.
3. **OS-hosting comparison** — HiveOS versus plain Ubuntu and any other justified candidate.
4. **Service placement matrix** — current host, candidate host, dependency, risk, and reason for every Riverview service.
5. **Storage/path mapping** — current logical data roles and proposed cross-platform configuration model.
6. **Secrets/identity plan** — locations and service identities without secret values.
7. **Network exposure matrix** — localhost dependencies, LAN listeners, tunnels, firewall requirements, and authentication.
8. **GPU/runtime compatibility matrix** — actual planned hardware against drivers and local-AI runtimes.
9. **Test and acceptance plan** — Windows/Linux regression coverage and real-boundary acceptance checks.
10. **Migration sequence** — bounded tranches with rollback points.
11. **Operational lifecycle plan** — supervisor/systemd ownership and restart/recovery behavior.
12. **Cookbook/diagnostic impact list** — required new or revised failure checkpoints.
13. **Effort estimate** — based on the inventory rather than a generic platform assumption.
14. **Explicit keep-on-Windows list** — capabilities that should not be migrated and why.
15. **Steward decision points** — OS choice, database placement, browser identity placement, and any architecture changes requiring explicit approval.

## Preliminary effort hypothesis

The repository's present architecture suggests that this is more likely to be a **moderate portability and deployment project than a rewrite**. The Python/PostgreSQL/MCP core appears well-suited to Linux, while the largest migration costs are expected at OS-specific launch/runtime paths, service ownership, operator adapters, filesystem paths, networking assumptions, and Windows-native edge integrations.

This is only a hypothesis. The future inventory must replace it with evidence before scheduling implementation.

## Why parked now

Riverview is already undergoing active migration and architecture work, while the physical compute layout is still evolving. The second Octominer's network identity and eventual role are not yet fully established, the broader daily-driver/development-machine split is still settling, and current Riverview work should not be interrupted by an unproven operating-system migration.

The idea is worth preserving now because current hardware and Linux availability make the question materially relevant, and near-term implementation choices should avoid unnecessarily deepening Windows-only coupling if a future Linux core is likely.

## Promotion condition

Promote this item for elaboration when one or more of the following occurs:

- the Steward explicitly directs a Linux/Ubuntu migration investigation;
- the current Riverview migration reaches a stable checkpoint where host-platform work will not destabilize active objectives;
- Linux hosting becomes a dependency for Octominer/GPU integration;
- Windows-specific runtime behavior becomes a material reliability or hardware-compatibility blocker;
- a dedicated Riverview server/core host is being selected;
- PostgreSQL or local-AI service placement is being reconsidered;
- the final daily-driver/development-machine/Octominer topology is sufficiently known to evaluate a durable split architecture.

## Explicit non-goals during future investigation

Unless separately authorized, the investigation must not:

- wipe or reinstall the current HiveOS system;
- move authoritative PostgreSQL state;
- shut down or replace working Windows Riverview services;
- redesign Stream Deck merely because the backend OS changes;
- expose internal services broadly on the LAN;
- convert Riverview into a container/Kubernetes project without a demonstrated need;
- change provider policy or add OpenAI API routing;
- relocate protected Undercurrent data to cloud or ordinary network paths;
- create a second authoritative operational database;
- treat Linux uniformity as more important than operator reliability;
- bundle GPU reallocation, storage redesign, and OS migration into one irreversible cutover.

## Related current work/evidence

- `README.md` — Riverview foundation commitments and local-first/event-driven architecture.
- `AI_HINTS.md` — canonical recovery and governance entry point.
- `docs/governance/RIVERVIEW_CHARTER.md` — mission, simplicity, diagnostics, authority, and anti-drift constraints.
- `config/runtime/riverview-runtime-services.json` — current Windows-oriented runtime command/path assumptions.
- `pyproject.toml` — Python 3.12 package/dependency foundation.
- `PL-0011` — Riverview Remote Machine Control Surface, including Octominer topology and Ubuntu 22.04.5/HiveOS context.
- Existing Quest/WebXR/spatial observability checkpoint.
- Existing Stream Deck inventory and maintenance documentation.
