"""
BQ25101 charge profile into a Grepow GRP0849049 (135 mAh, 4.20 V), NTC
thresholds on the TS pin, and charging heat in the card.

Charger behavior (TI BQ25101 datasheet SLUS??; values from our research notes):
  ICHG  = KISET / RISET, KISET = 135 A*ohm (typ)
  ITERM = 10% of ICHG (default), precharge = 2 x ITERM below VLOWV (~3.0 V)
  VREG  = 4.20 V (BQ25101), JEITA via 10k NTC on TS with internal 50 uA bias
Battery: Thevenin model, OCV(SOC) table for a typical LCO/LiPo cell,
  R0 (ohmic, incl. tabs) and one RC pair for polarization.
  Thin pouch cells have high resistance, so R0 is swept 0.3 to 1.5 ohm.
"""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

# typical LiPo OCV curve (SOC -> V), generic, from published LCO data shapes
soc_pts = np.array([0, .05, .1, .2, .3, .4, .5, .6, .7, .8, .9, .95, 1.0, 1.05])
ocv_pts = np.array([3.00, 3.45, 3.60, 3.68, 3.73, 3.77, 3.81, 3.86, 3.92, 3.99, 4.07, 4.13, 4.20, 4.32])
ocv = lambda s: np.interp(s, soc_pts, ocv_pts)

CAP_mAh = 135.0
KISET = 135.0
RISET = 2050.0
ICHG = KISET / RISET          # A
ITERM = 0.10 * ICHG
IPRE = 2 * ITERM
VREG, VLOWV = 4.20, 3.0

def simulate(R0, R1=0.25, C1=600.0, soc0=0.0, dt=1.0):
    q = soc0 * CAP_mAh * 3.6  # coulombs
    Qmax = CAP_mAh * 3.6
    v1 = 0.0; t = 0.0
    log = []
    phase = "pre"
    while t < 6 * 3600:
        s = q / Qmax
        vocv = ocv(s)
        # choose current: CC or CV limited
        if vocv + v1 < VLOWV:
            I = IPRE; phase = "pre"
        else:
            I = ICHG; phase = "cc"
            vterm = vocv + v1 + I * R0
            if vterm > VREG:
                I = max((VREG - vocv - v1) / R0, 0.0); phase = "cv"
        if phase == "cv" and I <= ITERM:
            break
        vterm = vocv + v1 + I * R0
        # update
        q += I * dt
        v1 += dt * (I / C1 - v1 / (R1 * C1))
        log.append((t, I * 1e3, vterm, s))
        t += dt
    a = np.array(log)
    return a

out = {"ICHG_mA": ICHG * 1e3, "C_rate": ICHG * 1e3 / CAP_mAh, "ITERM_mA": ITERM * 1e3}
plt.figure(figsize=(7, 4.2))
ax = plt.gca(); ax2 = ax.twinx()
for R0 in (0.3, 0.8, 1.5):
    a = simulate(R0)
    t_h = a[:, 0] / 3600
    ax.plot(t_h, a[:, 1], label=f"current, R0={R0} ohm")
    ax2.plot(t_h, a[:, 2], ls="--", label=f"voltage, R0={R0} ohm")
    out[f"R0_{R0}"] = {"charge_time_h": round(t_h[-1], 2), "final_SOC_pct": round(100 * a[-1, 3], 1)}
ax.set_xlabel("Hours on the pad (from empty)"); ax.set_ylabel("Charge current (mA)")
ax2.set_ylabel("Cell terminal voltage (V)")
ax.legend(loc="center left", fontsize=7); ax2.legend(loc="lower right", fontsize=7)
plt.title(f"BQ25101 charging 135 mAh cell, RISET={RISET/1e3:.2f}k -> {ICHG*1e3:.0f} mA")
plt.grid(alpha=.3); plt.tight_layout(); plt.savefig("../plots/charge_profile.png", dpi=150)

# ---- NTC on TS: 10k NTC beta 3370 (103AT), internal 50 uA bias -> V_TS
beta, R25 = 3370.0, 10e3
def R_ntc(Tc):
    T = Tc + 273.15
    return R25 * np.exp(beta * (1 / T - 1 / 298.15))
out["TS_voltage_at_temps_V"] = {f"{T}C": round(50e-6 * R_ntc(T), 3) for T in (0, 10, 25, 45, 60)}

# ---- Heat while charging
# Worst case: start of CC phase, VBAT = 3.0 V, BQ25101 linear drop from 5.0 V
P_charger = (5.0 - 3.0) * ICHG
P_charger_typ = (5.0 - 3.7) * ICHG
# BQ51003 (rectifier + LDO from ~6 V VRECT to 5 V) at the charger current + ~2 mA own
P_rx = (6.0 - 5.0) * (ICHG + 0.002) + 0.03   # + rectifier/FET conduction ~30 mW (estimate)
# coil copper: Irx_rms ~ 1.2x I_dc*Vbat/Vrect... use sim: ~0.12 A rms at 0.36 W, R=0.45 ohm
P_coil = 0.12 ** 2 * 0.45
P_total = P_charger + P_rx + P_coil
# Card: 85.6 x 54 mm, both faces; but one face is pressed on the pad through leather.
# Natural convection + radiation h ~ 10 W/m2K on the free face only (conservative)
A = 0.0856 * 0.054
dT_spread = P_total / (10 * A)
# Hot spot: heat confined to ~15 x 15 mm around the charger ICs before spreading through
# a 0.12 mm flex with 18 um copper: very poor spreading -> local rise estimate
out["heat"] = {"P_charger_worst_mW": round(P_charger * 1e3), "P_charger_typ_mW": round(P_charger_typ * 1e3),
               "P_receiver_mW": round(P_rx * 1e3), "P_coil_mW": round(P_coil * 1e3),
               "P_total_worst_mW": round(P_total * 1e3),
               "card_average_rise_C": round(dT_spread, 1),
               "note": "Pad heating (TX coil losses ~0.5-1.5 W in the sim) dominates; the cell sees pad heat through leather. NTC on the cell is mandatory."}
print(json.dumps(out, indent=1))
json.dump(out, open("charge_thermal.json", "w"), indent=1)
