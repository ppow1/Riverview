# Grace Open Eyes — fast on-demand vision reload (OCTO1)

**Purpose:** When Grace needs image processing and the vision model has been intentionally unloaded from the dedicated Tesla P100, restore the **already-deployed** validated Huihui 30B model without changing parameters, moving GPUs, or touching the 80B worker.

**Authoritative startup reference:** [CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md](../../CURRENT_RIVERVIEW_AI_MODEL_STARTUP_CONFIGURATION.md). **Implementation artifact:** [scripts/grace-open-eyes.sh](../../scripts/grace-open-eyes.sh). **Evidence:** [October 13 full validation](../model-evaluations/results/2026-10-13-huihui-p100-startup-baseline.md).

## Confirmed production state — 2026-10-13

Operator completed production deployment. Backup: `/usr/local/bin/grace-vision-fast.pre-32k-20261013-101303`. Changed existing `/usr/local/bin/grace-vision-fast` to `-c 32768 -np 8`; `bash -n` passed; `grace-vision.service` restart passed; `/health` was `ok`; `/slots` showed **8 slots, each n_ctx=4096**; `PRODUCTION_32K_PASS: True`. Both vision and 80B services `active`; GPU0 used **16022 MiB** and had **248 MiB free** at ready. This is a real production deployment confirmation, **not** merely a target.

## Fast reload command

Once the version-controlled helper has been installed on the host:

```bash
sudo /usr/local/sbin/grace-open-eyes
```

For a one-off operator reload *before* installing the helper, when GPU0 has been explicitly released and is free:

```bash
sudo systemctl start grace-vision.service
curl -fsS http://127.0.0.1:18080/health
curl -fsS http://127.0.0.1:18080/slots
```

**Do not use `restart` to open eyes**: `start` is idempotent and avoids disrupting a healthy running model. A systemd start loads the existing persistent launcher, which pins the model and projector to P100 UUID `GPU-ace423ce-ae61-803e-0734-a907283efe54` with `-c 32768 -np 8 -ngl all --no-warmup` and binds port `127.0.0.1:18080`.

## Installation (one-time, operator-authorized)

```bash
sudo install -o root -g root -m 0755 scripts/grace-open-eyes.sh /usr/local/sbin/grace-open-eyes
```

This assumes the repo has been checked out on the host and the command is run from its root. **The GitHub commit does not install the helper on OCTO1**. The helper requires bash, Python 3, `flock`, `systemctl`, `nvidia-smi`, and existing localhost vision API access. Test with an already-running service first; then separately verify stopped-service loading during an authorized GPU handoff. The helper uses a 60-second bounded readiness wait and refuses to seize GPU0 if it detects an existing GPU compute process. Its checks are best-effort; actual GPU ownership should be arbitrated by Riverview's resource scheduler. Do not grant arbitrary model-management commands to Grace.

## Grace orchestration contract

1. Grace requests the **vision capability**, not arbitrary root shell execution.
2. The resource manager confirms GPU0 has been released for vision, or reports **busy**. No forced kill of competing workloads.
3. An approved privileged executor invokes the fixed helper command, with no user-controlled shell arguments. The service account must have a narrowly scoped sudoers/polkit permission, if delegated; do not grant general passwordless sudo.
4. On exit 0 and `OPEN_EYES_READY: true`, Grace may submit image requests to `127.0.0.1:18080`.
5. On any nonzero exit, Grace must report unavailable/busy and preserve the 80B worker; no blind repeated restart loops.

The helper verifies a running service and checks its `/health` and `/slots` endpoints; if stopped, it verifies the pinned GPU UUID, checks for GPU compute-process conflicts, starts the systemd service, and waits for correct health/slots. **It does not automatically unload vision**. The separate 'close eyes' / GPU-release policy must be authorized and documented before automation. A manual `systemctl stop grace-vision.service` should occur only after a deliberate release decision.

## Performance and boundaries

- Tested startup: **5.865–5.93 seconds** (model readiness; not a guaranteed service SLA).
- Eight simultaneous text prompts of 3336 tokens: **8/8 passed**; batch **74.481 seconds**.
- Eight simultaneous small PNG image requests: **8/8 correct**, batch **31.77 seconds**.
- Peak GPU0 use sampled **16126 MiB**; minimum free **144 MiB**. This configuration has **minimal memory headroom**.
- 64K/8-slot configurations failed with CUDA OOM; **do not change to 64K**.
- The test images were 128×128 synthetic shapes; large-image endurance remains unverified.

## Diagnostics and recovery

```bash
sudo systemctl status grace-vision.service --no-pager
sudo journalctl -u grace-vision.service -n 80 --no-pager
sudo sed -n '1,180p' /usr/local/bin/grace-vision-fast
curl -fsS http://127.0.0.1:18080/health
curl -fsS http://127.0.0.1:18080/slots
nvidia-smi --query-gpu=index,name,uuid,memory.used,memory.free --format=csv
sudo systemctl is-active llama-server.service
```

Last confirmed pre-deployment backup: `/usr/local/bin/grace-vision-fast.pre-32k-20261013-101303`. Restore it only as an explicit rollback decision, not as part of normal Open Eyes operation.

**Documentation status:** The GitHub helper is written but its installation and Grace's integration with a privileged executor are **not yet verified**. The existing `grace-vision.service` and launcher are deployed and healthy. Do not claim Grace has an automated Open Eyes action until the helper is installed and the orchestrator actually invokes it.
