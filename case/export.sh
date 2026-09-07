#!/usr/bin/env bash
# Export base + lid + light pipe to STL, then rebuild the slicer project .3mf.
# The light pipe (openrz67-lightpipe.stl) prints in CLEAR/transparent filament; base and
# lid in normal opaque filament. The lid text (on by default) is a debossed pocket in the
# top face; colour it with a filament change at Z = 0.6mm (lid printed upside-down).
#
# Usage:
#   ./export.sh              # -> stl/ + openrz67-case.3mf
#   ./export.sh my-stl       # custom output dir (skips the .3mf unless it is stl/)
#
# Optional overrides, read by openrz67_case.py from the environment:
#   LID_TEXT_SHOW=false  ./export.sh    # turn the lid text OFF (on by default; the
#                                        # strings/sizes are the lid_texts constant)
#   SNAP_TEST=true      ./export.sh    # also export a corner test pair for tuning the snap
#   PCB_T=1.0            ./export.sh    # PCB thickness (sets the base/lid split height)
set -euo pipefail
cd "$(dirname "$0")"

OUTDIR="${1:-stl}"
command -v uv >/dev/null 2>&1 || { echo "uv not found (https://docs.astral.sh/uv/)" >&2; exit 1; }

OUTDIR="$OUTDIR" uv run openrz67_case.py
OUTDIR="$OUTDIR" uv run camera_plug.py

# Rebuild the Bambu/Orca project .3mf by swapping the fresh STLs into the hand-made
# template (bambu-template.3mf), keeping the print profile + plate layout + filament
# assignment (the light pipe stays on its clear filament). Disable with MAKE_3MF=false.
MAKE_3MF="${MAKE_3MF:-true}"
if [ "$MAKE_3MF" = "true" ] && [ -f bambu-template.3mf ]; then
  echo "==> project 3mf  ->  openrz67-case.3mf"
  python3 make_3mf.py --stl-dir "$OUTDIR" --out openrz67-case.3mf
fi
