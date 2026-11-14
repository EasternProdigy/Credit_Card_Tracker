"""
End-to-end backend proof against a real Traccar 6.6 server.

What it proves:
  1. Account + "bundle" (Traccar group) + tracker device creation via REST API.
  2. Ingest exactly like our fetcher scripts will: OsmAnd HTTP protocol on :5055
     with lat/lon/timestamp/accuracy/battery (the Google and Apple fetchers both
     push this way after decrypting).
  3. Low-battery path: a report with alarm=lowBattery produces an event that
     Traccar forwards to our alert bridge (stand-in for ntfy).
  4. The PWA's read path: /api/devices, /api/groups, /api/positions return
     everything a map + bundle view needs, including SIGNED longitude.
"""
import requests, time, json, sys

BASE = "http://127.0.0.1:8082/api"
OSMAND = "http://127.0.0.1:5055"
s = requests.Session()
res = {}

# 1. first user becomes admin
u = {"name": "Dwayne", "email": "dwayne@example.local", "password": "change-me-123"}
r = s.post(f"{BASE}/users", json=u); res["create_user"] = r.status_code
r = s.post(f"{BASE}/session", data={"email": u["email"], "password": u["password"]}); res["login"] = r.status_code

g = s.post(f"{BASE}/groups", json={"name": "Wallet bundle"}).json()
travel = s.post(f"{BASE}/groups", json={"name": "Travel bundle"}).json()
dev = s.post(f"{BASE}/devices", json={"name": "Wallet card", "uniqueId": "card-0001", "groupId": g["id"]}).json()
bag = s.post(f"{BASE}/devices", json={"name": "Backpack tag", "uniqueId": "tag-0002", "groupId": travel["id"]}).json()
res["groups"] = [g["name"], travel["name"]]; res["device"] = {"id": dev["id"], "groupId": dev["groupId"]}

# 2. ingest as the fetchers will (Google report, then Apple report with battery bits)
def push(uid, lat, lon, ts, acc, batt=None, extra=None):
    p = {"id": uid, "lat": lat, "lon": lon, "timestamp": int(ts), "accuracy": acc}
    if batt is not None: p["batt"] = batt
    if extra: p.update(extra)
    return requests.get(OSMAND, params=p).status_code

now = time.time()
res["ingest_google"] = push("card-0001", 42.37360, -71.11900, now - 600, 49, extra={"network": "google"})
res["ingest_apple"] = push("card-0001", 42.37421, -71.11812, now - 300, 33, batt=60, extra={"network": "apple"})
res["ingest_bag"] = push("tag-0002", 42.36010, -71.05890, now - 200, 20, batt=90)
# 3. low battery from the Apple status bits -> alarm
res["ingest_lowbatt"] = push("card-0001", 42.37425, -71.11810, now - 60, 30, batt=15, extra={"alarm": "lowBattery", "network": "apple"})
time.sleep(4)

# 4. PWA read path
pos = s.get(f"{BASE}/positions").json()
devs = s.get(f"{BASE}/devices").json()
res["positions"] = [{"deviceId": p["deviceId"], "lat": p["latitude"], "lon": p["longitude"],
                     "accuracy": p.get("accuracy"), "battery": p["attributes"].get("batteryLevel"),
                     "network": p["attributes"].get("network"), "alarm": p["attributes"].get("alarm"),
                     "fixTime": p["fixTime"]} for p in pos]
res["devices"] = [{"name": d["name"], "groupId": d["groupId"], "status": d["status"], "lastUpdate": d["lastUpdate"]} for d in devs]
fr = s.get(f"{BASE}/reports/route", params={"deviceId": dev["id"], "from": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 3600)),
                                             "to": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 60))},
           headers={"Accept": "application/json"})
res["history_points_for_card"] = len(fr.json()) if fr.ok else fr.status_code
try:
    ev = [json.loads(l) for l in open("/tmp/traccar/forwarded_events.jsonl")]
    res["forwarded_events"] = [{"type": e["event"]["type"], "alarm": e["event"].get("attributes", {}).get("alarm"),
                                "device": e.get("device", {}).get("name")} for e in ev]
except FileNotFoundError:
    res["forwarded_events"] = []
print(json.dumps(res, indent=1))
json.dump(res, open("/home/claude/verification/server/backend_e2e.json", "w"), indent=1)
