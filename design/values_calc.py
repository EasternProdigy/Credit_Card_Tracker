"""Recompute every calculated component value. Edit the inputs, rerun, and update
docs/03_schematic_spec.md and the decision log if anything changes.

    python3 design/values_calc.py
"""
import math

# ---- Qi tank (WPC dual resonance; method from TI BQ5105x/BQ51003 datasheets)
Ls_prime = 11e-6   # MEASURE: coil inductance on a shield, with the cell + leather in place (O10)
Ls = 10e-6         # free-space coil inductance (Wurth catalog 10 uH)
fS, fD = 100e3, 1e6
C1 = 1 / ((2 * math.pi * fS) ** 2 * Ls_prime)
C2 = 1 / ((2 * math.pi * fD) ** 2 * Ls - 1 / C1)
check1 = 1 / ((2 * math.pi * fS) ** 2 * 16e-6)                       # TI example: 158.3 nF
check2 = 1 / ((2 * math.pi * fD) ** 2 * 11e-6 - 1 / check1)            # TI example: ~2.34 nF

# ---- BQ51003 current limit
IMAX = 0.150
R_ILIM_total = 262 / IMAX          # R1 + RFOD

# ---- BQ25101 charge current
KISET = 135.0
RISET = 2050.0
ICHG = KISET / RISET
CELL_mAh = 135

# ---- NTC on TS (10k, beta 3370, internal 50 uA bias)
def v_ts(tc, beta=3370, r25=10e3, ibias=50e-6):
    return ibias * r25 * math.exp(beta * (1 / (tc + 273.15) - 1 / 298.15))

# ---- Divider
R3 = R4 = 10e6
I_div = 4.2 / (R3 + R4)

print(f"C1 = {C1*1e9:.1f} nF   C2 = {C2*1e9:.2f} nF   (TI check: {check1*1e9:.1f} nF, {check2*1e9:.2f} nF)")
built_C1 = 100e-9 + 100e-9 + 33e-9; built_C2 = 2.2e-9 + 330e-12
print(f"Built C1 = {built_C1*1e9:.0f} nF -> fS = {1/(2*math.pi*math.sqrt(Ls_prime*built_C1))/1e3:.1f} kHz (spec 90-105 kHz); built C2 = {built_C2*1e9:.2f} nF -> fD = {1/(2*math.pi*math.sqrt(Ls*(1/(1/built_C2+1/built_C1))))/1e3:.0f} kHz (spec 900-1100 kHz)")
print(f"BQ51003 R_ILIM total = {R_ILIM_total:.0f} ohm (R1 + RFOD) for IMAX {IMAX*1e3:.0f} mA")
print(f"BQ25101 ICHG = {ICHG*1e3:.1f} mA = {ICHG*1e3/CELL_mAh:.2f}C ; ITERM ~ {0.1*ICHG*1e3:.1f} mA")
print("TS voltage: " + ", ".join(f"{t} C -> {v_ts(t):.3f} V" for t in (0, 10, 25, 45, 60)))
print(f"Divider drain = {I_div*1e6:.2f} uA ; VBAT_SENSE at 4.2 V = {4.2*R4/(R3+R4):.2f} V")
