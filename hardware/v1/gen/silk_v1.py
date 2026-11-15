#!/usr/bin/env python3
"""Card Test 1 silkscreen: board name, section and jumper labels, test-pad legend, and the back-side
reference sheet. Works on the routed board in place (never moves copper). Every item it adds lives in
the PCB group 'card_test_silk'; a rerun deletes that group first. Each label tries candidate spots and
takes the first that clears pads, other parts' courtyards, existing silk and the board edge.
Run from hardware/v1:  python3 gen/silk_v1.py"""
import math, sys, pcbnew

PCB = 'card_v1.kicad_pcb'
GROUP = 'card_test_silk'
b = pcbnew.LoadBoard(PCB)
F, M = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(F(x), F(y))
FS, BS = pcbnew.F_SilkS, pcbnew.B_SilkS
X0, Y0, X1, Y1 = 100.0, 100.0, 185.6, 153.98      # board edge
EDGE = 0.6                                        # keep silk this far inside the edge

# ---------------------------------------------------------------- remove the previous run
for g in list(b.Groups()):
    if g.GetName() == GROUP:
        for it in list(g.GetItems()):
            b.Remove(it)
        b.Remove(g)
grp = pcbnew.PCB_GROUP(b); grp.SetName(GROUP); b.Add(grp)

# ---------------------------------------------------------------- obstacles per side
def box(bb, infl=0.0):
    return (M(bb.GetLeft()) - infl, M(bb.GetTop()) - infl, M(bb.GetRight()) + infl, M(bb.GetBottom()) + infl)

OBST = {FS: [], BS: []}
for fp in b.GetFootprints():
    for p in fp.Pads():
        ls = p.GetLayerSet()
        if ls.Contains(pcbnew.F_Cu): OBST[FS].append(('pad ' + fp.GetReference(), box(p.GetBoundingBox(), 0.2)))
        if ls.Contains(pcbnew.B_Cu): OBST[BS].append(('pad ' + fp.GetReference(), box(p.GetBoundingBox(), 0.2)))
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    if cy.OutlineCount() and fp.GetReference() != 'L1':
        OBST[FS].append(('body ' + fp.GetReference(), box(cy.BBox(), 0.05)))
    for g in fp.GraphicalItems():
        if fp.GetReference() == 'L1' and g.GetLayer() == FS: continue   # round coil outline: COIL circle check covers it
        if g.GetLayer() in (FS, BS) and g.IsVisible() if hasattr(g, 'IsVisible') else g.GetLayer() in (FS, BS):
            OBST[g.GetLayer()].append(('silk ' + fp.GetReference(), box(g.GetBoundingBox(), 0.1)))
for d in b.GetDrawings():
    if d.GetLayer() in (FS, BS):
        OBST[d.GetLayer()].append(('silk board', box(d.GetBoundingBox(), 0.1)))
for z in b.Zones():                               # antenna keep-out: keep ink off the radiator side (top)
    if z.GetIsRuleArea() and z.GetDoNotAllowTracks() and M(z.GetBoundingBox().GetTop()) > 140:
        OBST[FS].append(('antenna', box(z.GetBoundingBox(), 0.2)))
        ANT = box(z.GetBoundingBox())

COIL = (168.05, 115.0, 13.6)                      # L1 body on the front: D26.3 coil + margin
def hit(bx, layer, ignore=()):
    l, t, r, btm = bx
    if l < X0 + EDGE or t < Y0 + EDGE or r > X1 - EDGE or btm > Y1 - EDGE:
        return 'edge'
    if layer == FS:
        cx, cy, cr = COIL
        nx, ny = min(max(cx, l), r), min(max(cy, t), btm)
        if math.hypot(nx - cx, ny - cy) < cr: return 'coil L1'
    for name, (a, c, e, f) in OBST[layer]:
        if not name.startswith('pad') and any(name.endswith(' ' + i) for i in ignore): continue   # never ignore copper
        if l < e and r > a and t < f and btm > c:
            return name
    return None

def add(item, layer, solid=True):
    b.Add(item); grp.AddItem(item)
    OBST[layer].append(('silk new', box(item.GetBoundingBox(), 0.1)))
    return item

# ---------------------------------------------------------------- text
FAIL = []; DBG = {}
def text(s, cands, layer=FS, h=0.8, w=None, t=0.15, ignore=(), bold=False):
    """cands: list of (x, y, justify 'L'/'C'/'R', angle). First clear spot wins."""
    w = w or h; tried = []
    for (x, y, j, ang) in cands:
        tx = pcbnew.PCB_TEXT(b); tx.SetText(s); tx.SetLayer(layer)
        tx.SetTextSize(V(w, h)); tx.SetTextThickness(F(t)); tx.SetBold(bold)
        tx.SetHorizJustify({'L': pcbnew.GR_TEXT_H_ALIGN_LEFT, 'C': pcbnew.GR_TEXT_H_ALIGN_CENTER,
                            'R': pcbnew.GR_TEXT_H_ALIGN_RIGHT}[j])
        tx.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        if layer == BS: tx.SetMirrored(True)
        tx.SetTextAngleDegrees(ang); tx.SetPosition(V(x, y))
        why = hit(box(tx.GetBoundingBox()), layer, ignore); tried.append(((x, y, ang), why))
        if why is None:
            return add(tx, layer)
    FAIL.append((s, why)); DBG[s] = tried; return None

def seg(x1, y1, x2, y2, layer, w=0.15, check=True):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(F(w))
    s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2))
    if check:
        why = hit(box(s.GetBoundingBox()), layer)
        if why: FAIL.append((f'segment {x1:.1f},{y1:.1f}', why)); return None
    b.Add(s); grp.AddItem(s); return s

def poly_line(pts, layer, w=0.15, check=True, closed=False):
    pts = pts + [pts[0]] if closed else pts
    for (a, c), (e, f) in zip(pts, pts[1:]):
        seg(a, c, e, f, layer, w, check)

def arc_pts(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

# Board frame, both sides: rounded rectangle 0.8 mm inside the edge.
def frame(layer, inset=0.8, r=2.4):
    l, t, rr, bt = X0 + inset, Y0 + inset, X1 - inset, Y1 - inset
    pts = (arc_pts(l + r, t + r, r, 180, 270, 6) + arc_pts(rr - r, t + r, r, 270, 360, 6) +
           arc_pts(rr - r, bt - r, r, 0, 90, 6) + arc_pts(l + r, bt - r, r, 90, 180, 6))
    pts.append(pts[0])
    for (a, c), (e, f) in zip(pts, pts[1:]):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(F(0.15))
        s.SetStart(V(a, c)); s.SetEnd(V(e, f))
        b.Add(s); grp.AddItem(s); OBST[layer].append(('frame', box(s.GetBoundingBox(), 0.1)))
frame(FS); frame(BS)

def around(ref, gap=0.9):
    fp = b.FindFootprintByReference(ref); l, t, r, bt = box(fp.GetCourtyard(pcbnew.F_CrtYd).BBox())
    cx, cy = (l + r) / 2, (t + bt) / 2; out = []
    for d in (gap, gap + 0.8, gap + 1.6):
        out += [(cx, t - d, 'C', 0), (cx, bt + d, 'C', 0), (r + d - 0.5, cy, 'L', 0), (l - d + 0.5, cy, 'R', 0)]
    return out

# ================================================================ TOP
# Title block, bottom-left free corner, with a "find me" icon: map pin and two radio arcs.
TX, TY = 102.9, 147.6
icon = arc_pts(TX, TY - 0.6, 1.1, 180, 360, 16)
poly_line(icon + [(TX, TY + 2.0)] + [icon[0]], FS, 0.2)        # pin outline
poly_line(arc_pts(TX, TY - 0.6, 0.35, 0, 360, 12), FS, 0.15)    # pin dot
for r in (1.9, 2.6):
    poly_line(arc_pts(TX, TY - 0.6, r, -50, 50, 10), FS, 0.15)    # radio waves
text('CARD TEST 1', [(106.3, 145.2, 'L', 0)], h=1.8, w=1.45, t=0.3, bold=True)
text('WALLET TRACKER v1', [(106.3, 148.3, 'L', 0)], h=0.9, w=0.8, t=0.18)
text('DEV / BRING-UP BOARD', [(106.3, 150.2, 'L', 0)], h=0.9, w=0.8, t=0.18)
text('2026-11-15  -  info on back', [(106.3, 151.95, 'L', 0)], h=0.8, w=0.65)

# Test-pad legend: one line per grid row, left of the pads, names in pad order.
ROWS = [(107.98, 'V5_CHG  VCHG  nCHG'), (110.78, 'NTC  VCELL  BAT-'), (113.58, 'VBAT  PS  DO_GATE'),
        (116.38, 'CO_GATE  3V3  VDD_NRF'), (119.18, 'VBAT_SNS  SWDIO  SWDCLK'), (121.98, 'nRESET  GND  GND'),
        (124.78, 'GND  UART_TX  UART_RX'.replace('UART_', '')), (127.58, 'P1.06  SWO')]
for y, s in ROWS:
    if not text(s + '  >', [(123.7, y, 'R', 0)], h=0.8, w=0.62, ignore=('R32', 'R33')):
        FAIL.pop()                                   # row blocked: label each pad underneath instead
        for name, x in zip(s.split(), (125.0, 127.6, 130.2)):
            text(name, [(x, y + 1.55, 'C', 0)], h=0.8, w=0.5, t=0.15, ignore=('TP28', 'TP29', 'TP27', 'TP26', 'TP25'))
text('TEST PADS', [(123.7, 105.4, 'R', 0), (128.0, 105.2, 'C', 0)], h=0.9, w=0.8, t=0.18)

# Qi test pads TP3 TP4 TP1 TP2 TP5 (left to right): one short label per pad, above if it fits, else below.
for name, x in (('AC1', 172.2), ('AC2', 174.35), ('VRECT', 176.5), ('V5', 178.65), ('RXCHG', 180.8)):
    text(name, [(x, 140.55, 'C', 0)], h=0.8, w=0.45, t=0.15, ignore=('TP1', 'TP2', 'TP3', 'TP4', 'TP5'))

# Jumper labels: name + what it links. All are 0R links; remove one to isolate a stage.
JP = [('JP1', 'QI>CHG', 182.3, 134.78), ('JP2', 'CHG>CELL', 151.0, 132.98),
      ('JP3', 'CELL>BRD', 143.5, 119.98), ('JP4', 'LDO>nRF', 143.5, 143.98),
      ('JP5', 'SNS', 153.3, 142.18), ('JP6', 'nCHG', 153.3, 140.08)]
for ref, what, x, y in JP:
    c = [(x, y - 1.5, 'C', 0), (x, y + 1.5, 'C', 0), (x + 1.4, y, 'L', 0), (x - 1.4, y, 'R', 0),
         (x + 1.4, y, 'C', 90), (x - 1.4, y, 'C', 90), (x, y - 2.4, 'C', 0), (x, y + 2.4, 'C', 0),
         (x + 2.3, y, 'L', 0), (x - 2.3, y, 'R', 0), (x + 2.3, y, 'C', 90), (x - 2.3, y, 'C', 90)]
    if ref in ('JP2', 'JP5', 'JP6'):                 # vertical 0R links: try vertical labels first
        c = [k for k in c if k[3] == 90] + [k for k in c if k[3] != 90]
    if not text(f'{ref} {what}', c, h=0.8, w=0.65, ignore=(ref,)):
        FAIL.pop(); text(ref, c, h=0.8, w=0.65, ignore=(ref,))

# Section labels.
for s, ref, extra in [('Qi RX', 'U1', [(183.6, y, 'C', 90) for y in (124.0, 122.0, 126.0, 120.0)]), ('CHARGER', 'U2', []), ('PROTECT', 'U3', []), ('LDO', 'U4', []),
                      ('nRF54L15', 'U5', [(156.5, 127.3, 'C', 0), (157.0, 126.8, 'C', 0), (155.5, 127.6, 'C', 0), (158.4, 128.9, 'C', 0)]), ('CELL', 'BT1', []),
                      ('ANTENNA', None, [(x, 142.75, 'C', 0) for x in (166.5, 166.0, 167.0, 165.5, 167.5)]),
                      ('PPK2: pull JP3', 'J2', []), ('PPK2: pull JP4', 'J3', [])]:
    text(s, extra + (around(ref) if ref else []), h=0.8, w=0.7)

# ================================================================ BACK (B.Silkscreen, mirrored text)
# Mirrored text with left justify grows toward -x in board coordinates, so each block is anchored at its
# right edge here and reads left-aligned when the card is flipped.
def stack(block, xr, y, ymax, h_body=0.8):
    prev = None
    for s, h in block:
        if s is None: y += h; continue
        if prev is not None: y += prev * 0.915 + h * 0.915 + 0.3
        if y + h * 0.915 > ymax: FAIL.append((s, f'overflow y {y:.1f}')); continue
        text(s, [(xr, y, 'L', 0)], layer=BS, h=h, w=h * 0.85, t=0.2 if h > 0.85 else 0.15)
        prev = h

# Qi coil area (coil sits on the front): spiral artwork between the coil's ID and OD, label inside.
CX, CY = 168.05, 115.0
pts = []
for i in range(0, 9 * 72 + 1):
    a = math.radians(i * 5); r = 8.6 + (12.9 - 8.6) * i / (9 * 72)
    pts.append((CX + r * math.cos(a), CY + r * math.sin(a)))
for (a, c), (e, f) in zip(pts, pts[1:]):
    seg(a, c, e, f, BS, 0.15, check=False)
for s, y, h in [('Qi RX COIL', 112.0, 1.2), ('Wurth 760308101309', 114.3, 0.8), ('10 uH, on the front', 116.1, 0.8),
                ('charges on any Qi pad', 117.9, 0.8)]:
    text(s, [(CX, y, 'C', 0)], layer=BS, h=h, w=h * 0.85, t=0.2 if h > 1 else 0.15)

# Block 1: top band, above the J2 holes.
stack([('CARD TEST 1', 1.6), ('Wallet Tracker v1  -  dev / bring-up board', 0.8),
       ('4-layer FR4 0.8 mm ENIG  -  JLC04081H-3313  -  2026-11-15', 0.8),
       ('github.com/EasternProdigy/Credit_Card_Tracker', 0.8), (None, 0.4),
       ('JUMPERS  (0R links: remove one to isolate a stage)', 0.9),
       ('JP1  Qi RX  >  charger           V5_RX > V5_CHG', 0.8),
       ('JP2  charger  >  cell            VCHG > VCELL', 0.8),
       ('JP3  cell  >  board              PPK2 on J2', 0.8)], 152.2, 102.9, 118.3)
# Block 2: middle band, between the J2 and J3 holes.
stack([('JP4  LDO 3.3 V  >  nRF           PPK2 on J3', 0.8),
       ('JP5  VBAT sense  >  P1.04 / AIN0', 0.8),
       ('JP6  charge status nCHG  >  P1.05', 0.8), (None, 0.4),
       ('I/O', 0.9),
       ('LED0 red P2.06, LED1 yellow P1.11: high = on', 0.8),
       ('BTN0 P1.13, BTN1 P1.09: low = pressed (pull-up)', 0.8),
       ('UART J6, FTDI order: TX P0.00, RX P0.01', 0.8),
       ('   3.3 V LOGIC ONLY, cable VCC not connected', 0.8),
       ('SWD J4 10-pin 1.27 Cortex, SWO P2.07, RESET btn', 0.8),
       ('DNP trims: C1d C2c (Qi tank), C32-C34 (RF, NFC)', 0.8)], 152.2, 122.6, 142.0)
# Block 3: right band under the coil, above the antenna.
stack([('POWER PROFILING  (Nordic PPK2)', 0.9),
       ('Board: pull JP3, PPK2 on J2 (1 = cell, 2 = board)', 0.8),
       ('nRF: pull JP4, PPK2 on J3 (1 = LDO, 2 = nRF)', 0.8),
       ('nRF alone: pull JP4, source 3.3 V into J3 pin 2', 0.8)], 184.1, 132.2, 142.4)
# Block 4: bottom band left of the antenna.
stack([('POWER', 0.9), ('J1 cell (JST SH): pin 1 = CELL +', 0.8),
       ('~66 mA charge; nCHG low = charging', 0.8)], 152.0, 147.0, 152.9)
# Block 5: bottom-left corner.
stack([('DEV ONLY (gone on v2)', 0.9), ('JP1-JP6, J2-J6, SW1-SW3', 0.8),
       ('D1, D2, TP1-TP29, DNP trims', 0.8)], 123.4, 145.4, 152.9)

# Antenna area on the back: dashed line on its edge + label.
if 'ANT' in globals():
    l, t, r, bt = ANT
    x = l
    while x < r:
        seg(x, t, min(x + 1.0, r), t, BS, 0.15, check=False); x += 2.0
    text('2.4 GHz ANTENNA  -  no metal here', [((l + r) / 2, t + 1.8, 'C', 0)], layer=BS, h=0.9, w=0.8, t=0.18)

pcbnew.SaveBoard(PCB, b)
print('silk items:', len(list(grp.GetItems())))
for s, why in FAIL:
    print('NOT PLACED:', s, '->', why)
    if '-v' in sys.argv and s in DBG: print('   ', DBG[s])
