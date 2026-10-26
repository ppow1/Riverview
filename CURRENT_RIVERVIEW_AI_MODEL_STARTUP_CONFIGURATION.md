<!-- Revision: 1.0.1 | Current-status note added 2026-10-26 -->
# HISTORICAL RIVERVIEW AI MODEL STARTUP AND LOADING CONFIGURATION

> **Superseded for current OCTOMINER2 operations on 2026-10-26.** This document
> preserves the October 13 GPU allocation and deployment evidence; it is not the
> current hardware inventory or startup authority. OCTOMINER2 now has one Tesla
> P100 16 GB running Qwen 30B Vision through enabled `qwen30b-vision.service` on
> port 8080. The additional GPUs were moved to OCTOMINER1. Read
> [`OCTOMINER2_CURRENT_CONFIGURATION_2026-10-26.md`](docs/operations/octominer/OCTOMINER2_CURRENT_CONFIGURATION_2026-10-26.md)
> for current evidence.

> **START HERE for every Riverview model-loading, GPU-allocation, service-restart, or AI-worker change.** This is the canonical *documented target configuration*, not proof of current runtime state. Before changing anything, check the live launcher and systemd services. Updated 2026-10-13. Detailed evidence: [Huihui P100 baseline](docs/model-evaluations/results/2026-10-13-huihui-p100-startup-baseline.md); [model evaluation registry](docs/model-evaluations/README.md).

## Default model assignments (OCTOMINER2 / SSH alias octo1)

| Role | Model / precision | GPU allocation | Service / port | Status |
|---|---|---|---|---|
| Grace vision / multimodal | Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated **i1-IQ3_XS**; mmproj **Q8_0** | GPU0 Tesla P100 16GB, UUID `GPU-ace423ce-ae61-803e-0734-a907283efe54` | `grace-vision.service`, `/usr/local/bin/grace-vision-fast`, `0.0.0.0:18080` | **Validated target:** `-c 32768 -np 8`; **DEPLOYED AND VERIFIED 2026-10-13 10:13 local:** `-c 32768 -np 8`. |
| Large text/reasoning worker | `/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf` | GPUs 2–5, as observed in October 13 tests; inspect live placement before any change | `llama-server.service`, `0.0.0.0:8080` | Running during tests; **do not restart, reallocate, or modify** as part of vision changes |
| Reserved / not part of vision worker | RTX 4090, GPU1 | GPU1 | — | Remained idle during validation; not a license to assign it elsewhere without separate decision |

The machine's enumerated GPUs during the test: 0=P100, 1=RTX4090, 2=RTX3060Ti, 3–5=P100. GPU indices may change after hardware/driver changes: pin the vision worker by UUID and verify actual assignments.

## Validated vision startup (deployed and verified 2026-10-13)

```bash
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=GPU-ace423ce-ae61-803e-0734-a907283efe54
export LD_LIBRARY_PATH=/opt/llama.cpp/build-octo1-0.4.1-dev/bin:${LD_LIBRARY_PATH:-}

exec /opt/llama.cpp/build-octo1-0.4.1-dev/bin/llama-server \
  -m /mnt/model-storage/vision/Qwen3-VL-30B-A3B/Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.i1-IQ3_XS.gguf \
  --mmproj /mnt/model-storage/vision/Qwen3-VL-30B-A3B/Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.mmproj-Q8_0.gguf \
  -ngl all -c 32768 -np 8 \
  --host 0.0.0.0 --port 18080 --no-warmup
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

If `/slots` shows eight `n_ctx=4096` slots and health is OK, the running vision server matches the validated context profile. Verify launcher persistence separately. **Deployment confirmed by operator output 2026-10-13:** backup `/usr/local/bin/grace-vision-fast.pre-32k-20261013-101303`; launcher changed to `-c 32768 -np 8`; `bash -n` passed; `grace-vision.service` restarted; `/health` returned `ok`; `/slots` reported eight `n_ctx=4096`; `PRODUCTION_32K_PASS: True`; both `grace-vision.service` and `llama-server.service` active; GPU0 16022 MiB used / 248 MiB free after restart.

## Source of truth / change discipline

1. Read **this root file** and [model registry](docs/model-evaluations/README.md) first.
2. Consult [October 12 GPU campaign](docs/model-evaluations/results/2026-10-12-qwen3-vl-30b-gpu-campaign.md), [single-P100 retest](docs/model-evaluations/results/2026-10-12-qwen3-vl-30b-single-p100-retest.md), and [October 13 detailed baseline and failure log summaries](docs/model-evaluations/results/2026-10-13-huihui-p100-startup-baseline.md).
3. Preserve the 80B service and model/GPU allocation; back up launchers before edits, restart vision only, check service health and slots, and roll back on failure.
4. Production deployment was confirmed on 2026-10-13 as above. Future changes must update this file with the actual command, slot output, date and host evidence. Do not silently rewrite measured results or imply that uncommitted raw host logs are archived in GitHub.

**Raw-evidence caveat:** Some October 12 source archives and October 13 `/tmp` server logs are still on the host or were supplied in conversation, not committed as raw artifacts. GitHub records contain measured results and representative error excerpts, not every raw byte.


## Grace 'Open Eyes' on-demand loading

**Runbook:** [GRACE_OPEN_EYES_FAST_LOAD.md](docs/operations/GRACE_OPEN_EYES_FAST_LOAD.md). **Deployable script:** [scripts/grace-open-eyes.sh](scripts/grace-open-eyes.sh). This GitHub script is a version-controlled deployment artifact; it does **not** become installed on OCTO1 until copied there. The live systemd service and launcher are authoritative.

For a permitted operator/service account after installing the script on OCTO1: `sudo /usr/local/sbin/grace-open-eyes`. The script is idempotent, checks the live launcher for the approved context/slot flags and GPU UUID, verifies GPU0 is free before starting an unloaded service, waits for health and eight 4096-token slots, and does not touch the 80B service. The existing running vision service is checked rather than restarted. **Grace must not claim eyes are open until the command succeeds.** GPU0 handoff must be authorized by the resource scheduler; the script does not seize another worker's GPU.


## 2026-10-13 LAN binding repair — operator verified

**Operator-provided completed deployment output (14:51 EDT):** the network-only change was applied on `OCTOMINER1` (`eth0=192.168.1.160/24`), with timestamped backups, to the effective 80B systemd drop-in `/etc/systemd/system/llama-server.service.d/99-grace-brain.conf` and the vision launcher `/usr/local/bin/grace-vision-fast`. In each file, `--host 127.0.0.1` was replaced with `--host 0.0.0.0`, preserving all other arguments. Systemd was reloaded and both services restarted successfully.

**80B effective configuration:** `llama-server.service`, wrapper `/usr/local/bin/llama-server-octo1-known-good`, model `/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf`, `-ngl 999 -c 16384 -np 1 --fit off --host 0.0.0.0 --port 8080`; `CUDA_DEVICE_ORDER=PCI_BUS_ID`; `CUDA_VISIBLE_DEVICES=GPU-c2f0fffc-1e63-d3c5-bdb3-f103ec44d5b9,GPU-6785b322-899d-8eec-e817-31d83279a414,GPU-c0c253d2-ff9e-3121-f1f1-ba4990420a8c,GPU-7b1a4d4b-8593-d3b7-6cf9-480ff81ea013`. **Do not use the base unit's stale 65,536 context or 90-drop-in GPU0 assignment; the 99 drop-in wins.**

**Vision effective configuration:** `grace-vision.service`, `/usr/local/bin/grace-vision-fast`, pinned to `GPU-ace423ce-ae61-803e-0734-a907283efe54`, same Huihui i1-IQ3_XS GGUF and Q8 projector as above, `-ngl all -c 32768 -np 8 --host 0.0.0.0 --port 18080 --no-warmup`.

**Observed post-restart results:** `80B_LAN_READY: True`; `80B_CONTEXTS: [16384]`; `VISION_CONTEXTS: [4096,4096,4096,4096,4096,4096,4096,4096]`; `VISION_LAN_READY: True`; `ss -ltn` reported `0.0.0.0:8080` and `0.0.0.0:18080`; both services `active`. GPU0 P100 vision 16022 MiB used; GPU1 RTX4090 14 MiB; GPU2 RTX3060Ti 7425 MiB; GPU3/4/5 P100 13722/13564/13606 MiB used. Thus no observed GPU reassignment. The validation emitted unrelated snapd `RestartMode` and IPv6 warnings but completed.

**Still unverified:** HTTP requests from *Camrui* (`192.168.1.155`) or another LAN host, host firewall/router isolation, post-reboot survival, API authentication, Grace/Codex provider wiring. Next acceptance from Camrui: `Invoke-RestMethod http://192.168.1.160:8080/health` and `Invoke-RestMethod http://192.168.1.160:18080/health`; also verify `/v1/models` and actual inference. These inference ports are intended for trusted LAN access only; future internet traffic must use an authenticated gateway/reverse proxy, not public port forwarding.

**Backup filenames:** `/etc/systemd/system/llama-server.service.d/99-grace-brain.conf.pre-lan-20261013-145109`; `/usr/local/bin/grace-vision-fast.pre-lan-20261013-145109`.
