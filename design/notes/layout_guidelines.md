# Layout guidelines collected for v1 (sources cited)

## TI BQ51003 (SLUSBC8C section 11.1, p.33)
- Lowest possible resistance on AC1, AC2 (and OUT). Ratings at 1 A charge: AC 1.2 A, OUT 0.5 A, RECT 0.1 A rms, COMM 0.3 A, CLAMP 0.5 A, others ≤ 10 mA. We run 150 mA, so 0.4 mm AC traces are generous.
- Detection (C2) and resonant (C1) caps as close to the device as possible.
- COMM, CLAMP and BOOT caps as close to the device as possible.
- PGND via interconnect is critical: **two vias per power-stage cap**, one per small-signal cap.
- HF bypass caps close to RECT and OUT.
- Minimize the ILIM and FOD resistor loops to PGND.
- AC1, AC2, BOOT, COMM are the noise sources: put ground copper under them, and keep them away from sense traces.

## TI BQ25101 (SLUSBV8C section 11.1, p.24)
- IN and OUT caps as close as possible, with short runs to IN, OUT and GND.
- Keep low-current GND separate from the charge path; single-point ground.
- Size IN and OUT for the charge current.

## TI TPS7A02 (SBVS277C section 8.4.1)
- CIN and COUT close to the device. Thermal vias around the device, **never under the DQN thermal pad** (solder wicking).

## Nordic nRF54L15 QFN48 (datasheet v1.0, section 10.3.1, Fig. 180 notes)
- "Place matching network as close as possible to the IC."
- **C6 (our C25) ground connects ONLY to pin 32 (VSS_PA) on the top layer; pin 32 connects ONLY to pin 49 (center pad) underneath the package.**
- **C9 (our C26) ground must be isolated from all ground layers except the bottom ground layer.**
- Use Nordic's reference layout for RF performance (the PCB files on nordicsemi.com are blocked to scripts; not available tonight).
- General (Nordic, project docs/04): decaps at their pins, DC/DC inductor right at DCC with the smallest loop, 32 MHz crystal within 3 mm with no traces underneath, GND vias ≤ 3 mm apart along the RF path.

## Project rules (docs/04_layout_constraints.md)
- Coil Ø26 at (68.05, 38.98): no copper inside except the two lands. Antenna keep-out x 52.5 to 83.6, y 2.0 to 9.5: only IFA copper. Ground edge y = 10.5 with stitching ≤ 3 mm. V5_RX, VCELL, VBAT ≥ 0.3 mm; AC1/AC2 ≥ 0.4 mm.
