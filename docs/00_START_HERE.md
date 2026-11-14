# Start here

## Status at handoff (Nov 13, 2026)
- Architecture, parts, values and floorplan are decided and simulated (see `reports/VERIFICATION_REPORT.md`).
- Schematic: there is a reviewed draft (on the design review page), but nothing is in KiCad yet.
- Layout: placement zones and routing constraints are defined. The earlier routing sketch is **not** a layout; ignore it. Dwayne routes.
- Firmware and server: the approach is verified (protocol round trips, real Traccar run). Code work hasn't started.

## Order of work
1. **Project setup**
   - Create two KiCad projects or variants, `card_v1` (rigid FR4, QFN48) and `card_v2` (flex, CSP), sharing hierarchical sheets.
   - Set up git LFS for 3D models if they are large.
2. **Pin maps.** For every IC in `design/netlist.yaml`, write `design/pinmaps/<part>.md` mapping functional pin names to pin or ball numbers, with the datasheet page.
   - Start with the nRF54L15. Use Nordic's QFN48 and CAAA "config 1" reference schematics and the nRF54L15 DK and Tag design files.
3. **Symbols and footprints**
   - Use official or manufacturer sources (KiCad library, TI/Nordic CAD, SnapMagic/Ultra Librarian). Verify each footprint against the datasheet land pattern.
   - Set 3D model heights correctly, because the height budget depends on them.
4. **Schematic capture,** as hierarchical sheets matching the blocks:
   - `qi_rx.kicad_sch` (block A)
   - `charger.kicad_sch` (B)
   - `battery_protect.kicad_sch` (C)
   - `power_sense.kicad_sch` (D)
   - `mcu.kicad_sch` (E)
   - `rf_antenna.kicad_sch` (F)
   - `debug_nfc.kicad_sch` (test pads; NFC is not populated yet)
   - Use the net names exactly as in `design/netlist.yaml`.
5. **ERC clean.** Every warning is fixed or justified in the decision log.
6. **Simulations in KiCad (ngspice).** Reproduce `sims/power_path_ngspice.py` and `sims/qi_link_ngspice.py` on the real schematic with vendor models where they exist; behavioral models are fine where they don't. See `docs/08_verification_plan.md`.
7. **v1 board outline and zones.** Draw the ISO ID-1 outline, keep-outs, coil land, antenna region and stiffener zone from `docs/05_mechanical_stackup.md`. Then hand it to Dwayne for placement and routing.
8. **Review loop.** After each routing session, run DRC, check the constraints list in `docs/04_layout_constraints.md`, and report problems ranked by severity.
9. **v1 fab package:** Gerbers, BOM, CPL for JLCPCB PCBA (the DSBGA parts need machine placement).

## Bench work happens in parallel (Dwayne)
Demos 1 to 4 in `docs/08_verification_plan.md` run on dev boards while the schematic is being drawn. Their results feed back into C1, C2, the antenna arm length and the match values.
