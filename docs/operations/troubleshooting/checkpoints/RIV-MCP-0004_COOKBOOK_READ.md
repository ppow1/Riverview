<!-- Version: 0.9.10 -->
# RIV-MCP-0004 - Cookbook projection unavailable

Component and seam owner: `riverview.mcp.cookbook_sync` plus the bounded Cookbook reader in `riverview.mcp.read_model`.

Observed failure: the authoritative `cookbook_entries` table already existed with the established Kernel schema, while RV-004.4 attempted to use a second incompatible shape behind `CREATE TABLE IF NOT EXISTS`. The first repair corrected sync, then failed because its text regex did not recognize the existing read-model query shape.

Smallest safe repair: preserve the authoritative table; project RV-004.4 metadata into its existing JSONB fields; structurally patch the read query using Python AST; repair the canonical installer so reinstall cannot reintroduce the mismatch.

Recovery verification: compile, Ruff, Cookbook sync, MCP health, MCP contract tests, live stdio protocol acceptance, and PostgreSQL verification preserving pre-existing diagnostic rows.

Escalation boundary: no destructive schema replacement, arbitrary SQL authority, filesystem/process authority in MCP, secrets, credentials, Undercurrent access, or remote exposure.

Applicable implementation revision: 0.9.10.
