# Codex work order — integrate Grace Open Eyes end to end

**Objective:** Grace automatically acquires the existing on-demand Huihui vision capability, opens eyes using the exact tested model and P100 UUID, performs a multimodal request, and can relinquish GPU0 through the existing resource-ownership architecture without disturbing the 80B worker.

## Required first reads
- [AI model executive handoff](../handoffs/RIVERVIEW_AI_MODELS_EXECUTIVE_HANDOFF_2026-10-13.md)
- [Canonical startup configuration](../../CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md)
- [Open Eyes runbook](GRACE_OPEN_EYES_FAST_LOAD.md)
- [Committed helper](../../scripts/grace-open-eyes.sh)
- [Model registry](../model-evaluations/README.md)
- `AI_HINTS.md` and project requirements/process map; preserve Riverview's existing autonomy and execution-first behavior.
- Inspect current `src/riverview/residents/gateway.py`, `src/riverview/reasoning/resident_home.py`, existing provider and capability dispatchers, resource arbitration, authenticated routes, and actual OCTO1 host deployment. Do not assume `src/riverview/resources/registry.py` is a GPU registry: it currently projects Codex execution resources.

## Phase 1 — deploy and verify helper on OCTO1
1. Confirm the target host is OCTOMINER2 (SSH alias `octo1`) and live launcher is `/usr/local/bin/grace-vision-fast` with `-c 32768 -np 8`, correct UUID/model/mmproj.
2. Copy repo `scripts/grace-open-eyes.sh` to `/usr/local/sbin/grace-open-eyes` using `install -o root -g root -m 0755`. Do not replace `grace-vision-fast`.
3. Run `bash -n` on installed script; execute `sudo /usr/local/sbin/grace-open-eyes` with already-running service. Expect `OPEN_EYES_READY: true; slots=8; context_each=4096`.
4. During an approved GPU handoff, stop only `grace-vision.service`, verify GPU0 compute ownership/free status, invoke helper, verify start/readiness/slots and 80B health; restore service if interrupted.
5. Capture logs, service statuses, GPU UUID/PID mapping, exact command and timings. The script must not kill unrelated jobs. If service is disabled, `systemctl start` still works; do not change enable/boot behavior without separate policy.
6. **Review helper edge cases before production use:** its GPU conflict check uses `nvidia-smi --query-compute-apps` and must fail closed on query errors, not mistake an unreadable list for an empty GPU; validate that launcher checks match actual syntax and that service startup can handle a previously failed unit. Add tests for these.

## Phase 2 — wire Grace's existing capability dispatch, not a new standalone agent
1. Discover the authoritative Grace orchestration entry point, identity/security boundary, capability registry, GPU scheduler/lease mechanism and vision request path. Follow the actual architecture; no invented parallel routing stack.
2. Register a bounded `vision.ensure_ready` action. It accepts no arbitrary shell command and calls only the installed fixed helper via an approved local executor/SSH host boundary with least-privilege rights. No general-purpose root shell exposed to model output.
3. On image-bearing request: resolve vision capability -> reserve/confirm GPU0 allocation -> ensure ready -> verify health and slots -> submit image to `127.0.0.1:18080` from an authorized host or existing gateway -> return response -> record provenance and resource usage. If the gateway is on another host, use its existing authenticated internal network path, **not** direct public exposure of loopback port.
4. Preserve request/session identity, timeout budgets, cancellation, logging, classification rules, idempotency, bounded retries, and audit events. Avoid turn-by-turn manual operator approval when the resource manager already authorizes the allocation.
5. If GPU0 is busy, return a typed `resource_busy` response or use existing queue/retry policy. Never stop another worker to claim GPU0 without an explicit scheduler decision. Never touch `llama-server.service` or its GPUs2–5.
6. Decide whether/when to release vision through existing resource lease and idle-timeout policy. **Do not auto-stop a running vision request**. Preserve startup readiness and avoid churn.

## Acceptance tests (required evidence)
- Already healthy: Open Eyes returns ready without restarting service; service PID unchanged.
- Stopped and GPU free: Open Eyes starts in bounded time, health OK, eight slots `n_ctx=4096`, exact P100 UUID used, no duplicate server.
- GPU busy: no forced stop/preemption; typed busy and existing worker survives.
- Wrong launcher or wrong GPU UUID: fail with diagnostic, do not launch.
- No health / wrong slot layout / process exits: fail with bounded timeout and evidence; no false readiness.
- Concurrent image requests: one load attempt; all successful requests use correct multimodal endpoint and identity boundary.
- Grace end-to-end: image request triggers readiness and correct vision response; audit shows ensure-ready, dispatch, completion.
- 80B remains healthy and its service PID remains unchanged through tests.
- Record exact runtime state, logs and commands in [canonical startup](../../CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md) and [registry](../model-evaluations/README.md); link evidence from this work order.
- Run existing automated tests and new integration tests; do not claim complete until tests actually pass.

## Definition of done
Both the fixed helper **installed and tested on OCTO1** and the **real Grace request dispatcher invoking it** are verified with an end-to-end vision request, resource ownership, logs, and 80B isolation. A committed script alone is not completion. Keep all modifications reviewable, and provide PR/commit IDs and runtime evidence.


## 2026-10-13 operator installation verification

The operator transferred a PowerShell-embedded implementation of Grace Open Eyes over SSH to `/usr/local/sbin/grace-open-eyes` (after raw GitHub URL returned 404 and private Git clone required credentials). Installed script syntax check passed and execution returned:

```text
APPROVED_LAUNCHER: yes
VISION_SERVICE: already active; verifying
OPEN_EYES_READY: true; slots=8; context_each=4096
active
active
```

**Verified:** installed host helper correctly validates an *already-running* vision service, 8 slots x 4096, and both services remain active. **Not verified:** stopped-service reload, GPU-busy behavior, Grace dispatcher integration, or exact byte-for-byte equality between the manually transferred helper and the GitHub `scripts/grace-open-eyes.sh` (the transferred helper was an in-chat adaptation). Codex should reconcile/version the installed script with the repository before integration. Do not claim end-to-end Grace integration complete.
