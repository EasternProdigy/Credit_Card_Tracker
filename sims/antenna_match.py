"""Design a 2-element L-match for the in-wallet antenna (worst case: with battery,
eps_eff 1.3, arm 20 mm) using its NEC impedance across the BLE band, and report
the matched S11. Components are standard 0201 values (nearest E24-ish)."""
import numpy as np, json
from antenna_floorplan import zin, mm
L, xf, h = 20*mm, 6*mm, 6*mm
fs = np.array([2402, 2420, 2440, 2460, 2480.0])
Z = np.array([zin(L, xf, 3*mm, h, True, f*np.sqrt(1.3)) for f in fs])
w = 2*np.pi*fs*1e6
def s11_after(Ls, Cp, Z):   # series L toward antenna, then shunt C at chip side
    z1 = Z + 1j*w*Ls
    y = 1/z1 + 1j*w*Cp
    zin_ = 1/y
    return 20*np.log10(abs((zin_-50)/(zin_+50)))
best=None
for Ls in np.arange(0, 6.01, 0.1)*1e-9:
    for Cp in np.arange(0, 2.01, 0.05)*1e-12:
        s = s11_after(Ls, Cp, Z); worst = s.max()
        if best is None or worst < best[0]: best=(worst, Ls, Cp, s)
std_L=[1.0,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6]; std_C=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,1.0,1.2,1.5,1.8]
bestq=None
for Ls in std_L:
    for Cp in std_C:
        s=s11_after(Ls*1e-9,Cp*1e-12,Z); 
        if bestq is None or s.max()<bestq[0]: bestq=(s.max(),Ls,Cp,s)
out={"raw_S11_dB":[round(float(20*np.log10(abs((z-50)/(z+50)))),1) for z in Z],
     "ideal_match":{"L_series_nH":round(best[1]*1e9,2),"C_shunt_pF":round(best[2]*1e12,2),"S11_dB":[round(float(v),1) for v in best[3]]},
     "standard_values":{"L_series_nH":bestq[1],"C_shunt_pF":bestq[2],"S11_dB":[round(float(v),1) for v in bestq[3]]},
     "freqs_MHz":fs.tolist()}
print(json.dumps(out,indent=1)); json.dump(out,open("antenna_match.json","w"),indent=1)
