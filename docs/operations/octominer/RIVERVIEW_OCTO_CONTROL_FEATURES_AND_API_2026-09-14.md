<!--
File: docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md
Version: 0.6.3
Date: 2026-10-26
Purpose: OCTOMINER2 controller capabilities, managed workload API, and historical profile context.
-->

# Riverview OCTO Control v0.6.3 — Features and Remote API

Status: Updated source documentation. Check the live controller version and deployment separately.

> The v0.6.1 feature inventory and three-GPU snapshot below were captured on
> 2026-09-14 and are retained as historical evidence. Current OCTOMINER2 has one
> Tesla P100 16 GB; Qwen 30B Vision runs through `qwen30b-vision.service` on
> port 8080. Its additional GPUs were moved to OCTOMINER1. Current inventory:
> [`OCTOMINER2_CURRENT_CONFIGURATION_2026-10-26.md`](OCTOMINER2_CURRENT_CONFIGURATION_2026-10-26.md).

- Dashboard: `http://192.168.1.162:8180/`
- API base: `http://192.168.1.162:8180/api/v1`
- Host: `OCTOMINER2`
- Current GPU layout (verified 2026-10-26): GPU 0 Tesla P100 PCIe 16 GB
- Current inference workload: Qwen 30B Vision, `qwen30b-vision.service`, port 8080
- Dashboard/API: `http://192.168.1.162:8180/`, control token required for API routes
- Persistent monitor storage: `/mnt/octo-models-stage/riverview-octo-monitor/`

The feature descriptions inherited from the 2026-09-14 capture record v0.6.1
behavior. The managed workload endpoints below are the v0.6.3 source additions.
Other v0.6.1 profile examples remain historical and are not a current GPU
allocation recommendation.

The old multi-GPU model-profile examples later in this document are historical.
The managed workload API described below is separate from that profile catalog
and does not rewrite `models.json` or GPU assignments.

## Authentication

The dashboard (`GET /`) and F1 help page (`GET /help`) are readable on the
trusted LAN. Every `/api/v1/...` request requires:

```text
Authorization: Bearer CONTROL_TOKEN
```

The API has no token-retrieval endpoint. Provision an authorized Windows client
through administrator SSH:

```powershell
$Token = (& ssh.exe -T -n octo2 `
    'cat /opt/riverview-octo-control/control.token').Trim()
$Base = 'http://192.168.1.162:8180'
$Headers = @{ Authorization = "Bearer $Token" }
```

Never commit or log the token. The dashboard stores it in that browser's local
storage after Save. Each browser or device is provisioned separately.

## Current features

### Dashboard and quick deployment

- Visible controller version.
- Live status/GPU/instance polling every 5 seconds and fan polling every 10.
- Uptime, monitoring freshness, model elapsed time, and load history.
- Quick Deployment starts one predefined profile and replaces active model jobs.
- Profiles define model, optional vision projector, GPU allocation, context,
  tensor split, port, capabilities, reservation defaults, and Hermes status.
- Download Snapshot captures rendered UI state and synchronized diagnostics.
- F1 and **API Help (F1)** open `/help`.

### Managed systemd workloads

The authenticated **Managed Workloads** dashboard card reports each
allowlisted service's systemd state, HTTP readiness, PID, and boot-enabled
state. It provides start and stop controls for Qwen 30B Vision and renders
additional workload records from the same allowlist as they are added.

- `qwen30b-vision` maps only to `qwen30b-vision.service` and port 8080.
- Start and stop call only `systemctl start` or `systemctl stop`; they never
  enable or disable the service.
- The unit remains enabled at boot and retains `Restart=on-failure` for
  automatic startup after reboot and recovery after process failure.
- The workload status GET route is safe to poll. Start/stop controls require
  the existing Bearer token and are not live-tested without Steward
  authorization.
- Versioned source is in `deployment/octo2-control/`.

### Expandable independent instances

- Creates independently named llama.cpp processes.
- Detects GPUs dynamically; it is not limited to three slots.
- Assigns one or multiple GPUs to an instance.
- Supports multiple shared instances on a GPU when VRAM reservations fit.
- Supports exclusive GPU allocation and rejects collisions.
- Accepts optional port, context, tensor split, and per-GPU VRAM overrides.
- Allocates ports 8110–8199 when no port is supplied.
- Runs instances as separate transient systemd services.
- Stops/removes one instance or stops all instances.
- Reports actual VRAM and logical reservations independently.

Reservations are admission-control declarations, not hard CUDA limits. The
allocator retains a 512 MB safety margin on each GPU.

### Telemetry, monitoring, and snapshots

- GPU identity, total/used VRAM, utilization, temperature, and power.
- Per-GPU reservations and instance assignments.
- Octofan chassis-fan, PSU, sensor, and watchdog telemetry.
- Fan presets: Quiet 96; Normal 160; Maximum 255; Off 0.
- Controlled channels: 0, 2, 4, 6, and 8.
- Fans Off is rejected while a model is active or any GPU is at least 55 C.
- Persistent monitoring samples every 10 seconds and survives service restart.
- Monitor records live on the external model drive.
- Snapshots exclude the token, SSH material, environment variables, and model
  contents.

### Hermes Agent

- Reports installation and configuration.
- Configures Hermes for a supported Quick Deployment profile.
- Runs a Hermes one-shot test.
- Qwen3-Coder 30B/all GPUs is verified at 65,536 context including a terminal
  tool call.
- Huihui Qwen3-VL 30B is retained at 32,768 and classified unstable for Hermes
  after its 65K trial coincided with an OCTO2 reboot.
- Hermes currently targets Quick Deployment, not arbitrary independent
  instances.

## Implemented API routes

Every route below requires the Bearer token.

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/v1/status` | Version, host, deployment state, GPUs, monitor summary |
| GET | `/api/v1/gpus` | Live GPU telemetry |
| GET | `/api/v1/resources/gpus` | GPU telemetry, reservations, instances |
| GET | `/api/v1/fans` | Octofan, fan, PSU, sensor, watchdog telemetry |
| GET | `/api/v1/models` | Configured profile catalog |
| GET | `/api/v1/files` | Model/projector inventory |
| GET | `/api/v1/logs` | Recent Quick Deployment llama.cpp log |
| GET | `/api/v1/monitoring` | Persistent monitor state and load history |
| GET | `/api/v1/hermes` | Hermes installation and routing state |
| GET | `/api/v1/instances` | Independent instances and readiness |
| GET | `/api/v1/workloads` | Allowlisted systemd workload and readiness state |
| POST | `/api/v1/workloads/{id}/start` | Start an allowlisted workload without changing boot enablement |
| POST | `/api/v1/workloads/{id}/stop` | Stop an allowlisted workload without changing boot enablement |
| POST | `/api/v1/deployments` | Replace active models with Quick Deployment |
| DELETE | `/api/v1/deployments/current` | Stop Quick Deployment |
| POST | `/api/v1/instances` | Create an independent instance |
| DELETE | `/api/v1/instances/{instance_id}` | Stop and remove one instance |
| POST | `/api/v1/instances/stop-all` | Stop all independent instances |
| POST | `/api/v1/fans` | Set chassis-fan PWM 0–255 |
| POST | `/api/v1/hermes/configure` | Configure Hermes for `profile_id` |
| POST | `/api/v1/hermes/test` | Run Hermes one-shot test |
| POST | `/api/v1/snapshot` | Return a troubleshooting ZIP |

## Query all remote state

```powershell
$RemoteState = [ordered]@{
    Status       = Invoke-RestMethod "$Base/api/v1/status" -Headers $Headers
    GPUs         = Invoke-RestMethod "$Base/api/v1/gpus" -Headers $Headers
    GPUResources = Invoke-RestMethod "$Base/api/v1/resources/gpus" -Headers $Headers
    Fans         = Invoke-RestMethod "$Base/api/v1/fans" -Headers $Headers
    Models       = Invoke-RestMethod "$Base/api/v1/models" -Headers $Headers
    ModelFiles   = Invoke-RestMethod "$Base/api/v1/files" -Headers $Headers
    Logs         = Invoke-RestMethod "$Base/api/v1/logs" -Headers $Headers
    Monitoring   = Invoke-RestMethod "$Base/api/v1/monitoring" -Headers $Headers
    Hermes       = Invoke-RestMethod "$Base/api/v1/hermes" -Headers $Headers
    Instances    = Invoke-RestMethod "$Base/api/v1/instances" -Headers $Headers
}
$RemoteState | ConvertTo-Json -Depth 20
```

## Create an independent instance

```json
{
  "instance_id": "qwen-small-p100-1a",
  "profile_id": "qwen25-3b-3060",
  "gpu_ids": [1],
  "sharing_policy": "shared",
  "gpu_memory_budget_mb": 5000,
  "port": 8110,
  "context": 16384,
  "tensor_split": null
}
```

`instance_id`, `profile_id`, and `gpu_ids` are required. Instance IDs use
1–40 lowercase letters, numbers, or hyphens. `sharing_policy` is `shared`
(default) or `exclusive`. Every selected GPU requires a reservation of at
least 512 MB. Port, context, and tensor split are optional.

```powershell
$Body = @{
    instance_id = 'qwen-small-p100-1a'
    profile_id = 'qwen25-3b-3060'
    gpu_ids = @(1)
    sharing_policy = 'shared'
    gpu_memory_budget_mb = 5000
} | ConvertTo-Json

$Instance = Invoke-RestMethod "$Base/api/v1/instances" -Method Post `
    -Headers $Headers -ContentType 'application/json' -Body $Body
```

Stop one or all:

```powershell
Invoke-RestMethod "$Base/api/v1/instances/qwen-small-p100-1a" `
    -Method Delete -Headers $Headers

Invoke-RestMethod "$Base/api/v1/instances/stop-all" -Method Post `
    -Headers $Headers -ContentType 'application/json' -Body '{}'
```

## Quick Deployment, fans, and snapshots

```powershell
$Body = @{ profile_id = 'qwen3-coder-30b-all' } | ConvertTo-Json
Invoke-RestMethod "$Base/api/v1/deployments" -Method Post `
    -Headers $Headers -ContentType 'application/json' -Body $Body

$Body = @{ pwm = 160 } | ConvertTo-Json
Invoke-RestMethod "$Base/api/v1/fans" -Method Post `
    -Headers $Headers -ContentType 'application/json' -Body $Body

$Destination = Join-Path ([Environment]::GetFolderPath('Desktop')) `
    "octo2-api-snapshot-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
Invoke-WebRequest "$Base/api/v1/snapshot" -Method Post `
    -Headers $Headers -ContentType 'application/json' -Body '{}' `
    -OutFile $Destination
```

## Direct model inference

Port 8180 is the management API. Send inference directly to the `api_url`
returned by `/api/v1/status` or `/api/v1/instances`. Each live llama.cpp
server exposes an OpenAI-compatible API beneath `/v1` and browser UI at its
`chat_url`.

## Reserved, not implemented in v0.6.1

- `POST /api/v1/power/...` returns HTTP 501; smart-plug control is not
  configured.
- Multi-host scheduling, saved layouts, Wake-on-LAN orchestration, central
  manager control, and shutdown preparation remain future work.
- Arbitrary browser origins do not receive CORS headers.
- Exact paths are required; do not append cache-busting query strings.
- Available models remain defined by installed `models.json`.

## Verification evidence

Snapshot `octo2-snapshot-2026-09-14T19-39-19Z.zip` is historical evidence for
controller v0.6.1, its then-observed three GPUs, telemetry, profile catalog,
and Hermes configuration. It does not describe the current OCTOMINER2 hardware
or workload state.
