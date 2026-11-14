# 06 Firmware

Base: **Everytag** (github.com/vasimv/Everytag), Zephyr, nRF Connect SDK 2.8.0. The nRF54L15 is supported through `nrf54l15dk.overlay`. A custom board definition is needed for the card.

## Required changes (verified against Everytag source and the Find Hub spec)
| # | Change | Where | Why |
|---|---|---|---|
| F1 | FMDN frame type `0x41` → `0x40` | `main.c`, `adv_fmdn[]` | `0x41` = "unwanted tracking protection mode ON" (spec) |
| F2 | FMDN flags byte: send `flags_raw ^ mask`, where `flags_raw` = battery level in mask `0x06` (spec numbers bits MSB-first: 01 normal → `0x02`, 10 low → `0x04`, 11 critical → `0x06`), UTP bit `0x01` = 0 | `update_status_byte()` | Spec: XOR with the LSB of SHA256(r). The key is static, so r is constant: the Pi computes the mask once (see `sims/protocol_roundtrip.py`) and loads it into NVS. |
| F3 | `multPeriod = 1` | settings default | Each network every 1.93 s (Google wants ≤ 2 s) |
| F4 | `INTERVAL_SETTINGS = 600` | `myboards.h` | The 60 s window costs 1.3 µA |
| F5 | Change the settings password from `abcdefgh` | provisioning | Anyone nearby could reconfigure the card |
| F6 | Apple status: battery mode with base byte `0x20` | `statusFlags = 0x40000 | 0x20` | macless-haystack reads `0x00` as "unknown" |
| F7 | Battery thresholds for this cell (full 4.0, normal 3.7, low 3.45 V) and divider ×2 | board config | 10 M/10 M divider on AIN |
| F8 | Disable `bq2512x.c` (I2C BQ25120A); read `nCHG` on a GPIO (pause high-power bursts while charging, optional) | build config | We use the pin-programmed BQ25101 |
| F9 | Production build: `CONFIG_SERIAL=n`, logging off, unused RAM retention off | `prj-lowpower.conf` | UART alone can add over 150 µA |
| F10 | Keep the 32.768 kHz crystal enabled (LFXO) | board DTS | about 0.6 µA lower than LFRC |

## Keys
- **Apple:** up to 40 P-224 keys, rotating every 10 min (Everytag default). Generate them with macless-haystack's `generate_keys.py`.
- **Google:** one static EIK registered through GoogleFindMyTools (`main.py` → `r`).
  - The registration covers 4 days (337 × 1024 s slots). Keep it refreshed by the WebUI's polling or by a cron job every 2 to 3 days.
  - The EID is advertised; the EIK stays on the Pi.

## Measurement discipline (bench gate 2)
- Measure with a PPK2, the debugger disconnected, after a full power cycle.
- Target: ≤ 12 µA average in the recommended configuration (the model's median is 11.4 µA).
