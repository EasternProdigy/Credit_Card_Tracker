"""
End-to-end protocol check for both networks, using the real crypto code paths.

APPLE (OpenHaystack / Everytag "offline finding" frame)
  1. Generate a P-224 key pair (what Everytag stores; up to 40 keys).
  2. Build the exact 31-byte advertisement Everytag sends (template from
     Everytag main.c) and the static-random MAC derived from the key.
  3. Act as a finder iPhone: ECDH(P-224) with an ephemeral key, ANSI X9.63
     KDF (SHA-256) -> AES-GCM key + IV, encrypt the 10-byte location payload
     (lat int32, lon int32, accuracy, status). Report layout matches what
     macless-haystack decrypts (decrypt_reports.dart): ts(4) conf(1)
     eph_pub(57) ciphertext(10) tag(16).
  4. Act as our server: decrypt, decode SIGNED coordinates and battery bits.

GOOGLE (FMDN frame via GoogleFindMyTools crypto, imported from its source)
  1. Generate an EIK, compute the EID exactly as GoogleFindMyTools registers
     it (timestamp 0, K=10), build Everytag's FMDN service-data frame.
  2. Act as a finder Android: encrypt a location to the EID (foreign_tracker_cryptor.encrypt).
  3. Act as the owner: decrypt with the EIK.
  4. Compute the correct "hashed flags" mask for a static EID so the
     firmware can send a spec-correct flags byte without knowing the EIK.
"""
import sys, os, struct, hashlib, secrets, json, time
sys.path.insert(0, "/tmp/src/GoogleFindMyTools")
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization

report = {}

# ---------------------------------------------------------------- APPLE
def x963_kdf(shared, info, length):
    out, counter = b"", 1
    while len(out) < length:
        out += hashlib.sha256(shared + counter.to_bytes(4, "big") + info).digest()
        counter += 1
    return out[:length]

priv = ec.generate_private_key(ec.SECP224R1())
pub = priv.public_key().public_numbers()
adv_key = pub.x.to_bytes(28, "big")            # 28-byte advertised key (x coordinate)

# Everytag/OpenHaystack frame build
battery_level = 2                               # 0 full,1 medium,2 low,3 critical
status = 0x20 | (battery_level << 6)            # 0x20 = "battery updates supported" flag
adv = bytearray([0x1e, 0xff, 0x4c, 0x00, 0x12, 0x19, status])
adv += adv_key[6:28]                            # 22 bytes of key
adv += bytes([adv_key[0] >> 6, 0x00])           # top two bits of key[0], hint
mac = bytearray(adv_key[0:6]); mac[0] |= 0xC0   # static random address from key
report["apple_adv_len_bytes"] = len(adv)
report["apple_adv_fits_31B"] = len(adv) <= 31
report["apple_mac"] = ":".join(f"{b:02X}" for b in mac)

# Finder (iPhone) side
lat, lon = 42.37360, -71.11900                  # Cambridge, MA (negative longitude on purpose)
payload = struct.pack(">iiBB", int(lat * 1e7), int(lon * 1e7), 12, status)
eph = ec.generate_private_key(ec.SECP224R1())
eph_pub = eph.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
peer = ec.EllipticCurvePublicNumbers(pub.x, pub.y, ec.SECP224R1()).public_key()
shared = eph.exchange(ec.ECDH(), peer)
kd = x963_kdf(shared, eph_pub, 32)
key, iv = kd[:16], kd[16:]
ct = AESGCM(key).encrypt(iv, payload, None)
ts = int(time.time()) - 978307200               # Apple epoch 2001-01-01
blob = struct.pack(">IB", ts, 80) + eph_pub + ct  # ct includes 16-byte tag at end
report["apple_report_len"] = len(blob)          # expect 4+1+57+10+16 = 88

# Server (owner) side, mirroring decrypt_reports.dart but with SIGNED ints
eph_b = blob[5:62]; enc = blob[62:72]; tag = blob[72:]
eph_pt = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP224R1(), eph_b)
shared2 = priv.exchange(ec.ECDH(), eph_pt)
kd2 = x963_kdf(shared2, eph_b, 32)
pt = AESGCM(kd2[:16]).decrypt(kd2[16:], enc + tag, None)
la, lo, acc, st = struct.unpack(">iiBB", pt)
report["apple_decoded"] = {"lat": la / 1e7, "lon": lo / 1e7, "accuracy_m": acc,
                           "battery_bits": st >> 6, "battery_flag_set": bool(st & 0x20)}
assert abs(la / 1e7 - lat) < 1e-6 and abs(lo / 1e7 - lon) < 1e-6 and st >> 6 == battery_level
# Show the unsigned-decode pitfall (what you get if you decode as uint32 and do not correct)
report["apple_unsigned_pitfall_lon"] = struct.unpack(">I", struct.pack(">i", int(lon * 1e7)))[0] / 1e7

# ---------------------------------------------------------------- GOOGLE
from FMDNCrypto.eid_generator import generate_eid, calculate_r, ROTATION_PERIOD
from FMDNCrypto import foreign_tracker_cryptor as ftc

eik = secrets.token_bytes(32)
eid = generate_eid(eik, 0)                      # exactly what create_ble_device.py registers
# Spec numbers bits MSB-first (bit 0 = 0x80). Bits 5-6 = battery -> mask 0x06, bit 7 = UTP -> 0x01.
FLAG_BATT = {"unsupported": 0x00, "normal": 0x02, "low": 0x04, "critical": 0x06}
flags_raw = FLAG_BATT["normal"]                   # UTP off
r = calculate_r(eik, 0)
mask = hashlib.sha256(r.to_bytes(20, "big")).digest()[-1]   # LSB of SHA256(r)  [Find Hub spec "hashed flags"]
flags_hashed = flags_raw ^ mask
frame = bytes([0x02, 0x01, 0x06]) + bytes([0x19, 0x16, 0xAA, 0xFE, 0x40]) + eid + bytes([flags_hashed])
report["google_eid_len"] = len(eid)
report["google_adv_len_bytes"] = len(frame)
report["google_adv_fits_31B"] = len(frame) <= 31
report["google_registered_slots_4days"] = int(4 * 24 * 3600 / ROTATION_PERIOD)
report["google_hashed_flags_mask_for_this_static_eid"] = f"0x{mask:02X}"
report["google_flags_raw_correct"] = f"0x{flags_raw:02X}"
report["google_flags_on_air_correct"] = f"0x{flags_hashed:02X}"
ev = 0xC0 ^ mask  # what a phone recovers if Everytag's unhashed 0xC0 is un-xored by the phone
report["google_everytag_0xC0_as_seen_by_phone"] = {"byte": f"0x{ev:02X}", "reserved_bits_set": bool(ev & 0xF8),
  "battery_field": (ev >> 1) & 3, "utp_bit": ev & 1}
report["google_everytag_frame_type"] = "0x41 = 'unwanted tracking protection mode ON' per spec; should be 0x40"

# Finder (Android) side -> owner side
loc = b"lat=42.37360,lon=-71.11900"
enc_tag, Sx = ftc.encrypt(loc, secrets.token_bytes(20), eid)
dec = ftc.decrypt(eik, enc_tag, Sx, 0)
report["google_roundtrip_ok"] = dec == loc

print(json.dumps(report, indent=1))
json.dump(report, open(os.path.join(os.path.dirname(__file__), "protocol_roundtrip.json"), "w"), indent=1)
