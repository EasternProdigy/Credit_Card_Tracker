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
