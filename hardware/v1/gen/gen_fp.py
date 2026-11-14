#!/usr/bin/env python3
"""Custom footprints for v1 (sources in each docstring). Writes lib/wallet_tracker.pretty and the symbol lib."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sexp import Sym as S, dump
OUT = os.path.join(HERE, '..', 'lib', 'wallet_tracker.pretty')

def fp(name, descr, items, attr='smd', extra=None):
    doc = [S('footprint'), name, [S('version'), 20241229], [S('generator'), 'gen_fp.py'], [S('layer'), 'F.Cu'],
           [S('descr'), descr], [S('attr'), S(attr)]] + (extra or [])
    doc += [[S('property'), 'Reference', 'REF**', [S('at'), 0, -1.5, 0], [S('layer'), 'F.SilkS'],
             [S('effects'), [S('font'), [S('size'), 0.5, 0.5], [S('thickness'), 0.08]]]],
            [S('property'), 'Value', name, [S('at'), 0, 1.5, 0], [S('layer'), 'F.Fab'],
             [S('effects'), [S('font'), [S('size'), 0.5, 0.5], [S('thickness'), 0.08]]]]] + items
    open(os.path.join(OUT, name + '.kicad_mod'), 'w').write(dump(doc) + '\n')

def pad(num, shape, x, y, w, h, layers=('F.Cu', 'F.Paste', 'F.Mask'), extra=None):
    return [S('pad'), num, S('smd'), S(shape), [S('at'), x, y], [S('size'), w, h],
            [S('layers')] + list(layers)] + (extra or [])

def rect(layer, x1, y1, x2, y2, w=0.05):
    return [S('fp_rect'), [S('start'), x1, y1], [S('end'), x2, y2],
            [S('stroke'), [S('width'), w], [S('type'), S('solid')]], [S('fill'), S('no')], [S('layer'), layer]]

def line(layer, x1, y1, x2, y2, w):
    return [S('fp_line'), [S('start'), x1, y1], [S('end'), x2, y2],
            [S('stroke'), [S('width'), w], [S('type'), S('solid')]], [S('layer'), layer]]

def circle(layer, cx, cy, r, w=0.05):
    return [S('fp_circle'), [S('center'), cx, cy], [S('end'), cx + r, cy],
            [S('stroke'), [S('width'), w], [S('type'), S('solid')]], [S('fill'), S('no')], [S('layer'), layer]]

# ABLIC SNT-6A, land per PG006-A-L-SD-4.1: pads 0.30 x 0.52, pitch 0.5, rows 1.36 apart (inner edges).
yy = 0.68 + 0.26
items = [pad(str(n), 'rect', x, y, 0.30, 0.52) for n, x, y in
         ((1, -0.5, yy), (2, 0, yy), (3, 0.5, yy), (4, 0.5, -yy), (5, 0, -yy), (6, -0.5, -yy))]
items += [rect('F.Fab', -0.785, -0.8, 0.785, 0.8), rect('F.CrtYd', -1.0, -1.45, 1.0, 1.45),
          circle('F.SilkS', -1.05, 1.25, 0.06, 0.12)]
fp('ABLIC_SNT-6A', 'ABLIC SNT-6A, land PG006-A-L-SD-4.1, body 1.57x1.6x0.50 max (PG006-A-P-SD-2.1)', items)

# onsemi EFCP 4-bump, EFC4615R datasheet 7067-001: 1.46 sq, pitch 0.65, 0.37 tall. Top view: 1 BL, 2 BR, 3 TR, 4 TL.
h = 0.325
items = [pad(str(n), 'circle', x, y, 0.30, 0.30, extra=[[S('solder_mask_margin'), 0.03]]) for n, x, y in
         ((1, -h, h), (2, h, h), (3, h, -h), (4, -h, -h))]
items += [rect('F.Fab', -0.73, -0.73, 0.73, 0.73), rect('F.CrtYd', -0.95, -0.95, 0.95, 0.95),
          circle('F.SilkS', -0.95, 0.95, 0.06, 0.12)]
fp('onsemi_EFCP-4_1.46x1.46mm_P0.65mm', 'onsemi EFC4615R EFCP 4 bump, NSMD 0.30 pad (verify vs onsemi land)', items)

# Test pad 0.6 mm (RF feed: small to limit added capacitance)
fp('TestPoint_Pad_D0.6mm', 'Test pad 0.6 mm', [pad('1', 'circle', 0, 0, 0.6, 0.6, ('F.Cu', 'F.Mask')),
                                                circle('F.CrtYd', 0, 0, 0.55)])

# Battery tab lands, 2 x 3 mm, 5 mm pitch (hand solder; Grepow tab spacing to verify)
fp('Battery_Tabs_2x3mm', 'Cell tab lands 2x3 mm, 5 mm pitch',
   [pad('1', 'rect', -2.5, 0, 2.0, 3.0), pad('2', 'rect', 2.5, 0, 2.0, 3.0),
    rect('F.CrtYd', -3.75, -1.75, 3.75, 1.75), line('F.SilkS', -2.5, -2.0, -2.5, -2.4, 0.15)])

# Wurth 760308101309 coil: generic hand-solder lands (lead geometry NOT verified, O20).
cy = -15.0
fp('Wurth_760308101309_Lands', 'Wurth 760308101309 D26 Qi coil; lands generic 1.5x2.5, verify lead positions (O20)',
   [pad('1', 'rect', -2.0, 0, 1.5, 2.5), pad('2', 'rect', 2.0, 0, 1.5, 2.5),
    circle('F.Fab', 0, cy, 13.0, 0.1), circle('F.CrtYd', 0, cy, 13.25), rect('F.CrtYd', -3.0, -1.5, 3.0, 1.5)])

# Printed IFA, geometry from sims/antenna_floorplan.py: short at feed-3 mm, height 6 mm, arm 20 mm from feed, 0.5 mm trace.
# Origin = feed point on the ground edge; antenna extends +y (away from the ground).
W = 0.5
items = [pad('1', 'rect', 0, 0, W, W, ('F.Cu',)), pad('2', 'rect', -3.0, 0, W, W, ('F.Cu',)),
         line('F.Cu', 0, 0, 0, 6.0, W), line('F.Cu', -3.0, 0, -3.0, 6.0, W), line('F.Cu', -3.0, 6.0, 20.0, 6.0, W),
         rect('F.CrtYd', -3.5, -0.5, 20.5, 6.5), line('F.Fab', 15.0, 5.0, 23.0, 5.0, 0.05)]
fp('IFA_2G4_arm20_h6', 'Printed IFA 2.4 GHz, arm 20 mm (trim 19-24), feed-short 3 mm, h 6 mm, 0.5 mm', items,
   extra=[[S('net_tie_pad_groups'), '1, 2']])
print('footprints written')

# symbol library (same custom symbols as embedded in the schematic)
import gen_sch, design as D
syms = [gen_sch.custom_symbol(n) for n in D.CUSTOM_SYMBOLS]
lib = [S('kicad_symbol_lib'), [S('version'), 20251024], [S('generator'), 'gen_fp.py'], [S('generator_version'), '10.0']]
for s in syms:
    s[1] = s[1].split(':')[1]
    lib.append(s)
open(os.path.join(HERE, '..', 'lib', 'wallet_tracker.kicad_sym'), 'w').write(dump(lib) + '\n')
print('symbols written')
