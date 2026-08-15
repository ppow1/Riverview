# RIV-SPAT-0004 — Machine versus experiential acceptance mismatch

## Trigger

Backend/model/unit-test evidence is treated as sufficient for a human
experiential gate such as rendered Quest/3D presence, comfort, frame rate, or
end-to-end input latency.

## Required distinction

- `MACHINE_ACCEPTANCE`: contracts, data models, projections, synthetic inputs,
  and backend timing.
- `STEWARD_EXPERIENTIAL_ACCEPTANCE`: an actual rendered application, device or
  user-visible runtime, physical input, frame timing, and human judgment.

Backend timing must never be reported as render-frame timing or user-visible
latency. Recovery is to reopen the waypoint, preserve the historical transition,
record the missing runtime evidence, and require the correct experiential gate.

## Verification

Require executable identity, rendered-runtime evidence, device/runtime identity,
input modality evidence, frame timing, end-to-end latency, reconnect/degraded
operation evidence, and explicit Steward acceptance before promotion.
