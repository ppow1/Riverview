<!-- Version: 0.1.0 -->
# ADR-0002: Diagnostics Are Part of Implementation

Status: Accepted

## Decision

Every material Riverview change includes first-pass diagnostic metadata, stable checkpoints, focused probes, induced-failure tests where feasible, Cookbook candidate knowledge, and recovery verification.

## Reason

The Estate demonstrated that implementation without immediate diagnostic knowledge creates architectural archaeology and consumes excessive Steward attention.

## Consequences

- Missing diagnostic coverage blocks operational completion.
- Cookbook prose without linked code, tests, and evidence is not canonical.
- Changed code can mark applicable Cookbook knowledge stale.
- The implementing worker supplies first-pass knowledge; validation promotes it.
