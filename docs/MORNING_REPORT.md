# Morning report: overnight run 2026-11-14 (04:20 to 06:20)

> **Update 2026-11-14 afternoon:** Dwayne approved 4-layer.
> - Branch `overnight-routing` is now JLC 4-layer 0.8 mm, ENIG, with In1 as a solid GND plane.
> - DRC: 0 errors and 0 unconnected; only the 9 courtyard-overlap warnings remain.
> - The review package has been regenerated.
> - Correction: JLC doesn't fill and cap vias in pads on 4-layer (6-layer and up only), so the U1 vias stay open in the pad. Details in QUESTIONS 0 and the decision log.

**Bottom line:** v1 is captured, simulated, placed and routed as a proposal on branch `overnight-routing`. It's not ready to order, for one reason: **the BQ51003 DSBGA needs via-in-pad, which JLC only offers on 4-layer** (QUESTIONS item 0).

## Done
| Step | Result |
|---|---|
| 0 Merge rev 0.5 | Hooks, scripts and log in place. gitleaks not installed (`sudo dnf install gitleaks`). |
| 1 Pin maps | `design/pinmaps/`: BQ51003, BQ25101, S-82N1B, TPS7A02, nRF54L15 QFN48 (+ Nordic Fig. 180 wiring), EFC4615R. Datasheet pages cited. |
| 2 Schematic | `hardware/v1/card_v1` (7 hierarchical sheets), generated from `hardware/v1/gen/design.py`, with all dev-board features you asked for. **ERC 0** (all severities); netlist = design, 297 pins, 0 mismatches. |
| 3 Footprints | Library + custom (SNT-6A, EFCP-4, IFA, coil lands) checked against vendor drawings. v1 is exempt from the height budget (0603, headers, QFN 0.9 mm). |
| 4 JLC BOM | `design/bom_v1_jlc.csv`: 60 lines, LCSC + 2 substitutes each, 30 Extended, **2 not stocked (U3, U4)**. |
| 5 ngspice | Old sims reproduced via libngspice (match to rounding). New `sims/v1_checks_ngspice.py`: VDD_NRF min 3.226 V worst case; Qi fs 99 to 104 kHz, fd 0.96 to 1.01 MHz (WPC OK); divider 0.08 mV error. |
| 6 to 9 Layout | Outline, keepouts (antenna, coil, Nordic C25/C26 ground rules, Y1), MCU+RF and Qi in the electronics zone, dev parts in the battery area. Hand-routed RF chain, crystals, DC/DC/DEC, VSS_PA; Freerouting for the rest. |
| 10 DRC + gerbers | **0 clearance/short/width/hole errors.** 4 opens (below), 9 courtyard grazes, 2 starved thermals, GND pour fragments. Gerbers, drill, CPL, BOM and schematic PDF in `hardware/v1/review/`. Not ordered. |

## What the reviews caught (all fixed and logged)
- Netlist rev 0.4: **BQ51003 AD-EN grounded** (it's an output), **ILIM ball left floating**, **S-82N1B "4.20 V variant" doesn't exist**, **R6 2 k outside ABLIC's 300 to 750 Ω**.
- BOM: **L2 matched to a 15 mA / 2.1 Ω part** (now LQM18PN4R7MFRL), **Y1 ESR 80 Ω** (now 50 Ω Murata), RECT caps below TI's 4.7 µF after derating (C9d added).
- The rev 0.4 power sim had the 2.2 µF caps on VDD; Nordic puts them on DECD/DECA. Re-simulated: still 1.53 V of margin.
- Layout: DECRF under the 32 MHz lines (DevZone warning), Freerouting routing over the antenna stubs, BQ51003 balls with no escape.

## Routing quality and worst spots
- Good: the RF chain is straight and about 5.8 mm long, the IFA is clean with ground-edge stitching every 2 mm, the crystal is within 3 mm with no bottom tracks under it, and the DC/DC loop is tight.
- Worst: **the U1 BGA fan-out** (6 via-in-pad, 0.09 mm necks), **the MCU right-side decap column** (0.125 mm gaps by design), long 0.3 mm B.Cu power runs (VDD trunk, AC2 under the tank caps) that are Freerouting-ugly, not 45°/evenly spaced. The appearance pass is still to do.
- Opens to fix by hand: **U5 pin 36 VDD island**, nCHG_MCU at pin 6, NFC1 (DNP), P0.00 spare pad.

## Not done
- KiCad GUI simulator runs (same libngspice engine was used headless). Nordic's QFN48 *layout* files (only the datasheet was available), so placement isn't a copy of Nordic's reference.
- Würth coil land geometry (O20), the EFC4615R land (O21) and cell polarity (O24) need the physical parts.

## First 5 things to review
1. **QUESTIONS item 0: switch v1 to JLC 4-layer** (via-in-pad for U1; also fixes pin 36, DECRF shielding and QFAA certification risk).
2. `design/bom_v1_jlc.csv` and the decision log entries for R1, R6, R_PS, L2, Y1, C9d, L4/L5 (TN instead of HQ), plus how to source U3/U4.
3. `hardware/v1/review/electronics_zone_routed.png`, then `card_v1.kicad_pcb` on `overnight-routing`: the RF chain, the C25 → pin 32 → EP path, and the U1 fan-out.
4. The v1 placement split (dev parts in the battery area) and whether the IFA feed at x 58.6 is acceptable versus the sim's 58.5.
5. Coil lands and cell polarity against your samples before anything is ordered.

Regenerating: `python3 hardware/v1/gen/gen_pcb.py` rebuilds the **unrouted** board (placement + hand routes); then run `python3 hardware/v1/gen/route_best.py 3 100`. Hand edits in KiCad are lost if you regenerate, so after you start editing, the .kicad_pcb is the source.
