# Swap the charger, then thin the card

The plan's architecture is sound (nRF54L15, Everytag, a Qi charger, LDO, thin LiPo and a Pi backend), but the details need six fixes before you order boards. First, the **BQ51050B is the wrong charger**: its lowest charge setting is 500 mA, which is 4 to 10C for a 50 to 120 mAh cell, and it draws 12 µA typical from the battery in standby. That standby draw alone is roughly 105 mAh a year, more than the whole cell ([TI BQ51050B](https://www.ti.com/lit/ds/symlink/bq51050b.pdf)). The fix is a **BQ51003 Qi receiver feeding a BQ25101 10 to 250 mA linear charger**, which leaks 75 nA max from the battery ([TI BQ51003](https://www.ti.com/lit/ds/symlink/bq51003.pdf); [TI BQ25101](https://www.ti.com/lit/ds/symlink/bq25101.pdf)). Second, the **7 to 12 µA budget only holds if the card alternates networks** so that each one is heard every 4 s. Advertising each network every 2 s, as Google's spec expects, gives about 11 to 19 µA, before adding a protection IC that can cost another 4 µA ([Nordic Academy](https://academy.nordicsemi.com/courses/designing-low-power-bluetooth-le-products/lessons/lesson-4-bluetooth-le-power-optimization/topic/bluetooth-le-advertising-parameters-and-power-consumption/); [Google FHN spec](https://developers.google.com/nearby/fast-pair/specifications/extensions/fmdn); [TI BQ2970](https://www.ti.com/lit/gpn/bq2970)). Third, the **Google side needs a host refresh at least every 4 days**, and tags registered this way **do not appear in the Find Hub app** ([GoogleFindMyTools ESP32 README](https://github.com/leonboe1/GoogleFindMyTools/blob/main/ESP32Firmware/README.md)). Fourth, **Google sign-in does not work on ARM Linux**, so you sign in on Fedora and copy the secrets to the Pi ([traccar/google-find-hub-sync](https://github.com/traccar/google-find-hub-sync)). Fifth, at 1.30 mm tall, **the chip antenna cannot fit in a 1.5 mm v2 card** ([Johanson](https://www.johansontechnology.com/docs/3827/Antenna-2450AT18A0100001E-Rev4.0.pdf)). Sixth, **1.5 mm is thinner than any commercial tracker card**: published thicknesses run 2.0 to 2.6 mm ([How-To Geek](https://www.howtogeek.com/nomad-tracking-card-review/); [Anker](https://www.anker.com/ca/products/t87b1011)). A 1.5 mm card is still achievable with a 0.85 mm, 135 mAh cell placed beside (not under) the electronics. With these fixes, the card should last roughly 1 to 2 years per charge on paper, before self-discharge.

## Executive summary

Keep the nRF54L15. Its +8 dBm radio, 2.4 × 2.2 mm WLCSP option and DC/DC converter suit a card tracker ([Nordic product page](https://cd0.nordicsemi.com/Products/nRF54L15)). Keep Everytag too: it is **the only open firmware whose author reports testing on nRF54L15 hardware**, though it is pinned to NCS 2.8.0 and was last updated in April 2026 ([Everytag](https://github.com/vasimv/Everytag)). Its modern fork, MockingBeacon (NCS 3.2.4), has only been build-verified and simulated on nRF54L15 ([MockingBeacon](https://github.com/ak2k/MockingBeacon)).

Replace the BQ51050B with the BQ51003 plus BQ25101. Keep the TPS7A02 LDO at 3.0 V and keep the nRF54L15's internal DC/DC on ([TI TPS7A02](https://www.ti.com/product/TPS7A02); [DevZone 120473](https://devzone.nordicsemi.com/f/nordic-q-a/120473/high-current-consumption-with-ldo-regulator-mode-on-nrf54l-soc)). Choose a Grepow GRP0849049 cell (0.85 mm, 135 mAh) and a Würth 0.5 mm Ø26 mm receiver coil ([Grepow](https://grepow.com/shaped-battery/ultra-thin-battery.html); [Würth WE-WPCC](https://www.we-online.com/en/components/products/WE-WPCC-RECEIVER)).

On the server side, the main change is to use Traccar as the core instead of a fully custom backend. Traccar takes Google and Apple fixes over its OsmAnd HTTP protocol, models "bundles" as groups, and already has inactivity and low-battery events ([Traccar OsmAnd](https://www.traccar.org/osmand/); [Traccar events](https://www.traccar.org/documentation/events/)). Send alerts through a self-hosted ntfy server and the F-Droid ntfy app, which is the reliable choice on GrapheneOS ([ntfy docs](https://docs.ntfy.sh/subscribe/phone/)).

The biggest open risk is not the hardware. It is whether a GrapheneOS phone can unlock the Google end-to-end encryption (E2EE) owner key that Find Hub needs. No source confirms it either way ([GoogleFindMyTools README](https://github.com/leonboe1/GoogleFindMyTools)).

## Corrections to the plan

| # | Plan item | What is wrong | Fix |
|---|---|---|---|
| 1 | BQ51050B Qi receiver/charger | Its minimum programmable charge current is 500 mA, and the datasheet does not guarantee lower values. It draws 12 µA typical (20 µA max) from the battery in standby ([TI BQ51050B](https://www.ti.com/lit/ds/symlink/bq51050b.pdf)). | Use a BQ51003 receiver (2.5 W, 5 V output) feeding a BQ25101 charger (10 to 250 mA, 75 nA max leakage). TI's PMP11311 wearable reference design uses the same split ([TI BQ51003](https://www.ti.com/lit/ds/symlink/bq51003.pdf); [TI BQ25101](https://www.ti.com/lit/ds/symlink/bq25101.pdf)). |
| 2 | BQ51050BEVM for v0 | It benches a part you will not ship. | Bench the BQ51003 and BQ25101 instead. The EVM part number was not verified in the research. |
| 3 | 7 to 12 µA budget | This only holds for one advertisement every 2 s alternating between networks (each network every 4 s). Google expects frames "at least once every 2 seconds" ([Google FHN spec](https://developers.google.com/nearby/fast-pair/specifications/extensions/fmdn)). | Budget 7 to 12 µA for the alternating mode and 11 to 19 µA for 2 s per network. Then measure on the PPK2 (see the power section). |
| 4 | Generic "protection IC" | The BQ2970 family draws 4 µA typical, about 35 mAh a year, and needs two external FETs ([TI BQ2970](https://www.ti.com/lit/gpn/bq2970)). | Prefer a cell with a factory protection circuit module (PCM), or a protector under 1 µA. Firmware should also cut the load at a low-voltage threshold. |
| 5 | Chip antenna on v2 | The Johanson 2450AT18A100 is 3.20 × 1.60 × 1.30 mm ([Johanson](https://www.johansontechnology.com/docs/3827/Antenna-2450AT18A0100001E-Rev4.0.pdf)), which leaves no room in a 1.5 mm card. | Keep the chip antenna on v1. On v2, use a PCB trace antenna (inverted-F or meander), or a lower-profile antenna whose height you have verified. |
| 6 | ~1.5 mm card | The cards found run 2.0 mm (Nomad), 2.1 mm (KeySmart), 2.5 mm (Chipolo, Nomad Pro) and 2.6 mm (eufy) ([How-To Geek](https://www.howtogeek.com/nomad-tracking-card-review/); [KeySmart](https://keysmart.gorgias.help/en-US/smartcard-lite-(gen-2)-%7C-product-specs-4793794); [Chipolo](https://chipolo.net/en/blogs/all-about-chipolo-card); [Nomad Help Center](https://help.nomadgoods.com/en-US/tracking-card-pro-3155373); [Anker](https://www.anker.com/ca/products/t87b1011)). | Keep 1.5 mm as the v2 target. Place the cell and coil beside the electronics, never stacked on them. Treat 2.0 mm as an acceptable fallback. |
| 7 | Google network "just works" | Custom tags use one static EID (ephemeral identifier). You must re-run `main.py` at least every 4 days, and the tag "cannot" be viewed in the Find Hub app ([ESP32 README](https://github.com/leonboe1/GoogleFindMyTools/blob/main/ESP32Firmware/README.md); [SpotApi](https://github.com/leonboe1/GoogleFindMyTools/tree/main/SpotApi)). | Run a cron refresh every 2 to 3 days on the Pi. View locations only in your own app. |
| 8 | Pi runs GoogleFindMyTools end to end | "Authentication on ARM Linux is unsupported" ([traccar/google-find-hub-sync](https://github.com/traccar/google-find-hub-sync)). | Authenticate once on Fedora (x86_64), then copy `Auth/secrets.json` to the Pi. |
| 9 | Battery alerts via Google | Everytag writes the Find Hub battery bits raw, without the required XOR against SHA256(r) ([Everytag](https://github.com/vasimv/Everytag); [Google FHN spec](https://developers.google.com/nearby/fast-pair/specifications/extensions/fmdn)). | Read battery from the Apple status byte instead. macless-haystack decodes `status >> 6` as ok, medium, low or critical ([macless-haystack](https://github.com/dchristl/macless-haystack)). |
| 10 | Everytag defaults | It opens a 2 s connectable settings window every minute, and the default password is "abcdefgh" ([Everytag](https://github.com/vasimv/Everytag)). | Change the password before field use. |
| 11 | "Hand-solderable" v1 | The BQ51003 and BQ25101 come only as DSBGA in the cited datasheets ([TI BQ51003](https://www.ti.com/lit/ds/symlink/bq51003.pdf); [TI BQ25101](https://www.ti.com/lit/ds/symlink/bq25101.pdf)). | Reflow v1 with a stencil and hot plate or hot air, or pay for assembly of those two parts. Use the TPS7A02's SOT-23 option on v1 ([TI TPS7A02](https://www.ti.com/product/TPS7A02)). |

## Recommended final stack per layer

### Firmware and networks: Everytag now, two advertising sets later

Start with **Everytag on NCS 2.8.0** using its `nrf54l15dk.overlay`, which enables the SAADC on VDD and the `wdt31` watchdog. Use the `prj-smpsrv-lowpower.conf` profile, which disables logging, console and RTT ([Everytag](https://github.com/vasimv/Everytag)).

Everytag sends both networks from one legacy advertising set, swapping payloads every N seconds. The base interval is 938 to 994 ms, times a multiplier, and the nRF54L15 TX levels are −8, 0 and +8 dBm ([Everytag](https://github.com/vasimv/Everytag)). Begin at 0 dBm, because Google requires FHN advertisements to be "at least 0 dBm" conducted ([Google FHN spec](https://developers.google.com/nearby/fast-pair/specifications/extensions/fmdn)). Set the Apple status-byte mode to battery level (mode 4) and turn off the Find Hub battery flags.

A cleaner v2 firmware would run two extended advertising sets, Apple and Google at about 2 s each. **No existing DIY firmware does this.** MockingBeacon dropped extended advertising only because the nRF52810 ran out of RAM ([MockingBeacon](https://github.com/ak2k/MockingBeacon)).

Nordic's official alternatives are real but awkward here:

- **Google path:** the NCS `locator_tag` sample gives rotating EIDs and native Find Hub app visibility on `nrf54l15dk` ([sdk-nrf locator_tag](https://github.com/nrfconnect/sdk-nrf/blob/main/samples/bluetooth/fast_pair/locator_tag/README.rst)). However, provisioning goes through Fast Pair. Uncertified debug models have needed an allow-listed Google account ([DevZone 112503](https://devzone.nordicsemi.com/f/nordic-q-a/112503/issue-connection-for-google-find-my-device)), and GrapheneOS lost Fast Pair when Google removed it from AOSP ([GrapheneOS forum](https://discuss.grapheneos.org/d/7437-google-removes-fast-pair-from-aosp-affects-grapheneos)).
- **Apple path:** Nordic's Find My software is gated behind a private ticket ([DevZone 123154](https://devzone.nordicsemi.com/f/nordic-q-a/123154/dual-find-my-apple-google-tracker-support-in-nrf54l15)).

What to expect from each network:

- **Google reports** arrived in about 75 s on average but were about 5 to 6 times fewer, and less accurate, than Apple's: 166 vs 906 locations, with median accuracy of 121.8 m vs 57.5 m ([PETS 2025](https://petsymposium.org/popets/2025/popets-2025-0147.pdf)).
- **In Google's default high-traffic mode**, a location is released only after reports from at least two distinct devices ([PETS 2025](https://petsymposium.org/popets/2025/popets-2025-0147.pdf)).
- **Apple stays worth carrying** even though Google is the priority, because it adds pickup.

### MCU and RF: copy Nordic's tag, not just the DK

The CSP47 reference design ("config 1") uses these parts ([Nordic CAAA schematic](https://devzone.nordicsemi.com/cfs-file/__key/communityserver-discussions-components-files/4/nRF54L15_5F00_caaa_5F00_config1_5F00_schematic.pdf)):

- A 4.7 µH 0402 DC/DC inductor.
- A 32 MHz crystal in a 1612 package, and a 32.768 kHz crystal in a 2012 package.
- A Murata 0201 matching network: 3.6, 4.6 and 2.0 nH inductors, with 3.9, 1.2 and 1.2 pF capacitors.

The crystals need no external load capacitors, because the chip has internal ones programmable from 3 to 18 pF ([Nordic Academy, clocks](https://academy.nordicsemi.com/courses/designing-low-power-bluetooth-le-products/lessons/lesson-5-soc-specific-power-optimization-i/topic/clock-sources/)).

**Keep the 32.768 kHz crystal.** It saves about 0.6 µA compared with the internal RC oscillator, and it avoids recalibration every 4 to 8 s that "adds significant energy" ([Nordic Academy, clocks](https://academy.nordicsemi.com/courses/designing-low-power-bluetooth-le-products/lessons/lesson-5-soc-specific-power-optimization-i/topic/clock-sources/)).

Your best layout reference is the **nRF54L15 Tag** that Nordic launched in June 2026. It is a 33 mm tracker that ships with schematics, BOM, Gerbers and layout files, and it comes with Find My and Find Hub samples ([Nordic news](https://www.nordicsemi.com/Nordic-news/2026/06/Nordic-launches-compact-nRF54L15-prototyping-tag-optimized-for-Apple-Find-My-and-Google-Find-Hub)).

For NFC, the QFN48 "circuit configuration 1" is listed with "NFC: No" ([nRF54L15 datasheet](https://docs.nordicsemi.com/r/bundle/ps_nrf54l15/page/chapters/ref_circuitry.html-concept_refcircuit_config_1)). The NFC antenna circuit is therefore an add-on that the research did not size. Keep it as an optional v1 footprint, and keep any steel stiffener away from it ([JLCPCB flex](https://jlcpcb.com/capabilities/flex-pcb-capabilities)).

### Power and charging: a receiver that is dead off the pad

The charging chain is: coil → series C1 and parallel C2 tuning capacitors → BQ51003 → 5 V → BQ25101 → cell.

**Why this split works.** The BQ51003's 20 µA standby current is drawn from its output node, which has no source when the card is off the pad. The BQ25101 then isolates the cell to 50 nA max (0 to 85 °C) ([TI BQ51003](https://www.ti.com/lit/ds/symlink/bq51003.pdf); [TI BQ25101](https://www.ti.com/lit/ds/symlink/bq25101.pdf)).

**Setting the resistors:**

- **Receiver current limit:** RILIM = 262/IMAX.
- **Charge current:** RISET = 135/ICHG. That gives about 2.7 kΩ for 50 mA and 1.35 kΩ for 100 mA, or 0.4 to 0.75C on a 135 mAh cell.
- **Thermal cutoff:** the TS pin takes a 10 kΩ NTC (β 3370). It reduces current at 0 to 10 °C, reduces voltage at 45 to 60 °C, and stops charging outside that range ([TI BQ25101](https://www.ti.com/lit/ds/symlink/bq25101.pdf)).

**Coil tuning.** TI's method sets C1 = 1/((2π·100 kHz)²·Ls′), where Ls′ is the coil inductance measured over a shield. Then C2 = 1/((2π·1 MHz)²·Ls − 1/C1), where Ls is the free-space inductance ([TI BQ51050B](https://www.ti.com/lit/ds/symlink/bq51050b.pdf)). For a coil with Ls′ of about 10 µH, C1 comes out near 253 nF. Measure Ls′ with the final cell, shield and leather in place.

**Regulator.** Use a **TPS7A0230 (3.0 V)**. Its 25 nA quiescent current ("even in dropout") is about 0.3% of the budget ([TI TPS7A02](https://www.ti.com/product/TPS7A02)). An external regulator is required because a full LiPo exceeds the 1.8 to 3.6 V supply range ([nRF54L15 DK guide](https://farnell.com/datasheets/4424294.pdf)). Do not use an nPM2100, whose 0.7 to 3.4 V input cannot take a LiPo ([nPM2100](https://nordicsemi.com/Products/nPM2100)). Do not use an nPM1100 either: its 800 nA no-load draw is wasted when charging is handled elsewhere ([nPM1100](https://docs.nordicsemi.com/r/bundle/ps_npm1100/page/product_overview.html)).

**Battery voltage sensing.** Read the cell through a 10 MΩ / 10 MΩ divider that a GPIO switches on only for the sample. This is an engineering choice from the research, not a cited spec.

### Battery: 135 mAh at 0.85 mm is the ceiling

Grepow's ultra-thin options are 49 × 49 mm cells ([Grepow](https://grepow.com/shaped-battery/ultra-thin-battery.html)):

- **GRP0849049:** 135 mAh at 4.2 V, 0.85 mm. This is the one to use. Pair it with the BQ25101, or use the 4.35 V version with the BQ25101H.
- **GRP0449049:** 48 mAh at 4.35 V, 0.5 mm.
- **GRP1549049:** 375 mAh, but 1.5 mm thick, so it cannot fit a 1.5 mm card.

The page gives no bend specification and mentions no protection board, so ask Grepow whether a PCM is fitted ([Grepow](https://grepow.com/shaped-battery/ultra-thin-battery.html)).

### Mechanical stackup: side by side, cold-laminated

**v1** is a 0.4 mm rigid FR4 board. **v2** is a 2-layer JLCPCB flex, 0.11 to 0.12 mm finished. JLCPCB offers stainless stiffeners of 0.1 to 0.3 mm, which give good flatness for SMD parts but are slightly magnetic, and it does not support rigid-flex ([JLCPCB flex](https://jlcpcb.com/capabilities/flex-pcb-capabilities)).

Laminate cold with **3M 467MP** (0.06 mm acrylic adhesive) rather than hot card lamination, which would stress the LiPo ([3M](https://www.3m.com/3M/en_US/p/d/b40071696/)).

Place the Ø26 mm coil beside the 49 mm cell. Together they take 75 mm of the 85.6 mm card length, leaving about 10 mm for electronics. The Ø19 mm, 26 µH coil frees about 7 mm more and has the highest Q in the thin set ([Würth WE-WPCC](https://www.we-online.com/en/components/products/WE-WPCC-RECEIVER)).

### Server and app: Traccar core, two ingest paths, ntfy out

Run everything on a **Pi 4 or 5 with 8 GB and a 64-bit OS**. The Apple images are published for arm64 only, with no armv7 builds ([Docker Hub](https://hub.docker.com/r/christld/macless-haystack/tags); [anisette-v3-server](https://github.com/Dadoum/anisette-v3-server)). Traccar used about 400 MB of RAM and under 1% CPU on a Pi 4 ([Traccar forum](https://www.traccar.org/forums/topic/review-rasberrypi4-8gb/)).

**Google ingest.** Use GoogleFindMyTools, or **GoogleFindMyToolsWebUi**. The WebUi version was updated as recently as 2026-11-12 and adds per-device cron polling, stale-device alerts sent via Apprise, and Traccar forwarding. It is plain HTTP and "meant for a trusted LAN" ([Unraid CA](https://ca.unraid.net/apps/googlefindmytoolswebui-1qe73jg0kbqrg0); [GitHub](https://github.com/P6g9YHK6/GoogleFindMyToolsWebUi)). The research did not confirm whether WebUi performs the custom-tracker 4-day refresh by itself, so schedule `main.py` separately.

Expect breakage on the Google side. Users have hit FCM registration errors, and a server key that "expires periodically" ([Traccar forum p9](https://www.traccar.org/forums/topic/google-find-hub-devices-in-traccar/page/9/)).

**Apple ingest.** Use macless-haystack plus anisette-v3-server, or biemster/FindMy or FindMy.py, with a secondary Apple ID that has SMS two-factor authentication ([macless-haystack](https://github.com/dchristl/macless-haystack); [FindMy.py](https://github.com/malmeloo/FindMy.py/releases)). Apple sign-in is fragile. Recent issues report HTTP 503 and -80045 errors (October 2026) and "Account limit reached" ([macless-haystack issues](https://github.com/dchristl/macless-haystack/issues)), and Apple changed the report format in March 2026 ([commit aef28e3](https://github.com/dchristl/macless-haystack/commit/aef28e38bdf04bdcd90af20cd261c7551ab4a59d)). Back up `auth.json`.

**Core.** Post both feeds to Traccar's OsmAnd endpoint on port 5055, with a `batt` parameter ([Traccar OsmAnd](https://www.traccar.org/osmand/)). Use Traccar groups as your bundles, Device Inactive for "not seen" alerts, and the Low Battery alarm ([Traccar events](https://www.traccar.org/documentation/events/)). `event.forward.url` sends events on to an ntfy adapter ([Traccar config](https://www.traccar.org/configuration-file/)).

**App and alerts.** Build your PWA on Traccar's API. For alerts on GrapheneOS, use ntfy, not Traccar Manager: Traccar Manager's Firebase push is reported to fail on sandboxed Play ([Traccar forum](https://www.traccar.org/forums/topic/traccar-manager-notifications-not-working-on-microg-or-sandboxed-google-play-services/)).

**Remote access.** Keep all of it behind Tailscale. That choice comes from the research's general reasoning, not a fetched source.

## BOM by build stage

Heights marked "unverified" came from the research's training knowledge or could not be read from datasheets. Confirm them before layout.

| Stage | Function | Part | Package | Height |
|---|---|---|---|---|
| v0 | Dev kit | nRF54L15 DK (QFN48) ([DK guide](https://farnell.com/datasheets/4424294.pdf)) | Board | n/a |
| v0 | Reference tracker (optional) | nRF54L15 Tag, about $30 ([CNX](https://www.cnx-software.com/2026/06/23/nordic-nrf54l15-tag-prototyping-platform-supports-bluetooth-channel-sounding-matter-edge-ai/)) | Board | n/a |
| v0 | Power meter | Nordic PPK2 | Instrument | n/a |
| v0 | Qi bench | BQ51003 + BQ25101 eval or breakout (replaces BQ51050BEVM) | Board | n/a |
| v0 | Coil samples | Würth 760308101309 (Ø26, 10 µH) and 760308101214 (Ø19, 26 µH) ([Würth](https://www.we-online.com/en/components/products/WE-WPCC-RECEIVER)) | Shielded coil | 0.5 / 0.8 mm |
| v1 | SoC | nRF54L15 QFN48 ([Nordic](https://cd0.nordicsemi.com/Products/nRF54L15)) | 6 × 6 mm | about 0.85 mm (unverified) |
| v1 | HF crystal | 32 MHz | 1612 (Nordic ref) | unverified |
| v1 | LF crystal | 32.768 kHz | 2012 | unverified |
| v1 | DC/DC inductor | 4.7 µH ([CAAA schematic](https://devzone.nordicsemi.com/cfs-file/__key/communityserver-discussions-components-files/4/nRF54L15_5F00_caaa_5F00_config1_5F00_schematic.pdf)) | 0402 | unverified |
| v1 | Antenna | Johanson 2450AT18A100E ([Johanson](https://www.johansontechnology.com/docs/3827/Antenna-2450AT18A0100001E-Rev4.0.pdf)) | 3.2 × 1.6 mm | 1.30 mm |
| v1 | Qi receiver | TI BQ51003YFP ([TI](https://www.ti.com/lit/ds/symlink/bq51003.pdf)) | DSBGA-28, 1.9 × 3.0 mm | unverified |
| v1 | Charger | TI BQ25101YFP ([TI](https://www.ti.com/lit/ds/symlink/bq25101.pdf)) | DSBGA-6, 1.6 × 0.9 mm | 0.5 mm max |
| v1 | NTC | 10 kΩ, β 3370 (e.g. 103AT) ([TI](https://www.ti.com/lit/ds/symlink/bq25101.pdf)) | 0402 or film | unverified |
| v1 | LDO | TI TPS7A0230 ([TI](https://www.ti.com/product/TPS7A02)) | SOT-23 (2.9 × 2.8 mm) | unverified |
| v1 | Protection | Cell PCM, or BQ2970 + dual NMOS ([TI](https://www.ti.com/lit/gpn/bq2970)) | WSON-6, 1.5 × 1.5 mm | 0.8 mm max |
| v1 | Coil | Würth 760308101309 | Ø26 mm | 0.5 mm |
| v1 | Cell | Grepow GRP0849049, 4.2 V, 135 mAh ([Grepow](https://grepow.com/shaped-battery/ultra-thin-battery.html)) | 49 × 49 mm pouch | 0.85 mm |
| v1 | PCB | FR4 ([JLCPCB](https://jlcpcb.com/capabilities/flex-pcb-capabilities)) | Rigid | 0.4 mm |
| v2 | SoC | nRF54L15 WLCSP ([Nordic](https://cd0.nordicsemi.com/Products/nRF54L15)) | 2.4 × 2.2 mm, 300 or 350 µm pitch | about 0.4 to 0.5 mm (unverified) |
| v2 | Passives | Murata 0201 match per CAAA schematic | 0201 | unverified |
| v2 | Antenna | PCB trace antenna (inverted-F or meander) | Copper | 0 mm added |
| v2 | LDO | TPS7A0230 DQN or YCH ([TI](https://www.ti.com/product/TPS7A02)) | 1.0 × 1.0 or 0.64 × 0.64 mm | unverified |
| v2 | Qi, charger, coil, cell | Same as v1 | Same | Same |
| v2 | PCB | JLCPCB 2-layer polyimide flex, ENIG, plus 0.1 mm steel stiffener under the SoC only ([JLCPCB](https://jlcpcb.com/capabilities/flex-pcb-capabilities)) | Flex | 0.11 to 0.12 mm |
| v2 | Laminate | 3M 467MP ([3M](https://www.3m.com/3M/en_US/p/d/b40071696/)) | Transfer adhesive | 0.06 mm |

## Revised power budget: 7 to 19 µA, set by advertising mode

The model is **I_avg = I_floor + Q_event / T_event + I_static**, where:

- **I_floor** is the sleep current.
- **Q_event** is the charge per advertising event.
- **T_event** is the time between events.
- **I_static** is the drain from the LDO, charger leakage and protector.

**Where the numbers come from.** Nordic measured the nRF54L15 DK at 0 dBm with a 6-byte payload: 7 µA average at a 1 s interval and 5 µA at 2 s. A maximum-length legacy packet costs 7.47 µC per event, against 3.75 µC for the minimum ([Nordic Academy](https://academy.nordicsemi.com/courses/designing-low-power-bluetooth-le-products/lessons/lesson-4-bluetooth-le-power-optimization/topic/bluetooth-le-advertising-parameters-and-power-consumption/)). Find My and Find Hub frames are both near maximum length.

The sleep floor is 3.0 µA in System ON with 256 KB of RAM retained. TX current at +8 dBm is 9.8 mA, against 4.8 mA at 0 dBm ([Nordic blog](https://devzone.nordicsemi.com/nordic/nordic-blog/b/blog/posts/next-level-nrf54l-series-cutting-power-consumption-even-further)). The +8 dBm charge per event (about 13 µC) is therefore an estimate, not a measurement.

**Adders:**

- TPS7A02: 0.025 µA ([TI](https://www.ti.com/product/TPS7A02)).
- BQ25101 leakage: 0.05 µA max ([TI](https://www.ti.com/lit/ds/symlink/bq25101.pdf)).
- BQ2970 protector, if used: 4 µA ([TI](https://www.ti.com/lit/gpn/bq2970)).

| Scenario | I_avg (cell PCM, ~0.1 µA static) | I_avg with BQ2970 (+4 µA) |
|---|---|---|
| A0: alternate every 2 s, 0 dBm: 3 + 7.5/2 | 6.9 µA | 10.9 µA |
| A8: alternate every 2 s, +8 dBm: 3 + 13/2 | 9.6 µA | 13.6 µA |
| B0: each network every 2 s, 0 dBm: 3 + 7.5 | 10.6 µA | 14.6 µA |
| B8: each network every 2 s, +8 dBm: 3 + 13 | 16.1 µA | 20.1 µA |
| Old plan (A0 + BQ51050B 12 µA + BQ2970 4 µA) | 22.8 µA | n/a |

**Battery life = capacity (µAh) / I_avg (µA) hours.** The table below is ideal: it ignores self-discharge (not sourced) and the 1 to 3 µA margin the research adds for key rotation and connections.

| Scenario | 48 mAh (GRP0449049) | 135 mAh (GRP0849049) |
|---|---|---|
| A0, 6.9 µA | 0.79 yr | 2.2 yr |
| A8, 9.6 µA | 0.57 yr | 1.6 yr |
| B0, 10.6 µA | 0.52 yr | 1.45 yr |
| B8, 16.1 µA | 0.34 yr | 0.96 yr |
| A0 + BQ2970, 10.9 µA | 0.50 yr | 1.4 yr |
| Old plan, 22.8 µA | 0.24 yr | 0.68 yr |

As a sanity check, the Nomad Tracking Card Pro claims 16 months on 350 mAh ([Nomad Help Center](https://help.nomadgoods.com/en-US/tracking-card-pro-3155373)). My arithmetic puts that at about 30 µA average, so a 7 to 16 µA design is ambitious but plausible.

Three firmware traps can blow the budget:

- **UART logging** held one NCS 3.2 nRF54L15 build at 155 µA instead of about 4 µA ([DevZone 127837](https://devzone.nordicsemi.com/f/nordic-q-a/127837/nrf54l15-ncs-3-2-excessive-current-consumption-on-uart30-when-config_log_mode_immediate-n/565795)).
- **The DK's onboard debugger** can keep waking the SoC from System OFF ([DevZone 126020](https://devzone.nordicsemi.com/f/nordic-q-a/126020/nrf54l15-dk-the-soc-keeps-being-woken-up-from-system-off-by-the-onboard-debugger/556547)).
- **After flashing**, Everytag warns that chips can sit at milliamps until the battery is removed for 10 to 20 s ([Everytag](https://github.com/vasimv/Everytag)).

## Thickness stackup for v2

| Layer | Thickness (mm) | Source |
|---|---|---|
| Top overlay (PC or PET) | 0.125 | Research proposal, film stock unverified |
| 467MP adhesive | 0.06 | [3M](https://www.3m.com/3M/en_US/p/d/b40071696/) |
| Core frame with pockets | 0.95 to 1.00 | Research proposal |
| 467MP adhesive | 0.06 | [3M](https://www.3m.com/3M/en_US/p/d/b40071696/) |
| Bottom overlay | 0.125 | Research proposal |
| **Total** | **1.32 to 1.37** | Leaves about 0.13 mm of margin to 1.5 mm |

What each pocket must hold:

| Pocket | Contents | Height (mm) | Fits 0.95 mm? |
|---|---|---|---|
| Battery | GRP0849049 alone ([Grepow](https://grepow.com/shaped-battery/ultra-thin-battery.html)) | 0.85 | Yes |
| Coil | 760308101309 ([Würth](https://www.we-online.com/en/components/products/WE-WPCC-RECEIVER)) | 0.5 | Yes, if the listed height includes the ferrite (not stated) |
| Electronics, QFN | 0.12 flex + 0.1 stiffener + about 0.85 QFN ([JLCPCB](https://jlcpcb.com/capabilities/flex-pcb-capabilities)) | about 1.07 | No, which is why v2 uses WLCSP |
| Electronics, WLCSP | 0.12 flex + 0.1 stiffener + about 0.5 WLCSP, crystal or BQ25101 (0.5 max) | about 0.72 | Yes, if the unverified heights hold |
| Chip antenna | 0.12 flex + 1.30 ([Johanson](https://www.johansontechnology.com/docs/3827/Antenna-2450AT18A0100001E-Rev4.0.pdf)) | 1.42 | No |

Pocket rules:

- Leave 0.2 to 0.3 mm of side clearance in the battery pocket for swelling. Never solder to the pouch.
- Keep the coil off the cell's metal pouch, to avoid eddy heating.
- Keep gold foil artwork out of the antenna keep-out.

These rules come from the research's engineering judgment, not a cited spec.

## Open risks and unknowns

1. **GrapheneOS owner key.** The Google owner key is "locked" until an Android device has set up Find My Device, and no source confirms that sandboxed Play on GrapheneOS can unlock it ([GoogleFindMyTools README](https://github.com/leonboe1/GoogleFindMyTools)). The fallback is a cheap stock Android phone signed into the same dedicated account.
2. **Unofficial APIs.** The Google path impersonates GMS against undocumented endpoints ([MockingBeacon plan](https://github.com/ak2k/MockingBeacon/blob/main/docs/plans/2026-04-17-fhn-openhaystack-plan.md)). No account bans were found, but use dedicated accounts on both the Google and Apple sides.
3. **Frame type 0x41.** Both Everytag and the GoogleFindMyTools Zephyr firmware advertise frame type 0x41. The spec reserves 0x41 for unwanted-tracking-protection mode, and both use a static MAC ([Google FHN spec](https://developers.google.com/nearby/fast-pair/specifications/extensions/fmdn); [Zephyr firmware](https://github.com/leonboe1/GoogleFindMyTools/tree/main/ZephyrFirmware)). That may raise tracker alerts on nearby phones. It is untested.
4. **NCS age.** NCS 2.8.0 is old for nRF54L. MockingBeacon's NCS 3.2.4 port has not run on real nRF54L15 hardware ([MockingBeacon](https://github.com/ak2k/MockingBeacon)).
5. **Qi coupling through leather.** No minimum receiver coil size for Qi BPP detection was found, and there is no measured data on leather attenuation or temperature rise ([Würth](https://www.we-online.com/en/components/products/WE-WPCC-RECEIVER)).
6. **Qi pad compatibility.** Everytag's own Qi beacon "may not work with all Qi/WPC chargers because small receiving charging coil", and placing it on a pad generates an MCU reset pulse ([Everytag hardware](https://github.com/vasimv/Everytag/tree/main/hardware)).
7. **Coil Q requirement.** TI's "Q > 77" rule does not obviously match Würth's catalog Q of 13 to 25, which may be measured under different conditions. Check which Q the rule means ([TI BQ51003](https://www.ti.com/lit/ds/symlink/bq51003.pdf); [Würth](https://www.we-online.com/en/components/products/WE-WPCC-RECEIVER)).
8. **Unverified data.** Package heights, cell self-discharge, Grepow bend limits and whether the cell has a PCM are all unconfirmed. The Double Oak pocket depth and fit were not researched.
9. **Apple sign-in.** Apple authentication may be broken at any given moment (issue #249, October 2026) ([macless-haystack issues](https://github.com/dchristl/macless-haystack/issues)).

## Bench validation plan with pass/fail gates

**Demo 1: the DK is visible on Google and Apple from Fedora and the Pi.**

1. Flash Everytag with the low-power config, and get the Google key from GoogleFindMyTools ([Everytag](https://github.com/vasimv/Everytag)).
2. Authenticate on Fedora, then copy `secrets.json` to the Pi ([traccar/google-find-hub-sync](https://github.com/traccar/google-find-hub-sync)).
3. Run anisette-v3-server plus macless-haystack on the Pi.

*Pass:* within 7 days, the Pi decrypts at least one Google report and one Apple report, and the Apple status byte decodes to a battery level. The Google feed must also survive at least one cron-driven 4-day refresh boundary.
*Fail:* Google returns "encryption data is locked" and the stock-Android fallback does not clear it.

**Demo 2: PPK2 power.** Measure the DK's SoC rail with the debugger isolated, after a full power cycle ([DevZone 126020](https://devzone.nordicsemi.com/f/nordic-q-a/126020/nrf54l15-dk-the-soc-keeps-being-woken-up-from-system-off-by-the-onboard-debugger/556547)).

*Pass:* 12 µA or less in mode A at 0 dBm, and 19 µA or less in mode B. Also record the charge per event at 0, +4 and +8 dBm to replace the estimates above.
*Fail:* readings above about 50 µA point to logging, regulator-mode or debugger traps.

**Demo 3: Qi charging through leather.** Bench the BQ51003, BQ25101, the chosen coil and the GRP0849049 cell, with wallet leather between the pad and the coil. Test 2 to 3 cheap Qi pads plus one Qi2 or MagSafe-class pad.

*Pass:*

- Charging starts on every pad.
- Charge current holds at the RISET value.
- The NTC stays under 45 °C, the JEITA cutoff ([TI BQ25101](https://www.ti.com/lit/ds/symlink/bq25101.pdf)).
- Off-pad battery drain from the charge chain stays at 0.1 µA or less.

*Fail:* no handshake through leather with the Ø26 mm coil, or the cell heats from coil flux.

**Demo 4: app plus alerts.** Run Traccar, the PWA, ntfy (F-Droid app) and Tailscale.

*Pass:*

- A tag appears in its bundle (group) with fixes from both networks.
- A forced low Apple status byte triggers a Low Battery ntfy alert on the Pixel.
- Powering the DK off triggers a Device Inactive alert within the set period ([Traccar events](https://www.traccar.org/documentation/events/)).
- A deliberately broken refresh job raises an alert.

**Demo 5: v1 card.** Repeat Demos 1 to 4 on the v1 rigid card, inside the wallet pocket.

*Pass:*

- Pickup is comparable to the DK over a week of normal carry.
- Measured average current is within 20% of Demo 2.
- The card charges through the pocket leather.
- The RF match is tuned, since Nordic marks its match values as preliminary ([CAAA schematic](https://devzone.nordicsemi.com/cfs-file/__key/communityserver-discussions-components-files/4/nRF54L15_5F00_caaa_5F00_config1_5F00_schematic.pdf)).

**Do not order v2 flex boards, WLCSP parts or overlays until v1 passes Demo 5.** v2 changes the package, antenna and PCB all at once. Any unresolved v1 failure would then be indistinguishable from a v2 layout or thinness problem.

## Regulatory and safety notes

**FCC.** A device that is not marketed, not built from a kit and built in quantities of five or fewer for personal use needs no FCC equipment authorization. You must still follow good engineering practice, and the 15.5 no-harmful-interference rule still applies ([47 CFR 15.23](https://www.law.cornell.edu/cfr/text/47/15.23)). Giving or selling units ends that exemption. For comparison, Chipolo's card is certified at 1.4 mW conducted under Part 15C ([fccid.io](https://fccid.io/2AD85-C24R)).

**Network certification.** Commercial Find Hub devices must implement DULT (the anti-stalking accessory protocol), which requires a sound maker of at least 60 phon ([Google FHN spec](https://developers.google.com/nearby/fast-pair/specifications/extensions/fmdn); [IETF DULT draft](https://www.ietf.org/archive/id/draft-ietf-dult-accessory-protocol-01.html)). The speakerless design is acceptable only for personal use.

**Detection.** Scanners such as AirGuard now cover Google's network as well ([ATHENE](https://www.athene-center.de/en/news/news/airguard-extends-protection-with-google-tracker-ne-1732)), so expect the static Google identity to be visible to them. Never deploy the firmware on anyone else's belongings.

**LiPo safety.**

- Keep JEITA charging limits through the NTC.
- Keep hardware protection even with firmware load cutoff.
- Use pressure-sensitive adhesive, not rigid potting or heat lamination, around the cell.
- Keep the cell off the coil's flux path.

Metal RFID-blocking wallet parts can interfere with Bluetooth ([Nomad Help Center](https://help.nomadgoods.com/en-US/tracking-card-pro-3155373)).

## Conclusion

The biggest change is that the charging subsystem, not the radio, decides battery life. Moving from the BQ51050B to a BQ51003 plus BQ25101 chain roughly triples life on the same cell. Picking a protector with no standby drain matters nearly as much as the whole TX power choice. The second change is operational: Google's network works here only with a host that refreshes every 4 days and a sign-in done on x86. That makes the Pi part of the tracker, not an accessory, and it needs its own watchdog.

Treat v1 as the real experiment. It proves coupling through leather, pickup and current draw with forgiving parts. v2 is then an exercise in shrinking a design you already know works.
