from pathlib import Path
from datetime import datetime
import subprocess
import json
import urllib.request

REPO = Path(r"T:\OctoMiner_BIOS_Campaign\repo")
OUT = REPO / "REGROUND_PACKET.md"

CANONICAL = [
    "REGROUND_CONTRACT.md",
    "APPROVED_PROPOSAL.md",
    "CAMPAIGN_STATE.md",
    "PROVEN_FACTS.md",
    "PROVEN_NOT_WORKING.md",
    "LESSONS_LEARNED.md",
    "OPEN_QUESTIONS.md",
    "README.md",
]

def text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"[UNAVAILABLE: {exc}]"

def git(*args):
    try:
        p = subprocess.run(
            ["git", *args],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (p.stdout + p.stderr).strip()
    except Exception as exc:
        return f"[GIT UNAVAILABLE: {exc}]"

def steward():
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8785/api/status",
            timeout=3,
        ) as response:
            return json.dumps(
                json.load(response),
                indent=2,
            )
    except Exception as exc:
        return f"[STEWARD UNAVAILABLE: {exc}]"

parts = []

parts.append("# CAMPAIGN REGROUND PACKET")
parts.append("")
parts.append(
    "Generated: " +
    datetime.now().astimezone().isoformat(timespec="seconds")
)
parts.append("")
parts.append(
    "This packet is generated from durable campaign evidence. "
    "It is intended to be reviewed before the next test is designed."
)
parts.append("")

for name in CANONICAL:
    path = REPO / name

    parts.append("")
    parts.append("=" * 72)
    parts.append(f"# SOURCE: {name}")
    parts.append("=" * 72)
    parts.append("")

    if path.exists():
        parts.append(text(path))
    else:
        parts.append("[FILE NOT PRESENT]")

tests = REPO / "tests"

parts.append("")
parts.append("=" * 72)
parts.append("# COMPLETED / RECORDED TEST DOCUMENTS")
parts.append("=" * 72)
parts.append("")

if tests.exists():
    for path in sorted(tests.glob("*.md")):
        parts.append("")
        parts.append("-" * 72)
        parts.append(f"## TEST SOURCE: {path.name}")
        parts.append("-" * 72)
        parts.append("")
        parts.append(text(path))
else:
    parts.append("[TEST DIRECTORY NOT PRESENT]")

parts.append("")
parts.append("=" * 72)
parts.append("# CURRENT GIT COMMIT")
parts.append("=" * 72)
parts.append("")
parts.append(git("log", "-1", "--format=fuller"))

parts.append("")
parts.append("=" * 72)
parts.append("# CURRENT GIT STATUS")
parts.append("=" * 72)
parts.append("")
parts.append(git("status", "--short"))

parts.append("")
parts.append("=" * 72)
parts.append("# CURRENT STEWARD STATE")
parts.append("=" * 72)
parts.append("")
parts.append(steward())

parts.append("")
parts.append("=" * 72)
parts.append("# REQUIRED REASONING RESPONSE")
parts.append("=" * 72)
parts.append("")
parts.append("""
Before proposing another campaign test, explicitly report:

1. CURRENT PHASE
2. CAMPAIGN GOAL
3. CURRENT ROUND GOAL
4. CURRENT TEST / TRANSITION STATE
5. APPROVED ARCHITECTURE AND PLAYER ROLES
6. PROVEN FACTS THAT MATTER NOW
7. PROVEN FAILURES / APPROACHES NOT TO REPEAT
8. APPLICABLE LESSONS LEARNED
9. OPEN QUESTIONS
10. THINGS THAT MUST NOT BE REDISCOVERED
11. SAFETY / AUTHORITY BOUNDARIES
12. NEXT ROADMAP STEP
13. PROPOSED NEXT TEST

Do not substitute conversational memory for the sources above.
""".strip())

OUT.write_text(
    "\n".join(parts) + "\n",
    encoding="utf-8",
)

print(f"REGROUND_PACKET={OUT}")
print(f"SIZE={OUT.stat().st_size}")
print("BUILD=PASS")

