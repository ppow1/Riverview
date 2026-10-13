# OCTO1 Huihui 30B single-P100 startup baseline — 2026-10-13

**Status:** Verified 8K and 32K startup on one P100; 64K/8-slot startup failed. Production change pending; long-context workload and vision qualification pending. This is the reference for the fast launcher and persistent systemd service, **not proof that production was switched to 8 slots**.

## Why this configuration

The 2026-10-12 38-configuration campaign compared 19 GPU subsets with 4 and 8 slots. The single P100 had the fastest reported model readiness (~6–7 seconds) among tested subsets and leaves the 4090 and four other occupied GPUs available for other workers. The original single-P100 retest on 2026-10-12 reported 7.16 seconds (4 slots) and eight-way aggregate 110.655–143.018 generated tokens/sec (8 slots), zero request failures. On 2026-10-13 after correcting the cloned SSD's UUID and mount, the original retest script was rerun with production vision temporarily stopped; the model reached readiness in **7.333 s** (4 slots, process restart), **8.017 s** (4 slots, OS-cache warm) and **7.106 s** (8 slots), using the actual model files on /mnt/model-storage. The benchmark did **not** clear the OS page cache. GPU0 consumed ~13,714–13,746 MiB. The 80B worker was not intentionally stopped.

**Context vs concurrency tradeoff:** `-c 8192 -np 8` means **8,192 total context tokens** divided among 8 parallel slots (~1,024 per slot when evenly allocated), **not 8K per client**. For longer individual contexts use the separately verified `-np 4` (~2,048 per slot). A true 8K context for each of eight simultaneous clients would require substantially larger total context, not qualified here. On 2026-10-13, a dedicated **32K/8-slot** load test passed; 64K/8-slot failed. See addendum below.

**Scope:** Synthetic text-only prompt, max 160 generated tokens/request; not yet qualified for actual images, accuracy, realistic multi-turn prompts, 16K/32K context, or cold storage read. The 2026-10-13 eight-slot concurrency run should be retained with its raw JSONL before citing new exact aggregate measurements.

## Exact fast-load reference command (8-slot throughput profile)

```bash
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=GPU-ace423ce-ae61-803e-0734-a907283efe54
export LD_LIBRARY_PATH=/opt/llama.cpp/build-octo1-0.4.1-dev/bin:${LD_LIBRARY_PATH:-}

exec /opt/llama.cpp/build-octo1-0.4.1-dev/bin/llama-server \
  -m /mnt/model-storage/vision/Qwen3-VL-30B-A3B/Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.i1-IQ3_XS.gguf \
  --mmproj /mnt/model-storage/vision/Qwen3-VL-30B-A3B/Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.mmproj-Q8_0.gguf \
  -ngl all \
  -c 8192 \
  -np 8 \
  --host 127.0.0.1 \
  --port 18080 \
  --no-warmup
```

**4-slot longer-per-client-context variant:** Change **only** `-np 8` to `-np 4`. All other flags, paths, GPU UUID and context total remain the same. The benchmark used port 18083, while persistent production uses port 18080.

## Persistent service integration (planned; do not silently replace active configuration)

- Launcher: `/usr/local/bin/grace-vision-fast`. The last inspected deployed launcher had `-np 4`. Switching to this eight-slot profile requires an intentional launcher update and service restart.
- Unit: `grace-vision.service` with `ExecStart=/usr/local/bin/grace-vision-fast`.
- Ensure `/mnt/model-storage` is mounted **before** service startup. Suggested systemd drop-in: `[Unit]\nRequiresMountsFor=/mnt/model-storage`. Inspect existing unit and drop-ins before applying.
- SSD `/dev/sdb4` has UUID `a88d8af7-02e6-4aa6-8101-6370dc13fa21` and is configured in `/etc/fstab` at `/mnt/model-storage`; boot persistence has not been reboot-tested.
- To validate: `systemctl is-active grace-vision.service`; `curl -fsS http://127.0.0.1:18080/health`; `curl -fsS http://127.0.0.1:18080/props` (verify `total_slots=8`); `nvidia-smi --query-compute-apps=pid,gpu_uuid,used_gpu_memory --format=csv`. Verify 80B independently without altering its service.

## Provenance

- [38-config campaign](2026-10-12-qwen3-vl-30b-gpu-campaign.md)
- [2026-10-12 single-P100 retest](2026-10-12-qwen3-vl-30b-single-p100-retest.md)
- 2026-10-13 host run: `/root/qwen30b-p100-retest/run-20261013-093852` (original Python retest: `/tmp/riverview_qwen30b_p100_retest.py`, model paths updated to mounted SSD). Raw evidence currently on host, not claimed committed to GitHub.
- Production launcher's inspected paths and flags as of 2026-10-13: single P100, `-ngl all -c 8192 -np 4 --no-warmup`, port 18080.

**Decision dated 2026-10-13:** Use eight-slot command above as the documented **fast/concurrency reference**; retain four-slot alternative for larger per-request context. Do not represent either as proven image-quality qualification.


## 2026-10-13 context extension test — decisive update

**Procedure:** Temporarily stop `grace-vision.service`; start exact Huihui IQ3_XS weights and Q8 projector on GPU UUID `GPU-ace423ce-ae61-803e-0734-a907283efe54`, port 18083, with `-ngl all -np 8 --no-warmup`; vary only `-c` between 32768 and 65536; restore production service on exit. 80B GPUs 2–5 remained allocated. Test was a **load/health/slot-allocation** test, not a long-prompt or vision benchmark.

| Total context | Slots | Ready | Startup | Per-slot context | GPU0 used/free | Server log |
|---|---:|---|---:|---:|---|---|
| 32768 | 8 | **YES** | **5.908 s** | 4096 each (all eight reported) | 16022 / 248 MiB | `/tmp/huihui-context-32768.log` |
| 65536 | 8 | **NO**, exit 1 | 5.670 s until observed exit | N/A | 8 / 16263 MiB after exit | `/tmp/huihui-context-65536.log` |

**Interpretation:** 32K/8-slot startup is verified, leaving only 248 MiB free on the P100. 64K/8-slot startup fails; do not assert OOM until its log is inspected. 32K at 8 slots is a **candidate** persistent profile, but 8 concurrent long-context requests, sustained generation, actual images, and restart reliability are not yet tested. The earlier 8K/8-slot profile remains the proven concurrency-throughput baseline. `-c 32768` should **not** be substituted into the production launcher until load tests and operator approval.

The 80B `systemctl is-active` command was malformed by a Windows CR (`llama-server.service\\x0d`); the resulting `inactive` line does not establish an 80B failure. The restored `grace-vision.service` reported `active`.

**Next:** Read the 64K server log; optionally benchmark 32K/8-slot with real context and concurrency. If validated, promote it to the persistent service command and update this reference with measured results.


### 64K failure root cause (2026-10-13 log inspected)

The host log `/tmp/huihui-context-65536.log` confirms **CUDA out of memory during KV-cache initialization**, not an unidentified startup failure:

```text
ggml_backend_cuda_buffer_type_alloc_buffer: allocating 6144.00 MiB on device 0: cudaMalloc failed: out of memory
alloc_tensor_range: failed to allocate CUDA0 buffer of size 6442450944
llama_init_from_model: failed to initialize the context: failed to allocate buffer for kv cache
```

Next controlled candidate: retry `-c 65536 -np 8` with `--cache-type-k q8_0 --cache-type-v q8_0`, **only after confirming the binary accepts these flags**, and keep production launcher unchanged until load and inference are verified. KV quantization is a hypothesis to test, not yet a passing configuration.


### 64K / eight slots with Q8 K/V — measured failure

A controlled run with `-c 65536 -np 8 --cache-type-k q8_0 --cache-type-v q8_0` on the same single P100 failed. `READY: False` after 120.398 s of polling; server process PID 441850 aborted around 5.955 s during initialization. The multimodal projector loaded, followed by `ggml_cuda_compute_forward: PAD failed` and `CUDA error: out of memory` on device 0. After abort, GPU0 memory was 8 MiB used / 16263 MiB free. Log: `/tmp/huihui-64k-q8.log`. The cleanup trap restarted `grace-vision.service`, which reported `active`. Other GPU allocations stayed unchanged; no final independent 80B service health check was captured. This is **not** a passing 64K configuration. The 120-second polling loop did not exit early on child-process death; fix in future harnesses.

**Decision:** Do not promote 64K Q8. Keep existing production settings pending a realistic 32K eight-slot inference/vision stability test and explicit approval for a launcher change.


### 32K eight-slot long-context stress test — inconclusive (2026-10-13)

With `-c 32768 -np 8` and default F16 KV, server became ready in 5.88 s; `/slots` reported eight 4096-token contexts. GPU0 used 16022 MiB with 248 MiB free. The test submitted eight concurrent, highly repetitive text-only prompts (175 repeats of a technical passage; `max_tokens=96`). **All eight returned HTTP 400 within 0.057 s**; no inference completed, no CUDA memory error was observed. The harness failed to capture HTTP response bodies, so the precise rejection cause is **unknown**; overlong prompts relative to 4096-token slots are a hypothesis only. `grace-vision.service` and `llama-server.service` both reported `active` after cleanup. This test does **not** establish that eight long-context inferences work or fail. Next: obtain HTTP 400 response body with a single bounded probe, verify server-reported prompt-token count, then repeat concurrent test with confirmed fitting prompts and output headroom.


### 32K / eight-slot corrected concurrent text inference — PASS (2026-10-13)

Controlled run on GPU0 Tesla P100 16 GB with Huihui Qwen3-VL-30B-A3B IQ3_XS and multimodal projector; `-c 32768 -np 8`, default F16 KV. Startup READY in **5.93 s**. `/slots` confirmed eight slots, each `n_ctx=4096`. Eight concurrent OpenAI-compatible chat requests, each **3336 prompt tokens**, returned successful nonempty answers and `finish_reason=stop` (31 tokens for worker 1, 35 each for workers 2–8). Individual latencies **73.866–74.477 s**, wall time **74.481 s**. Aggregate completion throughput **3.71 tokens/s** (276 generated tokens / 74.481 s); note prompt processing dominates the wall time, so this is **not** a decode-only throughput measurement. GPU0 before **16022 MiB used / 248 MiB free**, after **16064 MiB used / 206 MiB free**; **peak memory not measured**. No CUDA errors in server log. Test reported `LONG_CONTEXT_CONCURRENCY_PASS: True`. Cleanup restored `grace-vision.service` and confirmed `llama-server.service` both `active`. The eight requests were **text-only**; concurrent vision/image handling remains unverified. Extremely narrow free-VRAM margin: do not claim production stability or deploy without peak-memory monitoring and representative vision workloads. This successful corrected run supersedes the earlier HTTP 400 test, whose prompts were 6847 tokens and exceeded 4096-token slots.
