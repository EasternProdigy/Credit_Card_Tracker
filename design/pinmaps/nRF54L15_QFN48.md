# U5 (v1): Nordic nRF54L15-QFAA (QFN48, 6 x 6 mm)
Source: Nordic "nRF54L15 | nRF54L10 | nRF54L05 Datasheet", chapter Pin assignments, "QFN48 (QFAA) package pin assignments", Table 4 (docs.nordicsemi.com, ps_nrf54l15/page/chapters/pin.html-qfn48), read 2026-11-14.
Cross-check: Nordic QFN48 config-1 schematic text gives DECRF 33, DECA 43, DECD 45, DCC 46; matches.

## Power, clock, RF, debug
| Functional name | Pin |
|---|---|
| VDD | 10, 22, 36, 47, 48 |
| VSS | 44, exposed pad 49 |
| VSS_PA (radio ground) | 32 |
| DECRF (0.9 V, must connect to DECA) | 33 |
| DECA (must connect to DECRF) | 43 |
| DECD | 45 |
| DCC (DC/DC output) | 46 |
| ANT | 31 |
| XC1 / XC2 (32 MHz) | 34 / 35 |
| XL1 / XL2 = P1.00 / P1.01 (32.768 kHz) | 1 / 2 |
| NFC1 / NFC2 = P1.02 / P1.03 | 3 / 4 |
| SWDIO | 25 |
| SWDCLK | 26 |
| nRESET | 30 |

## GPIO
P1.04/AIN0 5, P1.05/AIN1 6, P1.06/AIN2 7, P1.07/AIN3 8, P1.08/EXTREF 9, P2.00-P2.05 11-16, P2.06-P2.10 17-21 (P2.07 = SWO), P0.00 23, P0.01 24, P0.02 27, P0.03 28, P0.04 29, P1.09 37, P1.10 38, P1.11/AIN4 39, P1.12/AIN5 40, P1.13/AIN6 41, P1.14/AIN7 42.

## Proposed signal assignment (needs Dwayne/firmware OK, see QUESTIONS)
- VBAT_SENSE -> P1.04/AIN0 (pin 5): analog-capable, far from ANT (31).
- nCHG -> P1.05 (pin 6): plain GPIO with internal pull-up.
- Spare test pads: P2.07/SWO (pin 18), P0.00 (pin 23).

## Reference circuit (QFN48 config 1) BOM, from Nordic page text
C1, C2 2.2 uF 0201; C4, C7, C8 100 nF 0201; C10 100 nF 0201 (optional); C12 10 nF 0201; FB1 0201 bead (value not in text); L1 4.7 uH **0603**; X1 32.768 kHz 2012; X2 32 MHz **2016**; RF: L2 LQP03HQ2N7B02 (2.7 nH), L3 = L4 LQP03HQ3N5B02 (3.5 nH), C6 GJM0335C1E1R5WB01 (1.5 pF), C9 GJM0335C1E2R0WB01 (2.0 pF).

**BLOCKED (O2, extended):** the figure's wiring could not be read (Nordic's site blocks scripted downloads; the figure has no text netlist). Unknown: which pin each cap sits on, FB1 position, RF match series/shunt order. The netlist's L3-L5/C25-C27 values are from the **CSP** reference and do not apply to v1 QFN48.
