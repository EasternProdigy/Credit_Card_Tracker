"""Voltage/current stress on C1 (series) and C2 (parallel) across every Qi operating
point the transmitter could sit at (VRECT <= 15 V OVP). Sizes the voltage rating."""
import subprocess, re, tempfile, os, itertools, json
NET = """* qi c1 stress
Vp a 0 PULSE(-{vdc} {vdc} 0 20n 20n {{0.5/{f}-20n}} {{1/{f}}})
Rsrc a a1 0.15
Cp a1 b 400n
Lp b 0 6.3u
Ls c d 11u
K1 Lp Ls {k}
Vsen c cs 0
Rls cs c1 0.45
C1 c1 e 230n
C2 e d 2.56n
D1 e vr DS
D2 d vr DS
D3 0 e DS
D4 0 d DS
Cr vr 0 10u
Rload vr 0 {rl}
Bv1 v1 0 V=v(c1)-v(e)
Bv2 v2 0 V=v(e)-v(d)
.model DS D(Is=1e-6 N=1.05 Rs=0.08 Cjo=50p)
.tran 50n 1.5m 1.2m
.control
run
meas tran vc1 MAX v(v1) from=1.25m to=1.5m
meas tran ic1 RMS i(Vsen) from=1.25m to=1.5m
meas tran vc2 MAX v(v2) from=1.25m to=1.5m
meas tran vrect AVG v(vr) from=1.25m to=1.5m
quit
.endc
.end
"""
rows = []
for k, f, rl, vdc in itertools.product([0.25, 0.35, 0.45, 0.55], [110e3, 120e3, 130e3, 150e3, 175e3], [100, 1000], [5.0, 9.5]):
    fd = tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False); fd.write(NET.format(k=k, f=f, rl=rl, vdc=vdc)); fd.close()
    out = subprocess.run(["ngspice", "-b", fd.name], capture_output=True, text=True, timeout=60).stdout; os.unlink(fd.name)
    g = lambda n: float(re.search(n + r"\s*=\s*([-\d.eE+]+)", out).group(1))
    rows.append(dict(k=k, f_kHz=f / 1e3, rl=rl, vdc=vdc, vrect=g("vrect"), vc1_pk=g("vc1"), ic_rms=g("ic1"), vc2_pk=g("vc2")))
ok = [r for r in rows if r["vrect"] <= 15.5]
res = {
  "cases_within_OVP": f"{len(ok)} of {len(rows)}",
  "worst_C1_peak_V": max(ok, key=lambda r: r["vc1_pk"]),
  "worst_C2_peak_V": max(ok, key=lambda r: r["vc2_pk"]),
  "worst_coil_I_rms": max(ok, key=lambda r: r["ic_rms"]),
  "charging_points (RL 100, VRECT 5-8 V)": {
      "C1_peak_V_max": max(r["vc1_pk"] for r in ok if r["rl"] == 100 and 5 <= r["vrect"] <= 8),
      "I_rms_max": max(r["ic_rms"] for r in ok if r["rl"] == 100 and 5 <= r["vrect"] <= 8)},
}
print(json.dumps(res, indent=1)); json.dump(res, open("c1_stress.json", "w"), indent=1)
