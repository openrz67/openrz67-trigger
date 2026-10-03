#!/bin/sh
# Export the assembled board as STEP (out/openrz67-nrf.step, gitignored ~20 MB).
# Needs the per-part .step models; fetches them if any are missing.
#
# Override the tool path if KiCad lives elsewhere:
#   KICAD_CLI=/usr/bin/kicad-cli tools/export_step.sh
set -eu
cd "$(dirname "$0")/.."

APP=/Applications/KiCad/KiCad.app/Contents
KICAD_CLI=${KICAD_CLI:-$(command -v kicad-cli || echo "$APP/MacOS/kicad-cli")}
[ -x "$KICAD_CLI" ] || { echo "kicad-cli not found; set KICAD_CLI" >&2; exit 1; }

for w in openrz67-nrf.3dshapes/*.wrl; do
  [ -f "${w%.wrl}.step" ] || { tools/fetch_3d.sh; break; }
done
"$KICAD_CLI" pcb export step --subst-models --no-dnp -f -o out/openrz67-nrf.step openrz67-nrf.kicad_pcb
