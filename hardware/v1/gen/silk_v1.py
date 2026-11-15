#!/usr/bin/env python3
"""Card Test 1 silkscreen: board name, section/jumper/test-pad labels, and the back-side reference sheet.
Works on the routed board in place and never touches copper. Every item it adds lives in the PCB group
'card_test_silk'; a rerun deletes that group first. It also replaces the small labels gen_pcb.py makes
(UART pins, BTN/LED/SWD/RESET/PPK, cell '+') so all legend text follows one rule set.

Legend rules, JLCPCB capabilities page (Legend table, read 2026-11-15): text height >= 1.0 mm ("less than
1.0 mm will be unidentifiable"), stroke >= 0.15 mm, preferred stroke:height 1:6, pad to silkscreen
>= 0.15 mm. Here: text >= 1.0 mm high, stroke >= 0.17 mm, 0.2 mm kept from every pad, judged on the real
ink outline (not KiCad's text box, which is ~1.8x the letter height). Each label tries candidate spots and
takes the first that clears pads, other parts' bodies, other silk, the frame and the board edge.
Run from hardware/v1:  python3 gen/silk_v1.py [-v]"""
import math, sys, pcbnew

PCB = 'card_v1.kicad_pcb'
GROUP = 'card_test_silk'
LEGACY = {'GND', 'CTS', 'NC', 'TXD', 'RXD', 'RTS', 'UART 3V3', 'BTN0', 'BTN1', 'LED0', 'LED1', 'SWD', '+',
          'PPK BAT', 'PPK 3V3', 'RESET'}                 # gen_pcb.py's 0.8 mm labels, replaced below
b = pcbnew.LoadBoard(PCB)
F, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(F(x), F(y))
FS, BS = pcbnew.F_SilkS, pcbnew.B_SilkS
X0, Y0, X1, Y1 = 100.0, 100.0, 185.6, 153.98          # board edge
EDGE = 0.6
H, HW, HT = 1.0, 0.8, 0.17                             # body text: height, glyph width, stroke
HH, HHW, HHT = 1.2, 0.95, 0.2                          # headers

# DRC enforces the same minimums through card_v1.kicad_dru (rules jlc_legend_front / jlc_legend_back).

# ---------------------------------------------------------------- remove the previous run + legacy labels
GRAVE = []                                             # removed items must stay referenced, or SWIG frees them
for g in list(b.Groups()):                             # under KiCad and later calls see garbage
    if g.GetName() == GROUP:
        for it in list(g.GetItems()):
            GRAVE.append(it); b.Remove(it)
        GRAVE.append(g); b.Remove(g)
OLD = {}
for d in list(b.GetDrawings()):
    if d.GetClass() == 'PCB_TEXT' and d.GetLayer() == FS and d.GetText() in LEGACY:
        OLD.setdefault(d.GetText(), []).append((round(M(d.GetX()), 2), round(M(d.GetY()), 2)))
        GRAVE.append(d); b.Remove(d)
grp = pcbnew.PCB_GROUP(b); grp.SetName(GROUP); b.Add(grp)

# ---------------------------------------------------------------- obstacles per side
def box(bb, infl=0.0):
    return (M(bb.GetLeft()) - infl, M(bb.GetTop()) - infl, M(bb.GetRight()) + infl, M(bb.GetBottom()) + infl)

def ink(item, layer):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, 0, F(0.005), pcbnew.ERROR_OUTSIDE)
    return box(ps.BBox())

OBST = {FS: [], BS: []}
for fp in b.GetFootprints():
    ref = fp.GetReference()
    for p in fp.Pads():
        ls = p.GetLayerSet()
        for cu, sk in ((pcbnew.F_Cu, FS), (pcbnew.B_Cu, BS)):
            if ls.Contains(cu): OBST[sk].append(('pad ' + ref, box(p.GetBoundingBox(), 0.2)))
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    if cy.OutlineCount() and ref != 'L1':              # L1 is round: the COIL check below covers it
        OBST[FS].append(('body ' + ref, box(cy.BBox(), 0.05)))
    for g in fp.GraphicalItems():
        if ref == 'L1' and g.GetLayer() == FS: continue
        if g.GetLayer() in (FS, BS) and (g.GetClass() != 'PCB_TEXT' or g.IsVisible()):
            OBST[g.GetLayer()].append(('silk ' + ref, box(g.GetBoundingBox(), 0.1)))
for d in b.GetDrawings():
    if d.GetLayer() in (FS, BS):
        OBST[d.GetLayer()].append(('silk board', box(d.GetBoundingBox(), 0.1)))
ANT = None
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetDoNotAllowTracks() and M(z.GetBoundingBox().GetTop()) > 140:
        ANT = box(z.GetBoundingBox())
        OBST[FS].append(('area antenna', box(z.GetBoundingBox(), 0.2)))   # no ink on the radiator side

COIL = (168.05, 115.0, 13.6)                            # L1 body on the front: D26.3 coil + margin
def hit(bx, layer, ignore=()):
    l, t, r, btm = bx
    if l < X0 + EDGE or t < Y0 + EDGE or r > X1 - EDGE or btm > Y1 - EDGE:
        return 'edge'
    if layer == FS:
        cx, cy, cr = COIL
        nx, ny = min(max(cx, l), r), min(max(cy, t), btm)
        if math.hypot(nx - cx, ny - cy) < cr: return 'coil L1'
    for name, (a, c, e, f) in OBST[layer]:
        if not name.startswith('pad') and any(name.endswith(' ' + i) for i in ignore): continue  # never ignore copper
        if l < e and r > a and t < f and btm > c:
            return name
    return None

def keep(item, layer, bx):
    b.Add(item); grp.AddItem(item); OBST[layer].append(('silk new', (bx[0] - 0.1, bx[1] - 0.1, bx[2] + 0.1, bx[3] + 0.1)))
    return item

# ---------------------------------------------------------------- primitives
FAIL, DBG = [], {}
def text(s, cands, layer=FS, h=H, w=HW, t=HT, ignore=(), bold=False):
    """cands: (x, y, justify 'L'/'C'/'R', angle). First clear spot wins. On the back, text is mirrored and
    a left-justified anchor grows toward -x in board coordinates."""
    tried = []
    for (x, y, j, ang) in cands:
        tx = pcbnew.PCB_TEXT(b); tx.SetText(s); tx.SetLayer(layer)
        tx.SetTextSize(V(w, h)); tx.SetTextThickness(F(t)); tx.SetBold(bold)
        tx.SetHorizJustify({'L': pcbnew.GR_TEXT_H_ALIGN_LEFT, 'C': pcbnew.GR_TEXT_H_ALIGN_CENTER,
                            'R': pcbnew.GR_TEXT_H_ALIGN_RIGHT}[j])
        tx.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        if layer == BS: tx.SetMirrored(True)
        tx.SetTextAngleDegrees(ang); tx.SetPosition(V(x, y))
        bx = ink(tx, layer)
        why = hit(bx, layer, ignore); tried.append(((round(x, 2), round(y, 2), ang), why))
        if why is None:
            return keep(tx, layer, bx)
    FAIL.append((s, why)); DBG[s] = tried
    return None

def seg(x1, y1, x2, y2, layer, w=0.15, check=True, obstacle=False):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(F(w))
    s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2))
    bx = box(s.GetBoundingBox())
    if check:
        why = hit(bx, layer)
        if why: FAIL.append((f'segment {x1:.1f},{y1:.1f}', why)); return None
    b.Add(s); grp.AddItem(s)
    if obstacle: OBST[layer].append(('frame', (bx[0] - 0.1, bx[1] - 0.1, bx[2] + 0.1, bx[3] + 0.1)))
    return s

def poly_line(pts, layer, w=0.15, check=True, obstacle=False):
    for (a, c), (e, f) in zip(pts, pts[1:]):
        seg(a, c, e, f, layer, w, check, obstacle)

def arc_pts(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def around(ref, gap=0.9):
    fp = b.FindFootprintByReference(ref); l, t, r, bt = box(fp.GetCourtyard(pcbnew.F_CrtYd).BBox())
    cx, cy = (l + r) / 2, (t + bt) / 2; out = []
    for d in (gap, gap + 0.8, gap + 1.6):
        out += [(cx, t - d, 'C', 0), (cx, bt + d, 'C', 0), (r + d - 0.5, cy, 'L', 0), (l - d + 0.5, cy, 'R', 0)]
    return out

def stack(lines, xr, y, ymax):
    """Back-side text block, anchored at its right edge xr (reads left-aligned when flipped)."""
    prev = None
    for s, h in lines:
        if s is None: y += h; continue
        if prev is not None: y += prev * 0.8 + h * 0.8 + 0.25     # ink incl. parentheses, descenders ~1.6 h
        if y + h * 0.8 > ymax: FAIL.append((s, f'overflow at y {y:.1f}')); continue
        hdr = h > 1.05
        text(s, [(xr, y, 'L', 0)], layer=BS, h=h, w=h * (0.79 if hdr else 0.8), t=HHT if hdr else HT)
        prev = h

# ---------------------------------------------------------------- frame on both sides (first, so text avoids it)
def frame(layer, inset=0.8, r=2.4):
    l, t, rr, bt = X0 + inset, Y0 + inset, X1 - inset, Y1 - inset
    pts = (arc_pts(l + r, t + r, r, 180, 270, 6) + arc_pts(rr - r, t + r, r, 270, 360, 6) +
           arc_pts(rr - r, bt - r, r, 0, 90, 6) + arc_pts(l + r, bt - r, r, 90, 180, 6))
    poly_line(pts + [pts[0]], layer, 0.15, check=False, obstacle=True)
frame(FS); frame(BS)

# ================================================================ FRONT
# Title block, bottom-left corner: map pin + radio waves icon.
TX, TY = 102.9, 147.6
icon = arc_pts(TX, TY - 0.6, 1.1, 180, 360, 16)
poly_line(icon + [(TX, TY + 2.0), icon[0]], FS, 0.2)
poly_line(arc_pts(TX, TY - 0.6, 0.35, 0, 360, 12), FS, 0.15)
for r in (1.9, 2.6):
    poly_line(arc_pts(TX, TY - 0.6, r, -50, 50, 10), FS, 0.15)
text('CARD TEST 1', [(106.3, 144.9, 'L', 0)], h=2.0, w=1.5, t=0.3, bold=True)
text('WALLET TRACKER v1', [(106.3, 147.6, 'L', 0)], h=HH, w=0.85, t=HHT)
text('DEV / BRING-UP BOARD', [(106.3, 149.6, 'L', 0)], h=HH, w=0.8, t=HHT)
text('2026-11-15 - guide on back', [(106.3, 151.55, 'L', 0)], w=0.7)

# Replacements for gen_pcb.py's 0.8 mm labels (positions from gen_pcb.py, hardcoded so reruns keep them).
# UART pins are named from the board's side (RXI = into the nRF, TXO = out of it) so a generic USB-UART
# dongle can't be miswired; the three unused FTDI pins say nc.
for new, y in (('GND', 113.98), ('nc', 116.52), ('nc', 119.06), ('RXI', 121.6), ('TXO', 124.14), ('nc', 126.68)):
    text(new, [(102.5, y, 'C', 0), (102.3, y, 'C', 0)], w=0.75)
for s_, cands in (('UART 3V3', [(106.0, 111.58, 'C', 0), (106.0, 111.3, 'C', 0)]),
                  ('BTN0', [(109.0, 136.38, 'C', 0), (109.0, 136.1, 'C', 0)]),
                  ('BTN1', [(117.0, 136.38, 'C', 0), (117.0, 136.1, 'C', 0)]),
                  ('LED0', [(119.6, 127.98, 'C', 0), (119.9, 127.98, 'C', 0)]),
                  ('LED1', [(119.6, 130.48, 'C', 0), (119.9, 130.48, 'C', 0)]),
                  ('SWD', [(137.5, 122.7, 'C', 0), (132.4, 127.0, 'C', 0), (132.4, 126.2, 'C', 0)]),
                  ('RESET', [(133.4, 136.0, 'R', 0), (133.4, 134.6, 'R', 0), (133.4, 137.4, 'R', 0)]),
                  ('PPK2 BAT', [(136.5, 116.98, 'C', 0), (136.8, 116.98, 'C', 0)]),
                  ('PPK2 3V3', [(136.5, 140.98, 'C', 0), (136.8, 140.98, 'C', 0)])):
    text(s_, cands, w=0.75 if s_.startswith(('LED', 'BTN')) else 0.8)
# Cell polarity: '+' beside BT1's VCELL tab and right under J1 pin 1 (visible with the plug fitted).
text('+', [(133.9, 106.48, 'C', 0), (133.8, 105.0, 'C', 0)], h=1.2, w=1.2, t=0.2, ignore=('BT1',))
text('+', [(147.0, 110.6, 'C', 0), (147.0, 110.8, 'C', 0)], h=1.2, w=1.2, t=0.2, ignore=('J1',))

# Test-pad legend: one line per grid row, left of the pads, names in pad order (left to right).
ROWS = [(107.98, 'V5_CHG VCHG nCHG'), (110.78, 'NTC VCELL BAT-'), (113.58, 'VBAT PS DO_GATE'),
        (116.38, 'CO_GATE 3V3 VDD_NRF'), (119.18, 'VBAT_SNS SWDIO SWDCLK'), (121.98, 'nRESET GND GND'),
        (124.78, 'GND TX RX')]
for y, s in ROWS:
    text(s, [(123.6, y, 'R', 0)], w=0.7)
# Row 8 has two pads and D1 sits to its left: label each pad on its own side.
text('P1.06', [(123.85, 127.58, 'R', 0), (125.0, 128.95, 'C', 0), (125.0, 129.1, 'C', 0)], w=0.7, ignore=('TP28',))
text('SWO', [(128.6, 127.58, 'L', 0), (128.8, 127.58, 'L', 0)], w=0.7)
text('TEST PADS, left to right', [(123.6, 105.45, 'R', 0), (127.0, 105.3, 'C', 0)], h=HH, w=0.85, t=HHT)

# Qi test pads (TP3 TP4 TP1 TP2 TP5), pitch 2.15 mm: labels alternate above and below so 1.0 mm text fits.
# The lower ones reach 0.15 mm into the antenna keep-out, 6 mm from the radiator arm; silk ink there is harmless.
for name, x, up in (('AC1', 172.2, 1), ('AC2', 174.35, 0), ('VRECT', 176.5, 1), ('V5', 178.65, 0), ('RXCHG', 180.8, 1)):
    y = 140.55 if up else 143.3
    text(name, [(x, y, 'C', 0), (x, y + (0.1 if up else 0.15), 'C', 0)], w=0.7,
         ignore=('TP1', 'TP2', 'TP3', 'TP4', 'TP5', 'antenna', 'AE1'))

# Jumpers: name + what the 0R links. Remove one to isolate a stage.
JP = [('JP1', 'QI>CHG', 182.3, 134.78), ('JP2', 'CHG>CELL', 151.0, 132.98),
      ('JP3', 'CELL>BRD', 143.5, 119.98), ('JP4', 'LDO>nRF', 143.5, 143.98),
      ('JP5', 'SNS', 153.3, 142.18), ('JP6', 'nCHG', 153.3, 140.08)]
for ref, what, x, y in JP:
    c = [(x, y - 1.5, 'C', 0), (x, y + 1.5, 'C', 0), (x + 1.4, y, 'L', 0), (x - 1.4, y, 'R', 0),
         (x + 1.5, y, 'C', 90), (x - 1.5, y, 'C', 90), (x, y - 2.4, 'C', 0), (x, y + 2.4, 'C', 0),
         (x + 2.3, y, 'L', 0), (x - 2.3, y, 'R', 0), (x + 2.3, y, 'C', 90), (x - 2.3, y, 'C', 90)]
    if ref in ('JP2', 'JP5', 'JP6'):
        c = [k for k in c if k[3] == 90] + [k for k in c if k[3] != 90]
    if not text(f'{ref} {what}', c, w=0.72, ignore=(ref,)):
        FAIL.pop(); text(ref, c, w=0.72, ignore=(ref,))

# Section labels.
for s, ref, extra in [('Qi RX', 'U1', []), ('CHARGER', 'U2', []), ('PROTECT', 'U3', []), ('LDO', 'U4', []),
                      ('nRF54L15', 'U5', [(156.5, 127.3, 'C', 0), (157.0, 126.8, 'C', 0)]), ('CELL', 'BT1', []),
                      ('ANTENNA', None, [(x, 142.75, 'C', 0) for x in (166.5, 166.0, 167.0, 165.5, 167.5)]),
                      ('(pull JP3)', 'J2', [(136.5, 115.2, 'C', 0), (137.8, 115.3, 'C', 0), (136.5, 114.9, 'C', 0)]), ('(pull JP4)', 'J3', [])]:
    c = extra + (around(ref) if ref else [])
    if s == 'Qi RX': c += [(183.6, y, 'C', 90) for y in (124.0, 122.0, 126.0)]
    text(s, c, w=0.8)

# ================================================================ BACK (mirrored)
# Coil area (coil sits on the front): spiral artwork between the coil's ID and OD.
CX, CY = 168.05, 115.0
pts = [(CX + (8.6 + 4.3 * i / 648) * math.cos(math.radians(i * 5)),
        CY + (8.6 + 4.3 * i / 648) * math.sin(math.radians(i * 5))) for i in range(649)]
poly_line(pts, BS, 0.15, check=False)
for s, y, h in [('Qi RX COIL', 111.9, 1.4), ('Wurth 760308101309', 114.3, 1.0), ('10 uH, on the front', 116.0, 1.0),
                ('BQ51003 receiver', 117.7, 1.0)]:
    text(s, [(CX, y, 'C', 0)], layer=BS, h=h, w=h * 0.8, t=0.2 if h > 1.1 else HT)

# Block 1: top band, above the J2 holes.
stack([('CARD TEST 1', 1.8), ('Wallet Tracker v1 - dev / bring-up board', H),
       ('4L FR4 0.8 mm ENIG, JLC04081H-3313, 2026-11-15', H),
       ('github.com/EasternProdigy/Credit_Card_Tracker', H), (None, 0.3),
       ('JUMPERS: 0R links, remove one to isolate a stage', HH),
       ('JP1  Qi RX > charger     (V5_RX > V5_CHG)', H),
       ('JP2  charger > cell      (VCHG > VCELL)', H),
       ('JP3  cell > board        (PPK2 on J2)', H)], 152.2, 102.8, 118.3)
# Block 2: middle band, between the J2 and J3 holes.
stack([
       ('JP4  LDO 3.3 V > nRF     (PPK2 on J3)', H),
       ('JP5  VBAT sense > P1.04 / AIN0', H),
       ('JP6  charge status nCHG > P1.05', H), (None, 0.3),
       ('I/O', HH),
       ('LED0 red P2.06, LED1 yellow P1.11: high = on', H),
       ('BTN0 P1.13, BTN1 P1.09: low = pressed', H),
       ('UART J6, FTDI order, black = GND, 3.3 V only', H),
       ('TXO = nRF TX P0.00, RXI = nRF RX P0.01', H),
       ('SWD J4 10-pin 1.27 mm, SWO P2.07, SW3 = reset', H),
       ('DNP: C1d C2c Qi tune, C32 ant, C33 C34 NFC', H)], 152.2, 122.6, 142.1)
# Block 3: right band under the coil, above the antenna.
stack([('PPK2 POWER PROFILING', HH),
       ('Board: pull JP3, ammeter on J2', H),
       ('  VIN = J2 pin 1, VOUT = J2 pin 2', H),
       ('nRF only: pull JP4, ammeter on J3', H),
       ('nRF alone: pull JP4, source 3.3 V', H),
       ('  into J3 pin 2, GND to a GND pad', H)], 184.1, 132.3, 142.6)
# Block 4: bottom band, left of the antenna.
stack([('POWER', HH), ('J1 cell, JST SH: pin 1 = +', H), ('nCHG low = charging, ~66 mA', H)], 152.0, 147.0, 152.95)
# Block 5: bottom-left corner.
stack([('DEV ONLY (not on v2)', HH), ('JP1-6 J1-6 SW1-3 D1-2 BT1', H), ('R30-33 R_PS R_TSD TP1-29', H),
       ('C1d C2c C33 C34', H)], 123.4, 145.5, 152.95)

# Antenna area on the back: dashed line on its edge + label.
if ANT:
    l, t, r, bt = ANT
    x = l
    while x < r:
        seg(x, t, min(x + 1.0, r), t, BS, 0.15, check=False); x += 2.0
    text('2.4 GHz ANTENNA: keep metal away', [((l + r) / 2, t + 1.8, 'C', 0)], layer=BS, h=HH, w=0.9, t=HHT)

pcbnew.SaveBoard(PCB, b)
print('silk items:', len(list(grp.GetItems())), ' legacy labels replaced:', sum(len(v) for v in OLD.values()))
for s, why in FAIL:
    print('NOT PLACED:', s, '->', why)
    if '-v' in sys.argv and s in DBG: print('   ', DBG[s])
