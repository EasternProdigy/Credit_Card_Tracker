# 09 Open items (close each with a source or a measurement)

| # | Item | Why it matters | How to close |
|---|---|---|---|
| O1 | Pin and ball maps for every IC | Netlist uses functional names | Datasheets plus Nordic reference → `design/pinmaps/` |
| O2 | ~~nRF54L15 DEC* pins and FB1~~ **CLOSED 2026-11-14 (v1 QFN48):** datasheet v1.0 Fig. 180 / Table 87, see `design/pinmaps/nRF54L15_QFN48.md`; CSP still open for v2 | Core supply correctness | Nordic CAAA and QFN48 config-1 schematics, DK and Tag files |
| O3 | Package heights: nRF54L15 CSP, BQ51003 YFP, S-82N1B SNT-6A, crystals | Height budget 0.625 mm | Package drawings |
| O4 | ~~C1 height~~ **CLOSED rev 0.4:** 3 × 0402 X7R (TI says X7R works; split C1 three ways). Remaining: pick the C1c trim value after measuring Ls′ | | Bench gate 3 |
| O5 | ~~RECT cap height~~ **CLOSED rev 0.4:** 3 × 2.2 µF 16 V 0402. Confirm the exact MPN is ≤ 0.55 mm and check its DC-bias curve | | Datasheet |
| O6 | ~~Q1 dual NMOS part~~ **CLOSED 2026-11-14:** onsemi EFC4615R-TR, 0.37 mm, see `design/pinmaps/EFC4615R.md` | Protector needs FETs | Parametric search |
| O7 | ~~S-82N1B variant~~ **CLOSED 2026-11-14:** S-82N1BAA (4.31 V), PS to VSS; see `design/pinmaps/S-82N1B.md` | Protection thresholds | ABLIC datasheet |
| O8 | ~~TS/CTRL handling~~ **CLOSED 2026-11-14:** 10 kΩ to GND (SLUSBC8C p.5) | Correct enable | BQ51003 datasheet |
| O9 | Thin-film NTC on the cell (β ≈ 3370) | JEITA accuracy | Semitec JT or similar, plus JEITA threshold check |
| O10 | Real Ls′ with the cell pouch and leather in place | C1, C2 | Bench gate 3 |
| O11 | Pad FOD behavior at weak coupling (pad coil about 2 to 6 A rms) | Charging reliability | Bench gate 3 |
| O12 | In-wallet εr,eff for the antenna (1.3 assumed) | IFA length and match | Bench gate 5 (NanoVNA) |
| O13 | Everytag real idle floor on the nRF54L15 | Battery life | Bench gate 2 |
| O14 | GrapheneOS can unlock Google E2EE keys | Google setup | Try it; fallback is a stock Android phone, once |
| O15 | GoogleFindMyToolsWebUi arm64 image | Pi deployment | Pull or build |
| O16 | ~~nRF54L15 minimum VDD~~ **CLOSED:** 1.7 to 3.6 V (datasheet v1.0) | Not critical at 3.3 V | Datasheet |
| O17 | Grepow cell protection board present or not | Avoid double protection, thickness | Ask Grepow |
| O18 | ~~nRF54L15 QFN48 config-1 schematic wiring~~ **CLOSED 2026-11-14** (Dwayne supplied datasheet v1.0) (cap-to-pin, FB1 position, RF match order) | Blocks the v1 MCU sheet | Download Nordic's QFN48 reference design files by browser into `design/ref/` (site blocks scripts) |
| O19 | BQ51003 YFP package height | Height budget | TI YFP0028 drawing |
