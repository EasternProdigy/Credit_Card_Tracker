"""To-scale card floorplan (85.60 x 53.98 mm, ISO ID-1, r = 3.18 mm) with keep-outs,
and a thickness stack check (worst case and RSS) for every region."""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

W, H, R = 85.60, 53.98, 3.18
fig, ax = plt.subplots(figsize=(9, 5.9))
ax.add_patch(FancyBboxPatch((0, 0), W, H, boxstyle=f"round,pad=0,rounding_size={R}", fc="#111", ec="k"))
wall = 2.0
# battery
ax.add_patch(Rectangle((wall, (H - 49) / 2), 49, 49, fc="#5577aa", ec="w", lw=1))
ax.text(wall + 24.5, H / 2, "LiPo GRP0849049\n49 x 49 x 0.85 mm\n135 mAh", ha="center", va="center", color="w", fontsize=8)
# right column
xc = wall + 49 + 1.5
colw = W - wall - xc
# Qi coil (top of column)
coil_c = (xc + colw / 2, H - wall - 13)
ax.add_patch(Circle(coil_c, 13, fc="#aa7733", ec="w"))
ax.add_patch(Circle(coil_c, 4, fc="#111", ec="w"))
ax.text(*coil_c, "Qi coil\n26 mm, 0.5 mm\n(no copper\nunder it)", ha="center", va="center", color="w", fontsize=6.5)
# electronics ground zone
ey0, ey1 = wall + 8.5, coil_c[1] - 13 - 1.0
ax.add_patch(Rectangle((xc, ey0), colw, ey1 - ey0, fc="#2d6a3e", ec="w"))
ax.text(xc + colw / 2, (ey0 + ey1) / 2, "nRF54L15 CSP + xtals\nBQ51003 + BQ25101\nTPS7A0233 + S-82N1B\nstiffener zone", ha="center",
        va="center", color="w", fontsize=6.5)
# antenna keep-out strip along bottom long edge
ax.add_patch(Rectangle((xc, wall), colw, 7.5, fc="#333", ec="#e6c200", ls="--"))
x0 = xc + 3
ge = ey0; ya = ge - 6.0
ax.plot([x0, x0], [ge, ya], c="#e6c200", lw=2)                 # shorting leg
ax.plot([x0 + 3, x0 + 3], [ge, ya], c="#ff5555", lw=2)         # feed leg (to match network)
ax.plot([x0, x0 + 3 + 20], [ya, ya], c="#e6c200", lw=2)        # arm, open end at the card corner
ax.text(x0 + 3.4, ge - 1.6, "feed", color="#ff5555", fontsize=6)
ax.text(xc + colw / 2 + 2, wall + 0.6, "IFA: arm 20 mm, h 6 mm; keep-out: no copper, metal or gold foil", ha="center", color="#e6c200", fontsize=5.5)
ax.set_xlim(-2, W + 2); ax.set_ylim(-2, H + 2); ax.set_aspect("equal")
ax.set_title("Card floorplan to scale (mm): battery | coil + electronics column | antenna on the long edge")
ax.set_xlabel("mm"); ax.set_ylabel("mm")
plt.tight_layout(); plt.savefig("../plots/card_floorplan.png", dpi=160)

# ---- thickness stacks (mm): (nominal, tolerance)
skins = [("PC overlay top", 0.125, 0.010), ("3M 467MP adhesive", 0.058, 0.005),
         ("467MP adhesive", 0.058, 0.005), ("PC overlay bottom", 0.125, 0.010)]
regions = {
    "battery": [("LiPo GRP0849049 (swells ~3-5% over life)", 0.85, 0.05)],
    "coil": [("Wurth 760308101309 coil", 0.50, 0.05), ("flex PCB 2L", 0.12, 0.02)],
    "electronics (CSP side)": [("flex PCB 2L", 0.12, 0.02), ("PI stiffener", 0.10, 0.02),
                               ("tallest part: nRF54L15 CSP / BQ51003 YFP / 0201 caps ~0.33-0.625", 0.625, 0.03)],
    "electronics if QFN48 used": [("flex PCB 2L", 0.12, 0.02), ("PI stiffener", 0.10, 0.02), ("nRF54L15 QFN48", 0.85, 0.05)],
}
res = {}
skin_nom = sum(s[1] for s in skins); skin_tol = sum(s[2] for s in skins); skin_rss2 = sum(s[2] ** 2 for s in skins)
for name, layers in regions.items():
    nom = skin_nom + sum(l[1] for l in layers)
    wc = nom + skin_tol + sum(l[2] for l in layers)
    rss = nom + np.sqrt(skin_rss2 + sum(l[2] ** 2 for l in layers))
    res[name] = {"nominal_mm": round(nom, 3), "worst_case_mm": round(wc, 3), "RSS_mm": round(rss, 3),
                 "fits_1.5mm_worst_case": wc <= 1.5}
print(json.dumps(res, indent=1)); json.dump(res, open("thickness_stack.json", "w"), indent=1)
