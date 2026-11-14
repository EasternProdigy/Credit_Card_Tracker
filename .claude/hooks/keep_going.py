#!/usr/bin/env python3
"""Stop hook: keep Claude working overnight until the morning report exists."""
import json, os
from datetime import datetime
from pathlib import Path
ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
COUNT = ROOT / ".claude" / "keep_going_count"
MAX = 40
if (ROOT / "docs" / "MORNING_REPORT.md").exists():
    raise SystemExit
if 9 <= datetime.now().hour < 22:      # daytime: let it stop normally
    raise SystemExit
n = int(COUNT.read_text()) if COUNT.exists() else 0
if n >= MAX:
    raise SystemExit
COUNT.write_text(str(n + 1))
print(json.dumps({"decision": "block", "reason":
    f"Overnight run not finished (continuation {n+1}/{MAX}). Continue with the next "
    "unfinished step of overnight_prompt.md. Check docs/log for where you are. If a step "
    "is blocked, log it and move on. NEVER ask Dwayne anything: he is asleep. Decide the safest option yourself, note it in docs/QUESTIONS_FOR_DWAYNE.md, and keep going. NEVER ask Dwayne anything: he is asleep. Decide the safest option yourself, note it in docs/QUESTIONS_FOR_DWAYNE.md, and keep going. Follow the efficiency rules. Write docs/MORNING_REPORT.md "
    "when everything possible is done."}))
