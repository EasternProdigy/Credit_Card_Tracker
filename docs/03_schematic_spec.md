# 03 Schematic specification

Functional pin names only. Map them to pin or ball numbers from the datasheets before capture (see CLAUDE.md, rule 1). Net names must match `design/netlist.yaml`.

## Block A: Qi receiver (sheet `qi_rx`)
| Ref | Part | Value | Connections | Notes |
|---|---|---|---|---|
| L1 | Würth 760308101309 | 10 µH, Ø26 × 0.5 mm | pin1 → C1 → `AC1`; pin2 → `AC2` | shielded receiver coil |
| C1a, C1b, C1c | series resonant cap, **3 in parallel**, X7R 50 V **0402 (0.5 to 0.55 mm)** | 100 nF + 100 nF + 33 nF trim = 233 nF (target 230 nF; C1c is the bench-tuned trim) | `COIL1` ↔ `AC1` | TI recommends X7R and 3 parallel caps for C1. Simulated stress ≤ 1.5 V peak, ≤ 0.19 A rms. Parts: Murata GRM155R71H104KE14 or TDK C1005X7R1H104K050BE |
| C2a, C2b | parallel detection cap, **2 in parallel**, C0G 50 V 0402 | 2.2 nF + 330 pF = 2.53 nF (target 2.56 nF) | `AC1` ↔ `AC2` | Sees up to 15.2 V peak (simulated); 50 V rating |
| U1 | TI BQ51003YFP | | AC1, AC2, BOOT1, BOOT2, RECT, OUT, CLAMP1, CLAMP2, COMM1, COMM2, ILIM, FOD, TS/CTRL, AD, AD-EN, EN1, EN2, CHG, PGND | WPC v1.2, 5 V output |
| C3/C4 | BOOT1 to AC1, BOOT2 to AC2 | 10 nF, 25 V | | per TI typical application |
| C5/C6 | COMM1 to AC1, COMM2 to AC2 | 22 nF, 25 V | | |
| C7/C8 | CLAMP1 to AC1, CLAMP2 to AC2 | 470 nF, 25 V | | |
| C9a to C9c, C10 | RECT to PGND | 3 × 2.2 µF 16 V X5R 0402 (≤ 0.55 mm) + 100 nF | net `VRECT` | ≥ 4 µF effective at 7 V bias → about 25 mV ripple (simulated). TI rates RECT caps at 16 V; OVP is 15 V |
| C11 | OUT to PGND | 4.7 µF 10 V X5R 0402 + 100 nF | net `V5_RX` | TI uses 10 µF + 0.1 µF at 500 mA; we run 150 mA |
| R1 | ILIM to PGND, with RFOD | 1.55 kΩ | R1 + RFOD = 1.75 kΩ → IMAX = 262/1750 = 150 mA | |
| RFOD | FOD to ILIM node per datasheet | 200 Ω start | | calibrate with TI SLUC577 |
| R_TS | TS/CTRL to PGND | 10 kΩ | | no RX-side NTC; check the datasheet's TS-disable method |
| | AD, AD-EN | to PGND | | no wired input |
| | EN1, EN2 | to PGND | | enabled |
| | CHG | NC (or test pad) | | |

## Block B: charger (sheet `charger`)
| Ref | Part | Value | Connections |
|---|---|---|---|
| U2 | TI BQ25101YFP (DSBGA-6, 0.5 mm max) | | IN `V5_RX`, OUT `VCELL`, ISET, TS, CHG, VSS |
| C12 | IN to GND | 1 µF, 10 V | |
| C13 | OUT to GND | 1 µF, 6.3 V | |
| R2 | ISET to GND | 2.05 kΩ 1 % | ICHG = 135 A·Ω / 2.05 kΩ = 66 mA (0.49C) |
| TH1 | 10 kΩ NTC, β ≈ 3370, thin film bonded to the cell | | TS to GND. Candidates: 103AT class, or thin-film 103JT (β 3435; verify JEITA shift) |
| | CHG | | net `nCHG` (open drain) → U5 GPIO with internal pull-up |

## Block C: cell and protection (sheet `battery_protect`)
| Ref | Part | Value | Connections |
|---|---|---|---|
| BT1 | Grepow GRP0849049, 4.2 V, 135 mAh, 49 × 49 × 0.85 mm | | + → `VCELL`/`VBAT`; − → protection FETs |
| U3 | ABLIC S-82N1B (SNT-6A), choose the 4.20 V detection variant | 600 nA typ | VDD (via 330 Ω + 0.1 µF), VSS, DO, CO, VM (via 2 kΩ), PS |
| Q1 | dual N-MOSFET, common drain, ≤ 30 mΩ, CSP ≤ 0.4 mm tall | TBD | DO → discharge FET gate, CO → charge FET gate. Pack− = system `GND` |
| | PS pin | | Wire per datasheet for normal operation. Option: route to a U5 GPIO for a ship mode (50 nA). |

## Block D: supply and battery sense (sheet `power_sense`)
| Ref | Part | Value | Connections |
|---|---|---|---|
| U4 | TI TPS7A0233PYCH (v2) / TPS7A0233PDQN (v1) | 3.3 V, 25 nA | IN `VBAT`, EN tied to IN, OUT `VDD_3V3`, GND |
| C14 | IN | 1 µF | |
| C15 | OUT | 4.7 µF | |
| R3/R4 | VBAT → `VBAT_SENSE` → GND | 10 MΩ / 10 MΩ, 1 % | 0.21 µA |
| C16 | `VBAT_SENSE` to GND | 100 nF | lets the SAADC sample a 5 MΩ source (0.08 mV error, simulated) |

## Block E: nRF54L15 (sheet `mcu`)
Copy Nordic's reference exactly: CAAA config 1 for v2, QFN48 config 1 for v1. The listed values are from the CAAA config-1 schematic; DEC* pin assignments come from Nordic.
| Ref | Part | Value | Notes |
|---|---|---|---|
| U5 | Nordic nRF54L15-CAAA (v2) / -QFAA (v1) | | |
| C17 to C21 | VDD decoupling | 10 µF, 2.2 µF ×2, 100 nF ×2, 10 nF | place per Nordic layout |
| L2 | DC/DC inductor | 4.7 µH 0402 | + FB1 0201 ferrite bead per reference |
| Y1 | 32 MHz crystal, 1612 | per Nordic BOM | internal load caps |
| Y2 | 32.768 kHz crystal, 2012 | per Nordic BOM | saves about 0.6 µA versus LFRC; keep it |
| | AIN (P1.x analog) | `VBAT_SENSE` | |
| | GPIO | `nCHG` | |
| TP1 to TP5 | SWDIO, SWDCLK, nRESET, VDD_3V3, GND | pogo/Tag-Connect pads | |
| | NFC1/NFC2 | DNP until v2.1 | NFC loop antenna later |

## Block F: RF and antenna (sheet `rf_antenna`)
| Ref | Part | Value |
|---|---|---|
| L3, L4, L5 | Murata LQP03HQ 3.6 nH, 4.6 nH, 2.0 nH | Nordic CAAA config-1 match (Nordic marks it preliminary; use their latest) |
| C25, C26, C27 | 3.9 pF, 1.2 pF, 1.2 pF 0201 | same |
| L6 | 2.2 nH 0201, series toward the antenna | antenna L-match (NEC-2 result; retune on the bench) |
| C28 | 0.2 pF 0201, shunt | same; add DNP pads for a full π if space allows |
| ANT1 | printed IFA | arm 20 mm (trim zone 19 to 24 mm), short-to-feed 3 mm, height 6 mm above the ground edge, 0.5 mm trace |
