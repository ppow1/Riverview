# October 11 2026 Qwen 80B GPU campaign — exact reproduction record

**Campaign finished:** 2026-10-11 18:05:11 EDT. **Host:** `ssh octo1` (reported OCTOMINER2). **Model:** `/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf`, 48,410,988,384 bytes. **Service:** `llama-server.service`, localhost port 8080.

## Exact operator commands
```powershell
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\riverview_80b_campaign.ps1"
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\riverview_80b_monitor.ps1"
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\riverview_80b_resume_uuid.ps1"
ssh octo1 "ps -p 2733269 -o pid=,stat=,args="
ssh octo1 "tail -n 25 /root/80b-gpu-campaign/run-20261011-170737/monitor.txt"
```

**Important:** Do not run launch scripts to collect evidence; they modify service GPU allocations and start benchmarking. Original scripts exist in the separately generated local documentation ZIP and need byte-preserving upload to this repository.

## Exact benchmark request and controller behavior, as documented in original local source
- Endpoint: `POST http://127.0.0.1:8080/completion`.
- Prompt verbatim: `Explain transformer inference, attention, KV caching, and autoregressive token generation in technical detail.`
- Request fields: `prompt`, `n_predict=256`, `temperature=0`, `seed=42`, `cache_prompt=False`, `stream=False`.
- Per-config tests: cold, warm, warm2 (one request each), then concurrency 2, 3, 4, stopping escalation on failure.
- Parallel calls: Python `concurrent.futures.ThreadPoolExecutor(max_workers=n)`.
- Per-request generation speed: response `timings.predicted_per_second`.
- Aggregate throughput: sum of `tokens_predicted` divided by group wall-clock duration.
- Readiness: `GET /health` with status `ok`; polling every 4 seconds, max 150 attempts (~600s).
- Service change: stop `llama-server.service`; write `/etc/systemd/system/llama-server.service.d/80b-campaign.conf`; `systemctl daemon-reload`; start service; validate excluded GPU memory growth <=256 MiB.
- UUID override: `Environment="CUDA_DEVICE_ORDER=PCI_BUS_ID"` and `Environment="CUDA_VISIBLE_DEVICES=<comma-separated GPU UUIDs>"` in a `[Service]` systemd drop-in.
- Completion: stop service, remove temporary override, daemon-reload, start original service, write `CAMPAIGN_FINISHED`. The marker confirms restoration started, not readiness.

## GPU physical mapping
| Physical index | GPU | UUID |
|---:|---|---|
| 0 | P100 16GB | `GPU-ace423ce-ae61-803e-0734-a907283efe54` |
| 1 | RTX 4090 24GB | `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` |
| 2 | RTX 3060 Ti 8GB | `GPU-c2f0fffc-1e63-d3c5-bdb3-f103ec44d5b9` |
| 3 | P100 16GB | `GPU-6785b322-899d-8eec-e817-31d83279a414` |
| 4 | P100 16GB | `GPU-c0c253d2-ff9e-3121-f1f1-ba4990420a8c` |
| 5 | P100 16GB | `GPU-7b1a4d4b-8593-d3b7-6cf9-480ff81ea013` |

## Runs and evidence
- Original `/root/80b-gpu-campaign/run-20261011-163811`: A1–A3 accepted. First B1 had wrong GPU ordinal isolation and is **excluded**.
- UUID-corrected `/root/80b-gpu-campaign/run-20261011-170737`: B1–D2 accepted. Controller PID reported `2733269`, exited. Finished 18:05:11 EDT.
- Initial-run concurrency evidence: `A1-concurrency-2-evidence.log`, `A2-concurrency-2-evidence.log`, `A3-concurrency-2-evidence.log`.
- Corrected-run failure evidence: `C1-concurrency-2-evidence.log`, `C2-concurrency-2-evidence.log`, `C3-load-evidence.log`, `D2-load-evidence.log`.
- D1 loaded GPU VRAM: GPU0 13,746 MiB; GPU3 12,320; GPU4 12,320; GPU5 12,198; GPU1 14; GPU2 12.

## Critical reproducibility caveats
The full original controller and PowerShell script source, remote `results.jsonl`, logs, service journal, exact binary version, CUDA/driver versions, model SHA, and full service unit must be archived from the source host. The precise commands above identify launcher invocations, but **do not alone make the run reproducible**. No CUDA OOM or GPU defect diagnosis should be asserted until evidence logs are reviewed.

The ranked results, interactive visual and per-run evidence summaries are linked from [the registry index](README.md). The October 11 test establishes execution and throughput, not task-quality qualification.
