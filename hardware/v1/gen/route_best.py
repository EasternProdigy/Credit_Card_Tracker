#!/usr/bin/env python3
"""Run N Freerouting jobs in parallel on the same DSN, import each SES into a copy of the board,
count real unconnected items with kicad-cli DRC, keep the best. Usage: route_best.py N passes"""
import os, re, shutil, subprocess, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__)); V1 = os.path.join(HERE, '..')
PCB = os.path.join(V1, 'card_v1.kicad_pcb'); R = os.path.join(V1, 'route'); os.makedirs(R, exist_ok=True)
N, passes = int(sys.argv[1]), sys.argv[2]
JAR = os.path.expanduser('~/tools/freerouting-2.5.0.jar')
b = pcbnew.LoadBoard(PCB); DSN = os.path.join(R, 'card_v1.dsn'); assert pcbnew.ExportSpecctraDSN(b, DSN)
t = open(DSN).read()
t = re.sub(r'\(net GND\s*\(pins[^)]*\)\s*\)', '', t); t = re.sub(r'(\(class \S+[^()]*?)\bGND\b', r'\1', t)
t = t.replace('(via "Via[0-1]_500:250_um" "Via[0-1]_250:150_um")', '(via "Via[0-1]_500:250_um")')
open(DSN, 'w').write(t)
procs = [subprocess.Popen(['java', '-jar', JAR, '-de', DSN, '-do', os.path.join(R, f'run{i}.ses'), '-mp', passes, '-mt', '4'],
                          stdout=open(os.path.join(R, f'run{i}.log'), 'w'), stderr=subprocess.STDOUT) for i in range(N)]
for p in procs: p.wait()
best = None
for i in range(N):
    ses = os.path.join(R, f'run{i}.ses')
    if not os.path.exists(ses): continue
    bb = pcbnew.LoadBoard(PCB); pcbnew.ImportSpecctraSES(bb, ses); pcbnew.ZONE_FILLER(bb).Fill(bb.Zones())
    out = os.path.join(R, f'run{i}.kicad_pcb'); pcbnew.SaveBoard(out, bb)
    rpt = os.path.join(R, f'run{i}.rpt')
    subprocess.run(['kicad-cli', 'pcb', 'drc', '-o', rpt, out], capture_output=True)
    txt = open(rpt).read()
    unc = [blk for blk in txt.split('\n[') if blk.startswith('unconnected_items')]
    real = [u for u in unc if not re.search(r'Zone \[GND\].*\n.*Zone \[GND\]', u)]
    errs = len(re.findall(r'^\[(clearance|shorting_items|hole_clearance|track_width)\]', txt, re.M))
    score = len(real) * 10 + errs
    print(f'run{i}: unconnected {len(real)}, errors {errs}')
    if best is None or score < best[0]: best = (score, out, rpt)
shutil.copy(best[1], PCB); shutil.copy(best[2], os.path.join(R, 'best_drc.rpt'))
print('kept', os.path.basename(best[1]))
for f in os.listdir(R):
    if f.startswith('run') and f.endswith(('.kicad_pcb', '.kicad_pro', '.kicad_prl')): os.remove(os.path.join(R, f))
