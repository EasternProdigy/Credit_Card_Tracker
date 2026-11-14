# 08 Verification plan

## Simulations already run (reproduce in KiCad where possible)
| Sim | Script | Result | KiCad follow-up |
|---|---|---|---|
| Qi coupling (mutual inductance) | `sims/qi_coupling.py` | k 0.25 to 0.43 air-core | none (analytic) |
| Qi link transient | `sims/qi_link_ngspice.py` | ≥ 5.8 V VRECT in band; ping wakes at k ≥ 0.25 | Rebuild on the real schematic with the TI BQ51003 model if available; otherwise keep the behavioral rectifier |
| Charging + NTC + heat | `sims/charge_thermal.py` | 66 mA, 2.1 to 2.3 h, ≤ 0.24 W | BQ25101 TI PSpice model if available |
| Power path + divider | `sims/power_path_ngspice.py` | VDD ≥ 3.23 V; 0.08 mV divider error | Use the TI TPS7A02 PSpice model plus the real decoupling from the schematic |
| Battery life Monte Carlo | `sims/battery_montecarlo.py` | 10.7 months median | Update with PPK2 data |
| Antenna (NEC-2) | `sims/antenna_nec.py`, `antenna_floorplan.py`, `antenna_match.py` | S11 ≤ −12 dB in-wallet after a 2.2 nH / 0.2 pF match | Optional openEMS 3D check on the real v1 copper |
| Thickness stack | `sims/floorplan.py` + `thickness_stack_slim.json` | 1.137 mm worst case | Re-run with the real 3D model heights |
| Protocol round trip | `sims/protocol_roundtrip.py` | Apple + Google OK | n/a |
| Backend | `sims/backend_e2e.py` | All calls OK | n/a |

## Checks on every schematic or layout revision
- ERC clean.
- DRC clean, plus a manual check against `04_layout_constraints.md`.
- Height check: every footprint's 3D height is ≤ 0.6 mm (except the cell).
- BOM: every part Active and in stock; record alternates.
- Netlist diff against `design/netlist.yaml`.

## Bench gates (pass/fail)
1. **Both networks:** the DK running patched Everytag appears on Google (WebUI) and Apple (our fetcher) from the Pi.
2. **Power:** PPK2 average ≤ 12 µA with the recommended config, debugger detached, power-cycled.
3. **Qi through leather:**
   - Use 3 different pads, centered and 10 mm off-center, through the real pocket.
   - Pass: charges at about 66 mA, terminates at 4.20 V, cell ≤ 45 °C, no FOD shutdowns when centered.
   - Measure Ls′ in the final stack, then finalize C1 and C2.
4. **App + alerts:** PWA map and bundles work; a low-battery push arrives through ntfy; the not-seen alert fires.
5. **v1 card:**
   - Repeat 1 to 4 on our board.
   - NanoVNA S11 with the card in the wallet; trim the IFA arm and retune L6/C28 to ≤ −10 dB across 2402 to 2480 MHz.
   - Range walk test.

**Rule:** no v2 order until gate 5 passes.
