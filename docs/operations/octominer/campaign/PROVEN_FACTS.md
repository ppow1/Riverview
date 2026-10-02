# Proven Facts

## PF-001 — Octo2 80B inference operational
Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf successfully answered a live
OpenAI-compatible inference request on port 8080.

## PF-002 — Octo2 80B automatically returns after reboot
llama-server.service uses Restart=always and was observed running automatically
after the current Octo2 boot.

## PF-003 — Octo2 current GPU population
2 x Tesla P100-PCIE-16GB
1 x NVIDIA GeForce RTX 4090

## PF-004 — PiKVM HID path to OctoMiner1 works
OctoMiner1 enumerates the PiKVM composite HID device.

## PF-005 — Dedicated video acquisition works
video1 detects the MacroSilicon HDMI capture device as UVC and successfully
captured an OctoMiner1 MJPEG frame.

## PF-006 — DEV-side OCTO2 dependency monitor qualified
T-SCAF-001 proved that the campaign controller can independently detect OCTO2
boot identity, uptime, Qwen3-Next 80B process presence and API readiness.
The validated healthy state is `80B_READY`.

## PF-007 — OCTO2 spontaneous reboot observed during campaign
OCTO2 changed boot ID from
0557fb2e-0286-422f-b270-300795631ef1
to
45093b9d-0398-4e1d-a523-07b1513f750e
during T-SCAF-002.

## PF-008 — Campaign monitor survives OCTO2 reboot
DEV monitor PID 16416 remained operational through the observed OCTO2 outage
and subsequent recovery.

## PF-009 — OCTO2 automatically restarted the 80B service
After the observed reboot, systemd started llama-server.service without Steward
intervention and created llama-server PID 755.

## PF-010 — One measured 80B cold load required approximately six minutes
During T-SCAF-002, llama-server.service started at 20:58:19 EDT.
Model loading began at 20:58:23 EDT.
The server reported the model loaded and began listening on port 8080 at
21:04:18 EDT.

## PF-011 — Running llama-server PID does not prove API readiness
During T-SCAF-002, PID 755 existed while the monitor correctly observed
80B_NOT_READY. API readiness occurred later.

## PF-012 — OCTO2 recovery required no Steward intervention in T-SCAF-002
The observed reboot recovered through Linux boot, systemd service startup,
model loading and API readiness without manual action.

## PF-013 — Five-node campaign infrastructure health is live

T-SCAF-004 qualified live Steward health reporting for DEV, OCTO1, OCTO2,
PiKVM, and Video-KVM Pi. All five reported READY / GREEN during qualification.

## PF-014 — OCTO1 management path is qualified

OCTO1 is reachable at 192.168.1.160. SSH/22 and key-based SSH access through
the `octo1` alias were verified.

## PF-015 — PiKVM management path is qualified

PiKVM is reachable at 192.168.1.169. SSH/22, HTTP/80, HTTPS/443, and key-based
SSH access through the `pikvm` alias were verified.

## PF-016 — Video-KVM Pi management path is qualified

Video-KVM Pi is reachable at 192.168.1.101. SSH/22 and key-based SSH access
through the `video1` alias were verified.

## PF-017 — OCTO2 reboot count synchronized at two

Following the controlled reboot qualification, the OCTO2 campaign reboot count
was synchronized at 2 and is authoritative from that event forward.

## PF — OCTO1 independent video acquisition path proven

OCTO1 HDMI is observed through the dedicated video-acquisition Raspberry Pi.
That system is an observation/acquisition endpoint, not an HID-control endpoint.

Proven acquisition path:

OCTO1 HDMI
-> dedicated video-acquisition Pi
-> /dev/video0
-> single ffmpeg capture owner
-> SSH stream to DEV
-> controller/video1_relay.py
-> FFplay human view + runtime/video1/latest.jpg
-> HermesVisionGateway
-> hermes-multimodal
-> local Qwen3-VL 8B vision path on the DEV/3060 Ti system.

The relay was qualified with:
- one remote /dev/video0 owner,
- DEV SSH child,
- FFplay child,
- FFmpeg snapshot decoder,
- continuously generated latest.jpg.

Hermes multimodal successfully analyzed an acquired OCTO1 frame and reported:
SCREEN_TYPE=Linux terminal/console
TEXT_ENTRY_VISIBLE=TRUE
SAFE_FOR_UNSUBMITTED_TEXT=TRUE
DANGEROUS_OR_AMBIGUOUS_STATE=FALSE
CONFIDENCE=HIGH
DECISION=SAFE

The video-acquisition Pi must not be searched for or treated as the OCTO1 HID
actuator merely because the campaign also contains KVM/control infrastructure.

## PF — T-SCAF-005 video1 remained live after HID action

During T-SCAF-005 Step 4 failure diagnosis, the independent video1 acquisition
path remained live.

Successive latest.jpg observations:

23:57:43
23:57:45
23:57:47
23:57:49
23:57:51
23:57:53

The file timestamp advanced continuously while the SHA256 remained unchanged.

Interpretation:
- video1 acquisition and DEV snapshot generation were active,
- OCTO1 was displaying a static image,
- identical hashes represented identical visible pixels rather than a stale
  acquisition artifact.

Hermes independently observed a fresh OCTO1 frame and reported:
- terminal/console screen,
- visible prompt root@OCTO1N1:~#,
- empty input line,
- marker T-SCAF-005-KVM-PROOF absent,
- confidence HIGH.

Therefore the T-SCAF-005 Step-4 failure cannot currently be attributed to a
stale video1 frame.

## 2026-10-02 — OCTOMINER1 Control / Observation Proven Facts

- PiKVM role: HID/control.
- ideo1 Raspberry Pi role: independent HDMI/UVC acquisition.
- OCTOMINER1 SSH role: target OS diagnostics/configuration, not visual proof.
- PiKVM KVMD HID text endpoint: POST /hid/print.
- KVMD request acceptance alone does not prove physical HID delivery.
- PiKVM USB gadget can enter a state where KVMD is online but the USB link is not attached.
- Successful recovery observed tonight included Steward physical intervention; remote PiKVM reboot alone was NOT proven sufficient.
- After recovery OCTOMINER1 enumerated PiKVM 1d6b:0104 and its HID keyboard/mouse interfaces.
- PiKVM HID successfully caused OCTOMINER1 to execute ls.
- Independent ideo1 acquisition captured the resulting physical display change.
- ideo1 capture device is /dev/video0.
- Qualified ideo1 capture mode is MJPEG 1920x1080 at 30 fps.
- DEV relay implementation is controller/video1_relay.py.
- Machine-observation frame is untime/video1/latest.jpg.
- Advancing JPEG timestamps with identical hashes can represent a healthy live stream viewing a static screen.
- OCTOMINER1 active Xorg output is HDMI2.
- OCTOMINER1 supports 1920x1080 at 60 Hz.
- OCTOMINER1 was successfully changed from 3840x2160@30 to 1920x1080@60.
- 1080p materially improves captured terminal readability.
- Current 3060 Ti vision model improves substantially at 1080p but remains unqualified for BIOS-grade transcription.
- OCTOMINER reset/power intervention remains manual.
- PiKVM USB-link recovery currently may require manual Steward intervention.
