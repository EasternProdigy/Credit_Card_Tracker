"""
Re-simulate the IFA with the REAL card floorplan instead of a big ideal ground.

Card 85.6 x 54 mm. Battery 49 x 49 mm on the left. Right column ~30 mm wide holds
the Qi coil (top) and electronics (bottom). The antenna runs along the bottom
LONG edge, under the electronics ground, with its open end pointing at the
card's corner (away from the battery).

Ground cases:
  A) electronics copper only: 30 mm (x) x 16 mm (y)
  B) electronics copper + battery pouch acting as ground extension
     (49 x 49 mm grid tied on at two points, through the cell's negative tab)
"""
import numpy as np, json, itertools
from PyNEC import nec_context
mm = 1e-3; WR = 0.125 * mm; P = 3 * mm

def build(L, xf, xs, h, with_batt):
    c = nec_context(); g = c.get_geometry(); tag = 1
    def grid(x0, x1, y0, y1):
        nonlocal tag
        xs_ = np.round(np.arange(x0, x1 + 1e-9, P), 6); ys_ = np.round(np.arange(y0, y1 + 1e-9, P), 6)
        for y in ys_:
            for i in range(len(xs_) - 1):
                g.wire(tag, 1, xs_[i], y, 0, xs_[i+1], y, 0, WR, 1, 1); tag += 1
        for x in xs_:
            for j in range(len(ys_) - 1):
                g.wire(tag, 1, x, ys_[j], 0, x, ys_[j+1], 0, WR, 1, 1); tag += 1
    # electronics ground: x 0..30, y -16..0 ; antenna above y=0 ... we mirror so antenna is at the card edge
    grid(0, 30 * mm, -15 * mm, 0)
    if with_batt:
        grid(-51 * mm, -3 * mm, -45 * mm, 3 * mm)    # pouch region (approx, 48 x 48)
        g.wire(tag, 1, -3 * mm, 0, 0, 0, 0, 0, WR, 1, 1); tag += 1          # tab ties
        g.wire(tag, 1, -3 * mm, -15 * mm, 0, 0, -15 * mm, 0, WR, 1, 1); tag += 1
    g.wire(9000, 3, xf, 0, 0, xf, h, 0, WR, 1, 1)
    g.wire(9001, 3, xs, 0, 0, xs, h, 0, WR, 1, 1)
    g.wire(9002, 2, xs, h, 0, xf, h, 0, WR, 1, 1)
    g.wire(9003, max(3, int(L / (1.5 * mm))), xf, h, 0, xf + L, h, 0, WR, 1, 1)
    c.geometry_complete(0); c.ld_card(5, 0, 0, 0, 5.8e7, 0, 0)
    c.ex_card(0, 9000, 1, 0, 1.0, 0, 0, 0, 0, 0)
    return c

def zin(L, xf, xs, h, wb, f):
    c = build(L, xf, xs, h, wb); c.fr_card(0, 1, f, 0); c.xq_card(0)
    return c.get_input_parameters(0).get_impedance()[0]
G = lambda z: abs((z - 50) / (z + 50))
out = {}
for wb in (False, True):
    for eps in (1.0, 1.3):
        ft = 2440 * np.sqrt(eps)
        best = None
        for xs, xf, h, L in itertools.product([3*mm], [6*mm, 9*mm, 12*mm], [4*mm, 5*mm, 6*mm], np.arange(10, 27.1, 1.0) * mm):
            if xf + L > 33 * mm:    # arm may overhang 3 mm into the corner radius zone, no further
                continue
            z = zin(L, xf, xs, h, wb, ft)
            if best is None or G(z) < best[0]:
                best = (G(z), L, xf, h, z)
        g0, L, xf, h, z = best
        # bandwidth check at the in-situ condition
        s = [20*np.log10(G(zin(L, xf, 3*mm, h, wb, f*np.sqrt(eps)))) for f in (2402, 2440, 2480)]
        out[f"{'with_battery' if wb else 'electronics_ground_only'}__eps{eps}"] = {
            "arm_mm": round(L/mm, 1), "feed_x_mm": round(xf/mm, 1), "height_mm": round(h/mm, 1),
            "Zin": [round(z.real, 1), round(z.imag, 1)], "S11_dB_2402_2440_2480": [round(v, 1) for v in s]}
        print(out)
json.dump(out, open("antenna_floorplan.json", "w"), indent=1)
print(json.dumps(out, indent=1))
