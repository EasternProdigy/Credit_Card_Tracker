# Wallet tracker card: handoff package (rev 0.4, 2026-11-13)

## How to use this
1. Copy everything in this folder into your KiCad project folder (e.g. `~/Desktop/PCB/<project>/`).
2. `CLAUDE.md` goes in the project root. Claude Code reads it automatically.
3. Commit it: `git add . && git commit -m "Add design handoff package rev 0.4"`
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
