# RIV-REASON-0003 — Local GPU provider boundary

## SYMPTOM

A named GPU is unavailable, a model/runtime is incompatible, or resource provenance cannot be established for a bounded reasoning job.

## BOUNDARY

RTX 4090/P100 adapters over the provider-neutral reasoning contract.

## SAFE DIAGNOSTIC

Query `nvidia-smi` for device identity, driver, total/used memory before and after a bounded request; compare the named adapter and model evidence.

## EXPECTED HEALTHY RESULT

The RTX 4090 adapter returns a typed response with GPU/model evidence. The P100 adapter either returns equivalent evidence or rejects a runtime it cannot support.

## KNOWN FAILURE / REPAIR

Missing device, unsupported model, runtime mismatch, timeout, or unchanged resource evidence fails closed. The 2026-08-15 P100 probe started an isolated Ollama endpoint with `CUDA_VISIBLE_DEVICES=0`; the request returned, but P100 memory remained `9 MiB` while the RTX 4090 rose from `16692` to `22826 MiB`. This proves the Windows runtime ignored the attempted P100 binding for that process. Repair the local runtime/adapter registration or reject the task; do not invent parity.

## VERIFY

Repeat the measured request or deliberate incompatibility rejection and persist provider provenance through the reasoning registry.

## DO NOT

Do not route protected payloads, expose GPU controls through MCP, or claim a GPU job from inventory alone.

## EVIDENCE

Source: `src/riverview/reasoning/gpu.py`; Cookbook entry: `RIV-REASON-0003`. Runtime endpoint and measured device must both be recorded; an HTTP success is not GPU acceptance.
