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
