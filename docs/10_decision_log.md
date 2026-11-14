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
