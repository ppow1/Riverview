# RIV-UI-0008 — Riverview Open WebUI ownership and authentication boundary

## SYMPTOM

The local Open WebUI health endpoint returns 200, but `/api/models` returns 401 and no bounded Riverview conversation acceptance can be established.

## BOUNDARY

RV-010.1 Open WebUI adapter ownership, service identity, and authenticated model access.

## SAFE DIAGNOSTIC

Inspect only the listening process command line, bind address/port, `/health`, `/api/config`, and `/api/models` status. Resolve configuration only from an approved Riverview-owned runtime path; never read or copy secret keys. On 2026-08-15 the listener was PID 15188 running `A:\AI\OpenWebUI` on `127.0.0.1:8080`, which is an Estate-owned instance rather than a Riverview-owned service; `/health` and `/api/config` returned 200 while `/api/models` returned 401.

## EXPECTED HEALTHY RESULT

An explicitly Riverview-owned and authenticated instance routes one bounded request through the provider-neutral reasoning contract with preserved session, correlation, provider, and classification identity.

## KNOWN FAILURE / REPAIR

Health reachability does not prove authenticated model access. First locate or provision the approved Riverview service/configuration and resolve its supported authentication path. If credentials are absent from an accepted Riverview secret path, stop this lane at the credential boundary; do not use Estate credentials as a shortcut.

## VERIFY

Repeat `/health` and authenticated `/api/models` against the Riverview-owned endpoint, then run one bounded request and verify its typed response and correlation in PostgreSQL/River evidence.

## DO NOT

Do not treat a 200 health response as RV-010.1 acceptance, scrape or expose credentials, reuse an unrelated Estate service, or add shell/SQL authority to Open WebUI.

## EVIDENCE

Source: Riverview runtime process and HTTP probes on 2026-08-15; Cookbook entry: `RIV-UI-0008`.
