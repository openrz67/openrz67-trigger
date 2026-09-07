#!/bin/sh
# Regenerate everything under out/ from the KiCad sources, in one go.
#
# Run this after any change to openrz67.kicad_pcb or openrz67.kicad_sch, so the
# committed outputs and the check reports always describe the committed sources.
# Close KiCad first: tools/post_import.py rewrites the board and the project file
# in place.
#
# Override the tool paths if KiCad lives elsewhere:
#   KICAD_CLI=/usr/bin/kicad-cli KICAD_PY=/usr/bin/python3 tools/regen.sh
set -eu
cd "$(dirname "$0")/.."

APP=/Applications/KiCad/KiCad.app/Contents
KICAD_CLI=${KICAD_CLI:-$(command -v kicad-cli || echo "$APP/MacOS/kicad-cli")}
KICAD_PY=${KICAD_PY:-$APP/Frameworks/Python.framework/Versions/Current/bin/python3}
[ -x "$KICAD_CLI" ] || { echo "kicad-cli not found; set KICAD_CLI" >&2; exit 1; }
[ -x "$KICAD_PY" ]  || { echo "KiCad python not found; set KICAD_PY" >&2; exit 1; }

PCB=openrz67.kicad_pcb
SCH=openrz67.kicad_sch
mkdir -p out/gerber

echo "==> design rules, net classes, zone fill"
"$KICAD_PY" tools/post_import.py "$PCB" >/dev/null

echo "==> gerbers + drill"
rm -f out/gerber/*.gbr out/gerber/*.gbl out/gerber/*.gtl out/gerber/*.gbs out/gerber/*.gts \
      out/gerber/*.gbp out/gerber/*.gtp out/gerber/*.gbo out/gerber/*.gto out/gerber/*.gm1 \
      out/gerber/*.drl out/gerber/*.gbrjob
# Gerbers and drill share the position file's origin (the aux/drill origin at the
# board's top-left corner), so all three fab files are in one frame and the drill
# files diff directly against the rev-1 archive.
"$KICAD_CLI" pcb export gerbers \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts \
  --subtract-soldermask --use-drill-file-origin -o out/gerber/ "$PCB" >/dev/null
"$KICAD_CLI" pcb export drill --format excellon --excellon-units mm --drill-origin plot \
  --excellon-separate-th --generate-map --map-format gerberx2 -o out/gerber/ "$PCB" >/dev/null

echo "==> gerber zip"
rm -f out/openrz67-gerber.zip
( cd out && zip -qrX openrz67-gerber.zip gerber )

echo "==> position file"
"$KICAD_CLI" pcb export pos --format csv --units mm --side both --exclude-dnp \
  --use-drill-file-origin -o out/openrz67-pos.csv "$PCB" >/dev/null
# JLCPCB's CPL parser wants its own header names and rejects KiCad's; rewrite in
# place to the layout of the rev-1 file it accepted (same origin, same Y sign).
"$KICAD_PY" - out/openrz67-pos.csv <<'PY'
import csv, sys
p = sys.argv[1]
# Per-footprint rotation correction (degrees, counter-clockwise) added to the KiCad angle
# where JLCPCB's library orientation differs from the KiCad footprint, so their order
# preview shows the part as KiCad does and their engineers have nothing to re-orient.
# Derived from the preview on 2026-09-07 (pin-1 dot vs out/openrz67-top.png); the rev-1
# order had the same U1 offset and JLCPCB corrected it against the silkscreen mark.
ROT_FIX = {
    "QFN-32_L5.0-W5.0-P0.50-BL-EP3.7": 90,  # ESP32-C3 (U1): preview pin 1 top-left, KiCad bottom-left
    "SMD-4_L4.6-W3.7-P2.54-LS7.0-BR": 90,   # TLP172AM (U5/U6): preview leads top/bottom, pin 1 top-right
}
rows = list(csv.DictReader(open(p, newline="")))
with open(p, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in rows:
        rot = float(r["Rot"]) + ROT_FIX.get(r["Package"], 0)
        w.writerow([r["Ref"], f'{float(r["PosX"]):.3f}mm', f'{float(r["PosY"]):.3f}mm',
                    r["Side"].capitalize(), f'{rot % 360:g}'])
PY

echo "==> bill of materials"
# --ref-range-delimiter '' lists every designator explicitly, which is the form
# JLCPCB accepted for the rev-1 order; ranges like "C3-C7" are not documented as
# supported by their BOM parser.
"$KICAD_CLI" sch export bom \
  --fields 'Value,Reference,Footprint,Supplier Part,Manufacturer,Manufacturer Part,${QUANTITY}' \
  --labels 'Comment,Designator,Footprint,LCSC Part #,Manufacturer,MPN,Qty' \
  --group-by 'Value,Footprint,Supplier Part' --ref-range-delimiter '' --exclude-dnp \
  -o out/openrz67-bom.csv "$SCH" >/dev/null
# JLCPCB's BOM parser looks for these four leading column names; the footprint column
# is display-only, so drop KiCad's library prefix to match the rev-1 file it accepted.
"$KICAD_PY" - out/openrz67-bom.csv <<'PY'
import csv, sys
p = sys.argv[1]
rows = list(csv.reader(open(p, newline="", encoding="utf-8")))
with open(p, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for i, r in enumerate(rows):
        if i and ":" in r[2]:
            r[2] = r[2].split(":", 1)[1]
        w.writerow(r)
PY

echo "==> schematic pdf"
"$KICAD_CLI" sch export pdf -o out/openrz67-schematic.pdf "$SCH" >/dev/null

echo "==> renders"
"$KICAD_CLI" pcb render --side top    --width 1768 --height 984 --quality high \
  -o out/openrz67-top.png "$PCB" >/dev/null
"$KICAD_CLI" pcb render --side bottom --width 1768 --height 984 --quality high \
  -o out/openrz67-bottom.png "$PCB" >/dev/null

echo "==> checks"
"$KICAD_CLI" pcb drc --schematic-parity --severity-all -o out/drc.rpt "$PCB" >/dev/null
"$KICAD_CLI" sch erc --severity-all -o out/erc.rpt "$SCH" >/dev/null
grep -hE '\*\* (Found|ERC)' out/drc.rpt out/erc.rpt || true

# Gate on errors only. The remaining warnings are accepted and listed above:
# courtyard overlaps inherited from the fabricated rev-1 layout, and dangling
# wire ends inherited from the EasyEDA drawing. Note that --exit-code-violations
# counts warnings as violations too, so it cannot serve as this gate.
fail=0
grep -q '^\*\* Found 0 unconnected pads' out/drc.rpt || { echo "FAIL: unconnected pads" >&2; fail=1; }
grep -qE '^ \*\* ERC messages: [0-9]+  Errors 0' out/erc.rpt || { echo "FAIL: ERC errors" >&2; fail=1; }
if grep -q '; error$' out/drc.rpt; then echo "FAIL: DRC errors" >&2; fail=1; fi
if [ "$fail" -eq 0 ]; then echo "==> out/ regenerated, no errors"; fi
exit "$fail"
