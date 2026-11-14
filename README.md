# Wallet tracker card: handoff package (rev 0.5, 2026-11-13)

## How to use this
1. Copy everything in this folder into your KiCad project folder (e.g. `~/Desktop/PCB/<project>/`).
2. `CLAUDE.md` goes in the project root. Claude Code reads it automatically.
3. Set up git and the secret scanner once: `bash scripts/install_git_hooks.sh`, then `git add . && git commit -m "Add design handoff package rev 0.5"`
4. Start Claude Code in that folder and say: **"Read CLAUDE.md and docs/00_START_HERE.md, then start step 1."**

## Contents
- `CLAUDE.md`: role, rules and workflow for the KiCad Claude
- `docs/`: requirements, architecture, schematic spec, layout constraints, stackup, firmware, server, verification plan, open items, decision log
- `design/`: `netlist.yaml` (every part and net), `bom_v1.csv`, `bom_v2.csv`, `values_calc.py`
- `sims/`: every simulation and verification script, plus `results/` JSON
- `reports/`: research report and verification report
- `plots/`: simulation plots
- `server/`: Traccar config used in the backend test

## Rerun the sims on Fedora
```
sudo dnf install ngspice
pip install --user PyNEC numpy scipy matplotlib cryptography ecdsa pycryptodomex requests
cd sims && python3 qi_coupling.py && python3 power_path_ngspice.py   # etc.
```
`protocol_roundtrip.py` needs `git clone https://github.com/leonboe1/GoogleFindMyTools /tmp/src/GoogleFindMyTools`.
`backend_e2e.py` needs Traccar running with `server/traccar.xml`.

Design review page (3D model, floorplan, face, schematic draft): https://claude.ai/artifact/XV6vFWMy8m2t3a1oJFXLs5

## Auto-logging (open-source build log)
Every Claude Code session in this folder logs itself:
- `.claude/settings.json` registers two hooks. **SessionStart** loads the latest log so each session picks up where the last left off. **Stop** blocks Claude from finishing a turn if it changed files without writing to `docs/log/<today>.md`, or if raw data is sitting in `measurements/inbox/`.
- Drop PPK2 exports, NanoVNA `.s1p` files, scope screenshots and photos into `measurements/inbox/`. Claude files each into `measurements/<date>/` with a note and logs it (`scripts/log_measurement.py`).
- Tell Claude test results in plain words too; the rules in `CLAUDE.md` make it log them.
- Secrets live in `secrets/` (git-ignored), and the pre-commit hook runs gitleaks.
- Use the same folder (and `CLAUDE.md`) for the firmware, server and app sessions, under `firmware/`, `server/` and `app/`, so all of them write to one log.

Before making the repo public: pick licenses (common choice: CERN-OHL-S-2.0 for hardware, CC BY 4.0 for docs; firmware and server must match the upstream Everytag, GoogleFindMyTools and macless-haystack licenses), and add a README note that the unwanted-tracking alerts are kept on.
