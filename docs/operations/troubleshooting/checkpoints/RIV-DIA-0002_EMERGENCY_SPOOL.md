<!-- Version: 0.3.0 -->
# RIV-DIA-0002 — Emergency diagnostic spool failed

Trigger: Both PostgreSQL diagnostic persistence and the append-only local evidence spool failed.

Failure classes: missing runtime directory, permission denied, full disk, serialization failure, or filesystem fault.

Distinguish: Check the reported path, free space, Windows identity, and directory ACL. Preserve the originating exception and checkpoint.

Smallest repair: Restore only the local runtime directory or its ACL, then rerun the induced fallback check.

Verify: Run `.venv\Scripts\python.exe -m riverview.diagnostic_health fallback`; require one non-authoritative emergency record.