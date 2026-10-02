# Campaign Lessons Learned

## LL-001 — Preserve knowledge outside the chat

Every meaningful test must leave durable evidence containing:

- goal
- hypothesis
- preconditions
- action
- observation
- result
- postmortem
- lessons
- implications for the next test

The repository is the campaign memory.

## LL-002 — Host availability and model availability are separate states

An online OCTO2 does not imply that the 80B reasoning worker is usable.

The controller must distinguish host reachability, model-process presence,
model loading and API readiness.

## LL-003 — Process presence is not inference readiness

During T-SCAF-002, llama-server PID 755 existed for several minutes while the
80B model was loading and the API was not ready.

A PID check alone is insufficient.

## LL-004 — Timeout policy must be operation-specific

One generic timeout is inappropriate.

Separate timeout policies are required for operations including:

- POST / boot
- SSH return
- video acquisition
- BIOS programming
- 80B cold loading
- Steward response
- software reboot
- physical reset request

Timeouts should be based on measured campaign behavior where possible.

## LL-005 — Retain last known boot identity across outages

An unreachable sample must not erase the last known boot ID.

Boot-transition detection must compare a newly observed boot ID against the
last successfully observed boot ID.

## LL-006 — Monitoring belongs outside the monitored machine

The campaign monitor runs on DEV.

This allowed T-SCAF-002 to preserve evidence while OCTO2 itself was offline.

A monitor located only on OCTO2 could not provide equivalent outage evidence.

## LL-007 — Keep SSH boundary operations simple

Complex shell parsing across:

Windows -> SSH -> Linux shell

caused the first OCTO2 monitor implementation to misparse /proc/uptime and
falsely report the 80B process as down.

Prefer simple line-oriented remote output and parse structure locally.

## LL-008 — Preserve diagnostic information

Return codes and stderr should not be discarded when diagnosing infrastructure.

The initial monitor helper hid information that was useful for separating SSH
failure from host failure.

## LL-009 — Be cautious with PowerShell control flow and nested quoting

Multiple campaign scaffolding attempts demonstrated unreliable results from
complex PowerShell blocks containing nested here-strings, subexpressions and
if/else control flow.

Campaign implementation rule:

- prefer Python for substantive controller logic
- keep PowerShell primarily as a launcher / inspection surface
- avoid `else` where simple independent operations suffice
- test nontrivial PowerShell behavior before using it against campaign state
- never infer success from partial script execution

## LL-010 — Preserve failed telemetry rather than silently deleting it

Known-invalid observations from a controller defect remain useful evidence.

They must be labeled as invalid or attributable to instrumentation rather than
rewritten as genuine machine failures.

## LL-011 — Distinguish observation from policy

One measurement does not establish a universal threshold.

T-SCAF-002 measured approximately six minutes for one 80B cold start.

The initial 8-minute escalation threshold is therefore a provisional campaign
policy, not a proven invariant.

## LL-012 — Automatic recovery should remain automatic when proven

T-SCAF-002 required no Steward action for OCTO2 recovery.

The host rebooted, systemd restarted llama-server, the model loaded, and the
monitor returned to 80B_READY.

The campaign should observe this recovery before escalating to the Steward.

## Bounded network probes

Dashboard health checks must use explicit short timeouts. An earlier
Test-NetConnection probe demonstrated that an unavailable TCP port can make an
interactive health check appear hung.

Steward therefore uses bounded socket probes. Generic infrastructure monitoring
should eventually move to a persistent monitor/cache so HTTP response latency
is independent of unavailable hosts.

Also verify dictated port numbers before incorporating them into a persistent
management contract. Port 2222 entered the initial qualification only because
of a dictation error.

## LL — Context availability is not project grounding

### Observation

During campaign infrastructure work, the reasoning/planning layer began
reconstructing the role of the DEV RTX 3060 Ti and proposed rediscovery work
even though the approved campaign proposal had already defined the local
utility-model role, Hermes executor role, OCTO2 80B reasoning role, PiKVM HID
path, and video1 machine-perception path.

### Failure Mode

Information existing somewhere in conversation history or model context was
treated as though it would remain reliably active during later reasoning.

It did not.

The result was unnecessary rediscovery and temporary architectural drift.

### Rule

Context availability is not equivalent to project grounding.

Before advancing to another test, phase, or new reasoning session, reload the
authoritative campaign documents.

Do not reconstruct architecture, interfaces, machine roles, known failures, or
previously proven facts from conversational memory when canonical documentation
exists.

### Corrective Action

REGROUND_CONTRACT.md defines mandatory reground gates.

The controller must generate a canonical reground packet at required
boundaries. The next test is not designed until that packet has been reviewed.


### Durable knowledge must precede rediscovery

A process defect occurred during T-SCAF-005 preparation when an existing
HermesVisionGateway component was discovered locally and the next instinct was
to reverse-engineer its live implementation. Riverview already contained
documentation, a known-good deployment, and a multimodal qualification test
for that component.

The defect was not merely forgetting one interface. The failure was using the
wrong information-retrieval order.

Correct order:

campaign canonical record -> authoritative project repository -> installed
local implementation -> live runtime verification -> new investigation.

Durable knowledge before discovery; discovery before invention.

New locally qualified work must subsequently be promoted back into the durable
project record at an appropriate checkpoint so future sessions do not repeat
the investigation.

## Lesson — Do not conflate video acquisition with HID control

A dedicated video-acquisition system and an HID/control system are separate
architectural roles.

When a machine is documented and proven as the OCTO1 video-acquisition endpoint,
do not search that machine for keyboard injection, KVMD HID, marker typing, or
other actuation primitives.

For OCTO1 observation, preserve the proven chain:

OCTO1 HDMI -> video acquisition -> DEV relay -> machine/human perception.

If an action must later be injected into OCTO1, recover the authority for that
separate control path from durable campaign documentation before discovery or
invention.

Role names and nearby KVM terminology must never override the proven physical
data path.

## Lesson — Static video content cannot be used as a liveness test

For the video1 acquisition pipeline, an unchanged frame hash does NOT establish
that acquisition has stalled.

A static OCTO1 console can legitimately produce identical decoded JPEG content
across successive acquisitions.

Video-frame freshness must be established using acquisition/write timing or
another independent freshness indicator.

Observed T-SCAF-005 evidence:
- latest.jpg timestamps continued advancing approximately every two seconds.
- successive SHA256 hashes remained identical.
- therefore the video1 relay remained live while the visible OCTO1 screen
  remained unchanged.

Do not classify HASH_CHANGES=False as a frozen video pipeline when the frame
timestamp continues advancing.

## 2026-10-02 — OCTOMINER1 Closed-Loop Control / Observation Qualification

### Architecture — DO NOT CONFLATE THESE ROLES

The OCTOMINER1 BIOS campaign uses separate control and observation systems.

**CONTROL / ACTUATION**

DEV machine
-> SSH to pikvm
-> PiKVM KVMD HTTP HID API
-> PiKVM USB HID gadget
-> physical OCTOMINER1 keyboard input

PiKVM is the HID/control path.

PiKVM is NOT the authoritative video-acquisition path for this campaign.

**INDEPENDENT VIDEO OBSERVATION**

OCTOMINER1 HDMI
-> video matrix/path
-> ideo1 Raspberry Pi
-> HDMI/UVC capture device /dev/video0
-> remote ffmpeg MJPEG stream
-> DEV controller/video1_relay.py
-> untime/video1/latest.jpg

ideo1 is an observation/acquisition appliance.

Do NOT search ideo1 for keyboard/HID/actuation functions.

**TARGET OS DIAGNOSTIC PATH**

DEV
-> SSH octo1
-> OCTOMINER1 operating system

OCTOMINER1 SSH may be used for OS diagnostics and configuration when
authorized, but it is NOT independent proof of what appears on the
physical HDMI console.

### Proven PiKVM HID Method

The installed KVMD implementation exposes:

POST /hid/print

The request body is the text to type.

After successful USB enumeration, the following closed-loop test worked:

- PiKVM HID sent ls with LF terminator.
- OCTOMINER1 physically received and executed the command.
- OCTOMINER1 HDMI output changed.
- ideo1 independently captured the changed display.
- latest.jpg changed.
- The resulting screen visibly contained the ls command and directory output.

An HTTP success response from /hid/print proves KVMD accepted the request.
It does NOT by itself prove OCTOMINER1 received the keystrokes.

Closed-loop verification through ideo1 is required.

### PiKVM USB Failure / Recovery Limitation

A failure was observed where:

- KVMD remained online.
- /hid/print accepted requests.
- PiKVM's USB gadget was configured.
- PiKVM UDC reported 
ot attached.
- KVMD keyboard reported online: false.
- KVMD mouse reported online: false.
- OCTOMINER1 showed no response to accepted HID requests.

Therefore:

**KVMD API acceptance is not proof of physical HID delivery.**

The eventual recovery MUST NOT be attributed solely to a remote PiKVM reboot.

The Steward performed physical intervention involving the PiKVM/OCTOMINER1
USB/power connection and boot-switch sequence. After that physical recovery
sequence, the PiKVM returned and OCTOMINER1 successfully enumerated:

1d6b:0104 Linux Foundation Multifunction Composite Gadget

OCTOMINER1 kernel logs identified:

Product: PiKVM Composite Device

and enumerated PiKVM keyboard and mouse HID interfaces.

Current limitation:

**Recovery from this PiKVM USB-link failure requires Steward/manual
intervention until a reliable remote recovery procedure is separately
proven.**

Do not claim a remote reboot alone repairs this failure.

### Manual OCTOMINER Intervention

OCTOMINER reboot/reset/power intervention remains a manual Steward operation
at this stage of the campaign.

Do not assume unattended OCTOMINER reset capability.

### video1 Acquisition Qualification

ideo1 is a Raspberry Pi dedicated to HDMI/UVC acquisition.

Qualified capture device:

/dev/video0

Observed qualified mode:

- MJPEG
- 1920x1080
- 30 fps

The remote capture process uses ffmpeg against /dev/video0.

The DEV relay:

controller/video1_relay.py

fans the SAME MJPEG stream to:

1. the human ffplay viewer, and
2. an ffmpeg decoder that continuously replaces:

untime/video1/latest.jpg

Important freshness lesson:

A static OCTOMINER screen can legitimately produce consecutive JPEGs with
identical hashes.

**Identical image hashes do NOT prove the video relay is frozen.**

File modification timestamps were observed continuously advancing while the
screen remained visually static.

Use timestamp freshness plus controlled screen-change evidence when
qualifying the acquisition path.

### OCTOMINER1 Display Resolution

OCTOMINER1 uses Intel HD Graphics 530 / i915 for the active display.

DRM connector:

card0-HDMI-A-2

Xorg output:

HDMI2

Previous active mode:

3840x2160 @ 30 Hz

Supported preferred mode:

1920x1080 @ 60 Hz

The active Xorg display was successfully changed with:

DISPLAY=:0 xrandr --output HDMI2 --mode 1920x1080 --rate 60

The resulting 1080p HDMI image is substantially more readable through the
1920x1080 ideo1 capture path than the previous 4K desktop scaled into the
capture.

### Vision Model Qualification

Current vision path:

untime/video1/latest.jpg
-> local multimodal gateway
-> 3060 Ti vision model

At 3840x2160 OCTOMINER output, blind transcription was severely inaccurate
and hallucinated/garbled substantial screen content.

After changing OCTOMINER1 to 1920x1080, blind transcription improved
dramatically and correctly recovered substantial visible text.

However, the current model still does NOT provide sufficiently exact,
complete, dependable screen transcription for BIOS-control decisions.

Current qualification:

**3060TI_VISION_FOR_BIOS=UNQUALIFIED**

**1080P_IMPROVES_VISION_SUBSTANTIALLY=True**

Do not reduce the qualification test to questions such as whether a single
word or command appears on screen.

For BIOS work we require sufficiently reliable reading of the complete
relevant screen state, because a wrong menu item, value, warning, selection,
or prompt can cause an incorrect control decision.

Potential next architecture investigation:

1. stronger vision-language model that fits available OCTOMINER2 VRAM, and/or
2. dedicated OCR/transcription stage followed by the large reasoning model.

### Closed-Loop Architecture Proven Tonight

CONTROL:

DEV -> PiKVM -> KVMD HID -> USB -> OCTOMINER1

OBSERVATION:

OCTOMINER1 HDMI -> video1 -> /dev/video0 -> ffmpeg -> video1_relay.py -> latest.jpg

VISION:

latest.jpg -> vision model

The CONTROL and OBSERVATION paths are deliberately independent.

The control/observation mechanism is proven.

The remaining major machine-perception blocker is sufficiently accurate
vision/OCR for BIOS work.

Recorded: 2026-10-02 01:13:03 -04:00
