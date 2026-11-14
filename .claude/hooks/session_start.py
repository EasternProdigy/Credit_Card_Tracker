#!/usr/bin/env python3
"""SessionStart hook: gives Claude the project's recent history at the
start of every session, so it picks up where the last one left off."""
import os
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
LOGDIR = ROOT / "docs" / "log"
INBOX = ROOT / "measurements" / "inbox"

logs = sorted(p for p in LOGDIR.glob("20*.md"))
out = ["## Project log context (auto-loaded)"]
if logs:
    last = logs[-1]
    text = last.read_text(encoding="utf-8")
    tail = text[-3000:]
    out.append(f"Most recent log: docs/log/{last.name} (last part below).")
    out.append(tail)
else:
    out.append("No log entries yet. Start docs/log/<today>.md from TEMPLATE.md.")

inbox = [p.name for p in INBOX.glob("*") if p.is_file() and p.name != ".gitkeep"] \
    if INBOX.exists() else []
if inbox:
    out.append("Unlogged files waiting in measurements/inbox/: " + ", ".join(inbox))

out.append("Reminder: logging rules are in CLAUDE.md under 'Logging (mandatory)'.")
print("\n\n".join(out))
