#!/usr/bin/env bash
# Export the v1 review package (not an order): gerbers (4 copper layers), drill, CPL (DNP excluded),
# BOM copy, schematic PDF, DRC report (schematic parity on) and a top render. Run from hardware/v1.
set -euo pipefail
R=review; rm -rf "$R/gerbers"; mkdir -p "$R/gerbers"
kicad-cli pcb export gerbers -o "$R/gerbers/" -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts card_v1.kicad_pcb
kicad-cli pcb export drill -o "$R/gerbers/" --excellon-separate-th card_v1.kicad_pcb
kicad-cli pcb export pos -o "$R/card_v1_cpl.csv" --format csv --units mm --side both --exclude-dnp card_v1.kicad_pcb
cp ../../design/bom_v1_jlc.csv "$R/"
kicad-cli sch export pdf -o "$R/card_v1_schematic.pdf" card_v1.kicad_sch
kicad-cli pcb drc --schematic-parity --severity-all -o "$R/drc_final.rpt" card_v1.kicad_pcb || true
kicad-cli pcb render -o "$R/board_top_render.png" --side top -w 2400 --height 1520 --quality basic card_v1.kicad_pcb
# JLC upload set (review/jlc/): gerber+drill zip, BOM of placed parts only, CPL with JLC's column names
# (Designator, Mid X, Mid Y, Rotation, Layer per JLC's KiCad assembly guide).
mkdir -p "$R/jlc"; rm -f "$R/jlc/"*
(cd "$R/gerbers" && zip -q -j "../jlc/card_v1_gerbers.zip" ./*)
python3 - "$R" <<'PY'
import csv, sys
R = sys.argv[1]
rows = [r for r in csv.DictReader(open(f'{R}/bom_v1_jlc.csv')) if r['DNP'] == 'no']
with open(f'{R}/jlc/card_v1_bom_jlc.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC', 'MPN'])
    asc = lambda t: t.encode('ascii', 'ignore').decode().strip()   # LCSC MPNs can carry CJK text; JLC's parser chokes
    for r in rows: w.writerow([asc(r['Comment']), r['Designator'], asc(r['Footprint']), r['LCSC'], asc(r['MPN'])])
with open(f'{R}/jlc/card_v1_cpl_jlc.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Val', 'Package', 'Mid X', 'Mid Y', 'Rotation', 'Layer'])
    placed = {d.strip() for r in rows for d in r['Designator'].split(',')}
    for r in csv.DictReader(open(f'{R}/card_v1_cpl.csv')):
        if r['Ref'] not in placed: continue          # e.g. TP19, a bare test pad: nothing to place
        w.writerow([r['Ref'], r['Val'], r['Package'], r['PosX'] + 'mm', r['PosY'] + 'mm', r['Rot'], r['Side'].capitalize()])
print('jlc bom lines', len(rows))
PY
