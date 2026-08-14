<!-- Version: 0.3.0 -->
# RIV-DIA-0001 — Diagnostic persistence used its emergency seam

Trigger: A diagnostic could not be recorded in PostgreSQL and was written to the local emergency spool.

Failure classes: database unavailable, transaction failure, rejected record, or missing Cookbook foreign key.

Distinguish: Run the database health check, then inspect the latest spool envelope's failure type without exposing its diagnostic payload outside the authorized local environment.

Smallest repair: Restore the identified PostgreSQL boundary. Do not treat the spool as workflow state and do not delete it before verified replay tooling exists.

Verify: Run `.venv\Scripts\python.exe -m riverview.diagnostic_health database`; require destination `postgresql`.