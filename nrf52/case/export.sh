#!/usr/bin/env bash
# Export base + lid to stl/ and rebuild the slicer project openrz67-nrf-case.3mf from
# qidi-template.3mf (print profile and plate layout kept, meshes swapped by ../../case/make_3mf.py).
#
# Usage:
#   ./export.sh
#   SNAP_TEST=true ./export.sh    # also export a corner test pair (not in the .3mf)
set -euo pipefail
cd "$(dirname "$0")"
command -v uv >/dev/null 2>&1 || { echo "uv not found (https://docs.astral.sh/uv/)" >&2; exit 1; }

OUTDIR=stl uv run openrz67_nrf_case.py
python3 ../../case/make_3mf.py --template qidi-template.3mf --stl-dir stl --out openrz67-nrf-case.3mf \
  --objects openrz67-nrf-base.stl,openrz67-nrf-lid.stl
