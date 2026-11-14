# 04 Layout constraints (Dwayne routes; Claude checks)

The earlier routing sketch is not a layout. Only the constraints below are binding.

## Zones (card coordinates in mm, origin at the bottom-left corner, x along 85.6, y along 53.98)
| Zone | Bounds | Rule |
|---|---|---|
| Battery pocket | x 2.0 to 51.0, y 2.49 to 51.49 | No PCB under the cell (side by side). Tabs land in the stiffener zone. |
| Coil | circle center (68.05, 38.98), Ø26 | **No copper on any layer** inside the coil footprint, apart from its two lands. |
| Electronics + stiffener | x 52.5 to 83.6, y 10.5 to 25.0 | All ICs and passives. Solid GND on L2. |
| Antenna keep-out | x 52.5 to 83.6, y 2.0 to 9.5 | Only the IFA copper. No GND, no parts, no metallic ink or foil within 5 mm. |
| Ground edge | y = 10.5 | GND stitching vias every ≤ 3 mm along it |

## Height budget
- Max part height above the flex is **0.625 mm** (v2).
- Passives must be thin-profile, ≤ 0.6 mm: **0402 or 0201 only, nothing 0603 or larger.**
  - **C1 (solved, rev 0.4):** 3 × 0402 X7R 50 V in parallel (100 + 100 + 33 nF), 0.5 to 0.55 mm. Place all three right at the coil lands with short, wide traces.
  - **C2:** 2 × 0402 C0G (2.2 nF + 330 pF).
  - **RECT:** 3 × 2.2 µF 16 V X5R 0402 + 100 nF, tight to U1.RECT.
  - Crystals: 1612 and 2012 low-profile versions only.
- Check every footprint's 3D model height. List anything over 0.6 mm in `docs/09_open_items.md`.

## Critical routing
| Net / area | Rule |
|---|---|
| RF: U5.ANT → match → IFA feed | Under 3 mm total. GND on both sides, vias ≤ 3 mm apart. Match parts in a straight line. |
| DC/DC loop | L2 directly beside DCC, smallest loop to the VDD caps, nothing sensitive underneath |
| Y1 32 MHz | Within 3 mm of XC1/XC2, GND guard ring, no traces underneath on either layer |
| AC1/AC2 coil leads | ≥ 0.4 mm wide, short; C1/C2 at the coil lands |
| VRECT | RECT caps tight to U1; short, wide |
| V5_RX, VCELL, VBAT | ≥ 0.3 mm |
| Battery tabs | Land inside the stiffener zone, with strain relief; no solder joints across a bend |
| Flex (v2) | No vias or parts across bend lines; curved traces, teardrops; hatched GND outside the stiffener |
| Light | Leave room on the skin above U5 and U1 for printed light-shield dots (WLCSP) |

## Appearance (the window shows the board)
- Black coverlay, ENIG.
- Parts on a 0.5 mm grid, aligned edges, consistent rotation.
- Traces at 45° or curved, evenly spaced.
- Silkscreen minimal (white or gold).
- The antenna and coil copper are visible design elements.

## Stackups
- **v1:** 2-layer FR4, 0.4 mm, 1 oz, ENIG. JLCPCB PCBA needed for the DSBGA parts.
- **v2:** JLCPCB 2-layer polyimide flex, 0.12 mm finished, ENIG, black coverlay, 0.10 mm polyimide stiffener under the electronics zone only. No steel stiffener, because it detunes the coil and antenna.
- **RF trace:** too short for impedance control to matter (≈ 2 % of λ). Still, get the 50 Ω width from the fab's calculator for v1 (FR4) and v2 (thin PI). On thin PI, microstrip is very narrow, so use coplanar waveguide with ground (GCPW).
