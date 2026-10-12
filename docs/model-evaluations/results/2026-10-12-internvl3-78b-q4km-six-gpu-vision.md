# InternVL3-78B Q4_K_M — six-GPU vision qualification — 2026-10-12

## Decision

**Execution: PASS at 4K. Task quality: FAIL on required visual measurement/proportion work. Disposition: NOT QUALIFIED as Grace's primary screenshot/vision specialist in the tested configuration.**

**Principal failure: THE MODEL DID NOT DO WHAT IT WAS ASKED TO DO.** The user explicitly permitted approximate estimates; the model repeatedly substituted general descriptions or statements about measurement uncertainty for the requested measurements. Do not reclassify generic image recognition as task success, or quietly change the acceptance test after the failure.

## Test setup

- Host: OCTOMINER2 (SSH alias `octo1`).
- GPUs: four Tesla P100 16 GB, RTX 4090 24 GB, RTX 3060 Ti 8 GB; six-way model split, approximately 55 GB allocated in the observed 4K configuration.
- Model: `/opt/model-library/vision/InternVL3-78B-Q4KM/InternVL3-78B.Q4_K_M.gguf` (about 47.4 GB).
- Multimodal projector: `/opt/model-library/vision/InternVL3-78B-Q4KM/InternVL3-78B.mmproj-Q8_0.gguf` (about 6.08 GB).
- Runtime: `/opt/llama.cpp/build-octo1-0.4.1-dev/bin/llama-server`, build identifier reported by `/props`: `b10987-d1d3c3396`.
- Service: `internvl3-vision.service`, `-ngl all --fit off -sm layer -c 4096 -np 1 --host 127.0.0.1 --port 18080 --no-warmup`. Library-path drop-in preserved at `/etc/systemd/system/internvl3-vision.service.d/library-path.conf`.
- Windows browser reached the service through SSH forwarding on local port 18081.
- Interactive generation approximately 6 tokens/second; model loading approximately 5–6 minutes.

## Test A — engineering drawing

- Synthetic connector/cavity drawing; model recognized flange width 45 mm versus cavity width 40 mm and noted missing clearances for diagonal insertion and rotation. This demonstrated some useful perception, **not a verified feasible assembly solution**.
- First detailed response stopped mid-sentence at 255 generated tokens. Another response stopped at 166 generated tokens.
- Server log: `slot release: n_tokens = 4095, truncated = 1` following 255-token generation; `prompt eval ... 3620 tokens`.
- Follow-up requests explicitly failed: `request (4137 tokens) exceeds ... context size (4096 tokens)` and separately 4107 versus 4096.
- `/props` showed default `max_tokens = -1` and `n_predict = -1`. Evidence points to context exhaustion, not a universal 256-output-token cap.
- In a fresh chat, a short four-part drawing prompt produced a complete ~265-token response. A second-turn geometry explanation again ended mid-sentence after ~69 tokens. **4K is not adequate for sustained image-based conversation in this configuration.**

## Test B — Evelyn synthetic character visual canon (decisive task failure)

- Input: side-by-side studio renderings labeled “Original Canon” and “Qwen Edit,” with different clothing.
- User supplied height 5 ft 1 in and requested estimated measurements; explicitly requested best-effort approximations after the model declined. InternVL repeatedly declined to estimate.
- A subsequent, explicitly bounded character-design task asked for five normalized visual proportions using character height = 100%: **shoulder width, waist width, hip width, leg length, head-to-body height ratio**, plus approximate percentages/ratios and identification of clothing-obscured dimensions. The model did **not provide the requested quantitative results** in the observed exchange. It offered generic scene descriptions and continued descriptions instead.
- **Acceptance result: FAIL — 0/5 requested proportions delivered.** User did not ask for precise physical measurements; estimates and uncertainty qualifications were explicitly permitted.
- The repeated non-performance is a task-following/utility failure, distinct from the 4K truncation evidence. Cause (instruction tuning, refusal tendency, visual reasoning limits, or other) is **not established**. Abliteration/Heretic variants are hypothetical remedies, not validated improvements.

## Test C — 16K context

- A previous 16K context run loaded but **vision inference failed with CUDA out-of-memory on GPU 0**.
- This is **NOT** proof that 16K cannot work with further tuning or different hardware.
- Working hypotheses only: six-way GPU layer distribution, available per-card memory, KV/cache pressure, projector placement and multimodal image allocations. No causal attribution has been established.
- 8K vision inference was proposed but **not qualified or demonstrated** in this record. Do not mark 8K as tested.

## Disposition and next step

**Do not deploy this 78B configuration as Grace's primary visual specialist.** Preserve the model and evidence for optional future research; no claim that the model is universally incapable of visual reasoning.

**Next candidate:** identify the already-stored vision-enabled Qwen ~30B A3B variant and its exact GGUF, mmproj, quantization and runtime compatibility. Test it as a **single direct multimodal service**, rather than a 3060 Ti vision-to-text relay to another reasoning model. Confirm actual model files before deployment. Use unchanged task-quality gates: first-pass screenshot extraction, engineering drawing constraints, and the exact five-item visual-canon proportional-analysis task. Record execution, GPU topology, token budget, inference speed, task completion and refusal/uncertainty behavior separately.

Do not unload the running InternVL service until the next model and launch plan are verified.
