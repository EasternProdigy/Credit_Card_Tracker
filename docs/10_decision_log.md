# 10 Decision log

| Date | Decision | Reason |
|---|---|---|
| 2026-11-13 | Card lives alone in the outside leather pocket of a Double Oak bifold | No RF or Qi shielding from the aluminum |
| 2026-11-13 | Google Find Hub priority, plus Apple Find My | Owner is on GrapheneOS; Apple adds coverage and battery reporting |
| 2026-11-13 | No speaker | Battery and thickness |
| 2026-11-13 | "Balanced" cell: Grepow GRP0849049 135 mAh, 0.85 mm | About 10.7 months per charge |
| 2026-11-13 | nRF54L15 (newest Nordic) | Dual-network support, Everytag support, Nordic Tag reference |
| 2026-11-13 | Everytag firmware with fixes F1 to F10 | Only DIY firmware doing both networks |
| 2026-11-13 | BQ51050B rejected → BQ51003 + BQ25101 | 500 mA minimum charge and 12 µA drain on the BQ51050B |
| 2026-11-13 | Chip antenna rejected → printed IFA on the bottom long edge | 1.3 mm part too tall; NEC-2 IFA meets S11 with an L-match |
| 2026-11-13 | TPS7A0233 at 3.3 V | Lower battery current through the nRF DC/DC |
| 2026-11-13 | ABLIC S-82N1B protector | 0.6 µA vs 4 µA, worth about 2 months |
| 2026-11-13 | WLCSP nRF54L15 on v2; QFN48 on v1 | QFN stack is 1.38 mm worst case |
| 2026-11-13 | Slim skins: 0.075 mm PET + 25 µm adhesive | 1.21 → 1.05 mm nominal, same battery life |
| 2026-11-13 | Face: printed design zone on the left, clear window on the right | Owner's look; the coil doubles as the charging target |
| 2026-11-13 | Raspberry Pi server, Fedora backup; Traccar core; ntfy alerts | Self-hosted, works on GrapheneOS |
| 2026-11-13 | Dwayne does placement and routing; Claude reviews | Owner preference |
| 2026-11-13 | C1 = 3 × 0402 X7R 50 V (100 + 100 + 33 nF trim); C2 = 2 × 0402 C0G; RECT = 3 × 2.2 µF 16 V 0402 | TI: X7R is fine for the RX tank and C1 should be 3 caps in parallel. Simulated C1 stress ≤ 1.5 V pk; RECT ripple 25 mV at 4 µF. Every part ≤ 0.55 mm (`sims/c1_stress.py`) |

## 2026-11-14 (rev 0.6, overnight run, from datasheets)
- **BQ51003 AD-EN is now no-connect** (was PGND). It is a push-pull output; TI SLUSBC8C p.5 says float it if unused. Grounding it would fight the driver.
- **BQ51003 ILIM/FOD rewired** to ILIM → R1 1.55k → FOD → RFOD 200R → PGND, per Fig. 32 and p.28. The rev 0.4 netlist left the ILIM ball unconnected. Added ROS1 20k RECT→FOD (TI default) and DNP ROS2 and RFOD2 for FOD calibration.
- **S-82N1B variant: S-82N1BAA (VCU 4.310 V).** ABLIC lists no 4.20 V part, and a protector set at the charger's own 4.20 V would nuisance-trip. The protector is a backup above the charger.
- **S-82N1B PS pin to VSS through a 0R and a test pad.** A GPIO ship mode doesn't work directly because VPSH = 0.9·VDD.
- **v1 RF match follows Nordic's QFN48 config 1** (2.7 nH, 3.5 nH ×2, 1.5 pF, 2.0 pF), not the CSP values. Topology is pending the Nordic figure.
- **Q1 = onsemi EFC4615R-TR** (LCSC C605382). Common drain, 0.37 mm tall, 33 mOhm typical source-to-source at 3.1 V gate, 1000 in stock at JLC. Backup: EFC4626R (0.20 mm, 45 mOhm, 150 in stock). Discharge overcurrent then trips at about 0.9 to 1.2 A.
- **Nordic QFN48 config 1 adopted for v1** (Dwayne approved): Nordic's 50 Ohm RF match, then our IFA L-match as a second stage with DNP full pi pads; 0603 4.7 uH DC/DC inductor; 2016 32 MHz crystal.
- **R1 = 1.50 k (E96)** instead of 1.55 k, which isn't stocked or E96. R1 + RFOD = 1.70 k → IMAX 154 mA, hardware limit 185 mA (SLUSBC8C eq. 2). Still above the 66 mA charge plus the system load.
- **v1 BOM substitutions (JLC stock):** L4/L5 LQP03TN3N5B02 (TN, Q≈14) for Nordic's LQP03HQ3N5B02 (not stocked); C7/C8 470 nF 50 V X5R. U3 S-82N1BAA and U4 TPS7A0233PDQNR are not in JLC stock; order them through JLC Global Sourcing or consign them.
- **R6 (S-82N1B VM resistor) 2 k → 470 Ω.** ABLIC's external-parts table gives R2 = 300 to 750 Ω, typical 470 Ω. 2 k was outside the range in the rev 0.4 netlist. Found in improve pass 1.
- **R_PS 0 Ω → 1 kΩ.** ABLIC R3 (PS input protection) is typically 1 kΩ. PS still tied low (normal operation).
- **DECRF routing:** Nordic DevZone (thread 127617) warns that routing DECA/DECRF under XC1/XC2 couples noise into the HFXO and recommends 4-layer with an inner ground for QFAA. v1 2-layer: DECRF crosses XC at right angles only. On the 4-layer build (needed anyway for U1 via-in-pad), put DECRF on an inner signal layer under a ground layer.
- **Y1 = Murata XRCGB32M000F1S1BR0** (ESR 50 Ω, ±10 ppm). The 80 Ω part was marginal against Nordic Fig. 17.
- **L2 = Murata LQM18PN4R7MFRL** (4.7 µH, 620 mA, 550 mΩ). It meets Nordic's ≥ 120 mA / ≤ 650 mΩ; the value-only match had picked a 15 mA, 2.1 Ω part.
- **C9d 4.7 µF 25 V 0603 added on RECT (v1).** TI's minimum is 4.7 µF, and 3 × 2.2 µF 0402 derate below that at 7 V. For v2, re-check the derated total with the real MPN curves.
- **v1 layout split:** MCU+RF and Qi RX sit in the v2 electronics zone; charger, protector, LDO, jumpers, headers and test pads sit in the battery-pocket area (v1 only; the cell is off-board on J1/BT1).
- **NT1 removed:** pin 32 (VSS_PA) is GND in the netlist; Nordic's pin 32 → EP-only topology is enforced in the layout by keepouts and a scripted trace.

## 2026-11-14 (afternoon): v1 goes 4-layer
- **v1 stackup = JLC 4-layer, 0.8 mm, ENIG** (Dwayne approved 2026-11-14). F.Cu signals + GND pour | In1 solid GND plane (KiCad "power" layer, never routed) | In2 signals + GND pour | B.Cu signals + GND pour. Outer prepreg 3313, 0.0994 mm, Dk 4.1; inner copper 0.5 oz (jlcpcb.com/impedance). 0.8 mm is JLC's thinnest listed 4-layer impedance stackup; v1 thickness is free (CLAUDE.md).
- **Why:** the BQ51003 DSBGA inner balls need via-in-pad, and JLC's BGA guide only allows a via opening on one side of a BGA pad for 4-layer ("Only one side with openings: Available"; 2-layer: unavailable). Also gives the nRF54L15 the inner ground Nordic DevZone 127617 recommends.
- **Correction to the overnight note:** JLC does **not** resin-fill and cap (POFV) via-in-pad on 4-layer; that is default and free on 6-layer and up only. On 4-layer the U1 vias are open in the pad on top and tented on the bottom (board default tenting both sides), so some solder wicks into the 0.15 mm holes. Fallback if JLC's DFM rejects it or assembly yields voids: order 6-layer for free POFV.
- **RF line:** 50 Ω GCPW over In1 is now 0.20 mm wide with a 0.15 mm gap (h 0.0994, Dk 4.1, script calc 49.9 Ω), was 0.49 mm over 0.33 mm on 2-layer.
- **Keep-outs** for the antenna and the Qi coil now cover all four copper layers.
- **Rules:** JLC multilayer 0.09/0.09 mm track/space, via hole to track 0.2 mm, standard via 0.5/0.25; U1 via-in-pad 0.25/0.15 (extra-cost via option at order time) (jlcpcb.com/capabilities/pcb-capabilities).

## 2026-11-14 (afternoon, later): v1 dev I/O and coil footprint
- **Dev I/O added at Dwayne's request ("as much as possible a dev board"):** 2 LEDs, 2 user buttons, a reset button and an FTDI-order UART header. Details and values are in `docs/03_schematic_spec.md` (v1 dev-board additions) and `design/values_calc.py`.
- **Pins:** buttons and UART follow the nRF54L15 DK (Zephyr `nrf54l15dk_common.dtsi` / `-pinctrl.dtsi`, read 2026-11-14): sw0 P1.13, sw1 P1.09, uart30 TX P0.00 / RX P0.01. The LEDs moved off the DK pins (P2.09 / P1.10) to P2.06 / P1.11 because escapes for pins 20 and 38 are blocked by the VDD via at C22 and the DECA cap column.
- **No UART RTS/CTS:** logs don't need flow control, and dropping it frees two congested QFN escapes.
- **4.7 kΩ UART series resistors**, so an unpowered side is never back-fed by more than 0.57 mA. Cable VCC is not connected.
- **Coil footprint changed to the Würth hole pattern** (2 × Ø1.2 mm, 5.0 mm). The overnight SMD lands were a guess. The keep-out radius grew from 13.0 to 13.45 mm, because the coil is Ø26.3 ± 0.3 mm (the old keep-out was smaller than the coil).
- **Routing helpers:** small 0.3/0.15 escape vias are placed automatically for the new QFN pins (`postroute_v1.py`, `ESCAPES`); the tact-switch twin pads are linked under the body.
