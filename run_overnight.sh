#!/usr/bin/env bash
cd "$(dirname "$0")"

TOOLS="Bash(python3:*),Bash(bash:*),Bash(ngspice:*),Bash(kicad-cli:*),Bash(git:*),Bash(java:*),Bash(cp:*),Bash(mkdir:*),Bash(unzip:*),Bash(ls:*),Edit,Write,Read,Grep,Glob,WebFetch,WebSearch"

# Run 1: full prompt, fed through stdin
claude -p --max-turns 150 --permission-mode acceptEdits \
  --allowedTools "$TOOLS" < overnight_prompt.md

# Runs 2-6: resume the same conversation
for i in 2 3 4 5 6; do
  [ -f docs/MORNING_REPORT.md ] && echo "Done: morning report written." && break
  [ "$(date +%H)" = "09" ] && echo "9am, stopping." && break
  sleep 60
  echo "Continue the overnight plan from where the log says you stopped. Skip anything already done. Follow the efficiency rules." | \
    claude -p --continue --max-turns 150 --permission-mode acceptEdits --allowedTools "$TOOLS"
done
