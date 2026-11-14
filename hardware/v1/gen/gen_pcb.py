#!/usr/bin/env python3
"""Build hardware/v1/card_v1.kicad_pcb from design.py: outline, footprints + nets (linked to the
schematic by deterministic UUIDs), placement, keepouts, design rules (JLC 4-layer, Dwayne approved 2026-11-14), critical hand-routes.
Stack: F.Cu signals + GND pour | In1.Cu solid GND (no tracks) | In2.Cu signals + GND pour | B.Cu signals + GND pour.
Card coordinates (docs/04): origin bottom-left, y up. KiCad: K(x, y) = (100 + x, 153.98 - y).
Run with the system python (pcbnew module): python3 hardware/v1/gen/gen_pcb.py [--no-routes]
"""
import math, os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import design as D
import gen_sch as GS

PCB = os.path.join(HERE, '..', D.PROJECT + '.kicad_pcb')
FPROOT = '/usr/share/kicad/footprints'
LOCAL = os.path.join(HERE, '..', 'lib', 'wallet_tracker.pretty')
W, H, RAD = 85.60, 53.98, 3.18
X0, Y0 = 100.0, 100.0 + H
mm = pcbnew.FromMM
def K(x, y): return pcbnew.VECTOR2I(mm(X0 + x), mm(Y0 - y))
def card(v): return (pcbnew.ToMM(v.x) - X0, Y0 - pcbnew.ToMM(v.y))

# ---------------------------------------------------------------- 50 ohm GCPW, top over In1 GND
def _K(k):
    a, b = 1.0, math.sqrt(1 - k * k)
    for _ in range(30): a, b = (a + b) / 2, math.sqrt(a * b)
    return math.pi / (2 * a)
def gcpw_z(w, g, h, er):
    k = w / (w + 2 * g); k1 = math.tanh(math.pi * w / (4 * h)) / math.tanh(math.pi * (w + 2 * g) / (4 * h))
    kp, k1p = math.sqrt(1 - k * k), math.sqrt(1 - k1 * k1)
    q = _K(kp) / _K(k) * _K(k1) / _K(k1p)
    eeff = (1 + er * q) / (1 + q)
    return 60 * math.pi / math.sqrt(eeff) / (_K(k) / _K(kp) + _K(k1) / _K(k1p)), eeff
# JLC 0.8 mm 4-layer impedance stackup, outer prepreg 3313: 0.0994 mm, Dk 4.1 (jlcpcb.com/impedance, read 2026-11-14)
RF_GAP, RF_H, RF_ER = 0.15, 0.0994, 4.1
RF_W = min((round(w, 2) for w in [x / 100 for x in range(10, 80)]),
           key=lambda w: abs(gcpw_z(w, RF_GAP, RF_H, RF_ER)[0] - 50))

# ---------------------------------------------------------------- board + rules
board = pcbnew.NewBoard(PCB)
board.SetCopperLayerCount(4)
board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)   # In1: GND plane (exported to Freerouting as a plane, not routed)
CU4 = ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')
ds = board.GetDesignSettings()
ds.SetBoardThickness(mm(0.8))   # JLC's thinnest listed 4-layer impedance stackup; v1 thickness is free
ds.m_TrackMinWidth = mm(0.09); ds.m_MinClearance = mm(0.1); ds.m_ViasMinSize = mm(0.25)
ds.m_MinThroughDrill = mm(0.15); ds.m_HoleClearance = mm(0.15); ds.m_CopperEdgeClearance = mm(0.3)
ds.m_HoleToHoleMin = mm(0.25); ds.m_ViasMinAnnularWidth = mm(0.05)
nc = ds.m_NetSettings
nc.ClearNetclassPatternAssignments()
dflt = nc.GetDefaultNetclass()
dflt.SetClearance(mm(0.12)); dflt.SetTrackWidth(mm(0.15)); dflt.SetViaDiameter(mm(0.5)); dflt.SetViaDrill(mm(0.25))
CLASSES = {
    'QI_AC': (0.4, 0.15, ['AC1', 'AC2', 'COIL1']),
    'PWR': (0.3, 0.12, ['VRECT', 'V5_RX', 'V5_CHG', 'VCHG', 'VCELL', 'VBAT', 'BT_NEG', 'VDD_3V3']),
    'MCU_PWR': (0.2, 0.12, ['VDD_NRF', 'DCC', 'DECD', 'DECA']),
    'RF50': (RF_W, RF_GAP, ['RF_NRF', 'RF_A', 'RF_B', 'RF_MATCHED', 'ANT_FEED']),
}
for name, (tw, cl, nets) in CLASSES.items():
    c = pcbnew.NETCLASS(name); c.SetTrackWidth(mm(tw)); c.SetClearance(mm(cl))
    c.SetViaDiameter(mm(0.5)); c.SetViaDrill(mm(0.25))
    nc.SetNetclass(name, c)
    for n in nets: nc.SetNetclassPatternAssignment(n, name)

# ---------------------------------------------------------------- outline (ISO ID-1, R3.18)
def seg(a, b, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(a); s.SetEnd(b)
    s.SetLayer(layer); s.SetWidth(mm(w)); board.Add(s)
def arc(c, r, a0, layer=pcbnew.Edge_Cuts):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
    p = lambda a: K(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a)))
    s.SetArcGeometry(p(a0), p(a0 + 45), p(a0 + 90)); s.SetLayer(layer); s.SetWidth(mm(0.1)); board.Add(s)
r = RAD
seg(K(r, 0), K(W - r, 0)); seg(K(W, r), K(W, H - r)); seg(K(W - r, H), K(r, H)); seg(K(0, H - r), K(0, r))
arc((W - r, r), r, 270); arc((W - r, H - r), r, 0); arc((r, H - r), r, 90); arc((r, r), r, 180)

# ---------------------------------------------------------------- nets + footprints
nets = {}
def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(board, n); board.Add(ni); nets[n] = ni
    return nets[n]
FP = {}
lcsc = GS.lcsc_map()
for c in D.C:
    lib, name = c['fp'].split(':')
    path = LOCAL if lib == 'wallet_tracker' else f'{FPROOT}/{lib}.pretty'
    f = pcbnew.FootprintLoad(path, name)
    assert f, c['fp']
    f.SetFPID(pcbnew.LIB_ID(lib, name))
    f.SetReference(c['ref']); f.SetValue(c['value'])
    f.SetPath(pcbnew.KIID_PATH(f"/{GS.U('sheet', c['sheet'])}/{GS.U('sym', c['ref'])}"))
    f.SetSheetname(c['sheet']); f.SetSheetfile(c['sheet'] + '.kicad_sch')
    if c['dnp']: f.SetDNP(True)
    if c['sym'] == 'Connector:TestPoint': f.SetExcludedFromBOM(True)
    for k, v in (('MPN', c['mpn']), ('Source', c['src']), ('LCSC', lcsc.get(c['ref'], ''))):
        f.SetField(k, v or ''); f.GetField(k).SetVisible(False)
    padnames = {p.GetNumber() for p in f.Pads()}
    for pin, n in c['pins'].items():
        if pin not in padnames:
            raise SystemExit(f"{c['ref']}: pin {pin} has no pad in {c['fp']}")
    pin_names = {q[0]: q[1] for q in GS.get_symbol(c['sym'])[2]}
    for p in f.Pads():
        num = p.GetNumber()
        n = c['pins'].get(num)
        if n: p.SetNet(net(n))
        elif num in c['pins']:   # explicit no-connect: use KiCad's schematic name so parity matches
            p.SetNet(net(f"unconnected-({c['ref']}-{pin_names[num].replace('/', '{slash}')}-Pad{num})"))
    f.Reference().SetVisible(False)   # minimal silkscreen (docs/04); refs remain on F.Fab via ${REFERENCE}
    board.Add(f); FP[c['ref']] = f

# ---------------------------------------------------------------- placement helpers
def place(ref, x, y, rot=0, side='F'):
    f = FP[ref]; f.SetPosition(K(x, y)); f.SetOrientationDegrees(rot)
def padpos(ref, num):
    for p in FP[ref].Pads():
        if p.GetNumber() == num: return card(p.GetPosition())
    raise KeyError(ref + '.' + num)
def near(ic, pin, ref, dist=0.9, along=0.0, ic_center=None):
    """Put 2-pad part `ref` outward from IC pad `pin`, pads in line with the outward direction, pad 1 toward the IC."""
    px, py = padpos(ic, pin); cx, cy = ic_center or card(FP[ic].GetPosition())
    dx, dy = px - cx, py - cy
    ux, uy = (math.copysign(1, dx), 0) if abs(dx) >= abs(dy) else (0, math.copysign(1, dy))
    vx, vy = -uy, ux
    place(ref, px + ux * dist + vx * along, py + uy * dist + vy * along)
    orient(ref, (px, py))
def orient(ref, target):
    """Rotate a 2-pad part so pad 1 is closest to target, keeping the pad axis along the larger offset."""
    f = FP[ref]; fx, fy = card(f.GetPosition()); dx, dy = target[0] - fx, target[1] - fy
    best = None
    for rot in (0, 90, 180, 270):
        f.SetOrientationDegrees(rot)
        p1 = padpos(ref, '1'); d = math.hypot(p1[0] - target[0], p1[1] - target[1])
        if best is None or d < best[0]: best = (d, rot)
    f.SetOrientationDegrees(best[1])

# ---------------------------------------------------------------- placement (card mm)
# Electronics zone (x 52.5-83.6, y 10.5-25): MCU+RF (left) and Qi receiver (right) only, v2-like.
# Dev area (battery pocket region, x < 51 on v1): charger, protection, LDO/sense, jumpers, headers, test pads.
DIRS = {'W': 0, 'S': 90, 'E': 180, 'N': 270}   # 2-pad parts: direction of pad 1 from the part centre
def P(ref, x, y, d='W'):
    place(ref, x, y, DIRS[d] if isinstance(d, str) else d)
UX, UY = 58.4, 19.8
P('U5', UX, UY, 270)                 # rot 270: pin 31 (ANT) faces the antenna; see pinmaps for pin sides
ax, ay = padpos('U5', '31')
sx = round(ax, 2)
PITCH = 1.45
for i, ref in enumerate(['L3', 'L4', 'L5', 'L6']):
    P(ref, sx, ay - 1.25 - i * PITCH, 'N')
node = lambda i: ay - 1.25 - i * PITCH - PITCH / 2
P('C25', padpos('U5', '32')[0] + 0.28, ay - 1.5, 'S')   # RF_A shunt; GND pad straight below pin 32 (top only)
P('C26', sx - 1.1, node(1), 'E')     # RF_B shunt, ground via to bottom only
P('C27', sx - 1.1, node(2), 'E')     # RF_MATCHED shunt
P('C32', sx + 1.1, node(2), 'W')     # DNP pi
feed_y = 10.5
P('C28', sx - 1.1, node(3) + 0.35, 'E')   # ANT_FEED shunt
P('TP19', sx + 1.15, node(3) + 0.35)
P('AE1', sx, feed_y, 0)
for rot in (0, 90, 180, 270):                             # arm away from the battery, below the ground edge
    FP['AE1'].SetOrientationDegrees(rot)
    shx, shy = padpos('AE1', '2'); bb = FP['AE1'].GetBoundingBox(False)
    if shx < sx - 1 and card(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))[1] < feed_y: break
P('Y1', 62.0, 14.5, 0)               # XC1/XC2 pins at (59.8/60.2, 16.85): within 3 mm
P('C23', 62.3, 16.6, 'W')            # VDD pin 36
P('R7', 57.5, 15.55, 'E')             # pin 30 side = pad 1 (nRESET_IC)
P('C31', 57.5, 14.8, 'E')

# right side: DC/DC + DEC (pins 43..48 at x 61.35, y 20.0..22.0)
P('C21', 62.95, 22.35, 'W')          # VDD 48
P('C18', 62.95, 21.45, 'W')           # DECD
P('FB1', 62.95, 20.55, 'W')          # DECD -> DECA
P('C19', 62.95, 19.65, 'W')           # DECA
P('C24', 62.95, 18.75, 'W')
P('C30', 62.95, 17.85, 'W')
P('L2', 64.65, 21.1, 'N')            # DCC (top) -> DECD (bottom)
P('C17', 63.55, 23.75, 'S')          # 10 uF VDD 47/48
# top: VDD 10, NFC (DNP), 32 kHz
P('C20', 56.85, 23.85, 'S')
P('C33', 28.5, 9.0, 'S'); P('C34', 29.5, 9.0, 'S')   # NFC tuning (DNP) at the antenna pads
P('Y2', 60.95, 24.4, 180)          # rotated: XL1/XL2 do not cross
# left: VDD 22
P('C22', 54.4, 18.4, 'E')
P('JP6', 53.3, 13.9, 'N'); P('JP5', 53.3, 11.8, 'N')

# Qi receiver
P('L1', 68.05, 38.98 - 15.0, 0)      # lands at (66.05 / 70.05, 23.98)
for i, ref in enumerate(['C1a', 'C1b', 'C1c', 'C1d']):
    P(ref, 66.45 + i * 1.55, 20.0, 'N')       # COIL1 on top
for i, ref in enumerate(['C2a', 'C2b', 'C2c']):
    P(ref, 66.45 + i * 1.55, 15.6, 'N')       # AC1 on top
UQX, UQY = 75.6, 19.6
P('U1', UQX, UQY, 90)                # rot 90: AC balls (row B) face the tank caps on the left
# U1 courtyard ~ x 73.1-78.1, y 17.6-21.6
P('C3', 73.9, 22.55, 'S'); P('C5', 75.1, 22.55, 'S'); P('C7', 76.3, 22.55, 'S'); P('C10', 77.5, 22.55, 'S')
P('C4', 73.9, 16.65, 'N'); P('C6', 75.1, 16.65, 'N'); P('C8', 76.3, 16.65, 'N'); P('R_TS', 77.5, 16.65, 'N')
P('R1', 79.0, 17.1, 'W'); P('RFOD', 79.0, 16.1, 'W'); P('RFOD2', 79.0, 15.1, 'W')
P('ROS1', 76.5, 14.7, 'E'); P('ROS2', 74.4, 14.7, 'E')
for i, ref in enumerate(['C9a', 'C9b', 'C9c']):
    P(ref, 79.3 + i * 1.05, 22.35, 'S')
P('C11', 79.4, 19.65, 'W'); P('C11b', 79.4, 18.65, 'W')
P('JP1', 82.3, 19.2, 'N'); P('C9d', 82.9, 22.75, 'S')
for i, ref in enumerate(['TP3', 'TP4', 'TP1', 'TP2', 'TP5']):
    P(ref, 72.2 + i * 2.15, 12.0)

# dev area: charger
P('U2', 46.0, 22.0, 0)
P('C12', 48.2, 22.7, 'W'); P('C13', 43.8, 22.7, 'E'); P('R2', 48.2, 21.3, 'W'); P('TH1', 43.8, 21.3, 'E')
P('R_TSD', 43.8, 19.6, 'E'); P('JP2', 51.0, 21.0, 'N')
# protection + cell
P('J1', 46.5, 47.5, 180); P('BT1', 38.5, 47.5, 0)
P('U3', 44.0, 40.0, 0); P('Q1', 47.6, 40.0, 0)
P('R5', 42.2, 41.4, 'E'); P('C29', 42.2, 42.4, 'E'); P('R6', 42.2, 38.6, 'E'); P('R_PS', 42.2, 39.6, 'E')
P('JP3', 43.5, 34.0, 'W'); P('J2', 36.5, 34.0, 90)
# LDO + sense
P('U4', 45.0, 14.0, 0)
P('C14', 46.8, 14.6, 'W'); P('C15', 43.2, 14.6, 'E')
P('R3', 48.4, 14.0, 'N'); P('R4', 49.4, 14.0, 'N'); P('C16', 50.4, 14.0, 'N')
P('JP4', 43.5, 10.0, 'W'); P('J3', 36.5, 10.0, 90)
# debug
P('J4', 37.5, 26.0, 90)
P('J5', 26.0, 8.0, 0)
tps = [c['ref'] for c in D.C if c['ref'].startswith('TP') and c['ref'] not in ('TP19', 'TP1', 'TP2', 'TP3', 'TP4', 'TP5')]
for i, ref in enumerate(tps):
    P(ref, 25.0 + (i % 3) * 2.6, 46.0 - (i // 3) * 2.8)

# ---------------------------------------------------------------- courtyard resolver
BIG = lambda r: r[0] in 'UJY' or r in ('AE1', 'L1', 'BT1', 'Q1')
def cbox(f):
    c = f.GetCourtyard(pcbnew.F_CrtYd)
    if c.OutlineCount() == 0: return None
    b = c.BBox(); return [b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()]
HAND = {'C21', 'C18', 'FB1', 'C19', 'C24', 'C30', 'L2', 'C25', 'C23', 'C17', 'C20', 'C22', 'L3', 'L4', 'L5', 'L6',
        'C26', 'C27', 'C28', 'C32', 'TP19', 'R7', 'C31'}
def resolve(maxmove=0.5):
    """Only small-vs-big overlaps: push the small part straight away from the big one, at most maxmove."""
    report = []
    for r in FP:
        if BIG(r) or r in HAND: continue
        total = 0.0
        for _ in range(10):
            me = cbox(FP[r]); hit = None
            if not me: break
            for o in FP:
                if o == r or not BIG(o): continue
                st = cbox(FP[o])
                if not st: continue
                ox = min(me[2], st[2]) - max(me[0], st[0]); oy = min(me[3], st[3]) - max(me[1], st[1])
                if ox > 0 and oy > 0: hit = (o, st, ox, oy); break
            if not hit: break
            o, st, ox, oy = hit
            cxs, cys = (st[0] + st[2]) / 2, (st[1] + st[3]) / 2
            cxm, cym = (me[0] + me[2]) / 2, (me[1] + me[3]) / 2
            if abs(cxm - cxs) / max(st[2] - st[0], 1) >= abs(cym - cys) / max(st[3] - st[1], 1):
                v = pcbnew.VECTOR2I(int(math.copysign(ox + mm(0.02), cxm - cxs)), 0)
            else:
                v = pcbnew.VECTOR2I(0, int(math.copysign(oy + mm(0.02), cym - cys)))
            step = pcbnew.ToMM(abs(v.x) + abs(v.y))
            if total + step > maxmove: report.append((r, o)); break
            FP[r].Move(v); total += step
    return report
RESOLVE_ITERS = resolve()


# polarity marks (silk refs are hidden): "+" at cell pin 1, labels for the PPK2 and SWD headers
def silk(txt, x, y, sz=0.8):
    t = pcbnew.PCB_TEXT(board); t.SetText(txt); t.SetPosition(K(x, y)); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mm(sz), mm(sz))); t.SetTextThickness(mm(0.15)); board.Add(t)
for ref in ('J1', 'BT1'):
    px_, py_ = padpos(ref, '1'); silk('+', px_ - (1.8 if ref == 'BT1' else 0), py_ + 2.0)
for ref, lbl in (('J2', 'PPK BAT'), ('J3', 'PPK 3V3'), ('J4', 'SWD')):
    cx_, cy_ = card(FP[ref].GetPosition()); silk(lbl, cx_ - (4.5 if ref == 'J4' else 0), cy_ + 3.0)

# ---------------------------------------------------------------- keepouts
def rule_area(name, pts, layers=('F.Cu', 'B.Cu'), tracks=True, vias=True, pour=True, pads=False, fps=False):
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers: ls.AddLayer(board.GetLayerID(l))
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowZoneFills(pour)
    z.SetDoNotAllowPads(pads); z.SetDoNotAllowFootprints(fps)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(X0 + x), mm(Y0 - y))
    board.Add(z); return z
def circle_pts(cx, cy, r, n=48): return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
# antenna keep-out (docs/04): only IFA copper; footprints' own copper is allowed (pads=False keeps AE1 legal)
rule_area('ANT_KEEPOUT', [(52.5, 2.0), (83.6, 2.0), (83.6, 10.2), (52.5, 10.2)], layers=CU4, pour=True, tracks=True, vias=True)
# coil: no copper on any layer inside D26, except its lands (lands sit outside the circle)
rule_area('COIL_KEEPOUT', circle_pts(68.05, 38.98, 13.0), layers=CU4, tracks=True, vias=True, pour=True)
# In1 is the solid ground reference for the top layer (RF GCPW, HFXO). It is a 'power' layer, so Freerouting
# treats it as a plane and never routes on it (a wire keep-out here made Freerouting flag every via as a violation).
# Nordic Fig. 180: C25 ground only to pin 32 (top); keep the top pour away from C25's ground pad + pin 32
g25 = padpos('C25', '2'); p32 = padpos('U5', '32')
xs = [g25[0], p32[0]]; ys = [g25[1], p32[1]]
rule_area('C25_GND_ISOLATE', [(min(xs) - 0.4, min(ys) - 0.4), (max(xs) + 0.4, min(ys) - 0.4),
                              (max(xs) + 0.4, max(ys) + 0.25), (min(xs) - 0.4, max(ys) + 0.25)],
          layers=('F.Cu',), tracks=False, vias=False, pour=True)
# C26 ground: bottom ground only -> no top pour around its ground pad
g26 = padpos('C26', '2')
rule_area('C26_GND_ISOLATE', [(g26[0] - 0.45, g26[1] - 0.4), (g26[0] + 0.45, g26[1] - 0.4),
                              (g26[0] + 0.45, g26[1] + 0.4), (g26[0] - 0.45, g26[1] + 0.4)],
          layers=('F.Cu',), tracks=False, vias=False, pour=True)
# 32 MHz crystal: no foreign traces underneath on either layer
y1 = card(FP['Y1'].GetPosition())
rule_area('Y1_NO_TRACKS_B', [(y1[0] - 1.1, y1[1] - 0.9), (y1[0] + 1.1, y1[1] - 0.9), (y1[0] + 1.1, y1[1] + 0.9),
                             (y1[0] - 1.1, y1[1] + 0.9)], layers=('B.Cu',), tracks=True, vias=True, pour=False)

# ---------------------------------------------------------------- ground pours (filled after routing)
def pour(layer, pts, netname='GND', prio=0):
    z = pcbnew.ZONE(board); z.SetLayer(board.GetLayerID(layer)); z.SetNet(net(netname)); z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.15)); z.SetThermalReliefGap(mm(0.2))
    z.SetThermalReliefSpokeWidth(mm(0.25)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(X0 + x), mm(Y0 - y))
    board.Add(z); return z
card_pts = [(0.4, 0.4), (W - 0.4, 0.4), (W - 0.4, H - 0.4), (0.4, H - 0.4)]
pour('B.Cu', card_pts); pour('F.Cu', card_pts); pour('In1.Cu', card_pts); pour('In2.Cu', card_pts)

# ---------------------------------------------------------------- hand routes (critical nets), vias
TRK = []
def pad_obj(ref, num):
    for p in FP[ref].Pads():
        if p.GetNumber() == num: return p
def track(netname, pts, w, layer='F.Cu'):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board); t.SetStart(K(x1, y1)); t.SetEnd(K(x2, y2)); t.SetWidth(mm(w))
        t.SetLayer(board.GetLayerID(layer)); t.SetNet(net(netname)); t.SetLocked(True); board.Add(t); TRK.append(t)
VIAS = []
def via(netname, x, y, d=0.5, drill=0.25, locked=True):
    v = pcbnew.PCB_VIA(board); v.SetPosition(K(x, y)); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetNet(net(netname)); v.SetLocked(locked); board.Add(v); VIAS.append((x, y, d / 2, netname)); return v
def free(x, y, r, netname, clr=0.13):
    """True if a circle at (x, y) radius r keeps clr from every other-net pad, via and track (bbox test)."""
    X, Y = mm(X0 + x), mm(Y0 - y); R = mm(r + clr)
    if not (0.6 < x < W - 0.6 and 0.6 < y < H - 0.6): return False
    for f in FP.values():
        for p in f.Pads():
            if p.GetNetname() == netname and netname: continue
            b = p.GetBoundingBox()
            if b.GetLeft() - R < X < b.GetRight() + R and b.GetTop() - R < Y < b.GetBottom() + R: return False
    for vx, vy, vr, vn in VIAS:
        if vn != netname and math.hypot(vx - x, vy - y) < vr + r + clr: return False
        if vn == netname and math.hypot(vx - x, vy - y) < vr + r + 0.1: return False
    for t in TRK:
        if t.GetNetname() == netname: continue
        a, b = t.GetStart(), t.GetEnd(); hw = t.GetWidth() / 2
        if min(a.x, b.x) - hw - R < X < max(a.x, b.x) + hw + R and min(a.y, b.y) - hw - R < Y < max(a.y, b.y) + hw + R:
            return False
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias() and z.Outline().Contains(pcbnew.VECTOR2I(X, Y)):
            return False
    return True
pp = padpos
RFW = RF_W   # 50 ohm GCPW over In1 (0.20 mm on the 4-layer stack); was 0.30 on 2-layer
# RF chain (Nordic Fig.180 order), straight and short
segs = [(('U5', '31'), ('L3', '1'), 'RF_NRF'), (('L3', '2'), ('L4', '1'), 'RF_A'), (('L4', '2'), ('L5', '1'), 'RF_B'),
        (('L5', '2'), ('L6', '1'), 'RF_MATCHED'), (('L6', '2'), ('AE1', '1'), 'ANT_FEED')]
for a_, b_, n_ in segs:
    track(n_, [pp(*a_), pp(*b_)], RFW)
for ref, n_ in (('C26', 'RF_B'), ('C27', 'RF_MATCHED'), ('C32', 'RF_MATCHED'), ('C28', 'ANT_FEED')):
    x1, y1 = pp(ref, '1'); track(n_, [(x1, y1), (sx, y1)], 0.25)
tx, ty = pp('TP19', '1'); track('ANT_FEED', [(tx, ty), (sx, ty)], 0.2)
# C25 ground -> pin 32 only (top), pin 32 -> exposed pad only (under the IC)
g25 = pp('C25', '2'); p32 = pp('U5', '32')
track('GND', [g25, (p32[0] + 0.08, g25[1] + 0.24), (p32[0] + 0.08, 16.4), (p32[0], 16.6), p32], 0.15)
c25a = pp('C25', '1'); track('RF_A', [c25a, (sx, c25a[1])], 0.25)
track('GND', [p32, (p32[0], p32[1] + 0.75)], 0.2)          # inward to the EP edge (EP edge at UY-2.3)
# C26 ground: via straight to the bottom ground
g26 = pp('C26', '2'); via('GND', g26[0] - 0.55, g26[1]); track('GND', [g26, (g26[0] - 0.55, g26[1])], 0.25)
# antenna short to ground: via at the short pad
shp = pp('AE1', '2'); via('GND', shp[0], shp[1] + 0.75); track('GND', [shp, (shp[0], shp[1] + 0.75)], 0.5)
# crystal 32 MHz (no traces under it; Nordic: within 3 mm)
p34, p35, p36 = pp('U5', '34'), pp('U5', '35'), pp('U5', '36')
y1p1, y1p3 = pp('Y1', '1'), pp('Y1', '3')
track('XC1', [p34, (p34[0], y1p1[1]), y1p1], 0.15)
track('XC2', [p35, (p35[0], 16.0), (y1p3[0], 16.0), y1p3], 0.15)
# VDD_NRF pin 36 -> C23: left to Freerouting (locked stubs inside QFN pads made its normalizer oscillate)
p30 = pp('U5', '30'); r7a, c31a = pp('R7', '1'), pp('C31', '1')
track('nRESET_IC', [p30, (p30[0], p30[1] - 0.6), r7a, c31a], 0.15)
# 32 kHz
p1, p2 = pp('U5', '1'), pp('U5', '2'); y2a, y2b = pp('Y2', '1'), pp('Y2', '2')
track('XL1', [p1, (p1[0], 23.55), (y2a[0], 23.55), y2a], 0.15)
track('XL2', [p2, (p2[0], 23.55 if y2b[0] < p2[0] - 0.3 else y2b[1]), y2b], 0.15) if abs(y2b[0] - p2[0]) < 0.3 else None
# DEC / DCC / VDD on the right side: straight stubs where aligned
a_ = pp('U5', '43'); b_ = pp('C19', '1'); track('DECA', [a_, (a_[0] + 0.55, a_[1]), (b_[0] - 0.35, b_[1]), b_], 0.2)
p47, p48, c21 = pp('U5', '47'), pp('U5', '48'), pp('C21', '1')
# DCC: pin 46 -> L2 pad 1 through the gap between C21 and C18
p46 = pp('U5', '46'); l2a, l2b = pp('L2', '1'), pp('L2', '2'); c18, fb1a, fb1b = pp('C18', '1'), pp('FB1', '1'), pp('FB1', '2')
yg = (c21[1] + c18[1]) / 2
track('DCC', [p46, (p46[0] + 0.5, p46[1]), (p46[0] + 0.9, yg), (l2a[0] - 0.3, yg), l2a], 0.2)
# DECD: pin 45 -> FB1.1/C18.1 column (same net) -> gap between C18 and FB1 -> L2 pad 2
p45 = pp('U5', '45'); yd = (c18[1] + fb1a[1]) / 2
track('DECD', [p45, (fb1a[0], p45[1]), (fb1a[0], yd), (l2b[0] - 0.75, yd), (l2b[0] - 0.25, l2b[1] + 0.2)], 0.2)
track('DECD', [c18, (c18[0], yd)], 0.2); track('DECD', [fb1a, (fb1a[0], p45[1])], 0.2)
# DECA: FB1.2 -> right -> down -> gap between C19 and C24 -> C19.1 / C24.1 / C30.1
c19, c24, c30 = pp('C19', '1'), pp('C24', '1'), pp('C30', '1')
ya = (c19[1] + c24[1]) / 2
track('DECA', [fb1b, c19], 0.2)
track('DECA', [c19, c24, c30], 0.2)
c19g = pp('C19', '2'); via('GND', c19g[0] + 0.6, c19g[1]); track('GND', [c19g, (c19g[0] + 0.6, c19g[1])], 0.25)
c23g = pp('C23', '2'); via('GND', c23g[0] + 0.62, c23g[1]); track('GND', [c23g, (c23g[0] + 0.62, c23g[1])], 0.25)
y1g4, y1g2 = pp('Y1', '4'), pp('Y1', '2')
via('GND', y1g4[0] - 0.85, y1g4[1] - 0.15); track('GND', [y1g4, (y1g4[0] - 0.85, y1g4[1] - 0.15)], 0.25)
via('GND', y1g2[0] + 0.85, y1g2[1]); track('GND', [y1g2, (y1g2[0] + 0.85, y1g2[1])], 0.25)
# DECRF (pin 33): boxed in by C25 ground and the crystal; small via (4-layer class) and bottom run to the DECA node
p33 = pp('U5', '33'); va = (p33[0] + 0.05, 16.25); vb = (c30[0] - 0.15, c30[1] - 0.5)
track('DECA', [p33, (p33[0], 16.4), va], 0.15); via('DECA', va[0], va[1], 0.3, 0.15)
track('DECA', [va, (va[0], 16.62), (61.6, 16.62), (vb[0], vb[1] - 0.5), vb], 0.2, 'B.Cu')   # crosses XC1/XC2 at right angles only (DevZone 127617)
via('DECA', vb[0], vb[1], 0.3, 0.15); track('DECA', [vb, c30], 0.2)
# VDD_NRF trunk on B.Cu: JP4 -> J3 (PPK2) -> J4 (SWD VTref) -> TP17, and JP4 -> C22 / pin 22 at the MCU
jp4, j3, j4, tp17, c22, p22 = pp('JP4', '2'), pp('J3', '2'), pp('J4', '1'), pp('TP17', '1'), pp('C22', '1'), pp('U5', '22')
track('VDD_NRF', [c22, p22], 0.2)
vj = (jp4[0], jp4[1] + 0.95); via('VDD_NRF', *vj); track('VDD_NRF', [jp4, vj], 0.3)
v4 = (j4[0], j4[1] - 1.15); via('VDD_NRF', *v4); track('VDD_NRF', [j4, v4], 0.3)
vt = (tp17[0], tp17[1] - 1.0); via('VDD_NRF', *vt); track('VDD_NRF', [tp17, vt], 0.3)
vc = (c22[0] - 0.12, c22[1] - 1.0); via('VDD_NRF', *vc); track('VDD_NRF', [c22, vc], 0.25)
track('VDD_NRF', [j3, (j3[0], vj[1]), vj], 0.3, 'B.Cu')
track('VDD_NRF', [j3, (j3[0], v4[1] - 0.6), (v4[0] + 0.6, v4[1] - 0.6), v4], 0.3, 'B.Cu')
track('VDD_NRF', [v4, (v4[0] - 1.0, v4[1] + 1.0), (vt[0] + 0.0, vt[1] - 8.0), vt], 0.3, 'B.Cu')
track('VDD_NRF', [vj, (51.3, vj[1]), (vc[0], vj[1] + 3.42), vc], 0.3, 'B.Cu')
c20g = pp('C20', '2'); via('GND', c20g[0], c20g[1] + 0.7); track('GND', [c20g, (c20g[0], c20g[1] + 0.7)], 0.25)
c31g = pp('C31', '2'); via('GND', c31g[0] - 0.62, c31g[1]); track('GND', [c31g, (c31g[0] - 0.62, c31g[1])], 0.25)
# VDD_NRF local ring: each VDD pin to its decap on top, decaps dropped to a B.Cu ring around U5
p10, p36, c20a, c23a, c17a = pp('U5', '10'), pp('U5', '36'), pp('C20', '1'), pp('C23', '1'), pp('C17', '1')
track('VDD_NRF', [(p10[0], p10[1] + 0.1), (p10[0], c20a[1] - 0.3), c20a], 0.2)
track('VDD_NRF', [(p36[0], 16.6), c23a], 0.2)   # pin 36 + C23: no room for a via on 2 layers -> manual/4-layer link (see MORNING_REPORT)
track('VDD_NRF', [(p48[0] + 0.15, p48[1]), (p48[0] + 0.55, p48[1]), (p48[0] + 0.65, c21[1]), c21], 0.2)
track('VDD_NRF', [(p47[0] + 0.15, p47[1]), (p47[0] + 0.4, p47[1] + 0.15), (p48[0] + 0.55, p48[1])], 0.15)
track('VDD_NRF', [c21, (c21[0], c21[1] + 0.55), (c17a[0], c17a[1] - 0.25), c17a], 0.2)
v20 = (c20a[0] - 0.8, c20a[1] + 0.22); via('VDD_NRF', *v20); track('VDD_NRF', [c20a, v20], 0.2)
v21 = (c21[0] - 0.45, c21[1] + 0.9); via('VDD_NRF', *v21); track('VDD_NRF', [(c21[0], c21[1] + 0.55), v21], 0.2)
track('VDD_NRF', [vc, (vc[0], v20[1] - 1.45), v20], 0.25, 'B.Cu')
track('VDD_NRF', [v20, (v20[0] + 0.3, v20[1] + 0.3), (v21[0] - 0.6, v20[1] + 0.3), v21], 0.25, 'B.Cu')
# U1 same-net ball strings (deterministic; TI: lowest resistance on AC and OUT)
for balls, n_ in ((('B1', 'B2'), 'AC2'), (('B3', 'B4'), 'AC1'),
                  (('A1', 'A2', 'A3', 'A4'), 'GND'), (('C2', 'C3'), 'VRECT')):
    track(n_, [pp('U1', b_) for b_ in balls], 0.2)
# U1 AD/EN1/EN2 (G4, G3, G2) are GND: string them and drop a via outside the array
g4 = pp('U1', 'G4'); track('GND', [pp('U1', 'G2'), pp('U1', 'G3'), g4], 0.2)
via('GND', g4[0] + 0.6, g4[1] + 0.4); track('GND', [g4, (g4[0] + 0.6, g4[1] + 0.4)], 0.2)
# U4 (DQN) thermal pad to GND pin 2 on top; TI: no via under the DQN thermal pad
track('GND', [pp('U4', '5'), pp('U4', '2')], 0.2)
# EP ground vias (QFN48 thermal/ground, 3 x 3, 0.25 drill)
for i in (-1, 0, 1):
    for j in (-1, 0, 1):
        via('GND', UX + i * 1.2, UY + j * 1.2)
# U1 via-in-pad on the 5 enclosed balls (JLC 4-layer BGA guide: 0.15 drill / 0.25 copper)
for ball, n_ in (('C2', 'VRECT'), ('C3', 'VRECT'), ('E2', 'CLAMP2'), ('E3', 'CLAMP1'), ('F2', 'FOD'), ('D2', 'V5_RX')):
    x_, y_ = pp('U1', ball); via(n_, x_, y_, 0.25, 0.15)
# GND via beside every GND pad of small parts (pours on both layers), searching outward
GND_SKIP = {'C25', 'C26', 'AE1', 'U5', 'U1', 'TP23', 'TP24', 'TP25'}
for ref, f in FP.items():
    if ref in GND_SKIP or ref.startswith('J') or ref == 'BT1': continue
    cx, cy = card(f.GetPosition())
    for p in f.Pads():
        if p.GetNetname() != 'GND': continue
        px, py = card(p.GetPosition())
        dx, dy = px - cx, py - cy; L = math.hypot(dx, dy) or 1
        cands = []
        for dist in (0.55, 0.7, 0.9):
            for ang in (0, 25, -25, 50, -50, 90, -90):
                a = math.atan2(dy, dx) + math.radians(ang)
                cands.append((px + dist * math.cos(a), py + dist * math.sin(a)))
        for vx, vy in cands:
            path_ok = all(free(px + (vx - px) * t, py + (vy - py) * t, 0.125, 'GND', 0.13) for t in (0.45, 0.7, 0.85))
            if path_ok and free(vx, vy, 0.25, 'GND'):
                via('GND', vx, vy); track('GND', [(px, py), (vx, vy)], 0.25); break
# U1 PGND balls (row A, edge): via outward from each
for ball in ('A1', 'A2', 'A3', 'A4'):
    px, py = pp('U1', ball); cx, cy = card(FP['U1'].GetPosition())
    for dist in (0.6, 0.75, 0.9):
        vx, vy = px + math.copysign(dist, px - cx), py
        if free(vx, vy, 0.25, 'GND'):
            via('GND', vx, vy); track('GND', [(px, py), (vx, vy)], 0.2); break
# ground edge stitching (docs/04: <= 3 mm along y = 10.5), plus a 4 mm grid elsewhere
x = 53.0
while x < 83.4:
    for dy in (0.45, 0.7, 1.0):
        if free(x, 10.5 + dy, 0.25, 'GND', 0.2): via('GND', x, 10.5 + dy, locked=False); break
    x += 2.0
for gx in [2 + 4 * i for i in range(21)]:
    for gy in [12 + 4 * j for j in range(11)]:
        inside_coil = math.hypot(gx - 68.05, gy - 38.98) < 13.6
        if inside_coil or (52.0 < gx < 84 and gy < 26.5) or gy < 10.8: continue
        if free(gx, gy, 0.25, 'GND', 0.3): via('GND', gx, gy, locked=False)
print('vias', len(VIAS), 'hand tracks', len(TRK))

STACKUP = """		(stackup
			(layer "F.SilkS" (type "Top Silk Screen"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01) (epsilon_r 3.8))
			(layer "F.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 1" (type "prepreg") (thickness 0.0994) (material "3313") (epsilon_r 4.1) (loss_tangent 0.02))
			(layer "In1.Cu" (type "copper") (thickness 0.0152))
			(layer "dielectric 2" (type "core") (thickness 0.4808) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
			(layer "In2.Cu" (type "copper") (thickness 0.0152))
			(layer "dielectric 3" (type "prepreg") (thickness 0.0994) (material "3313") (epsilon_r 4.1) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness 0.035))
			(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01) (epsilon_r 3.8))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen"))
			(copper_finish "ENIG")
			(dielectric_constraints no)
		)
"""
# JLC 0.8 mm 4-layer: 1 oz outer, 0.5 oz inner, 3313 outer prepregs (jlcpcb.com/impedance); core = 0.8 mm minus the rest
# (JLC's own diagrams don't always sum to the header thickness: confirm the core with JLC at order time).
# ENIG: JLC requires ENIG/OSP for small vias; also flatter for the 0.4 mm BGA.

if __name__ == '__main__':
    pcbnew.SaveBoard(PCB, board)
    _t = open(PCB).read()
    assert '(stackup' not in _t
    _t = _t.replace('\t(setup\n', '\t(setup\n' + STACKUP, 1); open(PCB, 'w').write(_t)
    print(f'RF 50 ohm GCPW: w={RF_W} mm, gap={RF_GAP}, h={RF_H}, er={RF_ER} -> '
          f'{gcpw_z(RF_W, RF_GAP, RF_H, RF_ER)[0]:.1f} ohm; pin31 at ({ax:.2f},{ay:.2f}); '
          f'footprints {len(FP)}; nets {len(nets)}')
