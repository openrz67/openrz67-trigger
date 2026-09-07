#!/bin/sh
# Fetch STEP + WRL 3D models for every LCSC part in the BOM into openrz67.3dshapes/.
#
# WRL files are committed (small, used for rendering); STEP files are gitignored and
# only needed for tools/export_step.sh. Requires network.
#
# Parts without a model on LCSC are reported and skipped, so one missing model does
# not abort the run.
set -u
cd "$(dirname "$0")/.."

if command -v easyeda2kicad >/dev/null 2>&1; then E=easyeda2kicad
elif command -v uvx >/dev/null 2>&1; then E="uvx easyeda2kicad"
elif command -v pipx >/dev/null 2>&1; then E="pipx run easyeda2kicad"
else
  [ -x .venv-tools/bin/easyeda2kicad ] || { python3 -m venv .venv-tools && .venv-tools/bin/pip install -q easyeda2kicad; }
  E=.venv-tools/bin/easyeda2kicad
fi

BOM=out/openrz67-bom.csv
[ -f "$BOM" ] || { echo "$BOM missing; run tools/regen.sh first" >&2; exit 1; }

# Read the LCSC column by header name rather than by position, so reordering the
# BOM fields in regen.sh cannot silently empty this list.
ids=$(python3 - "$BOM" <<'PY'
import csv, sys
with open(sys.argv[1], newline="", encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
col = next((c for c in (rows[0].keys() if rows else []) if c.strip().upper().startswith("LCSC")), None)
if not col:
    sys.exit("no LCSC column in BOM")
seen = []
for r in rows:
    v = (r.get(col) or "").strip()
    if v.startswith("C") and v[1:].isdigit() and v not in seen:
        seen.append(v)
print("\n".join(sorted(seen)))
PY
) || exit 1

missing=""
for id in $ids; do
  if ! $E --3d --lcsc_id "$id" --output ./openrz67 --overwrite >/dev/null 2>&1; then
    missing="$missing $id"
  fi
done

if [ -n "$missing" ]; then
  echo "no 3D model on LCSC for:$missing" >&2
  echo "(the board still renders and exports; those parts are simply absent)" >&2
fi
echo "3D models in openrz67.3dshapes/: $(ls openrz67.3dshapes/*.wrl 2>/dev/null | wc -l | tr -d ' ') wrl"
