#!/usr/bin/env python3
"""Freerouting round trip for v1: export DSN (GND removed: it is carried by the pours + vias),
run Freerouting, import the SES, fill zones, save. Usage: python3 gen/route_v1.py [passes]"""
import os, re, subprocess, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__)); V1 = os.path.join(HERE, '..')
PCB = os.path.join(V1, 'card_v1.kicad_pcb'); DSN = os.path.join(V1, 'route', 'card_v1.dsn'); SES = DSN[:-3] + 'ses'
JAR = os.path.expanduser('~/tools/freerouting-2.5.0.jar')
os.makedirs(os.path.dirname(DSN), exist_ok=True)
passes = sys.argv[1] if len(sys.argv) > 1 else '40'
b = pcbnew.LoadBoard(PCB)
assert pcbnew.ExportSpecctraDSN(b, DSN)
t = open(DSN).read()
t = re.sub(r'\(net GND\s*\(pins[^)]*\)\s*\)', '', t)           # do not autoroute GND
t = re.sub(r'(\(class \S+[^()]*?)\bGND\b', r'\1', t)
t = re.sub(r'\(via ("Via\[0-\d\]_500:250_um") "Via\[0-\d\]_250:150_um"\)', r'(via \1)', t)  # small via: U1 only (pre-placed)
open(DSN, 'w').write(t)
extra = sys.argv[2:] if len(sys.argv) > 2 else []
log = subprocess.run(['java', '-jar', JAR, '-de', DSN, '-do', SES, '-mp', passes, '-mt', '8'] + extra,
                     capture_output=True, text=True, timeout=3000)
open(os.path.join(V1, 'route', 'freerouting.log'), 'w').write(log.stdout[-20000:] + log.stderr[-5000:])
assert os.path.exists(SES), 'no SES written; see route/freerouting.log'
b = pcbnew.LoadBoard(PCB)
assert pcbnew.ImportSpecctraSES(b, SES)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print('routed; tracks', len(b.GetTracks()))
