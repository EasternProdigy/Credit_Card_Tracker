#!/usr/bin/env python3
"""Generate the v1 hierarchical schematic from design.py.

Connections are made with labels on short wire stubs at every pin (global labels for
nets that cross sheets, local labels otherwise). UUIDs are deterministic (uuid5), so the
PCB generator can link footprints to schematic symbols.
Usage: python3 -I hardware/v1/gen/gen_sch.py
"""
import csv, os, sys, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexp
from sexp import Sym as S, dump
import design as D

OUT = os.path.normpath(os.path.join(HERE, '..'))
NS = uuid.UUID('6f1c2a52-6a1e-4f0e-9a6c-1d1e5ac0c0a1')
U = lambda *k: str(uuid.uuid5(NS, '/'.join(k)))
ROOT_UUID = U('root')
G = 2.54
snap = lambda v: round(v / G) * G
FONT = [S('effects'), [S('font'), [S('size'), 1.27, 1.27]]]
HIDE = [S('hide'), S('yes')]

def lcsc_map():
    p = os.path.join(OUT, '..', '..', 'design', 'bom_v1_jlc.csv')
    m = {}
    if os.path.exists(p):
        for row in csv.DictReader(open(p)):
            for ref in row['Designator'].split(','):
                m[ref.strip()] = row.get('LCSC', '')
    return m

# ---------------------------------------------------------------- symbols
def custom_symbol(name):
    d = D.CUSTOM_SYMBOLS[name]
    sides = {k: [p for p in d['pins'] if p[3] == k] for k in 'LRTB'}
    namelen = max(len(p[1]) for p in d['pins'])
    nlr = max(len(sides['L']), len(sides['R']), 1)
    ntb = max(len(sides['T']), len(sides['B']), 0)
    w = max(snap(namelen * 1.27 * 2 + 5.08), snap((ntb + 1) * G), 10.16)
    h = snap((nlr + 1) * G)
    if w % (2 * G): w += G
    if h % (2 * G): h += G
    pins = []
    def pin(p, x, y, a):
        pins.append([S('pin'), S(p[2]), S('line'), [S('at'), x, y, a], [S('length'), G],
                     [S('name'), p[1], FONT], [S('number'), p[0], FONT]])
    for i, p in enumerate(sides['L']): pin(p, -w / 2 - G, h / 2 - G * (i + 1), 0)
    for i, p in enumerate(sides['R']): pin(p, w / 2 + G, h / 2 - G * (i + 1), 180)
    for i, p in enumerate(sides['B']): pin(p, -w / 2 + G * (i + 1), -h / 2 - G, 90)
    for i, p in enumerate(sides['T']): pin(p, -w / 2 + G * (i + 1), h / 2 + G, 270)
    full = 'wallet_tracker:' + name
    prop = lambda k, v, y, hide=False: [S('property'), k, v, [S('at'), 0, y, 0]] + ([HIDE] if hide else []) + [FONT]
    return [S('symbol'), full, [S('pin_names'), [S('offset'), 0.508]], [S('exclude_from_sim'), S('no')],
            [S('in_bom'), S('yes')], [S('on_board'), S('yes')],
            prop('Reference', d['ref'], h / 2 + 3.81), prop('Value', name, -h / 2 - 5.08),
            prop('Footprint', d['fp'], 0, True), prop('Datasheet', d['ds'], 0, True),
            prop('Description', name, 0, True),
            [S('symbol'), name + '_0_1', [S('rectangle'), [S('start'), -w / 2, h / 2], [S('end'), w / 2, -h / 2],
                                         [S('stroke'), [S('width'), 0.254], [S('type'), S('default')]],
                                         [S('fill'), [S('type'), S('background')]]]],
            [S('symbol'), name + '_1_1'] + pins]

_symcache = {}
def get_symbol(lib_id):
    if lib_id not in _symcache:
        lib, name = lib_id.split(':')
        if lib == 'custom':
            s = custom_symbol(name); full = 'wallet_tracker:' + name
        else:
            s = sexp.lib_symbol(lib, name); full = lib_id
            s = [S('symbol'), full] + s[2:]
        _symcache[lib_id] = (full, s, sexp.symbol_pins(s))
    return _symcache[lib_id]

# ---------------------------------------------------------------- nets
sheet_of_net = {}
for c in D.C:
    for n in c['pins'].values():
        if n: sheet_of_net.setdefault(n, set()).add(c['sheet'])
for sh, nets in D.PWR_FLAGS.items():
    for n in nets: sheet_of_net.setdefault(n, set()).add(sh)
is_global = lambda n: True   # all nets global: PCB net names match exactly (no sheet-path prefixes)

def label(net, x, y, ang):
    just = {0: 'left', 180: 'right', 90: 'left', 270: 'right'}[ang]
    eff = [S('effects'), [S('font'), [S('size'), 1.27, 1.27]], [S('justify'), S(just)]]
    if is_global(net):
        return [S('global_label'), net, [S('shape'), S('passive')], [S('at'), x, y, ang],
                [S('fields_autoplaced'), S('yes')], eff, [S('uuid'), U('gl', net, str(x), str(y))]]
    return [S('label'), net, [S('at'), x, y, ang], [S('fields_autoplaced'), S('yes')], eff,
            [S('uuid'), U('ll', net, str(x), str(y))]]

def wire(x1, y1, x2, y2):
    return [S('wire'), [S('pts'), [S('xy'), x1, y1], [S('xy'), x2, y2]],
            [S('stroke'), [S('width'), 0], [S('type'), S('default')]], [S('uuid'), U('w', str(x1), str(y1), str(x2), str(y2))]]

# ---------------------------------------------------------------- placement
def bbox(pins):
    xs = [p[2] for p in pins] + [0]; ys = [p[3] for p in pins] + [0]
    return min(xs), max(xs), min(ys), max(ys)

def build_sheet(sheet, comps, lcsc, page_w=400):
    items, used = [], {}
    x0, y0, x, y, rowh = 15.24, 25.4, 15.24, 25.4, 0
    flags = [dict(ref=f'#FLG_{sheet}_{n}', sym='power:PWR_FLAG', pins={'1': n}, flag=True)
             for n in D.PWR_FLAGS.get(sheet, [])]
    for c in comps + flags:
        full, sdef, pins = get_symbol(c['sym'])
        used[full] = sdef
        nx0, nx1, ny0, ny1 = bbox(pins)
        maxlab = max([len(n or '') for n in c['pins'].values()] + [4]) * 1.0 + 6
        cw = (nx1 - nx0) + 2 * (G * 2 + maxlab) + 12
        ch = (ny1 - ny0) + 2 * (G * 2 + 3) + 10
        if x + cw > page_w:
            x, y, rowh = x0, y + rowh, 0
        sx = snap(x + G * 2 + maxlab - nx0 + 4); sy = snap(y + G * 2 + 6 + ny1)
        x += cw; rowh = max(rowh, ch)
        seen = set()
        for num, name, px, py, ang, ln, typ in pins:
            ax, ay = sx + px, sy - py
            if (ax, ay) in seen: continue
            seen.add((ax, ay))
            if num not in c['pins']:
                raise SystemExit(f"{c['ref']}: pin {num} ({name}) not mapped")
            net = c['pins'][num]
            if net is None:
                items.append([S('no_connect'), [S('at'), ax, ay], [S('uuid'), U('nc', c['ref'], num)]])
                continue
            dx, dy, la = {0: (-G, 0, 180), 180: (G, 0, 0), 90: (0, G, 270), 270: (0, -G, 90)}[int(ang)]
            items.append(wire(ax, ay, ax + dx, ay + dy))
            items.append(label(net, ax + dx, ay + dy, la))
        ref = c['ref']
        props = [[S('property'), 'Reference', ref, [S('at'), sx + nx1 + 1.27, sy + ny0 - 2.54, 0],
                  [S('effects'), [S('font'), [S('size'), 1.27, 1.27]], [S('justify'), S('left')]]]]
        if c.get('flag'):
            props[0] = [S('property'), 'Reference', ref, [S('at'), sx, sy + 2, 0], HIDE, FONT]
            props += [[S('property'), 'Value', 'PWR_FLAG', [S('at'), sx, sy - 3.81, 0], FONT],
                      [S('property'), 'Footprint', '', [S('at'), sx, sy, 0], HIDE, FONT],
                      [S('property'), 'Datasheet', '', [S('at'), sx, sy, 0], HIDE, FONT]]
        else:
            fp = c['fp'] or D.CUSTOM_SYMBOLS[c['sym'].split(':')[1]]['fp']
            c['fp'] = fp
            props += [[S('property'), 'Value', c['value'], [S('at'), sx + nx1 + 1.27, sy + ny0 - 0.0, 0],
                       [S('effects'), [S('font'), [S('size'), 1.27, 1.27]], [S('justify'), S('left')]]],
                      [S('property'), 'Footprint', fp, [S('at'), sx, sy, 0], HIDE, FONT],
                      [S('property'), 'Datasheet', '', [S('at'), sx, sy, 0], HIDE, FONT]]
            for k in ('mpn', 'src'):
                props.append([S('property'), {'mpn': 'MPN', 'src': 'Source'}[k], c[k] or '',
                              [S('at'), sx, sy, 0], HIDE, FONT])
            props.append([S('property'), 'LCSC', lcsc.get(ref, ''), [S('at'), sx, sy, 0], HIDE, FONT])
        dnp = bool(c.get('dnp'))
        sym = [S('symbol'), [S('lib_id'), full], [S('at'), sx, sy, 0], [S('unit'), 1],
               [S('exclude_from_sim'), S('no')], [S('in_bom'), S('no' if (c.get('flag') or c['sym'] == 'Connector:TestPoint' or dnp or ref in D.NOFAB) else 'yes')],
               [S('on_board'), S('no' if c.get('flag') else 'yes')], [S('dnp'), S('yes' if dnp else 'no')],
               [S('uuid'), U('sym', ref)]] + props
        for num in sorted({p[0] for p in pins}):
            sym.append([S('pin'), num, [S('uuid'), U('pin', ref, num)]])
        sym.append([S('instances'), [S('project'), D.PROJECT,
                    [S('path'), f'/{ROOT_UUID}/{U("sheet", sheet)}', [S('reference'), ref], [S('unit'), 1]]]])
        items.append(sym)
    return used, items, y + rowh

def write_sheet(path, uid, used, items, title, paper='A3'):
    doc = [S('kicad_sch'), [S('version'), 20260306], [S('generator'), 'eeschema'],
           [S('generator_version'), '10.0'], [S('uuid'), uid], [S('paper'), paper],
           [S('title_block'), [S('title'), title], [S('company'), 'Wallet tracker card v1'],
            [S('comment'), 1, 'Generated by hardware/v1/gen/gen_sch.py from design.py; do not hand-edit']],
           [S('lib_symbols')] + list(used.values())] + items
    if path.endswith(D.PROJECT + '.kicad_sch'):
        doc.append([S('sheet_instances'), [S('path'), '/', [S('page'), '1']]])
    doc.append([S('embedded_fonts'), S('no')])
    open(path, 'w').write(dump(doc) + '\n')

def main():
    lcsc = lcsc_map()
    sheets = []
    for i, (stem, title) in enumerate(D.SHEETS):
        comps = [c for c in D.C if c['sheet'] == stem]
        used, items, h = build_sheet(stem, comps, lcsc)
        paper = 'A2' if h > 270 else 'A3'
        write_sheet(os.path.join(OUT, stem + '.kicad_sch'), U('sheetfile', stem), used, items, title, paper)
        sheets.append((stem, title, i + 2))
    root_items = []
    for k, (stem, title, page) in enumerate(sheets):
        x, y = 25.4 + (k % 4) * 90, 40 + (k // 4) * 50
        root_items.append([S('sheet'), [S('at'), x, y], [S('size'), 76.2, 30.48],
            [S('fields_autoplaced'), S('yes')],
            [S('stroke'), [S('width'), 0.1524], [S('type'), S('solid')]], [S('fill'), [S('color'), 0, 0, 0, 0]],
            [S('uuid'), U('sheet', stem)],
            [S('property'), 'Sheetname', title, [S('at'), x, y - 0.7, 0],
             [S('effects'), [S('font'), [S('size'), 1.27, 1.27]], [S('justify'), S('left'), S('bottom')]]],
            [S('property'), 'Sheetfile', stem + '.kicad_sch', [S('at'), x, y + 31.1, 0],
             [S('effects'), [S('font'), [S('size'), 1.27, 1.27]], [S('justify'), S('left'), S('top')]]],
            [S('instances'), [S('project'), D.PROJECT, [S('path'), f'/{ROOT_UUID}', [S('page'), str(page)]]]]])
    for k, line in enumerate(['Wallet tracker card v1 (bring-up dev board). Nets connect by global labels across sheets.',
                              'Source of truth: hardware/v1/gen/design.py. Pin maps: design/pinmaps/.']):
        root_items.append([S('text'), line, [S('at'), 25.4, 20 + 4 * k, 0],
                           [S('effects'), [S('font'), [S('size'), 2, 2]], [S('justify'), S('left')]],
                           [S('uuid'), U('roottext', str(k))]])
    write_sheet(os.path.join(OUT, D.PROJECT + '.kicad_sch'), ROOT_UUID, {}, root_items,
                'Wallet tracker card v1', 'A4')
    print('sheets written:', [s[0] for s in sheets], 'components:', len(D.C))

if __name__ == '__main__':
    main()
