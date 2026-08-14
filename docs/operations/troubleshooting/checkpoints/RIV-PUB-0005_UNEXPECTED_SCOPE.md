<!-- Version: 0.2.1 -->
# RIV-PUB-0005 — Unexpected publication scope

Trigger: A modified or untracked path is not present in the publisher's explicit manifest.

Failure classes:

1. Legitimate project work was omitted from the manifest.
2. Unrelated user work is present in the working tree.
3. A generated, backup, credential, or runtime file escaped its ignore boundary.
4. A path was renamed or normalized differently than the manifest expects.

Diagnostic procedure: Read the exact `CHANGE` path in the publication report, inspect its contents and origin, and compare it with the accepted build scope. Never broaden the manifest to a directory merely to clear the gate.

Smallest repair: Add the single verified project file to the explicit manifest, move unrelated work out of the publication, or correct `.gitignore` for non-source artifacts.

Verification: Rerun the publisher. Every observed path must match one exact manifest entry; staged whitespace, acceptance, push, remote commit equality, and final clean-tree checks must pass.

Observed resolution: `tools/powershell/database/Install-RiverviewPostgreSQL.ps1` was created during the approved native PostgreSQL installation and was added as one exact path in publisher v0.2.1.
Observed status-view manifestation: default porcelain output condensed an untracked package to an untracked directory summary. Publication scope must use `--untracked-files=all` so every file is independently allowlisted.
