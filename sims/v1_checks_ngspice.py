"""
v1 bring-up board checks in ngspice (libngspice, the engine KiCad's simulator uses).
Values are read from hardware/v1/gen/design.py so the sim tracks the schematic.

1. Power path, v1: EFC4615R (44 mOhm max at VGS 3.1 V, design/pinmaps/EFC4615R.md) + JP3 0R (50 mOhm max),
   LDO out C15 4.7 uF, JP4 0R, then the Nordic QFN48 config-1 VDD set: C17 10 uF + 4 x 100 nF.
   (The rev 0.4 sim put 2 x 2.2 uF on VDD; Nordic's Fig. 180 puts them on DECD/DECA.)
   Two cap cases: nominal, and DC-bias derated at 3.3 V (0402 10 uF 6.3 V -55 %, 0402 4.7 uF 10 V -45 %).
2. Qi tank with the v1 0603 parts: series fs and parallel fd from an AC sweep, against WPC v1.2
   (fs 100 kHz +5/-10 %, fd 1.0 MHz +/-10 %), with Ls' = 11 uH as in sims/c1_stress.py and 10 uH nominal.
3. Battery divider sample (R3/R4, C16) as in power_path_ngspice.py.
Run from sims/:  python3 v1_checks_ngspice.py   (needs ngspice on PATH; ngspice_shim.py works)
"""
import json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hardware', 'v1', 'gen'))
import design as D

def spice(net):
    f = tempfile.NamedTemporaryFile('w', suffix='.cir', delete=False); f.write(net); f.close()
    p = subprocess.run(['ngspice', '-b', f.name], capture_output=True, text=True, timeout=300); os.unlink(f.name)
    return p.stdout

def val(ref):
    v = next(c for c in D.C if c['ref'] == ref)['value'].split()[0]
    m = re.match(r'([\d.]+)(p|n|u)?(F|H)?', v)
    return float(m.group(1)) * {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, None: 1}[m.group(2)]

fitted = lambda refs: sum(val(r) for r in refs if not next(c for c in D.C if c['ref'] == r)['dnp'])
res = {}

# ---- 1. power path
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'power_path_ngspice.py')).read()
NET = re.search(r'NET = """(.*?)"""', src, re.S).group(1)
pwl_src = re.search(r'(def load_pwl\(\):.*?return .*?\n)', src, re.S).group(1)
exec(pwl_src)
NET = NET.replace('Rfet bat batp 0.1', 'Rfet bat batp {rser}')
NET = re.sub(r'Cout vdd 0 4.7u\nCn1 vdd 0 10u\nCn2 vdd 0 2.2u\nCn3 vdd 0 2.2u\nIload vdd 0',
             'Cout vdd 0 {c15}\nRjp4 vdd vn 0.05\nCn1 vn 0 {c17}\nCn2 vn 0 100n\nCn3 vn 0 100n\nCn4 vn 0 100n\nCn5 vn 0 100n\nIload vn 0', NET)
NET = NET.replace('MIN v(vdd)', 'MIN v(vn)').replace('MAX v(vdd)', 'MAX v(vn)').replace('wrdata {out} v(vdd) v(batp)\n', '')
NET = NET.replace('.ic v(vdd)={vdd0}', '.ic v(vdd)={vdd0} v(vn)={vdd0}')
assert 'Iload vn 0' in NET
cases = [("full, warm (4.20 V, R0 0.3)", 4.20, 0.3), ("near dropout (3.40 V, R0 0.8)", 3.40, 0.8),
         ("empty (3.30 V, R0 1.0)", 3.30, 1.0), ("empty + cold/aged (3.30 V, R0 4.0)", 3.30, 4.0)]
rser = 0.044 + 0.05
pp = {}
for capcase, c15, c17 in (('nominal', val('C15'), val('C17')), ('dc_bias_derated', val('C15') * 0.55, val('C17') * 0.45)):
    for name, vocv, r0 in cases:
        vdd0 = min(3.3, vocv - 0.001)
        out = spice(NET.format(vocv=vocv, r0=r0, vref=3.3, pwl=load_pwl(), vdd0=vdd0, out='x', rser=rser,
                               c15=c15, c17=c17))
        g = lambda n: float(re.search(n + r"\s*=\s*([-\d.eE+]+)", out).group(1))
        pp[f'{capcase} | {name}'] = {'vdd_nrf_min': round(g('vmin'), 3), 'droop_mV': round((vdd0 - g('vmin')) * 1e3, 1),
                                     'margin_over_1.7V': round(g('vmin') - 1.7, 3)}
res['power_path_v1'] = pp

# ---- 2. Qi tank
C1 = fitted(['C1a', 'C1b', 'C1c', 'C1d']); C2 = fitted(['C2a', 'C2b', 'C2c'])
qi = {'C1_nF': round(C1 * 1e9, 1), 'C2_nF': round(C2 * 1e9, 3)}
for ls in (10e-6, 11e-6):
    net = f"""* series tank: coil + C1, then C2 across the rectifier input (rectifier off)
Vs a 0 AC 1
Ls a b {ls}
Rl b c 0.25
C1 c d {C1}
Rd d 0 1m
.ac dec 400 30k 3Meg
.control
run
meas ac fs WHEN vp(d)=0 FALL=1
quit
.endc
.end
"""
    out = spice(net)
    m = re.search(r'^fs\s*=\s*([-\d.eE+]+)', out, re.M)
    fs = float(m.group(1)) if m else None
    net2 = f"""* parallel detection: coil || C2 with C1 in series (WPC fd = 1/(2pi sqrt(Ls' (1/C1+1/C2)^-1)))
Is 0 a AC 1
Ls a b {ls}
Rl b 0 0.25
C1 a c {C1}
C2 c 0 {C2}
.ac dec 400 200k 5Meg
.control
run
meas ac fd WHEN vp(a)=0 FALL=1
quit
.endc
.end
"""
    out2 = spice(net2)
    m2 = re.search(r'^fd\s*=\s*([-\d.eE+]+)', out2, re.M)
    fd = float(m2.group(1)) if m2 else None
    qi[f"Ls={ls*1e6:.0f}uH"] = {'fs_kHz': round(fs / 1e3, 1) if fs else None, 'fd_MHz': round(fd / 1e6, 3) if fd else None,
                                'fs_in_WPC_90_105kHz': bool(fs and 90e3 <= fs <= 105e3),
                                'fd_in_WPC_0.9_1.1MHz': bool(fd and 0.9e6 <= fd <= 1.1e6)}
st = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'c1_stress.json')))['worst_C1_peak_V']
qi['stress_from_c1_stress.json'] = {'vc1_pk_V': st['vc1_pk'], 'vc2_pk_V': st['vc2_pk'], 'ic_rms_A': st['ic_rms'],
                                    'C1_rating_V': 50, 'C2_rating_V': 50, 'per_C1_part_rms_A': round(st['ic_rms'] * 100 / 233, 3)}
res['qi_tank_v1'] = qi

# ---- 3. divider
R3, R4, C16 = 10e6, 10e6, 100e-9
out = spice(f"""* divider + SAADC sample (4 pF, 40 us)
Vb vb 0 4.2
Rt vb mid {R3}
Rb mid 0 {R4}
Cf mid 0 {C16}
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
""")
vs = float(re.search(r"vs\s*=\s*([-\d.eE+]+)", out).group(1))
res['divider_v1'] = {'sampled_V': round(vs, 5), 'error_mV': round((2.1 - vs) * 1e3, 3), 'always_on_uA': round(4.2 / (R3 + R4) * 1e6, 3)}
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'v1_checks.json'), 'w'), indent=1)
