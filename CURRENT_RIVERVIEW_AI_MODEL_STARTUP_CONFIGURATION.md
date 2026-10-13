# CURRENT RIVERVIEW AI MODEL STARTUP AND LOADING CONFIGURATION

> **START HERE for every Riverview model-loading, GPU-allocation, service-restart, or AI-worker change.** This is the canonical *documented target configuration*, not proof of current runtime state. Before changing anything, check the live launcher and systemd services. Updated 2026-10-13. Detailed evidence: [Huihui P100 baseline](docs/model-evaluations/results/2026-10-13-huihui-p100-startup-baseline.md); [model evaluation registry](docs/model-evaluations/README.md).

## Default model assignments (OCTOMINER2 / SSH alias octo1)

| Role | Model / precision | GPU allocation | Service / port | Status |
|---|---|---|---|---|
| Grace vision / multimodal | Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated **i1-IQ3_XS**; mmproj **Q8_0** | GPU0 Tesla P100 16GB, UUID `GPU-ace423ce-ae61-803e-0734-a907283efe54` | `grace-vision.service`, `/usr/local/bin/grace-vision-fast`, `127.0.0.1:18080` | **Validated target:** `-c 32768 -np 8`; **deployment unconfirmed**. Last inspected production launcher: `-c 8192 -np 4`. |
| Large text/reasoning worker | `/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf` | GPUs 2–5, as observed in October 13 tests; inspect live placement before any change | `llama-server.service`, `127.0.0.1:8080` | Running during tests; **do not restart, reallocate, or modify** as part of vision changes |
| Reserved / not part of vision worker | RTX 4090, GPU1 | GPU1 | — | Remained idle during validation; not a license to assign it elsewhere without separate decision |

The machine's enumerated GPUs during the test: 0=P100, 1=RTX4090, 2=RTX3060Ti, 3–5=P100. GPU indices may change after hardware/driver changes: pin the vision worker by UUID and verify actual assignments.

## Validated vision startup (target, NOT independently verified as deployed)

```bash
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=GPU-ace423ce-ae61-803e-0734-a907283efe54
export LD_LIBRARY_PATH=/opt/llama.cpp/build-octo1-0.4.1-dev/bin:${LD_LIBRARY_PATH:-}

exec /opt/llama.cpp/build-octo1-0.4.1-dev/bin/llama-server \
  -m /mnt/model-storage/vision/Qwen3-VL-30B-A3B/Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.i1-IQ3_XS.gguf \
  --mmproj /mnt/model-storage/vision/Qwen3-VL-30B-A3B/Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.mmproj-Q8_0.gguf \
  -ngl all -c 32768 -np 8 \
  --host 127.0.0.1 --port 18080 --no-warmup
```

Total context **32768** is shared among **8 slots**, so each slot reports **4096 tokens**. It is **not** 32K tokens per user. F16/default KV was used for the successful 32K tests. Do not add Q8 KV flags from the failed 64K experiment.

## Evidence-backed qualification and limits

- 32K/8 slots: startup **5.865–5.93 s** across final trials.
- Eight parallel **text** requests: **8/8 pass**, each **3336 input tokens**, 31–35 generated tokens, batch **74.481 s**. Aggregate output per wall time **3.71 tok/s**; this includes prompt processing and is not decode-only speed.
- Eight parallel **vision** requests: **8/8 correct** on independent synthetic **128×128 PNGs**, each **1405 prompt tokens**, 2–3 output tokens, batch **31.77 s**.
- Sampled peak GPU0 used **16126 MiB**, minimum free **144 MiB** (59 samples). **Very little headroom**. High-resolution image loads, eight full 4K multimodal prompts, long-term operation, and production reliability remain unverified.
- 64K/8 slots with F16 KV: **FAIL**, CUDA OOM allocating 6144 MiB KV. 64K/8 slots with Q8 K/V: **FAIL**, CUDA OOM during compute/PAD after projector load.
- An earlier 32K text test with **6847-token** prompts returned 8 HTTP 400 errors because each slot holds 4096 tokens; **test-harness error**, not GPU inference failure.
- After the final test both `grace-vision.service` and `llama-server.service` reported **active**. That is **not** proof the production launcher has been changed to 32K.

## Mandatory live verification before acting

```bash
sudo systemctl cat grace-vision.service
sudo sed -n '1,180p' /usr/local/bin/grace-vision-fast
sudo systemctl is-active grace-vision.service llama-server.service
curl -fsS http://127.0.0.1:18080/health
curl -fsS http://127.0.0.1:18080/slots
nvidia-smi --query-gpu=index,name,uuid,memory.used,memory.free --format=csv
```

If `/slots` shows eight `n_ctx=4096` slots and health is OK, the running vision server matches the validated context profile. Verify launcher persistence separately. A documented rollout command was provided but **no deployment result was supplied** as of this update.

## Source of truth / change discipline

1. Read **this root file** and [model registry](docs/model-evaluations/README.md) first.
2. Consult [October 12 GPU campaign](docs/model-evaluations/results/2026-10-12-qwen3-vl-30b-gpu-campaign.md), [single-P100 retest](docs/model-evaluations/results/2026-10-12-qwen3-vl-30b-single-p100-retest.md), and [October 13 detailed baseline and failure log summaries](docs/model-evaluations/results/2026-10-13-huihui-p100-startup-baseline.md).
3. Preserve the 80B service and model/GPU allocation; back up launchers before edits, restart vision only, check service health and slots, and roll back on failure.
4. When live production deployment is **confirmed**, update this file's status with actual command, slot output, date and host evidence. Do not silently rewrite measured results or imply that uncommitted raw host logs are archived in GitHub.

**Raw-evidence caveat:** Some October 12 source archives and October 13 `/tmp` server logs are still on the host or were supplied in conversation, not committed as raw artifacts. GitHub records contain measured results and representative error excerpts, not every raw byte.
