<!-- Version: 0.9.3 -->
# RIV-BLD-0010 - Windows PowerShell UTF-8 no-BOM encoding incompatibility

Component and seam owner: PowerShell delivery tooling.

Triggering operation: RV-004.4 installer repository/report write under Windows PowerShell 5.1.

Observed evidence signature: `Set-Content -Encoding utf8NoBOM` is rejected because Windows PowerShell 5.1 does not define the `utf8NoBOM` encoding enumerator.

Known failure class: PowerShell-version-specific encoding enum incompatibility.

Safe distinguishing probe: inspect `$PSVersionTable.PSVersion` and search the executable script for the literal token `utf8NoBOM`.

Smallest permitted repair: use `System.IO.File.WriteAllText` with `System.Text.UTF8Encoding(false)`.

Recovery verification: rerun the complete RV-004.4 installer and require migration checksum/application, static checks, tests, compilation, database health, roadmap health, read-model health, and live stdio MCP protocol acceptance.

Escalation boundary: stop if any additional failure appears; do not broaden the repair.

Applicable implementation versions: failure observed in 0.9.0; repaired beginning 0.9.1 and normalized in 0.9.3.

Validation state: observed.