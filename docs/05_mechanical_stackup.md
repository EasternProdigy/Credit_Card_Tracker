# 05 Mechanical stackup (v2)

## Layers, bottom to top
| Layer | Material | Thickness (mm) | Tolerance |
|---|---|---|---|
| Bottom skin | Black PET | 0.075 | ±0.008 |
| Adhesive | 25 µm transfer adhesive | 0.025 | ±0.003 |
| Core | 1.0 mm black G10 or PC frame with laser-cut pockets; contents below | ≤ 0.85 | |
| ↳ battery pocket | Grepow GRP0849049 | 0.85 | ±0.05 |
| ↳ coil | flex 0.12 + coil 0.50 | 0.62 | |
| ↳ electronics | flex 0.12 + PI stiffener 0.10 + tallest part 0.625 | 0.845 | |
| Adhesive (print zone only) | 25 µm optically clear adhesive | 0.025 | ±0.003 |
| Top skin | Clear PET, reverse-printed on the left 51.5 mm | 0.075 | ±0.008 |

## Thickness results
| Region | Nominal | RSS | Worst case |
|---|---|---|---|
| Battery | 1.050 | 1.101 | 1.122 |
| Coil | 0.820 | 0.875 | 0.912 |
| Electronics (CSP) | 1.045 | 1.088 | 1.137 |
| Electronics if QFN48 | 1.270 | 1.329 | 1.382 |

The frame thickness should match the tallest pocket content plus about 0.05 mm, leaving swell room for the cell (LiPo grows 3 to 5 % over its life).

## Face
- **Left 51.5 mm:** design zone over the battery, second-surface printed black + metallic gold.
- **Right 33.6 mm:** clear window over the coil, the electronics and the antenna. The skin bonds to the frame perimeter only, with no glue over the parts.
- **Light-shield dots:** printed opaque above U5 (WLCSP) and U1 (DSBGA).
- **Metallic ink or foil:** never within 5 mm of the antenna keep-out, never over the coil.

## Assembly
- Cold lamination only. No heat or ultrasonic welding over the LiPo.
- The cell is bonded with pressure-sensitive adhesive, not potting, so it has room to swell.
- The NTC is bonded to the cell surface.

## Wallet fit
Double Oak bifold, outside leather pocket, the card alone in the pocket. Qi charges through one leather wall; place the wallet pocket-side down with the visible coil over the pad's center.
