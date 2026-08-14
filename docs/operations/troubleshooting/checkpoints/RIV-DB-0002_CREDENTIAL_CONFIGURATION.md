<!-- Version: 0.2.0 -->
# RIV-DB-0002 — Credential configuration unavailable

Trigger: River cannot read PostgreSQL metadata or its application-secret path.

Distinguish: Confirm `A:\Riverview\data\secrets\postgresql\credential-metadata.json` and the referenced `riverview-app.dpapi` file exist. Never paste their contents into chat.

Smallest repair: Rerun `tools\powershell\database\Initialize-RiverviewDatabase.ps1` as the intended Windows runtime user.

Verify: Run `.venv\Scripts\python.exe -m riverview.health database`; require `status: healthy`.