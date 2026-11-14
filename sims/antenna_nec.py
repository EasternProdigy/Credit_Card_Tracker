"""
Printed inverted-F antenna (IFA) for 2.4 GHz on the card's short edge,
simulated with NEC-2 method of moments (PyNEC).

Model
- Coplanar ground: a wire-grid copper plane 54 mm wide (card short edge)
  x 60 mm long (the PCB ground under the electronics plus the region the
  battery pouch couples to). Grid pitch 3 mm (< lambda/40 at 2.44 GHz).
- IFA in the same plane, in the ~10 mm antenna strip beyond the ground edge:
    shorting stub at x = xs, feed at x = xf, both rising h mm off the ground
    edge, then a radiating arm of length L along the edge.
- Traces 0.5 mm wide -> equivalent wire radius w/4 = 0.125 mm. Copper
  loss included (sigma = 5.8e7 S/m).
- Free space, no dielectric. The thin 0.12 mm polyimide barely loads it;
  leather and a hand/body nearby DO. We model that afterwards as an effective
  permittivity that scales the resonance down by 1/sqrt(eps_eff), and size the
  matching network to pull it back.
"""
import numpy as np, json, itertools
from PyNEC import nec_context
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

mm = 1e-3
GW, GL, P = 54 * mm, 60 * mm, 3 * mm
WR = 0.125 * mm
SIG = 5.8e7

def build(L, xf, xs=6 * mm, h=6 * mm):
    c = nec_context()
    g = c.get_geometry()
    tag = 1
    # ground grid: plane y in [-GL, 0], x in [0, GW]
    xs_grid = np.round(np.arange(0, GW + 1e-9, P), 6)
    ys_grid = np.round(np.arange(-GL, 1e-9, P), 6)
    for y in ys_grid:                                  # horizontal wires
        for i in range(len(xs_grid) - 1):
            g.wire(tag, 1, xs_grid[i], y, 0, xs_grid[i + 1], y, 0, WR, 1, 1); tag += 1
    for x in xs_grid:                                  # vertical wires
        for j in range(len(ys_grid) - 1):
            g.wire(tag, 1, x, ys_grid[j], 0, x, ys_grid[j + 1], 0, WR, 1, 1); tag += 1
    # IFA
    feed_tag = 9000
    g.wire(feed_tag, 3, xf, 0, 0, xf, h, 0, WR, 1, 1)          # feed leg
    g.wire(9001, 3, xs, 0, 0, xs, h, 0, WR, 1, 1)              # short leg
    g.wire(9002, 2, xs, h, 0, xf, h, 0, WR, 1, 1)              # top between short and feed
    nseg = max(3, int(L / (1.5 * mm)))
    g.wire(9003, nseg, xf, h, 0, xf + L, h, 0, WR, 1, 1)       # radiating arm
    c.geometry_complete(0)
    c.ld_card(5, 0, 0, 0, SIG, 0, 0)                           # copper loss on all wires
    c.ex_card(0, feed_tag, 1, 0, 1.0, 0, 0, 0, 0, 0)
    return c

def zin(L, xf, f_mhz):
    c = build(L, xf)
    c.fr_card(0, 1, f_mhz, 0)
    c.xq_card(0)
    return c.get_input_parameters(0).get_impedance()[0]

def gamma(z, z0=50.0):
    return (z - z0) / (z + z0)

out = {}
# ---- coarse design search at 2440 MHz
best = None
for L, xf in itertools.product(np.arange(14, 30, 1.0) * mm, np.array([9, 12, 15]) * mm):
    if xf + L > GW - 1 * mm:
        continue
    z = zin(L, xf, 2440.0)
    g = abs(gamma(z))
    if best is None or g < best[0]:
        best = (g, L, xf, z)
g0, Lb, xfb, zb = best
out["design"] = {"arm_length_mm": round(Lb / mm, 1), "feed_x_mm": round(xfb / mm, 1), "short_x_mm": 6.0, "height_mm": 6.0,
                 "trace_mm": 0.5, "Zin_2440": [round(zb.real, 1), round(zb.imag, 1)],
                 "S11_dB_2440": round(20 * np.log10(g0), 1)}

# ---- fine L search around best
fine = []
for L in np.arange(Lb / mm - 1.5, Lb / mm + 1.6, 0.25) * mm:
    if xfb + L > GW - 1 * mm:
        continue
    z = zin(L, xfb, 2440.0)
    fine.append((abs(gamma(z)), L, z))
g1, Lf, zf = min(fine, key=lambda t: t[0])
out["design"].update({"arm_length_mm": round(Lf / mm, 2), "Zin_2440": [round(zf.real, 1), round(zf.imag, 1)],
                      "S11_dB_2440": round(20 * np.log10(g1), 1)})

# ---- frequency sweep (free space) and dielectric detuning
freqs = np.arange(2200, 2701, 20.0)
s11 = []
zs = []
for f in freqs:
    z = zin(Lf, xfb, f); zs.append(z); s11.append(20 * np.log10(abs(gamma(z))))
s11 = np.array(s11)
f_res = freqs[np.argmin(s11)]
bw = freqs[s11 < -10]
out["free_space"] = {"f_res_MHz": float(f_res), "S11_min_dB": round(float(s11.min()), 1),
                     "-10dB_band_MHz": [float(bw.min()), float(bw.max())] if len(bw) else None,
                     "S11_at_2402_2440_2480_dB": [round(float(np.interp(f, freqs, s11)), 1) for f in (2402, 2440, 2480)]}

# Detuning: eps_eff scales the electrical length -> resonance moves to f/sqrt(eps)
det = {}
for eps in (1.0, 1.1, 1.25, 1.4):
    # equivalent: in-wallet antenna at f behaves like free-space antenna at f*sqrt(eps)
    vals = [20 * np.log10(abs(gamma(zin(Lf, xfb, f * np.sqrt(eps))))) for f in (2402, 2440, 2480)]
    det[str(eps)] = [round(v, 1) for v in vals]
out["detuning_S11_dB_at_2402_2440_2480_vs_eps_eff"] = det

# Gain / efficiency at 2440 (radiation pattern integration)
c = build(Lf, xfb); c.fr_card(0, 1, 2440.0, 0)
c.rp_card(0, 37, 73, 0, 5, 0, 0, 0.0, 0.0, 5.0, 5.0, 0, 0)
rp = c.get_radiation_pattern(0)
gains = np.array(rp.get_gain())
out["peak_gain_dBi"] = round(float(gains.max()), 2)
# NEC reports radiation efficiency in the RP output via average power gain
try:
    out["avg_power_gain"] = round(float(rp.get_average_power_gain()), 3)
except Exception:
    pass

plt.figure(figsize=(7, 4))
plt.plot(freqs, s11, label="free space (NEC-2)")
for eps in (1.1, 1.25, 1.4):
    plt.plot(freqs, [20 * np.log10(abs(gamma(zin(Lf, xfb, f * np.sqrt(eps))))) for f in freqs], ls="--",
             label=f"in wallet, eps_eff={eps}")
plt.axvspan(2402, 2480, color="g", alpha=.1, label="BLE band")
plt.axhline(-10, c="k", lw=.8, ls=":")
plt.xlabel("MHz"); plt.ylabel("S11 (dB)"); plt.title(f"Printed IFA: arm {Lf/mm:.1f} mm, feed {xfb/mm:.0f} mm, h 6 mm")
plt.legend(fontsize=7); plt.grid(alpha=.3); plt.tight_layout(); plt.savefig("../plots/antenna_s11.png", dpi=150)

print(json.dumps(out, indent=1))
json.dump(out, open("antenna_nec.json", "w"), indent=1)
