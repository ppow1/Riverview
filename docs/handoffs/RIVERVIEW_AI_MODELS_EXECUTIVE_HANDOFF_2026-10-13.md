# EXECUTIVE HANDOFF — Riverview AI model runtime and Grace Open Eyes

**As of 2026-10-13.** Prepared for another ChatGPT conversation and Codex. This is a record of verified evidence, not a claim that every planned integration has been installed.

## Read these first

1. [Canonical current startup configuration](../../CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md) — model paths, GPU UUID, exact flags, ports, verification.
2. [Grace Open Eyes fast-load runbook](../operations/GRACE_OPEN_EYES_FAST_LOAD.md) — lifecycle, handoff, installation, diagnostics.
3. [Grace Open Eyes helper script](../../scripts/grace-open-eyes.sh) — fixed-command implementation, committed to GitHub but host installation unconfirmed.
4. [Model evaluation registry](../model-evaluations/README.md) — all model evaluations and results.
5. [October 13 Huihui P100 startup, context and multimodal tests](../model-evaluations/results/2026-10-13-huihui-p100-startup-baseline.md) — complete chronology including failures.
6. [October 12 38-configuration 30B campaign](../model-evaluations/results/2026-10-12-qwen3-vl-30b-gpu-campaign.md) and [single-P100 retest](../model-evaluations/results/2026-10-12-qwen3-vl-30b-single-p100-retest.md).
7. [October 11 80B evaluation](../model-evaluations/2026-10-11-80b-reproducibility.md) and [GPU campaign](../model-evaluations/results/2026-10-11-qwen3-next-80b-gpu-campaign-uuid.md).
8. [Codex integration work order](../operations/GRACE_OPEN_EYES_CODEX_IMPLEMENTATION.md) — precise remaining work and acceptance criteria.

## Production model inventory (last operator-observed state)

**Host:** OCTOMINER2, SSH alias `octo1`. Six enumerated GPUs at time of deployment: GPU0 P100 16GB, GPU1 RTX4090 24GB, GPU2 RTX3060Ti 8GB, GPU3–5 P100 16GB. GPU indices are observations, not stable identifiers.

| Worker | Model and files | Allocation | Endpoint/service | Verified |
|---|---|---|---|---|
| Grace vision / multimodal | `Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.i1-IQ3_XS.gguf` plus `Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.mmproj-Q8_0.gguf` in `/mnt/model-storage/vision/Qwen3-VL-30B-A3B/` | GPU0 Tesla P100 UUID `GPU-ace423ce-ae61-803e-0734-a907283efe54` | `grace-vision.service`; launcher `/usr/local/bin/grace-vision-fast`; `127.0.0.1:18080` | **DEPLOYED 2026-10-13 10:13 local**, healthy, 8 slots x 4096 tokens |
| Large text/reasoning | `/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf` | GPUs2–5 (observed); 80B exact llama.cpp runtime flags **not captured in this handoff**, inspect live `systemctl cat` and process command line | `llama-server.service`; `127.0.0.1:8080` | **active** during and after vision deployment; no restart performed |
| GPU1 | RTX4090 24GB | Not assigned to the vision worker in this deployment | N/A | 14 MiB used at final `nvidia-smi` sample; do not assume indefinitely free |

**Vision exact launcher arguments:** binary `/opt/llama.cpp/build-octo1-0.4.1-dev/bin/llama-server`; `CUDA_DEVICE_ORDER=PCI_BUS_ID`; `CUDA_VISIBLE_DEVICES=GPU-ace423ce-ae61-803e-0734-a907283efe54`; `LD_LIBRARY_PATH=/opt/llama.cpp/build-octo1-0.4.1-dev/bin:${LD_LIBRARY_PATH:-}`; model and mmproj above; `-ngl all -c 32768 -np 8 --host 127.0.0.1 --port 18080 --no-warmup`. **32K is total shared context, not per-client**. No Q8 KV override; successful run used default F16 KV.

**Deployment proof supplied by operator:** backed up launcher to `/usr/local/bin/grace-vision-fast.pre-32k-20261013-101303`; changed context/slots; `bash -n` passed; restarted only `grace-vision.service`; health `{'status':'ok'}`; `/slots` returned `[4096,4096,4096,4096,4096,4096,4096,4096]`; `PRODUCTION_32K_PASS: True`; both vision and 80B services active. Final GPU used/free MiB: GPU0 **16022/248**, GPU1 **14/24197**, GPU2 **7425/543**, GPU3 **13722/2548**, GPU4 **13564/2706**, GPU5 **13606/2664**. These are one-time measurements, not guaranteed present values.

## Qualification record

- Single P100 startup ~**5.865–5.93 s** for 32K/8.
- Eight concurrent text requests: **8/8 success**, 3336 prompt tokens each, wall **74.481 s**; 276 generated tokens, ~3.71 output tokens/s over whole wall including prompt processing.
- Eight concurrent vision requests: **8/8 correct** with 128×128 synthetic PNGs, 1405 prompt tokens each; wall **31.77 s**; peak GPU0 used **16126 MiB**, minimum free **144 MiB** over 59 samples.
- 64K/8 F16 KV: **CUDA OOM**, 6144 MiB KV allocation. 64K/8 Q8 K/V: **CUDA OOM** during PAD. **Do not promote 64K**.
- Earlier eight HTTP400 responses were caused by **6847-token prompts exceeding 4096-token slots**, not a model failure.
- Real high-resolution images, long-running stability, and full 4K-per-slot image workloads **not qualified**.
- Original raw host test logs/archives are **not all committed** to GitHub; Markdown preserves measured results and selected evidence.

## Grace opens her eyes

**Existing operational reload:** `sudo systemctl start grace-vision.service` when intentionally unloaded and GPU0 is available. It reuses the verified launcher and parameters. Verify `/health` OK and eight `n_ctx=4096` slots before sending image requests.

**Version-controlled fixed helper:** `scripts/grace-open-eyes.sh`, intended installation `/usr/local/sbin/grace-open-eyes`; run `sudo /usr/local/sbin/grace-open-eyes`. It locks concurrent reloads, checks launcher flags/UUID, checks for conflicting GPU compute PIDs if stopped, starts the service, and verifies readiness. It must **not** kill or reassign any other GPU job or touch the 80B service.

**Unfinished integration (do not misrepresent as complete):**
1. Install and validate the committed helper on OCTO1. No remote shell/execution connector is available in this chat; GitHub commits alone do not install it.
2. Wire Grace's capability dispatcher/resource arbiter to invoke this fixed helper through an authorized execution boundary, then route multimodal requests to port 18080. No verified live Grace dispatcher integration yet. See Codex work order.
3. Merge PR #13 if still open; prior automated merge attempt was blocked. Do not assume merge succeeded.
4. Preserve/transfer remaining raw host evidence as needed.

## Operational invariants

- Do not stop, restart, or reconfigure `llama-server.service` (80B) as part of vision work.
- Do not launch a second ad hoc `llama-server` on the same GPU/port.
- Do not reclaim GPU0 from a different owner without the resource manager's allocation decision.
- Idempotent Open Eyes when already healthy; bounded timeout, explicit failure, no blind restart loop.
- Persist both code and evidence in GitHub, and update the root startup configuration after any verified changes.


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
