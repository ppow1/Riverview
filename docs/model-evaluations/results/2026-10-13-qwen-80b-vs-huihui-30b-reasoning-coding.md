# Riverview model evaluation — Qwen3-Next 80B vs Huihui Qwen3-VL 30B

**Recorded:** 2026-10-13  
**Scope:** Reasoning, engineering diagnosis, debugging, independent code creation, self-audit and repair.  
**Models:** Qwen3-Next-80B-A3B-Instruct-Q4_K_M (text); Huihui-Qwen3-VL-30B-A3B-Instruct-abliterated.i1-IQ3_XS (vision-capable).  
**Purpose:** Select appropriate roles for Riverview local agents. **This is not a throughput or final deployment configuration comparison.**

## Executive conclusion

The 80B was substantially stronger on the supplied engineering/coding exercises. The 30B occasionally gave competitive conceptual answers, but its scheduler implementations retained serious fundamental defects. The 80B can produce useful working code and identify genuine flaws in its own work, yet its audit and test-writing are fallible; **neither model is cleared to modify production autonomously**. Use independent tests, evidence review and human approval for consequential changes. The 30B's vision capability was **not evaluated** by these text/code tasks.

## Results log

| Test | Subject | 80B | 30B | Evidence and limitations |
|---|---|---|---|---|
| 1 | MoE / VRAM / PCIe / context questions | 62/100 | 48/100 | Conversational rubric; conceptual errors in both |
| 2 | Critique false 80B VRAM claim | 82/100 | 85/100 | Both rejected the idea that active MoE weights alone determine residency; detailed arithmetic imperfect |
| 3 | Allocate both models on six-GPU OctoMiner | Initially 60/100; assessment subsequently revised qualitatively | 15/100 | 80B proposed 80B on four P100s and 30B on 4090; four-P100 80B operation was independently established in Oct 11 campaign, but simultaneous pairing **not** verified. 30B proposed infeasible single-card placements. Do not treat initial 80B numeric score as final |
| 4 | Diagnose three-P100 load timeout and mixed-GPU concurrency failure | Initially 65, subsequently revised to ~75/100 | 25/100 | 80B separated evidence from speculation better, but presented memory hypothesis too confidently. Three-P100 result was a **timeout**, not confirmed OOM |
| 5 | Repair deliberately broken Python scheduler | Reported 6/7 checks | Reported 0/7 checks | 80B fixed ordering, task removal, failure records, and falsy results. 30B retained priority and execution defects. Prior chat reported execution but no reproducible harness/log archived with this report |
| 6 | Build persistent task engine from scratch | Reported 8/10 checks | Reported 2/10 checks | 80B produced substantially more complete scheduling, persistence, retry and recovery logic. 30B referenced missing `order` field during sorting and omitted persistence transitions. Prior chat reported execution but no reproducible harness/log archived with this report |
| 7 | 80B audits its own task engine | 68/100 (qualitative) | Not run | Found real risks: silent corrupted-store reset, nonserializable results, persistence failure. Also invented an unhandled invalid-type crash, incorrectly said `run_all` skipped failures, and proposed a fix that could not guarantee exactly-once external effects |
| 8 | 80B repairs code and writes unittest suite | Reported 10/14 self-tests passing; qualitative 72/100 | Not run | Four reported failures: crash-recovery test set up incorrectly; missing submit-time type validation; retry policy vs expected immediate failure; `run_all` returns attempts rather than final-task-only records. No reproducible test-run output archived here |

**Score caution:** Scores are informal assistant judgments, not standardized benchmark scores. Test 4's 80B score was explicitly revised after reconsidering conservative VRAM planning assumptions. Test 3's 80B score was challenged and the underlying allocation validated in part by separate GitHub GPU tests. Reported pass counts in Tests 5, 6, and 8 are previous conversational reports, **not newly reproduced or independently certified in this commit**.

## What the exercises actually demonstrated

**80B strengths:** Better compliance with multi-constraint engineering specifications, practical code structure, correct priority/FIFO design, failure handling, persistent-state architecture, and a meaningful ability to discover defects during self-review.

**80B limitations:** Can overstate root causes without logs, misread its own code during audit, create invalid test expectations, accept malformed task payloads, and mishandle persistence edge cases. The repaired implementation's in-memory crash recovery was not immediately saved to disk. External side effects cannot be made exactly-once merely by setting a JSON status or reverting to `running` after save failure.

**30B strengths:** In Test 2 it slightly outscored 80B on the specific conceptual critique. Vision/multimodal ability remains an independent potential role and was not measured here.

**30B limitations:** Repeated capacity/allocation reasoning errors, weak adherence to scheduler requirements, missing FIFO ordering field in newly written code, insufficient exception/persistence bookkeeping, and no reliable self-contained working scheduler in the supplied tests.

## Critical engineering distinctions

- The Qwen 80B GGUF file was measured at **48,410,988,384 bytes (~45.09 GiB)**; disk bytes are not the total required VRAM. Capacity budgeting should include cache, runtime and placement overhead, but a conservative budget is not proof of a specific failure cause.
- Separate Oct 11 GPU benchmark showed **four P100s** could host the 80B model, and **4090 + two P100s** also worked. **Three P100s timed out** in the measured run; root cause remains unconfirmed. See [80B GPU campaign](2026-10-11-qwen3-next-80b-gpu-campaign-uuid.md).
- Successful handler execution followed by crash before durable completion can repeat external side effects on restart. The JSON task engine is at-least-once under some failure windows; production requires idempotency keys, external deduplication, or transactional integration where possible.
- Atomic `os.replace()` is not by itself a guarantee of durability across sudden power loss; fsync/dir-sync and platform details matter.
- The 80B and 30B were evaluated on different GPUs, quantizations and model types (30B abliterated vision model versus 80B text model). Token rates and response times were deliberately **excluded from model-selection conclusions**; retest on deployment hardware if throughput becomes a selection criterion.

## Recommendation for Riverview

1. **Primary code and engineering candidate:** 80B, gated by automated tests, independently inspected execution evidence, controlled file changes and explicit approval before deployment.
2. **30B:** consider for vision or lighter workloads after **separate task-specific evaluation**; do not assign unsupervised engineering changes based on these results.
3. **Next validation:** archive actual `agent_engine.py`, `test_agent_engine.py`, and reproducible independent fault-injection logs; test disk failures, malformed payloads, restart behavior, retry semantics and idempotency. Compare deployment performance only after candidate placements are defined.

**Provenance:** User-supplied model outputs and discussion from Oct 11–13 2026; earlier Oct 11–12 GPU campaign documents in this repository. This file is an evaluation record, **not a production authorization or benchmark reproduction**.
