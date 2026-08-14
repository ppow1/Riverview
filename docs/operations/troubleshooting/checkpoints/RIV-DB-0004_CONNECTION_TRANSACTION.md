<!-- Version: 0.2.0 -->
# RIV-DB-0004 — PostgreSQL connection or transaction failed

Trigger: psycopg cannot connect, authenticate, or commit a transaction.

Distinguish: Check service `postgresql-x64-18`, listener port 5432, metadata host/port, then DPAPI recovery. Do not reset credentials until those probes identify authentication as the fault.

Smallest repair: Start the stopped service, correct metadata, or rerun provisioning only for confirmed credential failure.

Verify: Run `.venv\Scripts\python.exe -m riverview.health database`; require `status: healthy`.