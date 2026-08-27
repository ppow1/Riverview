<!-- Version: 1.0.0 | Date: 2026-08-26 | Status: CAPTURED -->
# PL-0011 — Riverview Remote Machine Control Surface

## Parking Lot metadata

- **ID:** PL-0011
- **Idea/title:** Riverview Remote Machine Control Surface
- **Category:** Operator UX / Stream Deck / Remote Compute / Infrastructure
- **Priority:** High
- **Originator:** Steward
- **Date captured:** 2026-08-26
- **Status:** CAPTURED
- **Explicit non-action:** This artifact preserves the design direction. It does not authorize broad Stream Deck restructuring, production credential deployment, SSH security weakening, or Wake-on-LAN changes.

## Why this is worth preserving

Riverview's physical computing topology is expanding while Riverview itself is being migrated. The Stream Deck needs to evolve from a few local Riverview controls into a practical operator surface for several machines that may host different parts of the AI workload.

The near-term environment includes:

1. The current Windows development machine, expected to retain the RTX 4090 and development responsibilities.
2. A small desktop that is likely to become the Steward's daily-driver machine.
3. **OCTOMINER1**, an Octominer X12 Ultra AI server already online and verified for SSH access.
4. A second Octominer X12 Ultra that has not yet been powered and inventoried sufficiently to establish its IP address.
5. P100-class and other GPUs expected to move into the Octominer systems for AI compute workloads.

The operator should not need to repeatedly open PowerShell and manually reconstruct routine remote-access commands. The Riverview Stream Deck profile should ultimately provide a compact, expandable remote-machine control surface.

## Current verified example — OCTOMINER1

The first Octominer establishes the working example for the future controls.

Known current facts:

- Hostname: `OCTOMINER1`
- IP address: `192.168.1.160`
- SSH user: `root`
- SSH is enabled and has been successfully exercised from the Windows development PC.
- OS: Ubuntu 22.04.5 / HiveOS.
- GPUs already tested in this chassis include an RTX 3060 Ti 8 GB and Tesla P100 16 GB.
- The machine will sometimes be intentionally powered down for GPU/hardware work, so an unavailable SSH endpoint is a normal operating condition and should be presented clearly rather than treated as an unexplained failure.

### Manual command that established the basic workflow

From Windows PowerShell, the verified operator workflow is conceptually:

```powershell
Clear-Host
ssh root@192.168.1.160
```

The desired Stream Deck experience is to replace that repeated manual setup with a single button that opens a visible interactive PowerShell session, identifies the target, and starts SSH.

Desired presentation is approximately:

```text
========================================
 OCTOMINER1 SSH
 192.168.1.160
========================================

Connecting...
```

followed by the normal SSH interaction.

If the machine is unavailable, a lightweight reachability/SSH-port check may instead present:

```text
OCTOMINER1 is currently offline or unreachable.
192.168.1.160
```

This should remain simple and diagnostic rather than becoming a separate remote-management subsystem.

## Existing Riverview Stream Deck architecture to preserve

Riverview already owns a native Stream Deck profile and plugin architecture. Stream Deck work must follow the dedicated Riverview Stream Deck documentation referenced from `AI_HINTS.md`, and the installed Elgato configuration under the user's AppData Stream Deck tree remains runtime truth.

Existing Riverview actions include Runtime, Quest Dev, and Quest Cast controls. Their plugin path uses the Riverview native plugin and a central PowerShell control script. Those existing operations are generally hidden/background controls.

Interactive SSH differs from those controls because the Steward needs a **visible terminal** for password entry and normal shell interaction. The SSH implementation therefore should reuse Riverview ownership, layout, PowerShell 7 conventions, logging, backup/re-inventory discipline, and deterministic paths without blindly forcing SSH through a hidden-console execution path.

A likely clean implementation is one reusable Riverview-owned remote/SSH launcher with target parameters rather than separate unrelated scripts for every machine. Machine identity and action should be separable so addresses and roles can change during migration without redesigning the whole Stream Deck surface.

## Near-term Stream Deck targets

The current planning assumption is to reserve room for at least three remote-host identities:

### OCTO 1

- Role: first Octominer AI compute server.
- Current target: `root@192.168.1.160`.
- Connect/SSH control can be implemented once active work is authorized.

### OCTO 2

- Role: second Octominer AI compute server.
- Hardware exists/planned for use, but its final network identity is not yet established because it has not yet been powered/inventoried for this purpose.
- The layout and launcher architecture should make adding it trivial once its IP/hostname are verified.

### DAILY PC

- Role: small desktop expected to become the Steward's daily-driver workstation while the current development machine retains the RTX 4090 and development role.
- Final network identity and remote-control requirements remain to be established.
- Reserve architectural room rather than hard-coding assumptions now.

## Expected future action families

This is larger than three SSH buttons. The likely eventual control family for each managed machine is:

1. **CONNECT / SSH** — open a visible interactive terminal to the target.
2. **SHUTDOWN** — request an orderly remote shutdown, likely through SSH where appropriate and authorized.
3. **WAKE** — send Wake-on-LAN if the target motherboard/NIC/BIOS and power state support it.

These controls are **not all being implemented now**. They are recorded so the first SSH-button layout and launcher do not create a dead-end architecture.

Wake-on-LAN must not be assumed. Before implementing WAKE for a target, verify BIOS/UEFI support, NIC support/configuration, Windows/Linux power-state behavior as applicable, network/broadcast behavior, and successful magic-packet wake from the intended operator machine.

Shutdown must be implemented as an explicit bounded action with clear target identity. It must not create a generic unaudited remote-command facility merely to obtain a shutdown button.

## Layout implications

The current Riverview Stream Deck page has substantial unused capacity, but the remote-machine control family can grow quickly. Three machines multiplied by CONNECT, SHUTDOWN, and WAKE is already nine controls.

Therefore implementation should avoid scattering one-off buttons across the primary page. During elaboration, consider either:

- a compact, consistent machine-control region;
- a dedicated Riverview page for remote machines; or
- another existing Stream Deck-native grouping mechanism if it preserves clarity and reliable navigation.

The current Runtime/Quest controls and profile/page navigation must be preserved. Live installed profile state must be re-inventoried immediately before any mutation because manual Stream Deck edits supersede older captured inventories.

## Temporary development credential — SECURITY FLAG

**SECURITY FLAG — MUST BE RESOLVED BEFORE PRODUCTION/BROADER DEPLOYMENT**

During the present development/migration phase, the Steward explicitly authorized use/documentation of the temporary SSH password:

`TEST`

This credential is temporary development scaffolding. Its presence in this parking-lot artifact is intentional so future workers understand the current test environment and do not mistake it for an approved production credential.

Before production or broader deployment:

1. Replace `TEST` on every system where it was used.
2. Remove any mechanism that automatically supplies or embeds that password.
3. Prefer an appropriate managed SSH authentication approach, likely key-based authentication, once machine ownership and migration topology are stable.
4. Verify that no scripts, Stream Deck manifests, logs, command histories, documentation intended for broader distribution, or other artifacts retain an obsolete production-capable password.
5. Do not weaken `sshd` security settings merely to make Stream Deck automation easier.

The current objective does **not** authorize changing Octominer SSH security settings.

## Implementation direction when promoted

When this item is pulled for elaboration/implementation, the smallest clean first tranche should be approximately:

1. Re-read `AI_HINTS.md` and the current Stream Deck inventory/maintenance documentation.
2. Re-inventory the **live installed** Riverview Stream Deck profile under Elgato AppData.
3. Back up the complete Stream Deck configuration according to the existing Riverview maintenance procedure.
4. Confirm the current Riverview profile UUID/page/layout and choose coordinates that preserve every existing control.
5. Add a reusable visible PowerShell 7 SSH/remote launcher under the existing Riverview Stream Deck tooling area rather than inventing an unrelated architecture.
6. Use `Clear-Host` at the beginning of the interactive launcher.
7. Parameterize machine display name, address/hostname, user, and action where practical so OCTO 2 and the daily PC can be added without script duplication.
8. Implement OCTOMINER1 CONNECT first using the verified `root@192.168.1.160` target.
9. Add only a lightweight offline/unreachable presentation if it is straightforward; reliable one-button SSH is the first priority.
10. Preserve an interactive visible terminal after connection so the Steward can work normally.
11. Verify the exact executable/script/arguments launched by the physical Stream Deck button.
12. Refresh durable Stream Deck inventory/recovery documentation after the live configuration is accepted.
13. Add OCTOMINER2 only after its actual network identity is verified.
14. Add DAILY PC controls only after its role, network identity, and remote-access configuration are established.
15. Evaluate SHUTDOWN and WAKE as later bounded additions rather than silently bundling them into the initial SSH work.

## Acceptance direction for initial CONNECT tranche

A future initial implementation should not be considered accepted merely because a script works when run manually. Acceptance should demonstrate the actual operator path:

`Press Riverview Stream Deck button -> visible PowerShell opens -> target is clearly identified -> SSH connection to OCTOMINER1 begins -> interactive session remains usable.`

For the offline case, the operator should receive a clear target-specific indication rather than an unexplained disappearing console.

No unrelated Riverview profile buttons or navigation may change.

## Why parked now

The design direction is valuable and sufficiently important to preserve, but Riverview is currently undergoing migration and the final machine topology is not yet settled. OCTOMINER2 and the daily-driver PC do not yet have all required network/control facts, and Wake-on-LAN capability has not been verified.

The immediate OCTOMINER1 SSH button may be pulled into active work separately when the Steward directs it, but the larger remote-machine control surface should remain bounded and documented so near-term convenience work does not accidentally dictate the long-term architecture.

## Promotion condition

Promote for elaboration when one or more of the following occurs:

- the Steward explicitly directs implementation of the broader remote-machine control surface;
- OCTOMINER2 is powered and its network identity is verified;
- the daily-driver PC enters service and requires Riverview remote controls;
- shutdown/Wake-on-LAN controls become an active operator requirement;
- Riverview migration settles enough to choose the durable Stream Deck page/grouping architecture.

## Related current work/evidence

- Riverview `AI_HINTS.md` Stream Deck pointers.
- Current Riverview Stream Deck inventory and maintenance procedure.
- Existing Riverview native Stream Deck plugin and PowerShell control architecture.
- Verified OCTOMINER1 SSH access from the Windows development PC.
- Ongoing Riverview migration and redistribution of AI compute roles across the development machine, daily-driver PC, and Octominer systems.
