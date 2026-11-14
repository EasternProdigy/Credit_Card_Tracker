#!/usr/bin/env python3
"""File a measurement and log it in one step.

Moves (or copies) a raw data file into measurements/<date>/, writes a
small sidecar note next to it, and appends a line to today's log.

Examples:
  python3 scripts/log_measurement.py measurements/inbox/ppk2.csv \
      --board v1 --what "sleep current, all jumpers in" --result "3.9 uA avg"
  python3 scripts/log_measurement.py ~/Downloads/coil.s1p --copy \
      --board v1 --what "Qi coil Ls' on board, battery fitted" --result "9.6 uH"
"""
import argparse
import shutil
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

KINDS = {
    ".csv": "PPK2 / data export", ".ppk2": "PPK2 capture", ".s1p": "NanoVNA S11",
    ".s2p": "NanoVNA S21", ".png": "image", ".jpg": "photo", ".jpeg": "photo",
    ".bmp": "scope screenshot", ".json": "data", ".txt": "notes", ".log": "serial log",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--what", required=True, help="what was measured and how")
    ap.add_argument("--result", default="", help="the number / outcome")
    ap.add_argument("--board", default="", help="dk, v1, v2, bench ...")
    ap.add_argument("--tool", default="", help="PPK2, NanoVNA, scope, multimeter ...")
    ap.add_argument("--copy", action="store_true", help="copy instead of move")
    a = ap.parse_args()

    src = Path(a.file).expanduser().resolve()
    today = date.today().isoformat()
    dest_dir = ROOT / "measurements" / today
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H%M%S")
    dest = dest_dir / f"{stamp}_{src.name}"
    (shutil.copy2 if a.copy else shutil.move)(src, dest)

    kind = KINDS.get(src.suffix.lower(), "file")
    rel = dest.relative_to(ROOT).as_posix()
    note = dest.with_suffix(dest.suffix + ".md")
    note.write_text(
        f"# {src.name}\n\n- Date: {today} {datetime.now():%H:%M}\n"
        f"- Board: {a.board or 'n/a'}\n- Tool: {a.tool or kind}\n"
        f"- What: {a.what}\n- Result: {a.result or 'see file'}\n",
        encoding="utf-8")

    log = ROOT / "docs" / "log" / f"{today}.md"
    if not log.exists():
        log.write_text(f"# {today}\n\n## Measurements\n", encoding="utf-8")
    with log.open("a", encoding="utf-8") as f:
        f.write(f"- {datetime.now():%H:%M} [{a.board or '-'}] {a.what}: "
                f"**{a.result or 'see file'}** ([data]({Path('../..') / rel}))\n")
    print(f"Filed {rel} and logged it in docs/log/{today}.md")


if __name__ == "__main__":
    main()
