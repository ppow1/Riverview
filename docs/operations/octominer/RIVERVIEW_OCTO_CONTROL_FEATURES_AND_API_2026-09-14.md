<!--
File: docs/operations/octominer/RIVERVIEW_OCTO_CONTROL_FEATURES_AND_API_2026-09-14.md
Version: 0.6.1
Date: 2026-09-14
Purpose: Current OCTOMINER2 controller capabilities and remotely queryable API.
-->

# Riverview OCTO Control v0.6.1 — Features and Remote API

Status: Installed and live on OCTOMINER2.

- Dashboard: `http://192.168.1.162:8180/`
- API base: `http://192.168.1.162:8180/api/v1`
- Host: `OCTOMINER2`
- Installed GPU layout: GPU 0 RTX 3060 Ti 8 GB; GPUs 1–2 Tesla P100 16 GB
- Persistent monitor storage: `/mnt/octo-models-stage/riverview-octo-monitor/`

This document records implemented v0.6.1 behavior. Planned control-plane routes
are explicitly separated from live routes.

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

Snapshot `octo2-snapshot-2026-09-14T19-39-19Z.zip` verified controller v0.6.1,
both services active, successful HTTP 200 API polling, three GPUs, complete
fan/PSU telemetry, eight configured profiles, no active instances at capture,
and Hermes configured for `qwen3-coder-30b-all` at 65,536 context.
