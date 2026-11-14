# 01 Requirements

| ID | Requirement | Target | Status |
|---|---|---|---|
| R1 | Form factor | ISO/IEC 7810 ID-1: 85.60 × 53.98 mm, corner radius 3.18 mm | fixed |
| R2 | Thickness | ≤ 1.15 mm worst case (v2); 1.05 mm nominal | simulated: 1.137 mm worst case |
| R3 | Location networks | Google Find Hub (priority) + Apple Find My, simultaneously | protocol verified |
| R4 | Google frame rate | ≥ 1 FHN frame every 2 s at ≥ 0 dBm (Find Hub spec) | 1.93 s with `multPeriod=1` |
| R5 | Charging | Any Qi BPP pad, through one wall of the leather pocket | simulated; needs bench gate 3 |
| R6 | Charge time | ≤ 3 h from empty | 2.1 to 2.3 h simulated |
| R7 | Battery life | ≥ 9 months per charge (90 % confidence) | 9.3 months p5, 10.7 median |
| R8 | Low-battery alert | Remote alert to the owner | via Apple status bits → Pi → ntfy |
| R9 | Not-seen alert | Alert if no report in N days | Traccar inactivity → ntfy |
| R10 | Owner app | Phone (GrapheneOS, no Google app) + desktop; items grouped in "bundles" | Traccar backend verified; PWA to build |
| R11 | Server | Raspberry Pi primary, Fedora backup | verified on Traccar 6.6 |
| R12 | Look | Left: printed black + gold design zone. Right: clear window over the electronics | defined |
| R13 | "If found" NFC | Passive NFC tag via the nRF54L15 NFCT | lowest priority, v2.1 |
| R14 | No speaker | Saves power and thickness | fixed |
| R15 | Safety | Cell protection, JEITA charging, NTC on the cell, no hot lamination over the LiPo | in design |
| R16 | Regulatory | Personal build, ≤ 5 units, 47 CFR 15.23; no marketing | n/a |
