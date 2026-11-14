# 02 Architecture

## Hardware blocks
```
Qi coil L1 ─ C1 (series) ─┬─ AC1 ┐
                          C2 ∥   ├─ U1 BQ51003 ── V5_RX (5.0 V) ── U2 BQ25101 ── VCELL ─┬─ BT1 135 mAh LiPo
                          └─ AC2 ┘   (Qi receiver,                (66 mA CC/CV,         │   + TH1 NTC → U2.TS
                                      rectifier, LDO)              JEITA)               │
                                                                                   U3 S-82N1B + Q1 (protection)
                                                                                         │ VBAT
                         VBAT ── U4 TPS7A0233 ── VDD_3V3 ── U5 nRF54L15 (internal DC/DC)
                         VBAT ── R3/R4 10M/10M + C16 ── VBAT_SENSE → U5 AIN
                         U2.CHG ── nCHG → U5 GPIO
                         U5.ANT ── Nordic match ── L6/C28 L-match ── ANT1 printed IFA
                         U5 SWD ── TP1–TP5
                         U5 NFC1/NFC2 ── (DNP) NFC loop, v2.1
```

## Data path
1. The card advertises an Apple Find My frame and a Google FMDN frame, alternating, one event about every 0.97 s (each network every 1.93 s).
2. Strangers' phones upload end-to-end-encrypted location reports to Apple or Google.
3. On the Pi:
   - **GoogleFindMyToolsWebUi** fetches and decrypts Google reports, and refreshes the custom tracker's key registration (registrations last 4 days).
   - **anisette-v3 plus our Python Apple fetcher** fetches Apple reports and decrypts them (P-224 ECDH, X9.63 KDF, AES-GCM, signed int32 coordinates).
4. Both fetchers push positions to **Traccar** (OsmAnd protocol, port 5055):
   - Groups are the bundles.
   - Alarms (`lowBattery`) and inactivity events go out through `event.forward.url` to an **ntfy** bridge (the F-Droid ntfy app on GrapheneOS).
5. A **PWA** reads Traccar's REST/WebSocket API for the map, bundles and history.

## Why these parts (short form; full reasoning in `reports/`)
- **nRF54L15:** newest Nordic part, supports both networks, Everytag supports it, and the Nordic Tag reference design exists.
- **BQ51003 + BQ25101:** the BQ51050B was rejected because its minimum charge current is 500 mA and it draws 12 µA from the battery. The BQ25101 charges at 10 to 250 mA and leaks ≤ 75 nA.
- **TPS7A0233 at 3.3 V:** 25 nA. A higher VDD means lower battery current through the nRF's DC/DC.
- **S-82N1B:** 0.6 µA protector, versus 4 µA for BQ2970-class parts (about 2 months of battery).
- **Printed IFA:** the chip antenna (1.3 mm) didn't fit the height budget.
- **Grepow GRP0849049:** 0.85 mm, 135 mAh, the thinnest cell with about a year of life.
