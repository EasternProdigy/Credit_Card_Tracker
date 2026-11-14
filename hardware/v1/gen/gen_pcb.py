#!/usr/bin/env python3
"""Build hardware/v1/card_v1.kicad_pcb from design.py: outline, footprints + nets (linked to the
schematic by deterministic UUIDs), placement, keepouts, design rules (JLC 2-layer), critical hand-routes.
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

# ---------------------------------------------------------------- 50 ohm GCPW (0.4 mm FR4)
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
RF_GAP, RF_H, RF_ER = 0.15, 0.33, 4.5   # JLC 0.4 mm 2-layer: ~0.33 mm dielectric, er ~4.5
RF_W = min((round(w, 2) for w in [x / 100 for x in range(20, 80)]),
           key=lambda w: abs(gcpw_z(w, RF_GAP, RF_H, RF_ER)[0] - 50))

# ---------------------------------------------------------------- board + rules
board = pcbnew.NewBoard(PCB)
ds = board.GetDesignSettings()
ds.SetBoardThickness(mm(0.4))
ds.m_TrackMinWidth = mm(0.1); ds.m_MinClearance = mm(0.1); ds.m_ViasMinSize = mm(0.45)
ds.m_MinThroughDrill = mm(0.2); ds.m_HoleClearance = mm(0.2); ds.m_CopperEdgeClearance = mm(0.3)
ds.m_HoleToHoleMin = mm(0.25); ds.m_ViasMinAnnularWidth = mm(0.1)
nc = ds.m_NetSettings
dflt = nc.GetDefaultNetclass()
dflt.SetClearance(mm(0.12)); dflt.SetTrackWidth(mm(0.15)); dflt.SetViaDiameter(mm(0.5)); dflt.SetViaDrill(mm(0.25))
CLASSES = {
    'QI_AC': (0.4, 0.15, ['AC1', 'AC2', 'COIL1']),
    'PWR': (0.3, 0.12, ['VRECT', 'V5_RX', 'V5_CHG', 'VCHG', 'VCELL', 'VBAT', 'BT_NEG', 'VDD_3V3', 'VDD_NRF', 'DCC', 'DECD']),
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
    f.SetReference(c['ref']); f.SetValue(c['value'])
    f.SetPath(pcbnew.KIID_PATH(f"/{GS.U('sheet', c['sheet'])}/{GS.U('sym', c['ref'])}"))
    f.SetSheetname(c['sheet']); f.SetSheetfile(c['sheet'] + '.kicad_sch')
    if c['dnp']: f.SetDNP(True)
    for k, v in (('MPN', c['mpn']), ('LCSC', lcsc.get(c['ref'], ''))):
        if v:
            f.SetField(k, v); f.GetField(k).SetVisible(False)
    padnames = {p.GetNumber() for p in f.Pads()}
    for pin, n in c['pins'].items():
        if pin not in padnames:
            raise SystemExit(f"{c['ref']}: pin {pin} has no pad in {c['fp']}")
    for p in f.Pads():
        n = c['pins'].get(p.GetNumber())
        if n: p.SetNet(net(n))
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
P('C25', sx + 1.1, node(0), 'W')     # RF_A shunt, ground pad toward pin 32 (top layer only)
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
P('R7', 56.9, 15.95, 'E')             # pin 30 side = pad 1 (nRESET_IC)
P('C31', 56.9, 15.05, 'E')
# right side: DC/DC + DEC (pins 43..48 at x 61.35, y 20.0..22.0)
P('C21', 62.45, 22.25, 'W')          # VDD 48
P('C18', 62.45, 21.35, 'W')          # DECD
P('FB1', 62.45, 20.6, 'W')           # DECD -> DECA
P('C19', 62.45, 19.85, 'W')          # DECA
P('C24', 62.45, 19.1, 'W')
P('C30', 62.45, 18.35, 'W')
P('L2', 64.15, 21.1, 'N')            # DCC (top) -> DECD (bottom)
P('C17', 63.25, 23.75, 'S')          # 10 uF VDD 47/48
# top: VDD 10, NFC (DNP), 32 kHz
P('C20', 56.85, 23.85, 'S')
P('C34', 57.95, 24.35, 'S'); P('C33', 58.95, 24.35, 'S')
P('Y2', 60.95, 24.4, 0)
# left: VDD 22
P('C22', 54.4, 18.4, 'E')
P('JP6', 53.3, 13.9, 'N'); P('JP5', 53.3, 11.8, 'N')

# Qi receiver
P('L1', 68.05, 38.98 - 15.0, 0)      # lands at (66.05 / 70.05, 23.98)
for i, ref in enumerate(['C1a', 'C1b', 'C1c', 'C1d']):
    P(ref, 65.85 + i * 1.55, 20.0, 'N')       # COIL1 on top
for i, ref in enumerate(['C2a', 'C2b', 'C2c']):
    P(ref, 65.85 + i * 1.55, 15.6, 'N')       # AC1 on top
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
P('JP1', 82.3, 19.2, 'N')
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
def resolve(maxmove=0.5):
    """Only small-vs-big overlaps: push the small part straight away from the big one, at most maxmove."""
    report = []
    for r in FP:
        if BIG(r): continue
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
rule_area('ANT_KEEPOUT', [(52.5, 2.0), (83.6, 2.0), (83.6, 9.5), (52.5, 9.5)], pour=True, tracks=True, vias=True)
# coil: no copper on any layer inside D26, except its lands (lands sit outside the circle)
rule_area('COIL_KEEPOUT', circle_pts(68.05, 38.98, 13.0), tracks=True, vias=True, pour=True)
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
pour('B.Cu', card_pts); pour('F.Cu', card_pts)

if __name__ == '__main__':
    pcbnew.SaveBoard(PCB, board)
    print(f'RF 50 ohm GCPW: w={RF_W} mm, gap={RF_GAP}, h={RF_H}, er={RF_ER} -> '
          f'{gcpw_z(RF_W, RF_GAP, RF_H, RF_ER)[0]:.1f} ohm; pin31 at ({ax:.2f},{ay:.2f}); '
          f'footprints {len(FP)}; nets {len(nets)}')
