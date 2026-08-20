<!-- Version: 1.0.0 | Date: 2026-08-20 | Status: CAPTURED -->
# PL-0002 — Alternative Local AI Inference Runtime Paths

## Parking Lot identity

- ID: PL-0002
- Category: Local AI / Resident Runtime Architecture
- Priority: Strategic
- Originator: Steward
- Date captured: 2026-08-20
- Status: CAPTURED

## Idea

Investigate whether Riverview should continue using Ollama/llama.cpp as its principal local resident inference path or support additional inference runtimes/providers better matched to Riverview's heterogeneous local hardware and future resident workload.

This investigation is intentionally broader than model selection. Riverview must distinguish the resident/model from the inference runtime used to execute that model. A resident should not become architecturally synonymous with Ollama, llama.cpp, or any single provider implementation.

## Why it is worth preserving

Riverview began with Ollama/llama.cpp because that path was locally available, comparatively easy to operate, and sufficient to get early local reasoning working. Recent Jessica qualification work has exposed reasons to revisit whether convenience has become an accidental architectural constraint.

The current host includes an RTX 4090 and Tesla P100. Prior work has demonstrated useful dual-GPU operation, while C475/C476 exposed an Ollama-specific GPU-discovery/runtime defect and demonstrated that runtime behavior can materially affect model qualification. Riverview's longer-term resident architecture also anticipates residents with different cognitive demands, model sizes, concurrency needs, and potentially different execution implementations.

A future investigation should therefore compare alternative local inference paths on their actual suitability for Riverview rather than assuming Ollama is either required or wrong.

## Candidate paths to investigate

The future investigation should consider, without limiting itself prematurely to:

- the existing Ollama path;
- direct llama.cpp execution without Ollama as the serving wrapper;
- other Windows-capable GGUF/local inference servers;
- LM Studio or equivalent local serving/testing paths where architecturally appropriate;
- GPU-first serving runtimes such as vLLM or SGLang where host/WSL/Linux requirements are acceptable;
- NVIDIA-optimized inference paths such as TensorRT/TensorRT-RTX where hardware and model compatibility justify them;
- direct framework execution where a resident workload genuinely benefits from it;
- a heterogeneous provider strategy in which different resident/model workloads may use different local runtimes behind a stable Riverview provider contract.

This list is investigative, not an approved technology selection.

## Questions the future investigation must answer

1. What inference-runtime characteristics do Riverview residents actually require?
2. Which runtimes best exploit the RTX 4090?
3. Which runtimes can make useful use of the Tesla P100, independently or alongside the 4090?
4. Which paths support the model families and quantizations needed by deeper residents such as Jessica, Grace, and Evelyn?
5. What are the practical limits for model size, context, throughput, latency, concurrency, batching, GPU offload, and multi-GPU use?
6. Which runtimes operate reliably on the current Windows host, and which require WSL/Linux or other infrastructure?
7. What operational burden, diagnostics burden, upgrade risk, and failure surface does each runtime introduce?
8. Can Riverview preserve a provider-neutral resident contract so model/runtime changes do not redefine resident identity or cognition architecture?
9. Should Riverview ultimately support more than one local inference implementation simultaneously?
10. What evidence would justify replacing, supplementing, or retaining Ollama?

## Relationship to current Jessica work

This idea is being parked specifically to avoid scope creep during Jessica's local onboarding and Tranche F validation.

The current repaired Ollama/4090 path remains available for Jessica testing. Parking this investigation does not authorize changing Jessica's current provider path, delaying her qualification while alternative runtimes are explored, or reopening the current runtime architecture without a concrete need.

If Jessica's immediate qualification reveals a blocker that cannot reasonably be solved through the existing provider-neutral boundary, the relevant narrow portion of this idea may be reconsidered earlier. Otherwise, Jessica remains the current priority.

## Why it is parked now

The investigation could become substantial engineering work and would distract from the immediate objective of completing Jessica's local onboarding and validation. Riverview now has enough evidence to know the question is worth preserving, but not enough reason to interrupt the current roadmap to answer it.

## Promotion condition

Promote for elaboration when one or more of the following becomes true:

- Jessica's onboarding reaches a stable point where inference-runtime comparison no longer threatens the critical path;
- the existing Ollama/provider path becomes a demonstrated blocker to a required resident capability;
- multi-resident operation makes inference concurrency/resource utilization a direct roadmap dependency;
- Riverview is preparing a durable local inference/provider architecture rather than a single-resident qualification path; or
- the Steward explicitly directs that the runtime alternatives investigation begin.

Promotion requires Steward direction and subsequent elaboration under `docs/operations/PARKING_LOT_AND_READY_BENCH.md`. This item is not Ready Bench work and has no implementation authorization.

## Explicit non-action

Do not, merely because this item exists:

- replace Ollama;
- remove llama.cpp support;
- install alternative inference runtimes;
- change GPU drivers or system configuration;
- alter Jessica's current qualification path;
- begin a broad provider abstraction rewrite;
- begin GPU scheduling or Autonomic Resident Layer work;
- select a permanent Riverview inference runtime;
- promote this item to the Ready Bench without Steward approval and the required durable elaboration.

## Related current evidence

Relevant evidence includes C475/C476 Jessica model qualification and GPU-runtime repair artifacts, the existing Riverview provider-neutral reasoning contracts, and the previously captured PL-0001 Resident Autonomic Cognition and Cognitive Resource Scheduling concept.

This parking-lot item does not supersede those artifacts and does not alter their authority or current roadmap state.
