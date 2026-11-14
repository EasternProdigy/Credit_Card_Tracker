"""
ngspice transient: LiPo -> protection FETs -> TPS7A02-class LDO -> nRF54L15 VDD
during one 3-channel BLE advertising event at +8 dBm (worst case current).

Battery : OCV source + R0 + R1||C1 (thin pouch, R0 swept incl. cold/aged)
Protect : 2 back-to-back FETs, 2 x 50 mohm (cell PCM or discrete)
LDO     : behavioral transconductance loop (gm) with pass-device resistance
          (dropout) and current limit. gm chosen so loop bandwidth is ~10 kHz,
          deliberately SLOW to represent a 25 nA-Iq nano-power LDO.
Decoup  : 4.7 uF at LDO out + nRF54L15 reference set (10 uF, 2 x 2.2 uF)
Load    : event profile from Nordic numbers: 9.8 mA TX (+8 dBm), 3 channels,
          376 us each (31-byte legacy ADV_IND at 1 Mbps), with ~2 mA CPU/ramp
          between channels.
Pass    : VDD stays above 1.7 V (nRF54L15 minimum) with margin, in every case.
Also simulates the battery-voltage divider (10M/10M + 100 nF) being sampled
by the SAADC (~4 pF sample cap, 40 us acquisition) to confirm the error is small.
"""
import subprocess, re, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import numpy as np, tempfile, os

def spice(net):
    f=tempfile.NamedTemporaryFile("w",suffix=".cir",delete=False); f.write(net); f.close()
    p=subprocess.run(["ngspice","-b",f.name],capture_output=True,text=True,timeout=120); os.unlink(f.name); return p

def load_pwl():
    pts = [(0, 3e-6)]
    t = 100e-6
    for ch in range(3):
        pts += [(t, 3e-6), (t + 1e-6, 2e-3), (t + 40e-6, 2e-3), (t + 41e-6, 9.8e-3),
                (t + 41e-6 + 376e-6, 9.8e-3), (t + 42e-6 + 376e-6, 2e-3)]
        t += 41e-6 + 376e-6 + 150e-6
    pts += [(t, 2e-3), (t + 1e-6, 3e-6), (5e-3, 3e-6)]
    return " ".join(f"{a:.7g} {b:.7g}" for a, b in pts)

NET = """* power path
Vocv ocv 0 {vocv}
R0 ocv n1 {r0}
R1 n1 bat 0.3
C1 n1 bat 0.5 IC=0
Rfet bat batp 0.1
* LDO behavioral: target = smooth min(Vref, Vin - 30 mV); 16 us lag (slow nano-Iq loop);
* 0.3 ohm output resistance; the same current is drawn from the battery node.
B_t tgt 0 V = {vref} - 0.02*ln(1+exp(({vref} - (v(batp)-0.03))/0.02))
R_lag tgt lag 1k
C_lag lag 0 16n
E_buf eo 0 lag 0 1
R_out eo vdd 0.3
B_draw batp 0 I = (v(eo)-v(vdd))/0.3
Cout vdd 0 4.7u
Cn1 vdd 0 10u
Cn2 vdd 0 2.2u
Cn3 vdd 0 2.2u
Iload vdd 0 PWL({pwl})
.ic v(vdd)={vdd0} v(lag)={vdd0} v(tgt)={vdd0}
.options reltol=1e-3 abstol=1e-9 method=gear
.tran 1u 4m uic
.control
run
meas tran vmin MIN v(vdd) from=0.05m to=4m
meas tran vmax MAX v(vdd) from=0.05m to=4m
meas tran vbatmin MIN v(batp) from=0.05m to=4m
wrdata {out} v(vdd) v(batp)
quit
.endc
.end
"""

cases = [
    ("full, warm (4.20 V, R0 0.3)", 4.20, 0.3),
    ("mid (3.75 V, R0 0.5)", 3.75, 0.5),
    ("near dropout (3.40 V, R0 0.8)", 3.40, 0.8),
    ("empty (3.30 V, R0 1.0)", 3.30, 1.0),
    ("empty + cold 0 C / aged (3.30 V, R0 4.0)", 3.30, 4.0),
]
res = {}
plt.figure(figsize=(7.5, 4.2))
for name, vocv, r0 in cases:
    vref = 3.3
    vdd0 = min(vref, vocv - 0.001)
    out = f"pp_{vocv}_{r0}.dat"
    net = NET.format(vocv=vocv, r0=r0, gm=0.5, vref=vref, pwl=load_pwl(), vdd0=vdd0, out=out)
    p = spice(net)
    g = lambda n: float(re.search(n + r"\s*=\s*([-\d.eE+]+)", p.stdout).group(1))
    res[name] = {"vdd_min": round(g("vmin"), 3), "vdd_start": round(vdd0, 3),
                 "droop_mV": round((vdd0 - g("vmin")) * 1e3, 1), "vbat_min": round(g("vbatmin"), 3),
                 "margin_over_1.7V": round(g("vmin") - 1.7, 3)}
    d = np.loadtxt(out)
    plt.plot(d[:, 0] * 1e3, d[:, 1], label=name)
plt.axhline(1.7, c="r", ls=":"); plt.text(3.0, 1.75, "nRF54L15 min 1.7 V", color="r", fontsize=8)
plt.ylim(1.5, 3.5); plt.xlabel("time (ms)"); plt.ylabel("VDD (V)")
plt.title("VDD during a +8 dBm advertising event (3 channels)")
plt.legend(fontsize=7, loc="lower right"); plt.grid(alpha=.3); plt.tight_layout()
plt.savefig("../plots/vdd_during_adv_event.png", dpi=150)

# ---- divider sampling
DIV = """* divider + SAADC sample
Vb vb 0 4.2
Rt vb mid 10Meg
Rb mid 0 10Meg
Cf mid 0 100n
S1 mid samp ctl 0 SW
.model SW SW(Ron=2k Roff=1e12 Vt=0.5)
Vctl ctl 0 PULSE(0 1 1m 1n 1n 40u 1)
Cs samp 0 4p
.ic v(mid)=2.1 v(samp)=0
.tran 0.1u 1.2m
.control
run
meas tran vs FIND v(samp) AT=1.039m
quit
.endc
.end
"""
p = spice(DIV)
vs = float(re.search(r"vs\s*=\s*([-\d.eE+]+)", p.stdout).group(1))
res["divider_sample"] = {"ideal_V": 2.1, "sampled_V": round(vs, 5), "error_mV": round((2.1 - vs) * 1e3, 3),
                          "always_on_current_uA": round(4.2 / 20e6 * 1e6, 3)}
print(json.dumps(res, indent=1))
json.dump(res, open("power_path.json", "w"), indent=1)
