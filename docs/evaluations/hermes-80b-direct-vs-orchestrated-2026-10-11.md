# Hermes direct-vs-orchestrated 80B evaluation — 2026-10-11

## Decision
Defer Hermes as Riverview's default reasoning path. Retain it as a candidate **controlled second-perspective escalation** when direct-model reasoning stalls. Different reasoning paths can yield different *wrong* answers; apply independent path-specific guardrails and verify claims against hardware facts and experiments. The ~3.7x end-to-end elapsed-time premium might be justified for a difficult blocked problem, but is not justified for ordinary inference.

## Test configuration
- Direct inference endpoint: `http://192.168.1.160:8080/v1` (OctoMiner One alias `octo1`; Linux hostname OCTOMINER2).
- Model ID: `/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf`; four Tesla P100 GPUs.
- Hermes CLI custom provider `octo1-80b` in `A:\AI\Tools\Hermes\data\config.yaml`, using `api`, `transport: chat_completions`, `default_model`. Old `localhost:8092` vision gateway bypassed.
- Engineering prompt: `A:\Riverview\runtime\diagnostics\models\hermes-80b-test-prompt.txt`.
- Windows diagnostics: `hermes-direct-warm-test.txt`, `hermes-80b-engineering-test.txt` in the same directory.

## Observations
| Path/test | Wall time | Other observations |
|---|---:|---|
| Direct 80B engineering baseline | 98 s | 3,153 output tokens; 32.17 tokens/s reported |
| Hermes direct-provider warm smoke test | 10.17 s | Correct `OCTO1 80B CONNECTED` response; exit 0; short prompt, not engineering comparison |
| Hermes direct-provider engineering prompt | 359.88 s | Exit 0; response contained serious engineering errors; trailing `[tool] ... formulating...` |

Hermes engineering test took **3.67x** the direct baseline wall time (approximately 6 minutes versus 1 minute 38 seconds). This is **not** a controlled tokens/s comparison: Hermes token count, model-call count, prompt/tool overhead, and server timings were not measured. The initial Hermes smoke test also passed; earlier provider-registration failures were configuration-path errors, not model failures.

## Quality differences and required guardrails
Both direct and Hermes answers were reported technically wrong **in different ways**; the complete direct-model response is not reproduced here, so do not infer its exact errors or assume one answer validates the other.

Observed Hermes-specific problems:
- Suggested NVLink pooling across RTX 4090 and Tesla P100s, which is not supported by that heterogeneous configuration.
- Computed a roughly 320 GB KV-cache figure from the 80B parameter count, an invalid formula for this MoE attention architecture.
- Proposed hybrid tensor/pipeline inference and alternative runtimes without demonstrating compatibility or addressing measured llama.cpp multi-P100 performance.
- Trailing tool-status text despite exit code 0; completion integrity should be checked.

For **direct-model** inference, enforce hardware topology, quantitative memory/cache calculations, evidence citation, and an independent correctness check on proposed changes. For **Hermes**, additionally enforce tool allowlists, turn/time/cost budgets, prompt and tool-call logging, completion-state verification, and separation of model assertions from observed system facts. For **cross-path escalation**, record both answers, compare disagreements, and validate with decisive measurements rather than voting by confidence. No unattended production deployment based on either response.

## Next step
Pause Hermes investigation; proceed with direct vision-model qualification on OctoMiner One. First verify downloaded GGUF and matching multimodal projector are on an actual SSD-backed filesystem using `findmnt`, `lsblk`, and file-size checks; avoid the known read-error-prone `/dev/sdc` backup disk.
