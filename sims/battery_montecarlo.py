"""
Monte Carlo battery life for the card (GRP0849049, 135 mAh), 20,000 draws per scenario.

Every input is a distribution, not a single guess:
  idle (System ON, RTC, RAM retained)   U(1.5, 3.2) uA   Nordic Academy: 3.0 uA full RAM, 0.7 none; DevZone ~3.2
  charge per 31-byte legacy adv event   N(7.5, 0.75) uC  Nordic Academy max-packet 7.47 uC at 0 dBm, 3.0 V
  events per second                     from Everytag constants (938-994 ms x multPeriod)
  +8 dBm burst                          Everytag INTERVAL_MAXPOWER=68 s for 2*multPeriod s, ~13 uC/event (est.)
  settings window                       Everytag INTERVAL_SETTINGS (60 s default), SETTINGS_WAIT 2 s,
                                        400 ms adv interval + bt_disable/enable (~50 uC est.)
  Apple key rotation                    every 600 s, bt_disable/enable ~50 uC (est.)
  LDO TPS7A02 Iq                        0.025 uA
  battery divider 10M/10M               0.21 uA (simulated)
  BQ25101 battery leakage               U(0.01, 0.05) uA (datasheet max 50 nA at 0-85 C)
  protection Iq                         U(0.3, 1.0) uA "low-Iq" or U(3, 5.5) uA "BQ2970/DW01 class"
  self-discharge                        U(1.5, 3.0) % of capacity per month
  usable capacity                       135 mAh x U(0.85, 0.95)   (cutoff ~3.3 V, some aging)
"""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

rng = np.random.default_rng(7)
N = 20000
H_PER_MONTH = 730.0

def scenario(mult_period, settings_interval, prot):
    idle = rng.uniform(1.5, 3.2, N)
    q_evt = rng.normal(7.5, 0.75, N)
    adv_interval = 0.966 * mult_period                       # mean of 938-994 ms
    ev_rate = 1 / adv_interval
    adv = q_evt * ev_rate
    burst = (2 * mult_period / adv_interval) * (13.0 - q_evt) / 68.0
    settings = (2.0 / 0.4 * q_evt + 50.0) / settings_interval
    rotation = 50.0 / 600.0
    fixed = 0.025 + 0.21 + rng.uniform(0.01, 0.05, N)
    p = rng.uniform(0.3, 1.0, N) if prot == "low" else rng.uniform(3.0, 5.5, N)
    i_avg = idle + adv + burst + settings + rotation + fixed + p          # uA
    cap = 135.0 * rng.uniform(0.85, 0.95, N)                             # mAh
    sd = rng.uniform(0.015, 0.030, N) * 135.0                            # mAh / month
    months = cap / (i_avg * 1e-3 * H_PER_MONTH + sd)
    google_gap = adv_interval * 2                                         # alternating -> each network every 2 events
    return i_avg, months, google_gap

cases = {
    "Everytag defaults (multPeriod 2, settings 60 s)": (2, 60, "low"),
    "Spec-compliant (multPeriod 1, settings 60 s)": (1, 60, "low"),
    "RECOMMENDED (multPeriod 1, settings 600 s, low-Iq protector)": (1, 600, "low"),
    "Recommended but BQ2970/DW01-class protector": (1, 600, "high"),
}
out = {}
plt.figure(figsize=(7.5, 4.3))
for name, (mp, si, pr) in cases.items():
    i, m, gap = scenario(mp, si, pr)
    p5, p50, p95 = np.percentile(m, [5, 50, 95])
    out[name] = {"avg_current_uA_median": round(float(np.median(i)), 2),
                 "months_p5": round(p5, 1), "months_median": round(p50, 1), "months_p95": round(p95, 1),
                 "each_network_every_s": round(gap, 2),
                 "meets_google_2s_rule": gap <= 2.0}
    plt.hist(m, bins=80, histtype="step", density=True, label=f"{name}\nmedian {p50:.1f} mo")
plt.xlabel("Months between charges"); plt.ylabel("probability density")
plt.title("Battery life Monte Carlo, 135 mAh card (20,000 draws each)")
plt.legend(fontsize=6.5); plt.grid(alpha=.3); plt.tight_layout()
plt.savefig("../plots/battery_life_montecarlo.png", dpi=150)
print(json.dumps(out, indent=1))
json.dump(out, open("battery_montecarlo.json", "w"), indent=1)
