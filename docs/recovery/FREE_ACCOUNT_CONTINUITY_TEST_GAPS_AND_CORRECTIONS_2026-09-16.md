<!--
File: docs/recovery/FREE_ACCOUNT_CONTINUITY_TEST_GAPS_AND_CORRECTIONS_2026-09-16.md
Version: 1.0.0
Date: 2026-09-16
Status: Active continuity remediation checkpoint
-->
# Free-Account Continuity Test — Gaps, Corrections, and Remediation

## Purpose

Preserve the first fresh-account Riverview continuity test and convert its misses into durable repository work. The test demonstrated that a fresh ChatGPT account can recover most Riverview architecture, Octominer history, 80B testing, BIOS/MMIO work, Command Chair matrix/VKMS work, and objective-continuity doctrine directly from GitHub. The principal remaining weakness is current-state recovery and Steward-specific operational conventions.

## Acceptance result

The fresh account successfully recovered conceptual queries such as:

- "the thing where the third P100 wouldn't work" -> multi-P100 BAR/MMIO investigation;
- "four screens on DDR" -> Camrui/VKMS/Command Chair display investigation;
- "continue the 80B/Hermes work" -> September 16 endurance/state-integrity experiment.

This proves that repository-based continuity is viable. It does not yet prove complete takeover readiness.

## Corrections supplied by the outgoing working context

The following facts were known in the active working context but were missing, weak, stale, or insufficiently discoverable in GitHub during the fresh-account test.

### Development machine

Current known identity:

- hostname: `DESKTOP-JA3RPNQ`
- IPv4: `192.168.1.88`
- MAC: `74:56:3c:7c:9d:f0`
- motherboard: Gigabyte B550M DS3H AC
- RAM: approximately 48 GB according to current Steward report
- RTX 4090 24 GB normally belongs to this machine; it was temporarily moved to OCTOMINER1 for the 80B experiment
- exact current CPU remains UNKNOWN and must be verified before evaluating an AM4 G-series APU swap
- Steward believes Ubuntu/Windows dual-boot capability exists, but current dual-boot state remains to be independently verified before consequential planning

RDP state:

- Remmina reached the Windows credential screen on the Dev machine.
- The unresolved issue was that the Steward normally uses Windows Hello/PIN and did not have the underlying Windows account password immediately available for RDP authentication.
- Dev SSH port 22 was observed closed at that time.

### Command Chair KM distinction

The physical input switch is a **16-to-1 KM switch**, not a KVM. Video is handled separately by the 16x16 HDMI matrix.

Current known KM selections:

- `Ctrl Ctrl 1` = Dev machine
- `Ctrl Ctrl 3` = current Linux daily-driver/Camrui path

Do not collapse the HDMI matrix and KM switch into a single KVM concept.

### Linux terminal conventions

The Steward's required command-block behavior:

- Windows PowerShell blocks begin with `Clear-Host`.
- Linux/SSH shell blocks begin with lowercase `clear`.
- For Windows PowerShell diagnostic/handoff work, capture relevant output and place it on the Windows clipboard at completion when practical.
- Hermes/Codex/PowerShell handoffs should be one clean code block with no commentary embedded inside the transfer block.
- Avoid extra command blocks when one complete block can do the job.

Kitty configuration already implemented:

- `map ctrl+c copy_or_interrupt`
- `map ctrl+v paste_from_clipboard`

Intended behavior:

- selected text + Ctrl+C = copy;
- no selection + Ctrl+C = SIGINT/interrupt;
- Ctrl+V = paste from clipboard.

### Linux screenshot-to-clipboard

Accepted working command:

`sh -c 'rm -f /tmp/screenshot-clipboard.png; gnome-screenshot -a -f /tmp/screenshot-clipboard.png && wl-copy --type image/png < /tmp/screenshot-clipboard.png'`

This solved the required region-screenshot -> clipboard -> paste workflow. Do not reintroduce Flameshot unless a new requirement justifies it.

### Dictation / microphone

Current local-first direction:

- Daily Driver captures audio.
- WAV/audio is sent over LAN to OCTOMINER2.
- OCTOMINER2 3060 Ti runs local Whisper.
- resulting text returns to clipboard / eventual auto-paste path.
- wake phrase direction: "Hey Jarvis" using OpenWakeWord.

Verified Logitech USB headset direct ALSA path:

`plughw:CARD=Headset,DEV=0`

A direct microphone recording path was proven. The Sony Bluetooth microphone path produced unusable/distorted microphone behavior and is not the accepted capture path.

### DDR role decision

`DDR` means Daily Driver.

Current status is PROPOSED / under reassessment, not final:

- Camrui may become the low-power always-on wake/orchestration/control appliance rather than the primary DDR.
- Dev is being evaluated as the stronger DDR because it already has substantially more CPU/RAM capability and may support Ubuntu as the normal environment while retaining Windows when needed.
- Octominers are compute appliances and are comparatively loud/power-hungry; they are not presently favored as always-on desk machines.
- exact Dev CPU and verified dual-boot state are required before final DDR/APU decisions.

### OCTOMINER1 hostname freshness

Historical recovery documentation recorded a stale software-hostname condition where physical OCTOMINER1 could report `OCTOMINER2`. Do not treat that historical defect as current without checking newer evidence.

Current working-session evidence on 2026-09-16 identified OCTOMINER1 as hostname `OCTOMINER1`, IP `192.168.1.160`, physical MAC `00:e0:4c:6b:05:a9`.

The repository must distinguish historical stale-hostname evidence from current state rather than allowing both to appear equally current.

### Direct 80B control result / Hermes causal conclusion

The fresh-account test found the September 16 endurance report still saying the final direct-80B control result had not been captured. The active working context contains a later direct self-correction result and therefore the endurance record is incomplete/stale.

Later direct 80B evidence, with Hermes removed from the request path, showed the model correctly withdrawing unsupported earlier conclusions when presented with authoritative contradictory evidence. It explicitly rejected the claims that Hermes had preserved exact-state fidelity and that KV-cache pressure was sufficient evidence for the fabricated alternate machine state.

Correct bounded conclusion:

- 80B inference-server endurance: PASS.
- Direct 80B reasoning/self-correction: strong positive evidence, but not proof that the model can never hallucinate.
- Hermes long-running factual-state integrity in this experiment: FAIL.
- Hermes remote-model/tool execution: PARTIAL / functionally demonstrated, but final state reporting became corrupted.
- corruption proven to originate inside the 80B: NOT PROVEN.
- corruption proven to originate in KV cache: NOT PROVEN.
- network as source: NOT SUPPORTED by current evidence.
- exact mechanism/component inside the Hermes + model orchestration/state path: UNKNOWN.
- Hermes must not be trusted as the sole long-running authoritative state store.

The direct self-correction run was approximately 990 prompt tokens + 784 completion tokens and generated at about 50.5 t/s. This later result must be appended/reconciled into the canonical September 16 endurance report.

## Fresh-account gaps to fix

Priority durable work:

1. Implement the conceptual-recovery redesign of `AI_HINTS.md`.
2. Create `docs/recovery/AI_MEMORY_INDEX.md` as semantic overflow/index, while retaining AI_HINTS as the one canonical starting point.
3. Create one current-system-state recovery document covering Dev, Camrui, OCTOMINER1, OCTOMINER2, GPU placement, network identity, DDR status, Command Chair, dictation, and current unknowns.
4. Reconcile current standalone/main/origin-main source authority with historical installed-runtime/provenance documents. Do not silently rewrite history; mark older records historical/superseded where appropriate.
5. Update the September 16 Qwen3-Next 80B/Hermes endurance record with the later direct-80B self-correction result and corrected causal conclusion.
6. Record current Dev identity/RDP state and exact CPU when verified.
7. Record the KM switch model/topology when physically verified; retain KM terminology.
8. Preserve Kitty, terminal-clearing, clipboard/handoff, screenshot, and microphone conventions in a discoverable current-state location.
9. Record OCTOMINER2 WOL acceptance only if/when physically tested; do not promote the OCTOMINER1 result to OCTOMINER2 by assumption.
10. Keep the DDR decision explicitly PROPOSED until the Steward decides it.
11. Distinguish resident fixtures/architecture from authoritative imported resident records.
12. Add current/historical/proposed/failed/unknown status markers to recovery-sensitive documents where ambiguity exists.

## Conceptual aliases that must route correctly

At minimum:

- third P100 / three P100s / too many P100s / P100 BAR / high MMIO
- big 80B / Qwen Next / 4090 plus two P100s / 50 tokens per second
- 56 GB node / 40 GB node / 96 GB cluster / second Octo
- fake third monitor / virtual monitor / VKMS / four screens / DDR screens
- long HDMI / 100-foot HDMI / matrix / Input 5 Output 3
- Camrui / DDR / daily driver / always-on wake machine
- Dev / development machine / `.88` / `DESKTOP-JA3RPNQ`
- Kitty copy / Ctrl+C / Ctrl+V / terminal clipboard
- screenshot clipboard / GNOME screenshot / wl-copy
- Logitech headset / Sony microphone / Jarvis / Whisper
- Hermes made up machine state / fake Octo facts / state corruption / long-context Hermes

## Acceptance criterion for account transfer

A fresh AI should be able to hear the Steward describe a remembered concept in ordinary language, recover the relevant authoritative current state and history from GitHub, distinguish current from historical/experimental/proposed material, and continue without requiring the Steward to remember filenames, commands, dates, hardware identifiers, or prior detailed decisions.

The Steward should remember the concept; Riverview should remember the details.
