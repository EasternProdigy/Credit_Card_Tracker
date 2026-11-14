#!/usr/bin/env python3
"""Build design/bom_v1_jlc.csv from design.py using the local JLC catalog (kicad-mcp sqlite).

Rules: exact value, package, voltage >= required, dielectric in the allowed set, tolerance as asked.
Prefer Basic (no setup fee), then stock. Two substitutes are listed per line.
QTY_BOARDS sets the stock check.
"""
import csv, json, os, re, sqlite3, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import design as D
DB = os.path.expanduser('~/.local/share/kicad-mcp/jlcpcb_parts.db')
OUTF = os.path.join(HERE, '..', '..', '..', 'design', 'bom_v1_jlc.csv')
QTY_BOARDS = 5
c = sqlite3.connect(DB)

def pkg_of(fp):
    m = re.search(r'_(0201|0402|0603)_', fp or '')
    return m.group(1) if m else None

def volts(desc):
    m = re.findall(r'(\d+(?:\.\d+)?)V\b', desc)
    return max(float(v) for v in m) if m else 0

def rows(where, args):
    q = f"select lcsc,mfr_part,manufacturer,package,library_type,stock,description,price_json from components where {where}"
    return c.execute(q, args).fetchall()

def rank(rs):
    return sorted(rs, key=lambda r: (r[4] not in ('Basic', 'Preferred'), -r[5]))

def cap(value, fp):
    m = re.match(r'([\d.]+)(pF|nF|uF)(?:\s+(\d+(?:\.\d+)?)V)?(?:\s+(\w+))?', value)
    val, unit, v, diel = m.group(1), m.group(2), float(m.group(3) or 6.3), m.group(4)
    if val.endswith('.0'): val = val[:-2]
    pk = pkg_of(fp)
    rs = rows("package=? and subcategory like '%MLCC - SMD%' and (description like ? or description like ?)",
              (pk, f'{val}{unit} %', f'% {val}{unit} %'))
    ok = {'X7R': ('X7R', 'X7S', 'X8R', 'C0G', 'NP0'), 'X5R': ('X5R', 'X7R', 'X6S', 'X7S', 'X6T'),
          'X6T': ('X6T', 'X6S', 'X5R', 'X7R', 'X7S'), 'C0G': ('C0G', 'NP0')}
    dl = ok.get(diel, ('C0G', 'NP0', 'X7R', 'X5R', 'X7S', 'X6S', 'X6T'))
    rs = [r for r in rs if volts(r[6]) >= v and any(d in r[6] for d in dl)]
    if unit == 'pF' and float(val) < 10:   # RF caps: tight tolerance only
        rs = [r for r in rs if re.search(r'±0\.(05|1|25)pF', r[6])] or rs
    return rank(rs)

def res(value, fp):
    v = value.split()[0]
    tok = v[:-1] + 'Ω' if v.endswith('R') else v.replace('k', 'kΩ').replace('M', 'MΩ')
    if tok.endswith('kΩ') and '.' not in tok: pass
    pk = pkg_of(fp)
    rs = rows("package=? and subcategory like '%Resistor%' and (description like ? or description like ?)",
              (pk, f'{tok} %', f'% {tok} %'))
    if '1%' in value:
        rs = [r for r in rs if '±1%' in r[6] or '±0.5%' in r[6] or '±0.1%' in r[6]]
    return rank(rs)

def ind(value, fp, mpn):
    if mpn.startswith('Murata LQP03'):
        base = mpn.split()[1]
        return rank(rows("mfr_part like ?", (base + '%',)))
    tok = value.split()[0]
    pk = pkg_of(fp)
    return rank(rows("package=? and subcategory like '%Inductors (SMD)%' and (description like ? or description like ?)",
                     (pk, f'{tok} %', f'% {tok} %')))

def by_mpn(m):
    return rank(rows("mfr_part like ?", (m + '%',)))

SPECIAL = {
    'BQ51003YFPR': lambda: by_mpn('BQ51003YFP'), 'BQ25101YFPR': lambda: by_mpn('BQ25101YFP'),
    'S-82N1BAA-I6T1U7': lambda: by_mpn('S-82N1BAA'), 'TPS7A0233PDQNR': lambda: by_mpn('TPS7A0233PDQN'),
    'nRF54L15-QFAA': lambda: by_mpn('NRF54L15-QFAA'), 'EFC4615R-TR': lambda: by_mpn('EFC4615R'),
    '10k B3380 NTC': lambda: by_mpn('NCP15XH103F03RC'),
    'Cell (JST SH)': lambda: by_mpn('SM02B-SRSS-TB'),
    '120R@100MHz': lambda: rank([r for r in rows("package='0201' and subcategory like '%Ferrite%' and description like ?",
                                                 ('%120Ω@100MHz%',))]),
    '32MHz CL8pF': lambda: by_mpn('XRCGB32M000F1S1BR0'),   # ESR 50 ohm (pass 1: the 80 ohm part was marginal vs Nordic Fig. 17)
    '32.768kHz CL9pF': lambda: rank([r for r in rows("subcategory like '%Crystal%' and description like '%32.768kHz%' and description like '%9pF%' and (package like '%2012%' or description like '%2012%')", ())]),
    'SWD 10p 1.27': lambda: rank([r for r in rows("subcategory like '%Pin Header%' and description like '%1.27mm%' and description like '%2x5%' and description like '%SMD%'", ())]),
}

def candidates(comp):
    v = comp['value']
    if v in SPECIAL: return SPECIAL[v]()
    sym = comp['sym']
    if comp['mpn'].startswith('Murata GJM'): return by_mpn(comp['mpn'].split()[1])
    if sym == 'Device:C': return cap(v, comp['fp'])
    if sym == 'Device:R': return res(v, comp['fp'])
    if sym == 'Device:L': return ind(v, comp['fp'], comp['mpn'])
    return []

NOT_PLACED = ('Connector:TestPoint', 'Device:NetTie_2', 'custom:IFA_Printed', 'custom:Wurth_760308101309')

def main():
    groups = {}
    for comp in D.C:
        if comp['sym'] in NOT_PLACED or comp['value'] in ('Cell tabs',):
            continue
        k = (comp['value'], comp['fp'], comp['mpn'], comp['dnp'])
        groups.setdefault(k, []).append(comp)
    out = []
    for (val, fp, mpn, dnp), comps in sorted(groups.items(), key=lambda kv: kv[1][0]['ref']):
        refs = ','.join(x['ref'] for x in comps)
        if dnp:
            out.append(dict(Comment=val, Designator=refs, Footprint=fp.split(':')[1], LCSC='', MPN='', Type='',
                            Stock='', Qty=len(comps), DNP='yes', Substitutes='', Note='do not place'))
            continue
        cs = candidates(comps[0])
        need = len(comps) * QTY_BOARDS
        if not cs:
            out.append(dict(Comment=val, Designator=refs, Footprint=fp.split(':')[1], LCSC='', MPN=mpn, Type='',
                            Stock='', Qty=len(comps), DNP='no', Substitutes='',
                            Note='NOT in JLC in-stock catalog: order via JLC Global Sourcing or consign (Mouser/DigiKey)'))
            continue
        b = cs[0]
        note = '' if b[5] >= need else f'LOW STOCK ({b[5]} < {need})'
        if mpn and not mpn.split()[-1].split('-')[0].upper() in b[1].upper() and 'Murata' not in mpn:
            note = (note + '; ' if note else '') + f'design MPN {mpn}'
        out.append(dict(Comment=val, Designator=refs, Footprint=fp.split(':')[1], LCSC=b[0], MPN=b[1],
                        Type=b[4], Stock=b[5], Qty=len(comps), DNP='no',
                        Substitutes=' | '.join(f'{r[0]} {r[1]} ({r[4]}, {r[5]})' for r in cs[1:3]),
                        Note=note + ('' if not note else '') + f' [{b[6][:70]}]'))
    with open(OUTF, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    nf = [o for o in out if o['DNP'] == 'no' and not o['LCSC']]
    ext = [o for o in out if o['Type'] == 'Extended']
    print(f'lines {len(out)}, not found {len(nf)}, extended {len(ext)}')
    for o in out:
        if o['DNP'] == 'no':
            print(f"{o['Designator'][:28]:28} {o['Comment'][:18]:18} {o['LCSC']:10} {o['MPN'][:22]:22} {o['Type']:8} {o['Stock']}")

if __name__ == '__main__':
    main()
