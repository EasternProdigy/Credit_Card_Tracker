"""
(1) Re-optimize the IFA arm for the in-wallet environment (eps_eff 1.3 estimate:
    0.12 mm polyimide + 0.125 mm PC skins + ~1.2 mm leather on both faces) by
    solving the free-space model at f*sqrt(eps_eff).
(2) Link budget to a finder phone (Friis + log-distance indoor model).
"""
import numpy as np, json
from antenna_nec import zin, gamma, mm
out = {}
for eps in (1.2, 1.3, 1.45):
    ftarget = 2440 * np.sqrt(eps)
    best = min(((abs(gamma(zin(L * mm, 15 * mm, ftarget))), L) for L in np.arange(12, 24.1, 0.5)), key=lambda t: t[0])
    out[f"arm_for_eps_{eps}"] = {"arm_mm": best[1], "S11_dB": round(20 * np.log10(best[0]), 1)}
# mismatch loss table
out["mismatch_loss_dB_for_S11"] = {s: round(-10 * np.log10(1 - 10 ** (s / 10)), 2) for s in (-20, -10, -7, -4, -2.4)}

# ---- link budget
f = 2.44e9; lam = 3e8 / f
def pl(d, n):          # log-distance, 1 m reference = free space
    return 20 * np.log10(4 * np.pi * 1.0 / lam) + 10 * n * np.log10(d)
P_tx = 0.0             # dBm (Everytag TX_POWER_NORMAL)
G_tx_free = 2.86       # dBi (NEC peak), use avg ~0 dBi omni-ish
cases = {
  "wallet on a table/bag, matched": {"G": 0.0, "mismatch": 0.5, "body": 0.0},
  "wallet in a back pocket (body loss 10 dB), matched": {"G": 0.0, "mismatch": 0.5, "body": 10.0},
  "back pocket, antenna NOT retuned (S11 -4 dB)": {"G": 0.0, "mismatch": 2.2, "body": 10.0},
}
G_rx = -3.0            # phone antenna, dBi typical
sens = -92.0           # dBm, practical phone BLE scan sensitivity with margin
rng = {}
for name, c in cases.items():
    eirp = P_tx + c["G"] - c["mismatch"] - c["body"]
    budget = eirp + G_rx - sens
    r = {}
    for n, env in ((2.0, "open air/outdoors"), (2.7, "indoors/street clutter")):
        d = 10 ** ((budget - 20 * np.log10(4 * np.pi / lam)) / (10 * n))
        r[env] = round(float(d), 1)
    rng[name] = {"EIRP_dBm": round(eirp, 1), "range_m": r}
out["link_budget_range"] = rng
print(json.dumps(out, indent=1))
json.dump(out, open("antenna_inwallet_link.json", "w"), indent=1)
