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

## Reference circuit: QFN48 config 1 (SOURCE OF TRUTH for the v1 MCU sheet)
Source: nRF54L15/L10/L05 Datasheet v1.0 (4503_018), section 10.3.1, Figure 180 "Circuit configuration 1 schematic" (p.890) and Table 87 BOM (p.891). Local copy downloaded by Dwayne: `~/Downloads/nRF54L15_nRF54L10_nRF54L05_Datasheet_v1.0.pdf`. Wiring read from the rendered figure.

| Nordic ref | Our ref | Value / spec (Table 87) | Connection (Fig. 180) |
|---|---|---|---|
| C3 | C17 | 10 uF X6S 6.3 V 0402 | VDD (pins 47, 48) to GND |
| C10 | C21 | 100 nF X7R 0201 (marked optional) | VDD (47, 48) to GND |
| C4, C7, C8 | C20, C22, C23 | 100 nF X7R 0201 | VDD (10, 22, 36) to GND, one each |
| L1 | L2 | 4.7 uH 0603, 120 mA, 650 mOhm | DCC (46) to DECD (45) |
| C1 | C18 | 2.2 uF X6T 2.5 V 0201 | DECD (45) to GND |
| FB1 | FB1 | 120 Ohm @ 100 MHz, 200 mA, 0201 | DECD (45) to DECA/DECRF node |
| C2 | C19 | 2.2 uF X6T 2.5 V 0201 | DECA (43) + DECRF (33) to GND |
| C12 | C24 | 10 nF X7R 6.3 V 0201 | DECA/DECRF to GND |
| C5 | C30 | 2.2 nF X7R 10 V 0201 | DECA/DECRF to GND |
| X2 | Y1 | 32 MHz 2016, CL 8 pF, +/-40 ppm total | XC1 (34), XC2 (35); no external load caps |
| X1 | Y2 | 32.768 kHz 2012, CL 9 pF, +/-20 ppm | P1.00/XL1 (1), P1.01/XL2 (2); no external load caps |
| R1 | R7 | 1 kOhm 1 % 0201 | nRESET pin (30) in series to the NRESET header net |
| C13 | C31 | 3.9 pF C0G 0201 | nRESET pin (30) to GND (pin side of R1) |
| L2 | L3 | 2.7 nH LQP03HQ2N7B02 | series, ANT (31) to node A |
| C6 | C25 | 1.5 pF GJM0335C1E1R5WB01 | shunt node A to **VSS_PA (32) only**, top layer; pin 32 joins pin 49 only under the IC |
| L3 | L4 | 3.5 nH LQP03HQ3N5B02 | series, node A to node B |
| C9 | C26 | 2.0 pF GJM0335C1E2R0WB01 | shunt node B to GND; **ground isolated from all layers except the bottom ground** |
| L4 | L5 | 3.5 nH LQP03HQ3N5B02 | series, node B to RF (50 Ohm port) |
| C11 | C27 | 0.3 pF C0G 50 V 0201 | shunt RF to GND |

- VSS: pin 44 + exposed pad 49. VDD range 1.7 to 3.6 V (closes O16, 1.7 V).
- Package QFN48 6 x 6 mm: A max 0.90 mm, pitch 0.40 mm, EP 4.6 mm (4.5 to 4.7). Height is fine for v1 only.
- Our antenna L-match (L6 2.2 nH series, C28 0.2 pF shunt) follows the Nordic 50 Ohm RF port as a separate stage, with full pi pads (C28 + C32, both DNP except C28) per Dwayne 2026-11-14.
