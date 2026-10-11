# UUID-corrected run: B1–D2

# October 11, 2026 — Qwen3-Next-80B-A3B-Instruct Q4_K_M GPU allocation benchmark

**Status:** benchmark completed at 2026-10-11 18:05:11 EDT. **Qualification:** measured inference speed and concurrency only; reasoning quality and vision capability NOT qualified by this run.

## Model and hardware
- Model file observed: `/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf`; 48,410,988,384 bytes (earlier inspection). Model hash and upstream revision not yet captured.
- Host: `octo1` SSH alias (OCTOMINER2 service host); physical GPUs: 0 P100 16GB, 1 RTX 4090 24GB, 2 RTX 3060 Ti 8GB, 3/4/5 P100 16GB.
- UUIDs: GPU0 `GPU-ace423ce-ae61-803e-0734-a907283efe54`; GPU1 `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2`; GPU2 `GPU-c2f0fffc-1e63-d3c5-bdb3-f103ec44d5b9`; GPU3 `GPU-6785b322-899d-8eec-e817-31d83279a414`; GPU4 `GPU-c0c253d2-ff9e-3121-f1f1-ba4990420a8c`; GPU5 `GPU-7b1a4d4b-8593-d3b7-6cf9-480ff81ea013`.
- Initial A-series run: `/root/80b-gpu-campaign/run-20261011-163811`; corrected UUID-isolated B/C/D run: `/root/80b-gpu-campaign/run-20261011-170737`. Original B1 from first run was not accepted due to CUDA ordinal/physical index mismatch.
- Final controller log: `2026-10-11T18:05:10 LOAD D2 ready=False seconds=600.71`, `2026-10-11T18:05:10 SKIP D2 load timeout/failure`, `2026-10-11T18:05:11 RESTORE_STARTED`, `2026-10-11T18:05:11 CAMPAIGN_FINISHED`.
- Original service observed `ActiveState=active` and `SubState=running` at 18:08; this does not alone establish inference readiness.

## Reproduction: commands actually observed

```powershell
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\riverview_80b_resume_uuid.ps1"
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\riverview_80b_monitor.ps1"
ssh octo1 "ps -p 2733269 -o pid=,stat=,args="
ssh octo1 "tail -n 25 /root/80b-gpu-campaign/run-20261011-170737/monitor.txt"
```

**Exact reproducibility limitation:** These are the observed invocation commands. The original launcher/controller source, prompts, sampling settings, service unit/arguments, and benchmark evidence must be collected from the host and archived. The local documentation package previously generated in the conversation contains copies of PowerShell launchers and a collector; these files are not automatically available to the GitHub connector. Do not invent omitted parameters or claim bitwise reproducibility until those artifacts are uploaded and checked.

## Raw evidence to preserve
- A-series concurrency failure: `run-20261011-163811/A1-concurrency-2-evidence.log`, `A2-concurrency-2-evidence.log`, `A3-concurrency-2-evidence.log`.
- Corrected run: `run-20261011-170737/C1-concurrency-2-evidence.log`, `C2-concurrency-2-evidence.log`, `C3-load-evidence.log`, `D2-load-evidence.log`.
- D1 GPU VRAM at load: GPU0 13,746 MiB; GPU3 12,320; GPU4 12,320; GPU5 12,198; GPU1 14; GPU2 12.
- Failure reasons remain unconfirmed until inspecting evidence. Concurrency FAIL is not proof of a 3060 Ti hardware defect.

## Rankings: generation first, then concurrency

| Rank | ID | GPUs | Warm2 generation tok/s | 4-way aggregate tok/s | Concurrency result |
|---:|---|---|---:|---:|---|
| 1 | A3 | 4090 + 3060 Ti + 2 P100 | 45.86 | — | 2 failed |
| 2 | B3 | 4090 + 2 P100 | 44.58 | 70.419 | 4 passed |
| 3 | A2 | 4090 + 3060 Ti + 3 P100 | 41.46 | — | 2 failed |
| 4 | B2 | 4090 + 3 P100 | 40.92 | 65.348 | 4 passed |
| 5 | A1 | 4090 + 3060 Ti + 4 P100 | 39.04 | — | 2 failed |
| 6 | B1 | 4090 + 4 P100 | 38.61 | 64.136 | 4 passed |
| 7 | C2 | 3060 Ti + 3 P100 | 34.37 | — | 2 failed |
| 8 | C1 | 3060 Ti + 4 P100 | 33.63 | — | 2 failed |
| 9 | D1 | 4 P100 only | 32.25 | 54.82 | 4 passed |
| 10 | C3 | 3060 Ti + 2 P100 | not loaded | — | load timeout |
| 11 | D2 | 3 P100 only | not loaded | — | load timeout |

**Interpretation:** B3 is the fastest four-request tested setup at 70.419 aggregate tok/s; A3 has the fastest single-request speed (45.86) but failed concurrency 2. D1 achieves four-request concurrency using P100s only, freeing the RTX GPUs. Four-way aggregate includes request overhead and is not equivalent to the sum of per-request generation speeds. C3/D2 never reached inference.

## Best configurations by intended use
1. **Fastest proven 4-way worker: B3**, 4090 + 2 P100, 44.58 warm2 generation, 70.419 four-way aggregate.
2. **Fastest single request: A3**, 4090 + 3060 Ti + 2 P100, 45.86; unsuitable for the measured two-way workload.
3. **RTX-free 4-way worker: D1**, 4 P100, 32.25 warm2, 54.82 four-way aggregate.
4. **3060 Ti-based single worker: C2**, 3060 Ti + 3 P100, 34.37; concurrency 2 failed.

**Disposition:** retain benchmark as performance baseline; retest concurrency failure modes after evidence review; do not mark the model as task-quality qualified.


## Concurrency 2 / 3 / 4 aggregates (tok/s)

| ID | 2 | 3 | 4 |
|---|---:|---:|---:|
| B1 | 53.439 | 57.718 | 64.136 |
| B2 | 57.719 | 62.815 | 65.348 |
| B3 | 61.887 | 64.911 | 70.419 |
| C1 | FAIL | — | — |
| C2 | FAIL | — | — |
| C3 | LOAD TIMEOUT | — | — |
| D1 | 46.429 | 50.441 | 54.82 |
| D2 | LOAD TIMEOUT | — | — |

D1 per-request speeds at concurrency 4: [16.57,16.57,16.57,16.57]. B3 per-request speeds at concurrency 4: [21.87,21.87,21.87,21.87].