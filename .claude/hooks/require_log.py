#!/usr/bin/env python3
"""Stop hook: Claude may not end a turn after changing project files
until today's log in docs/log/ is newer than every changed file.

It also blocks while unlogged files sit in measurements/inbox/.
Claude Code passes JSON on stdin; we answer with JSON on stdout.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
LOG = ROOT / "docs" / "log" / f"{date.today().isoformat()}.md"
INBOX = ROOT / "measurements" / "inbox"

# Paths that never need a log entry.
SKIP_DIRS = {".git", "docs/log", "__pycache__", "node_modules", ".venv",
             "build", "measurements/inbox", ".claude"}
SKIP_SUFFIX = (".lck", ".bak", "-bak", ".pyc", "fp-info-cache", ".kicad_prl")


def skipped(rel: str) -> bool:
    if rel.endswith(SKIP_SUFFIX) or "-backups" in rel:
        return True
    return any(rel == d or rel.startswith(d + "/") for d in SKIP_DIRS)


def newest_change(since: float):
    newest, which = 0.0, None
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT).replace("\\", "/")
        rel_dir = "" if rel_dir == "." else rel_dir
        dirnames[:] = [d for d in dirnames
                       if not skipped(f"{rel_dir}/{d}".lstrip("/"))]
        for f in filenames:
            rel = f"{rel_dir}/{f}".lstrip("/")
            if skipped(rel):
                continue
            m = (Path(dirpath) / f).stat().st_mtime
            if m > since and m > newest:
                newest, which = m, rel
    return newest, which


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    # Never loop forever: if we already blocked once this stop, let it end.
    if data.get("stop_hook_active"):
        return

    reasons = []

    inbox = [p.name for p in INBOX.glob("*") if p.is_file() and p.name != ".gitkeep"] \
        if INBOX.exists() else []
    if inbox:
        reasons.append(
            "Unlogged measurement files in measurements/inbox/: "
            + ", ".join(sorted(inbox)[:10])
            + ". For each one, run scripts/log_measurement.py <file> --what \"...\" "
            "--result \"...\" (ask Dwayne what it was if you can't tell)."
        )

    log_mtime = LOG.stat().st_mtime if LOG.exists() else 0.0
    # Only look at changes from the last 24 h so old files don't trigger it.
    import time
    newest, which = newest_change(max(log_mtime, time.time() - 86400))
    if which:
        reasons.append(
            f"Project files changed (latest: {which}) after the last entry in "
            f"docs/log/{LOG.name}. Append an entry using docs/log/TEMPLATE.md: "
            "what was done, why, results or measurements, decisions, next step. "
            "Then commit if git is set up."
        )

    if reasons:
        print(json.dumps({"decision": "block", "reason": " ".join(reasons)}))


if __name__ == "__main__":
    main()
