# Questions for Dwayne (overnight run 2026-11-14)

1. **Nordic reference files (blocking).** docs.nordicsemi.com returns 403 to scripts. Please download the nRF54L15 QFN48 reference design (config 1 schematic + layout) and the nRF54L15 DK hardware files in a browser into `design/ref/`. Without them I can't wire the decoupling, FB1 or RF match without guessing, which the rules forbid. *Safe choice taken:* MCU sheet not captured.
2. **MCU pin assignment:** VBAT_SENSE on P1.04/AIN0 (pin 5), nCHG on P1.05 (pin 6). OK for firmware?
3. **S-82N1BAA (4.31 V)** instead of a "4.20 V" variant, which doesn't exist off the shelf and would trip at the charger's 4.20 V. OK?
4. **Freerouting:** no jar in `~/tools/`. Download the official GitHub release, or will you route it all by hand?
5. **gitleaks** isn't installed, so the pre-commit secret scan is a no-op: `sudo dnf install gitleaks`.
6. **Q1 (O6)** still has no part: a common-drain dual NMOS, CSP, ≤ 0.4 mm. Do you want me to shortlist parts in stock at LCSC?
