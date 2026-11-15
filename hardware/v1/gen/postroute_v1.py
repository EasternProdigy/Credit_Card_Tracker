#!/usr/bin/env python3
"""Post-route fix for v1 (run after route_best.py): every GND pour fragment with no GND via gets one.
For each such fragment, try via spots around the GND pad inside it (0.5/0.25 via, short F.Cu stub),
keep the first spot that clears all other-net copper on every layer (0.15 mm, holes 0.2 mm), then refill.
With --preroute (run between gen_pcb.py and route_best.py) it instead gives a locked via to every small-part
GND pad that has no GND via within 1.0 mm, so Freerouting routes around it.
Usage: python3 gen/postroute_v1.py [--preroute]"""
import math, os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__)); PCB = os.path.join(HERE, '..', 'card_v1.kicad_pcb')
mm, M = pcbnew.FromMM, pcbnew.ToMM
CLR, HCLR = mm(0.15), mm(0.2)
b = pcbnew.LoadBoard(PCB); gnd = b.FindNet('GND')
CU = [l for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)]

def others(layer, netcode=None):
    nc = gnd.GetNetCode() if netcode is None else netcode
    for t in b.GetTracks():
        if t.GetNetCode() != nc and t.IsOnLayer(layer): yield t
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() != nc and p.IsOnLayer(layer): yield p

def clear(item, layers, skip=None):
    nc = item.GetNetCode()
    for l in layers:
        s = item.GetEffectiveShape(l)
        for o in others(l, nc):
            if o.GetEffectiveShape(l).Collide(s, CLR): return False
    if item.GetClass() == 'PCB_VIA':
        h = item.GetEffectiveHoleShape()
        for l in CU:
            for o in others(l, nc):
                if o.GetEffectiveShape(l).Collide(h, HCLR): return False
    return True

def gnd_vias(): return [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetCode() == gnd.GetNetCode()]

def in_via_keepout(v):
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias():
            for l in CU:
                if z.IsOnLayer(l) and z.Outline().Collide(v.GetEffectiveShape(l), mm(0.05)): return True
    return False

def link_to_via(p, locked=True):
    """No room for a new via: run a straight F.Cu link to the nearest GND via or neighbor GND pad, if it clears."""
    pc = p.GetPosition()
    tg = [v.GetPosition() for v in gnd_vias()] + [q.GetPosition() for f in b.GetFootprints() for q in f.Pads()
          if q.GetNetCode() == gnd.GetNetCode() and q.IsOnLayer(pcbnew.F_Cu) and q.GetParentFootprint() != p.GetParentFootprint()]
    for tp in sorted(tg, key=lambda q: (q - pc).EuclideanNorm()):
        if (tp - pc).EuclideanNorm() > mm(1.3): break
        t = pcbnew.PCB_TRACK(b); t.SetStart(pc); t.SetEnd(tp); t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd)
        if clear(t, [pcbnew.F_Cu]):
            t.SetLocked(locked); b.Add(t); return (p.GetParentFootprint().GetReference(), 'linked')
    return None

def place_near(p, locked=False):
    pc = p.GetPosition()
    for d in (0.5, 0.6, 0.7, 0.85, 1.0, 1.2):
        for a in range(0, 360, 15):
            pos = pcbnew.VECTOR2I(pc.x + mm(d * math.cos(math.radians(a))), pc.y + mm(d * math.sin(math.radians(a))))
            v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetWidth(mm(0.5)); v.SetDrill(mm(0.25)); v.SetNet(gnd)
            t = pcbnew.PCB_TRACK(b); t.SetStart(pc); t.SetEnd(pos); t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd)
            if clear(v, CU) and clear(t, [pcbnew.F_Cu]) and not in_via_keepout(v):
                v.SetLocked(locked); t.SetLocked(locked); b.Add(v); b.Add(t)
                return (p.GetParentFootprint().GetReference(), round(M(pos.x), 2), round(M(pos.y), 2))
    return None

ESCAPES = [('U5', '17'), ('U5', '37'), ('U5', '39'), ('U5', '41')]   # dev I/O pins: 0.3/0.15 escape via + stub

def escape(ref, num):
    """0.3/0.15 via just outside a QFN pad, outward from the IC, with a short F.Cu stub; first spot that clears."""
    f = b.FindFootprintByReference(ref); p = [q for q in f.Pads() if q.GetNumber() == num][0]
    c, pc = f.GetPosition(), p.GetPosition()
    d = pc - c; ax = abs(d.x) > abs(d.y)                                   # pad on a left/right side?
    out = pcbnew.VECTOR2I((1 if d.x > 0 else -1) if ax else 0, 0 if ax else (1 if d.y > 0 else -1))
    lat = pcbnew.VECTOR2I(0, 1) if ax else pcbnew.VECTOR2I(1, 0)
    start = pcbnew.VECTOR2I(pc.x + out.x * mm(0.3), pc.y + out.y * mm(0.3))
    for o in (0.75, 0.85, 1.0, 1.2, 1.4, 1.7, 2.0):
        for l in (0, 0.2, -0.2, 0.4, -0.4, 0.6, -0.6, 0.8, -0.8):
            pos = pcbnew.VECTOR2I(pc.x + out.x * mm(o) + lat.x * mm(l), pc.y + out.y * mm(o) + lat.y * mm(l))
            v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetWidth(mm(0.3)); v.SetDrill(mm(0.15)); v.SetNet(p.GetNet())
            mid = pcbnew.VECTOR2I(pc.x + out.x * mm(o - 0.25 if l else o), pc.y + out.y * mm(o - 0.25 if l else o))
            segs = []
            for a_, b_ in ((start, mid), (mid, pos)):
                if a_ == b_: continue
                t = pcbnew.PCB_TRACK(b); t.SetStart(a_); t.SetEnd(b_); t.SetWidth(mm(0.15)); t.SetLayer(pcbnew.F_Cu); t.SetNet(p.GetNet()); segs.append(t)
            ok = clear(v, CU) and not in_via_keepout(v) and all(clear(t, [pcbnew.F_Cu], skip=f) for t in segs)
            if ok:
                for it in [v] + segs: it.SetLocked(True); b.Add(it)
                return (ref + '.' + num, round(M(pos.x), 2), round(M(pos.y), 2))
    return ('NO ESCAPE', ref + '.' + num)

if '--preroute' in sys.argv:
    print('escape vias:', [escape(r, n) for r, n in ESCAPES])
    SKIP = ('U', 'J', 'BT', 'AE')
    added = []
    for f in b.GetFootprints():
        if f.GetReference().startswith(SKIP) or f.GetReference() in ('C25', 'C26'): continue   # C25/C26: Nordic Fig. 180 ground rules
        for p in f.Pads():
            if p.GetNetCode() != gnd.GetNetCode(): continue
            pc = p.GetPosition()
            if any((v.GetPosition() - pc).EuclideanNorm() < mm(1.0) for v in gnd_vias()): continue
            r = place_near(p, locked=True) or link_to_via(p); added.append(r or ('NO SPOT', f.GetReference()))
    for i, r in enumerate(added):
        if r[0] == 'NO SPOT':
            f = b.FindFootprintByReference(r[1])
            added[i] = link_to_via([p for p in f.Pads() if p.GetNetCode() == gnd.GetNetCode()][0]) or r
    pcbnew.SaveBoard(PCB, b); print('pre-route GND vias:', added); sys.exit()

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
added = []
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu): continue
    fp = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(fp.OutlineCount()):
        if any(fp.Contains(v.GetPosition(), i) for v in gnd_vias()): continue
        pads = [p for f in b.GetFootprints() for p in f.Pads()
                if p.GetNetCode() == gnd.GetNetCode() and p.IsOnLayer(pcbnew.F_Cu) and fp.Contains(p.GetPosition(), i)]
        for p in pads:
            r = place_near(p)
            if r: added.append(r); break
        else:
            if pads: print('no via spot for fragment with', [p.GetParentFootprint().GetReference() for p in pads])
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print('GND vias added:', added)
