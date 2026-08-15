# RIV-UI-0009 — Riverview-owned Open WebUI service boundary

## SYMPTOM

Riverview operator requests reach an unowned service, lack authentication, exceed the bounded schema, or lose reasoning correlation.

## BOUNDARY

RV-010.1 isolated Riverview Open WebUI adapter.

## SAFE DIAGNOSTIC

Probe only loopback `/health`, authenticated `/api/models`, and bounded `/api/chat`; inspect service identity, port, data-path reference, and typed response correlation.

## EXPECTED HEALTHY RESULT

Riverview-owned service identity, isolated runtime/data path, bearer authentication, approved provider-neutral response, and preserved request/correlation IDs.

## REPAIR / VERIFY

Restart only the Riverview service, verify health/auth/model discovery, then run one bounded typed request and compare correlation.

## DO NOT

Do not reuse Estate Open WebUI state, expose credentials, add shell/SQL authority, or accept browser prose as operational state.

## EVIDENCE

Source: `src/riverview/operator/openwebui.py`; test: `tests/test_openwebui_riverview.py`.
