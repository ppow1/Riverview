<!-- Version: 0.1.0 -->
# Riverview AI Hints

Status: Canonical fast-recovery entry point.

Pat is the Steward and final authority. Grace coordinates operational progression but is not the whole Estate at Riverview.

Before creating, modifying, testing, deploying, or promoting Riverview software, read completely:

1. `docs/architecture/RIVERVIEW_FOUNDATION.md`
2. `docs/operations/RIVERVIEW_EXECUTION_PLAN.md`
3. `docs/operations/troubleshooting/README.md`
4. `docs/decisions/ADR-0001_POSTGRESQL_AUTHORITY.md`
5. `docs/decisions/ADR-0002_DIAGNOSTICS_FIRST.md`

Rules:

- Inspect before adding.
- Preserve unrelated work.
- Do not claim GitHub publication until the remote commit is verified.
- Diagnostics are part of implementation.
- Tests must exercise the boundary being claimed.
- Conversation memory is not authoritative state.
- Do not add governance unless an existing document cannot absorb the requirement.
- Do not route work through an OpenAI API model.
- Do not expose Undercurrent or sensitive data through ordinary River paths.
- A capability is not complete until its failure behavior is diagnosable and recovery is verifiable.
