# Local AI Chat Worker Testing and Startup

Status: Provisional operational baseline, 2026-09-01.

This document is the recovery point for the local conversational/VLM worker experiments performed on the development RTX 4090 and OCTOMINER1 (`192.168.1.160`) with an RTX 3060 Ti 8 GB and Tesla P100 16 GB.

The immediate objective is not to freeze a permanent model architecture. It is to establish two usable local workers quickly enough to perform real work and evaluate whether mostly-local chat/coding is practical before the September 16 decision point. Models are replaceable; the startup and routing interfaces should remain stable.

## Current provisional topology

### Worker A — fast conversational worker

- Node: `OCTOMINER1`
- GPU: NVIDIA GeForce RTX 3060 Ti 8 GB (`CUDA_VISIBLE_DEVICES=0`)
- Model: `Qwen3VL-8B-Uncensored-HauhauCS-Aggressive-Q6_K.gguf`
- Mode: text-only; no mmproj loaded
- llama.cpp server port: `8094`
- Context: `16384`
- KV cache: `q8_0` K + `q8_0` V
- GPU layers: `999` (full offload requested)
- Bind: `0.0.0.0`
- Direct endpoint: `http://192.168.1.160:8094/v1/chat/completions`
- Proven VRAM residency: about `7470 MiB / 8192 MiB`
- Direct short-probe generation: about `41.36 tok/s`
- Role: provisional fast resident conversational engine.

This checkpoint is VL-capable by family, but the 3060 worker deliberately does not load the projector. Full VL on the same 8 GB card was too tight; text-only provides much better placement.

### Worker B — independent visual / second-opinion worker

- Node: `OCTOMINER1`
- GPU: Tesla P100-PCIE-16GB (`CUDA_VISIBLE_DEVICES=1`)
- Model: `adi-gemma3-12b-ablit-glm5.2-q4_k_m.gguf`
- Model family: Gemma 3 12B, abliterated/uncensored, GLM-5.2 distilled
- Vision projector: `mmproj-gemma3-12b-f16.gguf`
- Mode: full multimodal/VL
- llama.cpp server port: `8095`
- Context: `32768`
- KV cache: `q8_0` K + `q8_0` V
- GPU layers: `999` (full offload requested)
- Bind: `0.0.0.0`
- Direct endpoint: `http://192.168.1.160:8095/v1/chat/completions`
- Proven VRAM residency at 32K: about `10366 MiB` after load and `10492 MiB` after a short generation
- Direct generation: about `17.97 tok/s`
- Role: independent VLM, image understanding, second opinion, and cross-check worker.

The different model families are intentional. Qwen + Gemma gives a more useful independent cross-check/brainstorm pair than two closely related checkpoints that may share the same failure modes.

## OCTOMINER1 hardware proof

The installed llama.cpp build was proven to use both GPUs independently:

- RTX 3060 Ti: compute capability 8.6, 8192 MiB physical VRAM.
- Tesla P100-PCIE-16GB: compute capability 6.0, 16384 MiB physical VRAM.
- Driver observed during testing: `550.144.03`.
- llama.cpp build observed during testing: build `10615`, commit `f280b2698`.

A small Qwen2 3B Q4_K_M benchmark successfully ran full CUDA inference on each card individually:

- 3060 Ti: prompt processing ~3338 tok/s, generation ~94.2 tok/s.
- P100: prompt processing ~1529 tok/s, generation ~49.4 tok/s.

This eliminated the earlier suspicion that the P100/3060 combination required a driver upgrade merely because an Ollama matrix had failed.

## Chatability bake-off evidence

### GPT-OSS 20B

The first completed five-turn `chatability_harness.py` run used `gpt-oss:20b` on the development machine. It was extremely fast: roughly 158–168 output tok/s across the recorded turns. It completed the recovery probe and produced substantial useful content, but it tended toward long, highly structured answers rather than the desired low-friction conversational style.

Recorded examples include:

- turn 1: ~168.17 tok/s
- turn 2: ~167.58 tok/s
- turn 3: ~159.01 tok/s
- turn 4: ~157.56 tok/s
- recovery probe: ~158.31 tok/s

This remains an interesting fast worker/orchestrator candidate, but it was not selected as the provisional resident mouth.

### Qwen3.5 27B Abliterated Q4_K_M

`Qwen3.5-27B-abliterated-Q4_K_M.gguf` was registered in Ollama with 32K context and tested using the same multi-turn chatability fixture.

Observed generation was roughly 15–16 tok/s in the captured run, with very long TTFT on several turns (about 99–207 seconds). It understood the conversation and recovery correction, but the latency made it unattractive for the always-on conversational role compared with the smaller Qwen3-VL 8B candidate.

Representative metrics:

- turn 1: TTFT 107.0 s, 14.84 tok/s
- turn 2: TTFT 138.2 s, 16.25 tok/s
- turn 3: TTFT 99.4 s, 16.29 tok/s
- turn 4: TTFT 129.0 s, 16.22 tok/s
- recovery probe: TTFT 207.1 s, 15.25 tok/s

### Huihui Mistral Small 3.2 24B Abliterated Q5_K_M

`Huihui-Mistral-Small-3.2-24B-Instruct-2506-abliterated-v2-Q5_K_M.gguf` was registered as `mistral32-24b-abliterated` with 32K context and run through the same fixture.

It was faster and had much better warm-turn latency than the Qwen3.5 27B run, but it became very assistant-like: headings, numbered lists, many follow-up questions, and praise-heavy framing.

Representative metrics:

- turn 1: TTFT 24.1 s, 22.15 tok/s
- turn 2: TTFT 2.46 s, 21.95 tok/s
- turn 3: TTFT 3.02 s, 22.27 tok/s
- turn 4: TTFT 16.76 s, 17.03 tok/s
- recovery probe: TTFT 0.58 s, 19.65 tok/s

The recovery probe did return to the prior CAD discussion after correction, so contextual discrimination was useful even though style was too presentation-like.

## Qwen3-VL 8B placement experiments

Two local artifacts were available:

- `qwen3-vl-8b-instruct-q5_k_m.gguf` (~5.45 GB)
- `Qwen3VL-8B-Uncensored-HauhauCS-Aggressive-Q6_K.gguf` (~6.26 GB)

Matching vision projectors were also available locally.

### Q5 full-VL on RTX 3060 Ti

With the F16 projector loaded, the 8 GB 3060 Ti was too tight for useful larger contexts. The 8K attempt could generate at about 52.5 tok/s but emitted CUDA OOM diagnostics and occupied essentially the whole card. 16K failed during projector allocation; 32K failed allocating KV cache.

Conclusion: do not use the 3060 Ti as the full-VL home for this model.

### Q5 full-VL on P100

The same Q5 model + projector loaded successfully on the P100 at 8K, 16K, and 32K. Generation was about 29.5 tok/s in the short probes.

This proved the P100 can be a useful VL host despite its older Pascal architecture.

### Q5 text-only on RTX 3060 Ti

Removing the mmproj was the key placement discovery. With the same Qwen3-VL Q5 weights in text-only mode:

- 8K: ~52.5 tok/s generation; ~717 tok/s prompt processing.
- 16K: ~52.4 tok/s generation; ~719 tok/s prompt processing.

This established the architecture of using the 3060 as a fast text mouth and delegating vision to another worker.

### Chatability and decoding experiments

Longer multi-turn chatability tests showed a strong trained-in helpful-assistant/presentation style: frequent praise, repeated summaries, headings, many follow-up questions, and recurring rhetorical patterns.

One uncontrolled run catastrophically degenerated on turn 4 to about 6205 words over ~202.5 seconds, followed by an empty turn 5 response. The test plumbing was then corrected so the system prompt was unquestionably injected by the adapter and generation was bounded.

A later controlled adapter used:

- hard output cap (700–1200 tokens during different experiments)
- temperature ~0.35
- top-p ~0.90
- min-p ~0.08
- repeat penalty ~1.12
- repeat-last-n 512
- modest presence/frequency penalties
- DRY anti-repetition settings

These controls eliminated the catastrophic runaway but did not fully remove the presentation/helpful-assistant personality. Importantly, the model continued to understand conversation context and could distinguish pasted Hermes material from an assignment after correction.

Decision: this is good enough for provisional real-world use; do not spend days benchmarking or over-gating it before actual work provides better evidence.

## Qwen3-VL 8B Q6 placement experiments

The uncensored HauhauCS Q6 checkpoint was tested separately.

### P100 text-only

Q6 text-only loaded comfortably on the P100 at 16K and produced usable conversational performance. It did not materially solve the assistant-style personality problem, but it confirmed the checkpoint itself was viable.

### 3060 Ti text-only, ordinary KV

At 8K the Q6 loaded successfully at roughly `7379 MiB / 8192 MiB`. At 16K with the ordinary cache configuration it failed with a CUDA OOM while attempting a ~2304 MiB KV allocation.

### 3060 Ti text-only, Q8/Q8 KV

Changing only the KV cache to `q8_0` for both K and V made 16K fit cleanly:

- load VRAM: ~7469 MiB
- post-generation VRAM: ~7471 MiB
- short prompt: ~551 tok/s
- short generation: ~41.36 tok/s
- status: PASS

A subsequent five-turn harness completed against this exact 3060 Ti / Q6 / 16K / Q8-KV server configuration. The conversational style remained verbose/presentation-like, but the hardware placement and multi-turn continuity were sound enough for provisional service.

## Gemma 3 12B Abliterated full-VL P100 experiments

Selected model:

`adi-gemma3-12b-ablit-glm5.2-q4_k_m.gguf`

The model card describes it as Gemma 3 12B built on an abliterated base, distilled from GLM-5.2, uncensored/minimal-refusal, and vision-capable. The language GGUF is about 6.8 GB. The repository did not actually contain the advertised projector, so the official Gemma 3 12B F16 projector was used because the model author states the vision tower was preserved unchanged.

Local/remote projector name:

`mmproj-gemma3-12b-f16.gguf`

### 16K full-VL

Configuration:

- P100 only (`CUDA_VISIBLE_DEVICES=1`)
- 16K context
- Q8/Q8 KV cache
- full mmproj enabled
- port 8095

Results:

- loaded as a multimodal model
- ~9678 MiB P100 VRAM after load
- ~9868 MiB after an actual image request
- prompt processing ~99.23 tok/s on the image test
- generation ~17.81 tok/s
- image request ~6 seconds total

The controlled test image contained a blue square on the left, a red circle on the right, and the text `VISION TEST 42`. The model identified both shapes/colors/positions and read the text exactly. This is an actual image-understanding proof, not merely a metadata/load proof.

### 32K full-VL

The same model, projector, and Q8/Q8 KV cache were restarted at 32768 context.

Results:

- `RESULT=32K_LOAD_OK`
- model endpoint reported `n_ctx=32768`, training context 131072
- P100 VRAM after load: ~10366 MiB
- P100 VRAM after short generation: ~10492 MiB
- short generation: ~17.97 tok/s
- dev-machine health check: PASS

Decision: 32K full-VL is the provisional P100 configuration. There is no need to push context further before real use.

## Why the two-worker split exists

The provisional architecture is deliberately asymmetric:

```text
Steward / resident conversation
        |
        +--> Qwen3-VL 8B Q6 / 3060 Ti / text-only / 16K
        |       fast conversational response
        |
        +--> Gemma 3 12B Abliterated / P100 / full-VL / 32K
                vision, independent cross-check, second opinion
```

A resident using the fast Qwen worker can delegate visual inspection or ask the Gemma worker for an independent view. The two different model families reduce correlated mistakes and make brainstorming/cross-checking more useful.

The RTX 4090 remains free for heavier reasoning, coding, engineering, or overflow work rather than being consumed by routine resident conversation.

## Operational philosophy

This is a provisional baseline, not a permanent model decision.

- New models and quantization/runtime improvements are expected.
- Prefer stable interfaces and replaceable checkpoints.
- Do not require hundreds of synthetic tests before use.
- Five-turn harnesses are smoke tests, not proof of long-term conversational quality.
- Learn from normal daily work and replace a model when real usage shows a better candidate is needed.
- Keep mechanical controls (context, KV precision, output limits) separate from personality steering.
- Do not recreate a large gate stack merely to force a checkpoint into a preferred conversational personality.

## Startup artifacts

Individual startup templates:

- `tools/local-ai/Start-Octominer1-Qwen3060Chat.ps1`
- `tools/local-ai/Start-Octominer1-GemmaP100VL.ps1`

Combined startup template:

- `tools/local-ai/Start-Octominer1-ChatWorkers.ps1`

Each script is intended to be recoverable from GitHub and runnable from the canonical Riverview checkout. The combined script wakes OCTOMINER1 when necessary, waits for SSH, and starts both provisional workers.

## Expected endpoints after startup

- Qwen conversational worker health: `http://192.168.1.160:8094/health`
- Qwen OpenAI-compatible chat: `http://192.168.1.160:8094/v1/chat/completions`
- Gemma VLM health: `http://192.168.1.160:8095/health`
- Gemma OpenAI-compatible chat/VL: `http://192.168.1.160:8095/v1/chat/completions`

These direct endpoints are provisional testing/recovery interfaces. Future Riverview/Residential Gateway/Stream Deck integration may wrap or replace them without changing the model-placement findings in this report.
