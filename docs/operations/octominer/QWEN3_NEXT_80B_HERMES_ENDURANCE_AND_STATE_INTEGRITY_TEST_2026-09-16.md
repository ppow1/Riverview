<!--
File: docs/operations/octominer/QWEN3_NEXT_80B_HERMES_ENDURANCE_AND_STATE_INTEGRITY_TEST_2026-09-16.md
Date: 2026-09-16
Status: Evidence record / current findings
-->
# Qwen3-Next 80B + Hermes Endurance and State-Integrity Test — 2026-09-16

## Purpose

Record the 2026-09-16 local-inference and Hermes endurance experiment conducted before returning the RTX 4090 from OCTOMINER1 to the development machine. This document preserves the observed topology, model/server performance, Hermes remote-model/tool behavior, long-context failure mode, reboot/watchdog findings, and the direct-80B control experiment that was started afterward.

This is an evidence record. It intentionally distinguishes direct observations from architectural interpretation.

## Physical topology used for the test

### OCTOMINER1 — inference node

- Hostname: `OCTOMINER1`
- Management IP: `192.168.1.160`
- Management NIC MAC: `00:e0:4c:6b:05:a9`
- GPUs during the test:
  - GPU 0: Tesla P100-PCIE-16GB — `16384 MiB`
  - GPU 1: Tesla P100-PCIE-16GB — `16384 MiB`
  - GPU 2: NVIDIA GeForce RTX 4090 — `24564 MiB`
- Aggregate physical VRAM: approximately 56 GB.

### OCTOMINER2 — Hermes/tool node

- Hostname: `OCTOMINER2`
- Management IP: `192.168.1.162`
- Management NIC MAC: `00:e0:4c:53:9e:5e`
- Hermes Agent installed and used here during the endurance test.

The two machines were not treated as one shared VRAM pool. Hermes executed tools on OCTOMINER2 while the language-model inference requests were sent across the LAN to OCTOMINER1.

## Model and llama.cpp server

Model:

`/mnt/octo-models/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf`

Observed model/server metadata:

- model: `Qwen3-Next-80B-A3B-Instruct-Q4_K_M`
- quantization: `Q4_K - Medium`
- parameter count exposed by `/v1/models`: `79674391296`
- GGUF size exposed by `/v1/models`: `48405005312` bytes
- configured server context: `65536`
- model training context exposed by server: `262144`
- server executable: `/root/llama.cpp/build/bin/llama-server`
- API port: `8096`
- API base: `http://192.168.1.160:8096/v1`

Server launch used during the Hermes test:

```text
/root/llama.cpp/build/bin/llama-server \
  -m /mnt/octo-models/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf \
  -ngl 999 \
  -c 65536 \
  --host 0.0.0.0 \
  --port 8096
```

Representative loaded VRAM state during the 64K run:

- P100 #0: about `15672 MiB`
- P100 #1: about `14228 MiB`
- RTX 4090: about `20181 MiB`

## Model-drive mount issue discovered and corrected

Model SSD:

- device: `/dev/sda1`
- label: `OCTO_MODELS`
- UUID: `8ce9956b-5316-45cd-989b-3a4f3b6f9b1c`
- intended mount: `/mnt/octo-models`

At first boot validation, the SSD existed and was healthy but `/mnt/octo-models` was not mounted automatically and there was no persistent model-drive entry in `/etc/fstab`.

The following entry was added:

```text
UUID=8ce9956b-5316-45cd-989b-3a4f3b6f9b1c /mnt/octo-models ext4 defaults,nofail 0 2
```

Manual mount then succeeded and the approximately 46 GB GGUF became visible. At the time of the initial evidence packet, current mount was VERIFIED and the fstab entry was CONFIGURED; reboot persistence had not yet been independently accepted from that evidence alone.

## Direct llama.cpp performance before Hermes

Observed generation measurements included:

- `49.6 t/s`
- `50.5 t/s`
- `50.5 t/s`
- `50.1 t/s`
- `50.0 t/s`
- `49.7 t/s`
- `49.4 t/s`

Prompt processing improved substantially on repeated/warm work and reached hundreds of tokens per second. The split 4090 + 2x P100 configuration was therefore unexpectedly strong for this 80B MoE workload.

During later very-large-context Hermes traffic, generation remained roughly `44–49 t/s` rather than collapsing.

## Hermes installation used

On OCTOMINER2:

- Hermes Agent: `v0.21.2 (2026.9.11)`
- upstream identifier shown: `8c3a35b6`
- install directory: `/usr/local/lib/hermes-agent`
- install method: `git`
- Python: `3.11.16`
- OpenAI SDK: `2.24.0`

Hermes was configured with a custom OpenAI-compatible endpoint:

- display name: `OCTO1 Qwen3-Next 80B 64K`
- base URL: `http://192.168.1.160:8096/v1`
- model: `/mnt/octo-models/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf`
- context length: `65536`
- API mode: `chat_completions`
- reasoning disabled for this model in Hermes configuration.

## Remote-model path acceptance test

A small grounded tool-use test asked Hermes to use its terminal tool to run `hostname` and `date`, then answer only from the tool results.

Hermes returned:

```text
hostname: OCTOMINER2
date: Wed Sep 16 01:07:28 PM EDT 2026
```

Independent node checks established:

- Hermes process was running on OCTOMINER2 / `192.168.1.162`.
- llama.cpp 80B server was running on OCTOMINER1 / `192.168.1.160:8096`.
- OCTOMINER1 server logs showed real inference tasks corresponding to the Hermes request, including a large prompt and a follow-up request after the tool result.

Therefore the accepted observed path was:

```text
Hermes/tool execution on OCTOMINER2 (.162)
        -> LAN OpenAI-compatible request
Qwen3-Next 80B on OCTOMINER1 (.160:8096)
        -> model requests tool action
Hermes executes terminal tool on OCTOMINER2
        -> tool result returned to OCTOMINER1 80B
        -> final model answer returned through Hermes
```

This proved that Hermes was not merely answering with an OCTOMINER2-local model during that test.

## Long-running Hermes endurance experiment

Hermes was then given a deliberately broad read-only audit objective covering system identity, hardware, Hermes installation/configuration, current model-provider path, other local AI endpoints, tools, skills, processes/network, cross-checking, and a final evidence-based report.

The prompt contained an explicit objective-continuity requirement: model-response boundaries and tool-call boundaries were not to be treated as objective completion.

### Positive behavior observed

Hermes successfully:

- performed many real terminal and file-inspection tool calls;
- repeatedly returned to the 80B for additional reasoning;
- kept working across many model/tool cycles;
- reached large prompt sizes while the 80B continued processing normally;
- compacted context and continued instead of immediately abandoning the objective;
- persisted a session that could later be resumed after OCTOMINER2 rebooted.

The original session ID was:

`20260916_130508_e7a83b`

On later recovery Hermes reported the same session as resumed with `106 total messages`.

### Context growth and compaction

The Hermes working context was configured at about `65.5K` tokens. During the audit, the visible context climbed through approximately:

- 19K / 65.5K
- 41K / 65.5K
- 50K / 65.5K
- 53K / 65.5K

Hermes then repeatedly compacted/summarized earlier conversation state. It explicitly reported:

```text
Session compressed 2 times - accuracy may degrade.
Session compressed 3 times - accuracy may degrade.
Session compressed 4 times - accuracy may degrade.
```

Hermes also repeatedly revisited skill files and reference material. The long task therefore consumed far more time and context than intended. This was scope/orchestration inefficiency even before the later state-integrity failure became visible.

## 80B behavior under very large Hermes requests

The OCTOMINER1 monitor showed the model continuing to process very large prompts and long outputs.

Representative observations included:

- prompt states exceeding 50K tokens;
- a request with approximately `50523` prompt tokens;
- generation remaining around `44–49 t/s` at large context;
- one observed long generation exceeding 6K generated tokens before cancellation;
- prompt ingestion typically in the hundreds of tokens per second.

At one point llama.cpp reported:

```text
failed to prepare attention ubatches
failed to find a memory slot for batch of size 2048
failed to find free space in the KV cache, retrying with smaller batch size
```

The server recovered and continued. This was a real KV-cache/batch-memory pressure event, not a server crash.

The 64K server had multiple slots, and the experiment showed that large Hermes requests could put meaningful pressure on prompt/KV-cache management. This should be treated separately from Hermes's own conversation-compaction behavior.

## OCTOMINER2 reboot during the endurance run

OCTOMINER1 uptime later showed boot time:

`2026-09-16 11:46:08`

OCTOMINER2 showed boot time:

`2026-09-16 13:58:54`

Thus OCTOMINER2 genuinely rebooted while OCTOMINER1 remained online.

The saved Hermes session was subsequently resumed successfully, demonstrating useful session durability across a host reboot.

## Watchdog/reboot evidence

Hive software watchdog evidence:

```text
WD_ENABLED=0
Watchdog disabled in config (/hive-config/rig.conf)
```

Linux watchdog evidence:

- device identity: `iTCO_wdt`
- state: `inactive`

Octominer controller evidence:

- `Watch-Dog Mode: 2`
- `Reset Counter = 27`
- short timeout: `120s`
- long timeout: `732s`

The hardware-controller watchdog is therefore present and has historical reset counts, but the evidence collected does **not** prove that reset counter 27 corresponds to the reboot observed during this test.

Accepted status:

- Hive software watchdog caused the reboot: NOT SUPPORTED.
- Octominer hardware watchdog involvement: POSSIBLE, NOT PROVEN.
- Exact reboot cause: UNKNOWN.

The controller query also exposed useful real PSU telemetry. At the captured idle/light-load state, the three PSUs reported approximately 72/73 W, 20 W, and 83/84 W AC respectively, roughly 175–177 W aggregate AC input at that moment.

## Critical Hermes state-integrity failure

After several context compactions, interruption, reboot, session resume, and continuation, Hermes produced a final report that confidently asserted a different machine/runtime state and marked those claims VERIFIED.

Examples of claims in the final Hermes report that conflict with the directly established test environment included:

- OCTOMINER2 IP `10.10.10.50` instead of `192.168.1.162`;
- MAC `00:11:22:33:44:55` instead of `00:e0:4c:53:9e:5e`;
- GPU `GTX 1080` with `8119 MiB` instead of the established current topology;
- Hermes version `1.8.4-ubuntu22` instead of v0.21.2;
- Hermes path `/opt/hermes` instead of `/usr/local/lib/hermes-agent`;
- `.deb` installation instead of `git`;
- `/etc/hermes/config.yaml` instead of the actual Hermes configuration path used in this test;
- provider/model `openai` / `gpt-4o-80b` instead of the configured remote Qwen3-Next endpoint;
- context `32768` instead of `65536`;
- model server `127.0.0.1:5000` instead of remote `192.168.1.160:8096`;
- API endpoint `https://api.hermes.internal/v1` instead of `http://192.168.1.160:8096/v1`.

Despite these contradictions, Hermes stated that no claim had been made without direct evidence and declared the objective `COMPLETE`.

This is the most important negative result of the test.

### Current interpretation

The evidence does **not** prove that Qwen3-Next 80B itself originated the false state. The long-running failure occurred after repeated Hermes context compaction and later session recovery/resume. The failed final report therefore demonstrates a breakdown in trustworthy state/evidence preservation across the complete Hermes orchestration path.

Accepted current classification:

- Qwen3-Next 80B inference/endurance performance: STRONG / PASSED OBSERVED LOADS.
- Hermes ability to call the remote model and execute tools: VERIFIED.
- Hermes session persistence/resume: VERIFIED.
- Hermes long-running factual-state integrity after repeated compaction/resume: FAILED.
- Source of the corrupted state specifically inside the 80B model: NOT PROVEN.

## Architectural implication for Riverview

The experiment reinforces an existing Riverview design rule: conversation memory must not be authoritative operational state.

PROPOSED architecture boundary:

```text
Riverview objective/state controller = authority
Hermes = tool/execution shell
Qwen3-Next 80B = reasoning engine
persistent structured evidence ledger = durable truth/state boundary
```

The durable layer should own at minimum:

- objective identity and acceptance criteria;
- completed/pending steps;
- evidence pointers;
- claim state (`UNKNOWN`, `CONFIGURED`, `VERIFIED`, `INVALIDATED`, etc.);
- approval gates;
- retries/recovery state;
- explicit provenance for every promotion to VERIFIED.

A model or compaction summary should not be able to promote a claim to VERIFIED without attached evidence.

Raising model/Hermes context may reduce compaction frequency but does not by itself solve authoritative-state corruption.

## Direct 80B sealed-evidence control experiment

Before removing the RTX 4090, a control test was started directly against:

`http://192.168.1.160:8096/v1/chat/completions`

Hermes was explicitly excluded from this control.

The control supplied a sealed authoritative evidence packet plus the contradictory claims from the failed Hermes report and instructed the 80B to classify contradictions without tools, context compaction, or session recovery.

Observed server activity for this direct control showed a new request (`task 53234`) with approximately 3.1K prompt tokens processed at roughly 350 tokens/sec during the captured monitor interval. The Steward reported the control response time as approximately 90 seconds.

The final textual result of that sealed-evidence control was not yet captured into this record at the moment this document was created. Do not infer its verdict from the timing alone. Append the model's actual output before using this control as proof of model-vs-Hermes fault isolation.

## Current decision point

The RTX 4090 is planned to return to the development machine after this control experiment.

The split 4090 + 2x P100 result was substantially better than expected and should remain a serious reference topology for future large local MoE inference work.

The next orchestration work should focus on externally authoritative objective/evidence state and on proving continuity through deliberate context exhaustion, interruption, reboot, and resume without allowing summarized conversational state to become evidence.
