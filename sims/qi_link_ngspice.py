"""
ngspice transient simulation of a Qi BPP link: A11-style transmitter -> card receiver.

TX : full-bridge inverter (square wave +/-Vdc) -> Cp 400 nF -> Lp 6.3 uH (A11 values)
RX : Ls 11 uH (Wurth 760308101309 with TX ferrite nearby) -> C1 series -> C2 parallel
     -> full-bridge rectifier (BQ51003 uses synchronous FETs; modeled as low-Vf diodes)
     -> Crect 10 uF -> load = charging power for a 66 mA charge
Coupling k is swept from the air-core worst case (0.25 = worst gap + 10 mm offset)
up to nominal.
A real Qi TX regulates by moving frequency (110-205 kHz) until the receiver
reports VRECT on target. We sweep frequency to see whether a target of
VRECT >= 5.5 V (enough for the BQ51003 to regulate 5.0 V out) is reachable,
and that VRECT stays under the 15 V OVP.
"""
import subprocess, re, json, itertools, os
import numpy as np

NET = """* qi link
.param Vdc={vdc} f={f} kc={k}
Vp a 0 PULSE(-{vdc} {vdc} 0 20n 20n {{0.5/{f}-20n}} {{1/{f}}})
Rsrc a a1 0.15
Cp a1 b 400n
Lp b 0 6.3u
Rlp b b0 0.0001
Ls c d 11u
K1 Lp Ls {k}
Rls c c1 0.45
C1 c1 e {c1}
C2 e d {c2}
* full bridge rectifier
D1 e vr DS
D2 d vr DS
D3 0 e DS
D4 0 d DS
Cr vr 0 10u
Bpw pw 0 V=-v(a)*i(Vp)
Rload vr 0 {rl}
.model DS D(Is=1e-6 N=1.05 Rs=0.08 Cjo=50p)
.tran 50n 1.5m 1.2m
.control
run
meas tran vrect AVG v(vr) from=1.25m to=1.5m
meas tran itx RMS i(Vp) from=1.25m to=1.5m
meas tran pin AVG v(pw) from=1.25m to=1.5m
quit
.endc
.end
"""

def run(vdc, f, k, c1=220e-9, c2=2.56e-9, rl=100.0):
    net = NET.format(vdc=vdc, f=f, k=k, c1=c1, c2=c2, rl=rl)
    p = subprocess.run(["ngspice", "-b", "/dev/stdin"], input=net, capture_output=True, text=True)
    txt = p.stdout + p.stderr
    def g(name):
        m = re.search(name + r"\s*=\s*([-\d.eE+]+)", txt)
        return float(m.group(1)) if m else float("nan")
    vr = g("vrect"); pin = g("pin")
    pout = vr * vr / rl
    return {"vrect": vr, "itx_rms": g("itx"), "pin_W": pin, "pout_W": pout,
            "eff_pct": 100 * pout / pin if pin and pin > 0 else float("nan")}

if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    results = {}
    freqs = np.arange(110e3, 206e3, 5e3)
    plt.figure(figsize=(7,4.2))
    for k in (0.20, 0.25, 0.35, 0.45):
        vr = []
        for f in freqs:
            r = run(5.0, f, k, rl=100.0)
            vr.append(r["vrect"]); results[f"k{k}_f{int(f/1e3)}"] = r
        plt.plot(freqs/1e3, vr, marker="o", ms=3, label=f"k = {k}")
    plt.axhline(5.5, ls="--", c="k", lw=1); plt.text(180, 5.7, "VRECT needed (~5.5 V)", fontsize=8)
    plt.axhline(15, ls=":", c="r", lw=1); plt.text(180, 15.3, "BQ51003 OVP 15 V", fontsize=8, color="r")
    plt.xlabel("Transmitter frequency (kHz)"); plt.ylabel("Rectified voltage on card (V)")
    plt.title("Qi link: 5 V full-bridge A11 pad, card charging at ~0.36 W")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig("../plots/qi_vrect_vs_freq.png", dpi=150)
    # operating point: lowest-power freq meeting 5.8 V (TX controller target band)
    ops = {}
    for k in (0.20, 0.25, 0.35, 0.45):
        cands = [(f, results[f"k{k}_f{int(f/1e3)}"]) for f in freqs if results[f"k{k}_f{int(f/1e3)}"]["vrect"] >= 5.8]
        if cands:
            f, r = max(cands, key=lambda x: x[0])
            ops[str(k)] = {"f_kHz": f/1e3, "vrect": round(r["vrect"],2), "pout_mW": round(r["pout_W"]*1e3), "pin_mW": round(r["pin_W"]*1e3), "eff_pct": round(r["eff_pct"],1), "itx_rms_A": round(r["itx_rms"],3)}
        else:
            ops[str(k)] = "cannot reach 5.8 V in 110-205 kHz"
    print(json.dumps(ops, indent=1))
    json.dump({"operating_points": ops, "sweep": results}, open("qi_link_results.json","w"), indent=1)
