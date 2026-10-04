#!/bin/sh
# Rebuild the schematic and board from tools/design.py, then everything under out/.
#
# Run after any change to tools/design.py (or the generators / libraries). Close KiCad
# first: the generators overwrite openrz67-nrf.kicad_sch and openrz67-nrf.kicad_pcb.
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

PCB=openrz67-nrf.kicad_pcb
SCH=openrz67-nrf.kicad_sch
mkdir -p out/gerber

echo "==> schematic + board from tools/design.py"
python3 tools/gen_sch.py >/dev/null
"$KICAD_PY" tools/gen_pcb.py 2>&1 | grep -v wxApp || true

echo "==> gerbers + drill"
rm -f out/gerber/*
"$KICAD_CLI" pcb export gerbers \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts \
  --subtract-soldermask --use-drill-file-origin -o out/gerber/ "$PCB" >/dev/null
"$KICAD_CLI" pcb export drill --format excellon --excellon-units mm --drill-origin plot \
  --excellon-separate-th --generate-map --map-format gerberx2 -o out/gerber/ "$PCB" >/dev/null

echo "==> gerber zip"
rm -f out/openrz67-nrf-gerber.zip
(cd out/gerber && zip -q -X ../openrz67-nrf-gerber.zip ./*)

echo "==> position file"
"$KICAD_CLI" pcb export pos --format csv --units mm --side both --use-drill-file-origin \
  --exclude-dnp -o out/openrz67-nrf-pos.csv "$PCB" >/dev/null
# JLCPCB's CPL parser rejects KiCad's header names; rewrite to the layout the main board's
# file was accepted in (pcb/kicad/tools/regen.sh).
"$KICAD_PY" - out/openrz67-nrf-pos.csv <<'PY'
import csv, sys
p = sys.argv[1]
# Rotation added where JLCPCB's library orientation differs from the KiCad footprint.
# The TLP172AM offset is the one measured on the main board's order preview.
ROT_FIX = {
    "SMD-4_L4.6-W3.7-P2.54-LS7.0-BR": 90,
    # MY-2032-16 (BT1): preview put the wide notched foot on the 3.5 mm pad; datasheet has it on the 5.0 mm one
    "BAT-SMD_MY-2032-16": 180,
}
rows = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
with open(p, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in rows:
        rot = float(r["Rot"]) + ROT_FIX.get(r["Package"], 0)
        w.writerow([r["Ref"], f'{float(r["PosX"]):.3f}mm', f'{float(r["PosY"]):.3f}mm',
                    r["Side"].capitalize(), f'{rot % 360:g}'])
PY

echo "==> bill of materials"
"$KICAD_CLI" sch export bom \
  --fields 'Value,Reference,Footprint,LCSC,Manufacturer,MPN,${QUANTITY}' \
  --labels 'Comment,Designator,Footprint,LCSC Part #,Manufacturer,MPN,Qty' \
  --group-by 'Value,Footprint,LCSC' --ref-range-delimiter '' --exclude-dnp \
  -o out/openrz67-nrf-bom.csv "$SCH" >/dev/null
"$KICAD_PY" - out/openrz67-nrf-bom.csv <<'PY'
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
"$KICAD_CLI" sch export pdf -o out/openrz67-nrf-schematic.pdf "$SCH" >/dev/null

echo "==> renders"
"$KICAD_CLI" pcb render --side top    --width 1400 --height 1400 --zoom 0.95 --quality high \
  -o out/openrz67-nrf-top.png "$PCB" >/dev/null
"$KICAD_CLI" pcb render --side bottom --width 1400 --height 1400 --zoom 0.95 --quality high \
  -o out/openrz67-nrf-bottom.png "$PCB" >/dev/null

echo "==> checks"
"$KICAD_CLI" pcb drc --schematic-parity --severity-all -o out/drc.rpt "$PCB" >/dev/null
"$KICAD_CLI" sch erc --severity-all -o out/erc.rpt "$SCH" >/dev/null
grep -hE '\*\* (Found|ERC)' out/drc.rpt out/erc.rpt || true

fail=0
grep -q '^\*\* Found 0 unconnected pads' out/drc.rpt || { echo "FAIL: unconnected pads" >&2; fail=1; }
grep -qE '^ \*\* ERC messages: [0-9]+  Errors 0' out/erc.rpt || { echo "FAIL: ERC errors" >&2; fail=1; }
if grep -q '; error$' out/drc.rpt; then echo "FAIL: DRC errors" >&2; fail=1; fi
if [ "$fail" -eq 0 ]; then echo "==> out/ regenerated, no errors"; fi
exit "$fail"
