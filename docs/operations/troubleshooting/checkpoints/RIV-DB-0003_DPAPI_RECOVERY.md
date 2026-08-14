<!-- Version: 0.2.0 -->
# RIV-DB-0003 — DPAPI credential recovery failed

Trigger: The application credential cannot be decrypted by the running Windows identity.

Distinguish: Compare the current Windows user with the user that ran database provisioning. Do not move or disclose the encrypted value.

Smallest repair: Run provisioning again as the service/runtime identity so DPAPI creates a CurrentUser-protected replacement.

Verify: Run `.venv\Scripts\python.exe -m riverview.health database`; require `status: healthy`.