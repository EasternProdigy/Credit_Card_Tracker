# Questions for Dwayne (overnight run 2026-11-14)

## TOP ISSUE (blocks ordering v1 as specified)
0. **The BQ51003 (DSBGA-28, 0.4 mm, 4 x 7) can't be routed on a standard JLC 2-layer board.** Five inner balls are fully enclosed by edge balls on other nets: RECT (C2, C3), CLAMP2 (E2), CLAMP1 (E3), FOD (F2). The gap between balls is 0.15 mm, and a trace needs at least 0.27 mm. They need via-in-pad. JLC's BGA guide supports 0.15 mm drill / 0.25 mm via-in-pad (plugged) on 4-layer boards and lists that option as unavailable on 2-layer (https://jlcpcb.com/help/article/bga-design-guidelines---pcb-layout-recommendations-for-bga-packages).
   *Safe option taken:* the routing branch uses 0.15/0.25 via-in-pad on those 5 balls only, with everything else at 2-layer JLC rules. **Order v1 as JLC 4-layer** (add solid GND on In1 and In2; thickness doesn't matter for v1), or use an HDI-capable fab. Get JLC's DFM check on the via-in-pad before paying. This also applies to v2 flex: ask the flex fab about microvias, or choose a different Qi RX package.
   **Answered 2026-11-14: 4-layer OK.** The routing branch is now JLC 4-layer 0.8 mm (see decision log, "v1 goes 4-layer").
   **Correction:** the note above says "plugged". JLC does not fill and cap vias in pads on 4-layer; free POFV is 6-layer and up only. On 4-layer the 0.15 mm vias stay open in the pad (tented on the bottom), so a little solder wicks in. Also, JLC lists a 0.25 mm minimum BGA pad; TI's land is 0.23 mm (ours 0.225 mm). Ask JLC's DFM to accept both, or order 6-layer (free POFV) if they won't.

1. **Nordic reference files (blocking).** docs.nordicsemi.com returns 403 to scripts. Please download the nRF54L15 QFN48 reference design (config 1 schematic + layout) and the nRF54L15 DK hardware files in a browser into `design/ref/`. Without them I can't wire the decoupling, FB1 or RF match without guessing, which the rules forbid. *Safe choice taken:* MCU sheet not captured.
2. **MCU pin assignment:** VBAT_SENSE on P1.04/AIN0 (pin 5), nCHG on P1.05 (pin 6). OK for firmware?
3. **S-82N1BAA (4.31 V)** instead of a "4.20 V" variant, which doesn't exist off the shelf and would trip at the charger's 4.20 V. OK?
4. **Freerouting:** no jar in `~/tools/`. Download the official GitHub release, or will you route it all by hand?
5. **gitleaks** isn't installed, so the pre-commit secret scan is a no-op: `sudo dnf install gitleaks`.
6. **Q1 (O6)** still has no part: a common-drain dual NMOS, CSP, ≤ 0.4 mm. Do you want me to shortlist parts in stock at LCSC?

## Added during the run (safe option taken, keep going)
7. **Coil lands (O20):** Würth's datasheet is blocked to scripts. v1 has generic 1.5 x 2.5 mm lands 4 mm apart at the bottom of the coil circle. Check them against your coil sample before ordering.
8. **Dev parts in the battery area:** on v1 the cell sits off-board on J1/BT1. The SWD header, PPK2 headers and spare test pads go in the left (battery pocket) area, which gets a ground pour that stands in for the cell pouch in the antenna sim. The electronics zone layout stays v2-like.
9. **v1 NTC:** TH1 is an on-board 0402 10 k NTC (B 3380). For JEITA on the real cell, swap TH1 for a wired NTC or set R_TSD.
10. **Answered by you at 05:15 (logged):** Nordic files, MCU pins, S-82N1BAA, Freerouting, Q1. Thanks. Items 1 to 6 above are closed.
11. **Hand-fix opens on the routed v1** (branch `overnight-routing`): U5 pin 36 VDD + C23 island (no via room on 2 layers), nCHG_MCU at pin 6, NFC1 (DNP), P0.00 → TP26. *Safe option taken:* left for you; on a 4-layer build pin 36 is one inner-layer link. **Closed 2026-11-14:** the 4-layer reroute connects all of them (0 unconnected).
12. **Cell polarity:** J1/BT1 pin 1 = VCELL (+), marked "+" on silk. Check the Grepow lead order before plugging in (O24).
13. **U3 S-82N1BAA and U4 TPS7A0233PDQNR are not in JLC stock.** Order through JLC Global Sourcing, or consign them.
14. **R6 470 Ω, R_PS 1 kΩ, L2 LQM18PN4R7MFRL, Y1 XRCGB32M000F1S1BR0, C9d added:** datasheet-driven fixes from the improve passes. Shout if any conflicts with something you know from the bench.
