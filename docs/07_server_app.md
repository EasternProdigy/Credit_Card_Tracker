# 07 Server and app

Host: Raspberry Pi 4 or 5 (8 GB, 64-bit Raspberry Pi OS). The Fedora desktop is the backup host and is also used once for Google sign-in (Chrome).

## Services (Docker Compose)
| Service | What it does | Notes |
|---|---|---|
| GoogleFindMyToolsWebUi (`ghcr.io/p6g9yhk6/googlefindmytools`, port 4321) | Polls Find Hub, decrypts, refreshes the custom tracker key, forwards to Traccar (OsmAnd preset) | Sign in on Fedora, then copy `Auth/secrets.json`. Home network only. Set `SECRETS_ENCRYPTION_KEY`. Check for an arm64 image, or build one. |
| anisette-v3-server (`dadoum/anisette-v3-server`) | Apple auth data | arm64 image exists |
| Apple fetcher (ours, Python) | Fetches encrypted Find My reports through the anisette and macless-haystack endpoint flow, decrypts (P-224 ECDH, X9.63 KDF, AES-GCM), and pushes to Traccar | Decode coordinates as **signed** int32 / 1e7. Decrypter verified in `sims/protocol_roundtrip.py`. Use a secondary Apple ID with SMS 2FA. Apple sign-in has been fragile (503 / -80045 errors, Sep to Oct 2026). |
| Traccar 6.6 (port 8082 web/API, 5055 OsmAnd) | Database, groups (bundles), alarms, inactivity, REST and WebSocket | Config in `server/traccar.xml` |
| ntfy (self-hosted) | Push to GrapheneOS through the F-Droid ntfy app | Receives Traccar `event.forward.url` through a tiny bridge |
| Caddy + Tailscale | HTTPS and remote access with nothing exposed publicly | |

## Verified API contract (run against real Traccar 6.6, see `sims/backend_e2e.py`)
- `POST /api/users`, `POST /api/session`, `POST /api/groups`, `POST /api/devices`
- Ingest: `GET :5055/?id=<uniqueId>&lat=&lon=&timestamp=&accuracy=&batt=&alarm=lowBattery&network=apple|google`
- Read: `GET /api/devices`, `GET /api/positions`, `GET /api/reports/route?deviceId&from&to`
- Events forwarded as JSON to `event.forward.url` (seen: `deviceOnline`, `alarm/lowBattery`)

## PWA (to build)
- **Map:** Leaflet with OSM tiles.
- **Bundle list:** Traccar groups.
- **Item detail:** last seen, which network, accuracy, battery, history trail.
- **Alerts screen.**
- **Settings:** inactivity threshold per item.

Auth goes through a Traccar session. Install it on GrapheneOS and Fedora.
