<!-- Version: 1.0.0 | Date: 2026-10-26 | Status: Current verified inventory -->
# OCTOMINER2 Current Hardware and Workload Configuration

This is the current verified operational inventory as of 2026-10-26. It
supersedes earlier OCTOMINER2 multi-GPU placement statements for present-day
operations. Those older records remain useful as dated history; the additional
GPUs described there were moved to OCTOMINER1.

## Identity and access

- Hostname: `OCTOMINER2`
- IPv4: `192.168.1.162`
- Physical management NIC: `eth0`, MAC `00:e0:4c:53:9e:5e`
- Windows OpenSSH alias: `octo2`, user `root`, existing identity
  `C:/Users/wille/.ssh/octominer1_nopass`
- Identity was checked over the established alias using strict host-key
  checking on 2026-10-26.

## PCIe and NVIDIA inventory

Captured over SSH on 2026-10-26:

```text
00:02.0 Intel HD Graphics 530 [8086:1912] (display adapter)
01:00.0 NVIDIA GP100GL [Tesla P100 PCIe 16GB] [10de:15f8]
GPU 0: Tesla P100-PCIE-16GB
UUID: GPU-83125857-5cbe-b7b3-4861-479383b01613
Memory: 16384 MiB total, 16060 MiB used at capture
Utilization: 0%; temperature: 54 C; power: 40.47 W
```

There is one NVIDIA GPU on OCTOMINER2: a Tesla P100 16 GB. The RTX 3060 Ti
and the two additional Tesla P100s in older records are no longer installed
on this node; they were moved to OCTOMINER1. Do not plan GPU assignments from
those historical layouts.

## Active inference workload

- Model: Qwen 30B Vision (`Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.i1-IQ3_XS`)
- Unit: `qwen30b-vision.service`
- State: enabled at boot and active/running at capture
- Endpoint: `http://192.168.1.162:8080`
- Health: `GET /health` returned HTTP 200
- Process at capture: `llama-server`, PID 180620
- Service policy: `Restart=on-failure`; `RestartSec=15`; `TimeoutStopSec=45`
- Unit binds `CUDA_VISIBLE_DEVICES=0`, uses the P100, and listens on `0.0.0.0:8080`.

The model was left running during verification. No GPU assignment or service
configuration was changed.

## Website controller

The existing Riverview OCTO Control dashboard and authenticated API run at
`http://192.168.1.162:8180/`. The versioned controller source is in
`deployment/octo2-control/`. Version 0.6.3 was deployed on 2026-10-26. The
dashboard returned HTTP 200 with the Managed Workloads card, and the
authenticated API reported Qwen running, ready, and enabled at boot. The
controller source hashes matched the local commit. The controller restart did
not interrupt Qwen: its PID remained 180620 and `/health` returned HTTP 200.

The managed-workload surface reports the systemd unit state and `/health`
readiness, and starts or stops only explicitly allowlisted units. For Qwen 30B
Vision it uses `systemctl start/stop qwen30b-vision.service`; neither action
changes the unit's boot-enabled state. The dashboard does not expose a general
systemd command interface.

Controller API start/stop actions are not live-tested against Qwen without the
Steward's explicit authorization. Local tests use mocked systemd results.

## Superseded records

- `AI_HINTS.md` and `docs/operations/network/RIVERVIEW_SSH_STANDARD.md` point
  here for current node state and retain the existing `octo2` SSH mapping.
- `docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md`
  preserves the original profile/API evidence; its multi-GPU layout is
  historical.
- `docs/hardware/gpu/OCTOMINER_TWO_NODE_96GB_LOCAL_AI_MILESTONE_2026-09-16.md`
  and `OCTOMINER_THREE_NODE_COMPUTE_AND_DISPLAY_DECOUPLING_2026-09-18.md`
  remain dated historical topology records.
- `CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md` and the
  `docs/handoffs/RIVERVIEW_AI_MODELS_EXECUTIVE_HANDOFF_2026-10-13.md` preserve
  the earlier deployment and are superseded for current OCTOMINER2 state.
