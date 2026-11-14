Overnight session. I'm asleep until about 9am. Work without waiting on me. If something needs my decision, write it in docs/QUESTIONS_FOR_DWAYNE.md, pick the safest option, keep going.

EFFICIENCY RULES (important, I'm paying for every token)
- Read only what you need: grep or read line ranges, never dump whole datasheets or big files into context. Don't re-read a file you already read unless it changed.
- When you pull facts from a datasheet, save them once to design/pinmaps/ or design/notes/ and reuse that file instead of fetching again.
- Run sims and checks quietly; read only the summary or the errors.
- Batch independent tool calls. No long explanations to yourself; the log is where explanations go.
- Stop improving anything once a pass finds nothing meaningful. Diminishing returns = move on.

STEP 0: Merge handoff rev 0.5 from ~/Downloads/wallet-tracker-rev05/.
- Copy .claude/, scripts/, docs/log/, .gitignore, README.md.
- Merge CLAUDE.md (keep existing edits, add the "Logging (mandatory)" section).
- If git isn't set up, run bash scripts/install_git_hooks.sh. Commit.
- Follow the logging rules from here on. Commit after every task.

BUILD PHASE
1. Pin maps: every IC in design/netlist.yaml, mapped from the official datasheet or Nordic reference, saved to design/pinmaps/<part>.md with source and page. v1 = nRF54L15 QFN48.
2. v1 schematic (hierarchical: MCU+RF, Qi, charger+battery+protection, LDO+sense, NFC) per docs/03_schematic_spec.md and netlist.yaml. v1 is a DEV BOARD:
   - 0 ohm jumpers between every section; PPK2 break points on battery and 3.3 V
   - Test pads on every rail, rectifier output, battery, SWD, antenna feed
   - DNP pi match on the antenna, trim caps on the Qi tank, NFC tuning caps
   - Qi tank and trim caps in 0603; 10-pin 1.27 mm SWD header; optional battery connector
   ERC clean or every warning explained.
3. Footprints + 3D heights checked against docs/04_layout_constraints.md.
4. JLCPCB BOM with LCSC numbers, stock, basic/extended, substitutes: design/bom_v1_jlc.csv.
5. ngspice in KiCad: power path, Qi tank with 0603 values, battery divider. Compare with sims/results/.

ROUTING PHASE (on a git branch named overnight-routing; never touch main's PCB)
6. Board outline 85.60 x 53.98 mm R3.18, keepouts from docs/04, antenna region.
7. Placement: copy Nordic's nRF54L15 reference layout for the MCU, crystals, DCDC inductor and RF path as closely as possible. Keep the Qi section away from the antenna.
8. Hand-route the critical nets first: RF feed and match, crystals, DCDC loop, decoupling, Qi coil and rectifier (wide, short). Use Nordic's reference layout and TI's EVM layouts as the model; research their layout guidelines first.
9. Autoroute the rest with Freerouting (export Specctra DSN, run Freerouting, import the SES). Then clean it up by hand: no acute angles, no needless vias, solid ground pour with stitching vias, nothing under the antenna.
10. DRC with JLC's rules. Export gerbers to a review folder (don't order).

IMPROVE PHASE (max 3 passes, stop early if a pass finds nothing important)
Each pass, review your own work as a skeptical senior engineer:
- Recheck pin maps against datasheets, net names, values vs sources, footprint pads vs datasheet land patterns, polarity, power ratings, voltage ratings.
- Research known mistakes: Nordic DevZone, TI E2E, Everytag issues for these exact parts.
- Re-run ERC, DRC, sims. Fix what's wrong, log what you fixed and why. Note the improvement count; if it's near zero, stop.

FINAL: docs/MORNING_REPORT.md (one page): what's done, what's not, ERC/DRC status, what the improve passes caught, routing quality and the worst spots, open questions, and the first 5 things I should review. Then stop.

Hard rules: never delete my work, never push or order anything, no placeholder pin numbers, every value has a source. If a step is blocked, log why and move on.
