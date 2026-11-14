#!/usr/bin/env python3
"""Compare a KiCad netlist export (schematic) against design.py, pin by pin."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sexp, design as D
nl = sexp.parse(open(sys.argv[1]).read())
got = {}
for net in sexp.find(sexp.first(nl, 'nets'), 'net'):
    name = sexp.first(net, 'name')[1].split('/')[-1]
    for n in sexp.find(net, 'node'):
        ref, pin = sexp.first(n, 'ref')[1], sexp.first(n, 'pin')[1]
        got[(ref, pin)] = None if name.startswith('unconnected-') else name
bad = 0
for c in D.C:
    for pin, net in c['pins'].items():
        g = got.get((c['ref'], pin), 'MISSING')
        if g != net and not (net is None and g in (None, 'MISSING')):
            print('MISMATCH', c['ref'], pin, 'want', net, 'got', g); bad += 1
print('pins checked:', sum(len(c['pins']) for c in D.C), 'mismatches:', bad)
sys.exit(1 if bad else 0)
