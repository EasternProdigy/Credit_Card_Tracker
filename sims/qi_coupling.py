"""
Qi coupling through a leather wallet: mutual inductance, coupling factor k,
receiver tuning capacitors, and maximum link efficiency.

Method
- Model each spiral coil as N concentric circular filaments (radii spread
  evenly between inner and outer radius).
- Mutual inductance between two coaxial circular filaments (Maxwell):
    M = mu0 * sqrt(a*b) * [ (2/k - k) K(k) - (2/k) E(k) ],
    k^2 = 4ab / ((a+b)^2 + d^2)
  with K, E the complete elliptic integrals of the first and second kind.
- Self inductance from the same sum (i == j uses a wire-radius offset) and
  cross-checked against the Wheeler planar spiral formula.
- Lateral misalignment handled by numerically integrating the Neumann
  double line integral.
- This is AIR CORE. Real Qi coils have ferrite shields on both sides, which
  raise both L and k (typically 1.3-2x on k). So air-core k is a
  conservative lower bound.

Geometry sources
- TX: WPC "A11" transmitter (the most common BPP pad): 10 turns, outer
  diameter about 43 mm, inner about 20.5 mm, L about 6.3 uH. The interface
  surface sits about 2-3 mm above the coil. These are typical published
  A11 values; check against the WPC spec or the specific pad.
- RX: Wurth 760308101309: 26 mm OD, 0.5 mm thick, 10 uH (catalog). The
  turn count and ID are not published, so they are solved for here to
  hit 10 uH with ferrite assist.
"""
import numpy as np
from scipy.special import ellipk, ellipe
import json, sys

mu0 = 4e-7 * np.pi

def m_coax(a, b, d):
    k2 = 4 * a * b / ((a + b) ** 2 + d ** 2)
    k = np.sqrt(k2)
    # scipy uses parameter m = k^2
    K = ellipk(k2); E = ellipe(k2)
    return mu0 * np.sqrt(a * b) * ((2 / k - k) * K - (2 / k) * E)

def m_offset(a, b, d, rho, n=720):
    """Neumann integral for two circular loops, axial gap d, lateral offset rho."""
    t1 = np.linspace(0, 2 * np.pi, n, endpoint=False)
    t2 = t1.copy()
    T1, T2 = np.meshgrid(t1, t2)
    x1, y1 = a * np.cos(T1), a * np.sin(T1)
    x2, y2 = rho + b * np.cos(T2), b * np.sin(T2)
    dl1x, dl1y = -a * np.sin(T1), a * np.cos(T1)
    dl2x, dl2y = -b * np.sin(T2), b * np.cos(T2)
    R = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + d ** 2)
    integrand = (dl1x * dl2x + dl1y * dl2y) / R
    return mu0 / (4 * np.pi) * integrand.sum() * (2 * np.pi / n) ** 2

def coil_radii(r_in, r_out, N):
    return np.linspace(r_in, r_out, N)

def self_L(radii, wire_r):
    L = 0.0
    for i, a in enumerate(radii):
        for j, b in enumerate(radii):
            if i == j:
                # single loop self inductance
                L += mu0 * a * (np.log(8 * a / wire_r) - 2)
            else:
                L += m_coax(a, b, 0.0)
    return L

def mutual(r1, r2, d, rho=0.0):
    if rho == 0:
        return sum(m_coax(a, b, d) for a in r1 for b in r2)
    return sum(m_offset(a, b, d, rho, n=240) for a in r1 for b in r2)

def wheeler_spiral(N, d_out, d_in):
    # Mohan modified Wheeler, circular approx: K1=2.46? use square K1=2.34,K2=2.75 as rough
    davg = (d_out + d_in) / 2
    rho = (d_out - d_in) / (d_out + d_in)
    K1, K2 = 2.46, 3.56  # circular (Mohan et al. 1999)
    return K1 * mu0 * N ** 2 * davg / (1 + K2 * rho)

out = {}

# ---- TX: A11-like
tx_N, tx_rin, tx_rout = 10, 20.5e-3 / 2, 43e-3 / 2
tx = coil_radii(tx_rin, tx_rout, tx_N)
L_tx_air = self_L(tx, 0.4e-3)
out["TX_A11_air_L_uH"] = L_tx_air * 1e6
out["TX_wheeler_uH"] = wheeler_spiral(tx_N, 43e-3, 20.5e-3) * 1e6

# ---- RX: Wurth 760308101309 (26 mm OD). Solve turns for 10 uH incl. ferrite.
# A single-sided ferrite backing roughly multiplies L by ~1.4-1.8 for thin
# sheets. Use 1.5 as the central assumption -> air-core target 6.7 uH.
rx_rout = 13e-3
rx_rin = 4e-3
ferrite_gain = 1.5
best = None
for N in range(8, 30):
    L = self_L(coil_radii(rx_rin, rx_rout, N), 0.15e-3)
    if best is None or abs(L * ferrite_gain - 10e-6) < abs(best[1] * ferrite_gain - 10e-6):
        best = (N, L)
rx_N, L_rx_air = best
rx = coil_radii(rx_rin, rx_rout, rx_N)
out["RX_turns_solved"] = rx_N
out["RX_air_L_uH"] = L_rx_air * 1e6

# ---- Gap through the wallet.
# TX coil to pad surface: 2.5 mm (A11 typical range 2-3 mm)
# Leather (one wall of the outside pocket): 1.0-2.0 mm
# Card skin + adhesive: 0.2 mm ; coil internal (winding above ferrite): ~0.1 mm
gaps = {
    "best (2.0 + 1.0 leather + 0.3)": 3.3e-3,
    "nominal (2.5 + 1.5 leather + 0.3)": 4.3e-3,
    "worst (3.0 + 2.0 leather + 0.3)": 5.3e-3,
}
k_table = {}
for name, d in gaps.items():
    M = mutual(tx, rx, d)
    k = M / np.sqrt(L_tx_air * L_rx_air)
    row = {"gap_mm": d * 1e3, "M_nH": M * 1e9, "k_air": k}
    # lateral misalignment sweep at this gap
    for rho_mm in (5, 10):
        Mr = mutual(tx, rx, d, rho_mm * 1e-3)
        row[f"k_air_offset_{rho_mm}mm"] = Mr / np.sqrt(L_tx_air * L_rx_air)
    k_table[name] = row
out["coupling"] = k_table

# ---- Max link efficiency, series-series resonant (classic result):
# eta_max = k^2 Q1 Q2 / (1 + sqrt(1 + k^2 Q1 Q2))^2
Q1, Q2 = 80, 20   # TX coil Q (typical Qi TX 60-100) ; RX Wurth catalog Q=20
eff = {}
for name, row in k_table.items():
    for label, kmult in (("air", 1.0), ("ferrite_x1.5", 1.5)):
        k = row["k_air"] * kmult
        fom = k * k * Q1 * Q2
        eff[f"{name} / {label}"] = {"k": round(k, 3),
                                    "eta_max_coils_pct": round(100 * fom / (1 + np.sqrt(1 + fom)) ** 2, 1)}
out["link_efficiency"] = eff

# ---- Receiver tuning (WPC dual resonance, method from TI BQ5105x/BQ51003 datasheets)
fS, fD = 100e3, 1e6
w = lambda f: 2 * np.pi * f
tune = {}
for Ls_prime, Ls in ((11e-6, 10e-6), (12e-6, 10e-6)):
    C1 = 1 / (w(fS) ** 2 * Ls_prime)
    C2 = 1 / (w(fD) ** 2 * Ls - 1 / C1)
    tune[f"Ls'={Ls_prime*1e6:.0f}uH,Ls={Ls*1e6:.0f}uH"] = {"C1_nF": round(C1 * 1e9, 1), "C2_nF": round(C2 * 1e9, 2)}
# Check against TI's worked example: Ls'=16uH, Ls=11uH -> 158.3 nF, 2.34 nF
C1x = 1 / (w(fS) ** 2 * 16e-6); C2x = 1 / (w(fD) ** 2 * 11e-6 - 1 / C1x)
tune["TI_example_check(16uH,11uH)"] = {"C1_nF": round(C1x * 1e9, 1), "C2_nF": round(C2x * 1e9, 2)}
out["tuning"] = tune

json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/stdout", "w"), indent=2)
print(json.dumps(out, indent=2))
