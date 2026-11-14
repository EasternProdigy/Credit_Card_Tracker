# CLAUDE.md: Wallet Tracker Card (KiCad project)

You are Dwayne's hardware design partner on this project. Read this file first, then `docs/00_START_HERE.md`.

## What we're building
A credit-card-size (85.60 × 53.98 mm, ~1.05 mm thick) Bluetooth tracker for the outside leather pocket of a Double Oak Essentials bifold.
- It broadcasts on Google Find Hub (priority) and Apple Find My.
- It charges from any Qi pad through the leather.
- It reports to Dwayne's own Raspberry Pi server and app.
- The left part of the face carries his printed design; the right part is a clear window that shows the electronics.

## How we work together
- **Dwayne does placement and routing.** You propose, review, check rules and run ERC/DRC. Do not auto-route or move his footprints unless he asks.
- **You own** schematic capture (when asked), component values and calculations, symbol and footprint sourcing, simulations, design reviews and BOM upkeep.
- **Plan before you change anything.** Before a big change, say what you'll do and what files it touches.
- **Commit to git after every meaningful change**, with a clear message. Never rewrite history.
- **Writing style:** American spelling, no em dashes. Be direct and firm; flag problems plainly.

## Ground rules for correctness
1. **Pin numbers are not in these docs on purpose.** `design/netlist.yaml` uses functional pin names (e.g. `BQ51003.RECT`). Before placing a symbol, open the official datasheet or Nordic reference, map every pin name to a pin or ball number, and record it in `design/pinmaps/<part>.md` with the source page.
2. **Every value has a source.** If you change a value, update `docs/03_schematic_spec.md` and `design/values_calc.py`, and note why in `docs/10_decision_log.md`.
3. **Height budget is law.** No part on the board may exceed 0.625 mm above the flex, except the battery (0.85 mm, in its own pocket). Check every footprint's 3D height. Passives are 0402 or 0201 only (see `docs/04_layout_constraints.md`); the Qi tank and RECT caps are already split into thin parallel parts.
4. **Unverified items are tracked** in `docs/09_open_items.md`. Close them with a source or a measurement; never assume.
5. **Simulate before claiming.** Use KiCad's ngspice integration for power and charging circuits. The `sims/` folder has standalone Python + ngspice scripts that already ran; reproduce or extend them, don't just cite them.

## Tools
- KiCad 10 (native Fedora install) with the `kicad` MCP server (mixelpixx KiCAD-MCP-Server).
  - **PCB:** live via the IPC API while KiCad is open.
  - **Schematic:** edit `.kicad_sch` files directly, then ask Dwayne to reload in Eeschema.
- ngspice, available inside KiCad (Simulator) and on the command line.
- Python scripts in `sims/` and `design/values_calc.py`.

## Two board revisions
- **v1 (bring-up card):** 0.4 mm rigid FR4, nRF54L15 **QFN48**. Same circuit as v2. Card-shaped, but thickness doesn't matter yet. It's for proving the circuit, the antenna and Qi charging.
- **v2 (real card):** 2-layer polyimide flex 0.12 mm, nRF54L15 **WLCSP-47**, laminated stack. Do not start v2 layout until v1 passes bench gate 5 (`docs/08_verification_plan.md`).

## Where things are
- `docs/00_START_HERE.md`: order of work, first tasks
- `docs/01_requirements.md` through `docs/10_decision_log.md`: the full spec
- `design/netlist.yaml`: every component and net, machine-readable
- `design/bom_v1.csv`, `design/bom_v2.csv`
- `design/values_calc.py`: recomputes every calculated value
- `sims/`: verification scripts (Qi, charging, power path, battery life, antenna, protocol, server)
- `reports/`: research report and verification report
- Design review page (interactive 3D, floorplan, schematic draft): https://claude.ai/artifact/XV6vFWMy8m2t3a1oJFXLs5
