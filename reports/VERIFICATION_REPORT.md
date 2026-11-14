> Note (rev 0.3): thickness figures here assume the original 0.125 mm skins. The current stack is slim skins: 1.05 mm nominal, 1.137 mm worst case. See docs/05_mechanical_stackup.md.

# Wallet tracker card: deep technical verification pass

Date: November 13, 2026. Scope: every electronic subsystem, both tracking networks, and the server/app backend. Everything below was either simulated, computed from first principles, run against the real open-source code, or checked against a datasheet. Every number can be regenerated with the scripts in this folder.

## Verdict

The design works on paper and in simulation, with **one hard requirement and six corrections**. Nothing found here blocks the project. The remaining risks are things only real hardware can answer, and each one has a bench test assigned.

| Subsystem | Method | Result | Status |
|---|---|---|---|
| Qi coupling through leather | Maxwell/Neumann mutual-inductance model (elliptic integrals), 3 gaps, 3 offsets | k = 0.25 to 0.43 air-core (ferrite raises it) | PASS |
| Qi power transfer | ngspice transient of pad + card tank + rectifier, 110 to 205 kHz, k 0.20 to 0.45 | 5.8 V+ rectified at every k in the Qi band | PASS |
| Qi wake-up (ping) | ngspice at 175 kHz, light load | k ≥ 0.25 wakes the BQ51003 (UVLO 2.7 V); k = 0.20 does not | **CONDITIONAL**: card needs an alignment mark |
| Charging | BQ25101 CC/CV + Thevenin cell model, R0 0.3 to 1.5 Ω | 66 mA (0.49C), full in 2.1 to 2.3 h | PASS |
| Charging heat | Loss budget per part | ≤ 0.24 W in card, about 5 °C average rise | PASS (cell NTC still mandatory) |
| Supply under radio bursts | ngspice: cell + FETs + LDO model + nRF decoupling, +8 dBm event | VDD never below 3.23 V (min allowed 1.7 V), even with a cold aged cell | PASS |
| Battery voltage sensing | ngspice: 10M/10M divider + 100 nF + SAADC sample cap | 0.08 mV error, 0.21 µA draw | PASS |
| Battery life | Monte Carlo, 20,000 draws, inputs from Nordic measurements and Everytag source | Median 10.7 months (90%: 9.3 to 12.4) | PASS |
| PCB antenna | NEC-2 method of moments (PyNEC), real floorplan, battery coupling, in-wallet detuning, L-match | S11 ≤ -12 dB across all BLE channels after a 2.2 nH + 0.2 pF match | PASS (tune on bench) |
| Radio range | Friis + log-distance, body loss | about 20 to 25 m indoors, 70 to 80 m outdoors from a back pocket | PASS |
| Thickness | Worst-case and RSS tolerance stack per region | 1.31 mm worst case (CSP); QFN48 would be 1.56 mm | PASS with CSP only |
| Apple frame + crypto | Real P-224 ECDH + X9.63 KDF + AES-GCM round trip, frame built from Everytag's template | 31-byte frame; report decrypts with correct signed coordinates and battery bits | PASS |
| Google frame + crypto | GoogleFindMyTools' own EID and finder-encryption code, owner decryption | 29-byte frame; round trip OK; 337 key slots per 4-day registration | PASS after fix |
| Backend | Real Traccar 6.6 server: users, bundles, ingest, alarm forwarding, history | All calls 200; low-battery alarm forwarded to the alert bridge | PASS |

## Corrections found in this pass (new)

1. **Everytag's Google frame violates the Find Hub spec. Fix it before first flash.** Everytag hard-codes frame type `0x41` and a raw flags byte `0xC0`. The Find Hub spec says `0x41` means "unwanted tracking protection mode is on," and the flags byte must be XORed with the least significant byte of SHA256(r). The spec also numbers bits from the most significant end, so battery sits in mask `0x06` and the UTP bit is `0x01`. Everytag puts battery at `<< 5`, which is the wrong position.
   - **Fix:** send frame type `0x40`. Because our Google key is static, r never changes, so the server can precompute the XOR mask (the demo computed it) and the firmware just sends a constant correct byte, for example `0x02 ^ mask` for "normal battery." This is a roughly 10-line firmware patch.
2. **Everytag's default timing breaks Google's 2-second rule.** With the default `multPeriod = 2`, each network gets a frame only every 3.86 s. The spec expects at least one frame every 2 s at 0 dBm or more.
   - **Fix:** set `multPeriod = 1` (each network every 1.93 s). This costs about 3 months of battery (12.8 to 9.8 months); the settings fix below wins about 1 month back, giving the 10.7-month figure.
3. **Everytag opens a connectable "settings window" every 60 s.** That costs about 1.3 µA.
   - **Fix:** raise `INTERVAL_SETTINGS` to 600 s and change the default settings password `abcdefgh`.
4. **Apple battery reporting needs the support flag.** macless-haystack decodes battery from the top two status bits, but it treats a status byte of `0x00` as "unknown." Everytag's battery mode with a full cell sends `0x00`.
   - **Fix:** set Everytag's first status byte to `0x20`, so the status becomes `0x20 | (level << 6)`. The demo confirms a "low" report decodes correctly.
5. **Our Pi must decrypt Apple reports itself.** macless-haystack's server only fetches encrypted reports, and decryption happens in its Flutter app. Our backend decrypts in Python, and the protocol demo is that decryptor.
   - It must decode coordinates as **signed** 32-bit integers. Decoded as unsigned, Cambridge's longitude comes out as 358.38 instead of -71.12.
6. **Use a 3.3 V LDO, not 2.8 to 3.0 V, plus a low-Iq protector.** With an LDO, battery current equals load current, and the nRF54L15's internal DC/DC draws less current at a higher supply. So the highest VDD under the 3.6 V limit wins. TPS7A0233 (3.3 V, 0.64 mm DSBGA, 25 nA) exists and is Active.
   - Pair it with the ABLIC **S-82N1B** protector (600 nA typical, 990 nA max) instead of a BQ2970/DW01 class part (4 µA or more). That is worth about 2 extra months.

Also confirmed: the Everytag repo's `bq2512x.c` targets TI's I2C BQ25120A charger. We use the pin-programmed BQ25101, so that driver gets disabled and the charger's CHG pin is read on a GPIO instead.

## The hard requirement: alignment mark

The card only wakes up on the pad if coupling k ≥ 0.25. In the coupling model, that holds at the worst gap (3 mm pad surface + 2 mm leather) only within about 10 mm of center. This matches the Everytag author's note that small receive coils don't work with every charger.

The card face needs a visible coil-center mark, the way Nomad does it, and the coil should be the largest one that fits (26 mm). Bench Demo 3 has to try at least 3 different pads.

## Numbers you'll use in the schematic

| Item | Value | Basis |
|---|---|---|
| Qi coil | Würth 760308101309, 26 mm, 0.5 mm, 10 µH | catalog |
| C1 (series) | about 220 to 230 nF (measure Ls' in the final stack) | C1 = 1/((2π·100 kHz)²·Ls'), verified against TI's worked example |
| C2 (parallel) | about 2.56 nF | C2 = 1/((2π·1 MHz)²·Ls − 1/C1) |
| BQ51003 RILIM | about 1.75 kΩ for IMAX 150 mA (VRECT then regulates near 5.11 V) | RILIM = 262/IMAX, dynamic VRECT table |
| BQ25101 RISET | 2.05 kΩ → 66 mA | ICHG = 135 A·Ω / RISET |
| NTC on TS | 10 kΩ, β 3370 (103AT), direct | TS: 1.41 V at 0 °C, 0.25 V at 45 °C with the internal 50 µA bias |
| LDO | TPS7A0233PYCHR, 3.3 V | VDD ≥ 3.23 V in every simulated case |
| Protector | ABLIC S-82N1B + dual N-FET | 0.6 µA typical |
| Battery divider | 10 MΩ / 10 MΩ + 100 nF to the SAADC | 0.21 µA, 0.08 mV sampling error |
| Antenna | IFA on the long edge: arm 20 mm (trim zone 19 to 24 mm), short-to-feed 3 mm, height 6 mm, 0.5 mm trace | NEC-2 |
| Match | series 2.2 nH, shunt 0.2 pF (0201), placed after Nordic's reference match | NEC-2 Zin + L-network optimizer |
| Firmware | `multPeriod=1`, `INTERVAL_SETTINGS=600`, status `0x20` + battery mode, frame `0x40`, hashed flags | Everytag source + Find Hub spec |

## Battery life (Monte Carlo, 135 mAh)

| Configuration | Avg current | Months, median (90% range) | Google 2 s rule |
|---|---|---|---|
| Everytag defaults | 8.9 µA | 12.8 (11.2 to 14.8) | fails (3.9 s) |
| Compliant, 60 s settings window | 12.7 µA | 9.8 (8.7 to 11.3) | meets |
| **Recommended** | **11.4 µA** | **10.7 (9.3 to 12.4)** | **meets** |
| Recommended but 4 µA protector | 15.0 µA | 8.7 (7.6 to 10.0) | meets |

## What still needs real hardware (the bench gates)

These can't be settled by simulation. Each one maps to a bench demo:

1. **Pad compatibility and FOD.** At weak coupling the pad runs about 2 to 6 A rms in its coil to deliver 0.36 W. Some pads may read that as a foreign object and shut off. *Demo 3: three pads, card centered and 10 mm off-center, through your actual leather.*
2. **Real Ls' with the battery pouch next to the coil.** The pouch will shift inductance. *Measure, then finalize C1 and C2.*
3. **Antenna in the pocket.** I assumed the in-wallet permittivity (εr_eff about 1.3). *NanoVNA with the card in the wallet; trim the arm and adjust the 0201 match.*
4. **Measured nRF54L15 current with Everytag.** The model uses Nordic's numbers; Everytag's actual idle floor is unmeasured. *Demo 2: PPK2, debugger detached, power-cycled.*
5. **Whether GrapheneOS can unlock Google's E2EE keys.** Unchanged from the research; the fallback is a stock Android phone, once.
6. **Package heights not in hand.** I used 0.625 mm for the tallest part; the nRF54L15 CSP and BQ51003 YFP drawings still need checking.

## Limits of these simulations (read this)

- The Qi model is air-core plus ideal diodes. Real ferrite raises k, so it's conservative on coupling. TX losses depend on the specific pad.
- The antenna model is a free-space wire model with permittivity applied as a scaling factor. It's a good first design, but not a substitute for measuring in the wallet. A full 3D EM solve (openEMS) was not possible here, because building it from source was blocked in this environment.
- The LDO model is behavioral, not TI's transistor model. Its result agrees with TI's published transient spec (under 10 µs settling, 100 mV dip).
- The battery OCV curve is a generic LiPo curve, not Grepow's measured curve.

## Files

- `sims/`: qi_coupling.py, qi_link_ngspice.py, charge_thermal.py, power_path_ngspice.py, battery_montecarlo.py, antenna_nec.py, antenna_floorplan.py, antenna_match.py, antenna_inwallet_and_link.py, floorplan.py, each with JSON results
- `protocol/protocol_roundtrip.py`: Apple and Google frame build plus crypto round trip (needs GoogleFindMyTools cloned)
- `server/backend_e2e.py` and `traccar.xml`: the Traccar proof (Traccar 6.6, OsmAnd on :5055, event forwarding)
- `plots/`: floorplan, Qi curves, charge profile, VDD transient, antenna S11, battery-life distribution

To rerun on Fedora: `sudo dnf install ngspice`, `pip install PyNEC numpy scipy matplotlib cryptography ecdsa pycryptodomex requests`, then run each script from `sims/`.
