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
# rev 0.6: E96 values. R1 = 1.50k (1.55k is not E96), RFOD = 200R (TI uses 196R). SLUSBC8C eq. 2.
R1_v, RFOD_v = 1500, 200
print(f"BQ51003 chosen R1 {R1_v} + RFOD {RFOD_v} = {R1_v+RFOD_v} ohm -> IMAX {262/(R1_v+RFOD_v)*1e3:.0f} mA, ILIM {314/(R1_v+RFOD_v)*1e3:.0f} mA")
print(f"BQ25101 ICHG = {ICHG*1e3:.1f} mA = {ICHG*1e3/CELL_mAh:.2f}C ; ITERM ~ {0.1*ICHG*1e3:.1f} mA")
print("TS voltage: " + ", ".join(f"{t} C -> {v_ts(t):.3f} V" for t in (0, 10, 25, 45, 60)))
print(f"Divider drain = {I_div*1e6:.2f} uA ; VBAT_SENSE at 4.2 V = {4.2*R4/(R3+R4):.2f} V")

# ---- v1 dev I/O (2026-11-14 afternoon)
# LEDs: GPIO high (standard drive, nRF54L15 datasheet v1.0 p.899: IOH,SD >= 1 mA at VDD-0.4 V) -> R -> LED -> GND.
# KT-0603R red Vf 1.8-2.4 V @ 20 mA (LCSC C2286); NCD0603Y2 yellow Vf 1.6-2.6 V @ 25 mA (LCSC C89811). At ~1-2 mA Vf ~1.7-1.8 V.
VDD, R_LED, VF_LO, VF_HI = 3.3, 1000, 1.7, 2.0
I_LED_max, I_LED_min = (VDD - VF_LO) / R_LED, (VDD - 0.4 - VF_HI) / R_LED
print(f"LED: R {R_LED} ohm -> {I_LED_min*1e3:.2f} to {I_LED_max*1e3:.2f} mA (GPIO standard drive, IOH,SD min 1 mA at VDD-0.4)")
# UART series resistors: back-feed into an unpowered nRF or cable through ESD diodes, and bit-time margin.
R_UART, C_PIN = 4700, 10e-12
print(f"UART: R {R_UART} ohm -> back-feed {(VDD-0.6)/R_UART*1e3:.2f} mA max; RC {R_UART*C_PIN*1e9:.0f} ns vs 1000 ns bit at 1 Mbaud, 8680 ns at 115200")
# Buttons: internal pull-up RPU 12-16 kOhm (p.899) -> press current
print(f"Button: press current {VDD/12e3*1e6:.0f} uA max (RPU 12-16 k, datasheet p.899); only while held")
